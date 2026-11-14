"""
Ayrik zamanli IoV gorev aktarim simulatoru.

Her adimda (dt):
  1) araclar hareket eder,
  2) bu adimda uretilen gorevler icin yontem bir edge dugumu (EN) secer;
     gorev parca-parca ARQ ile Nakagami-m kanalindan EN'ye yuklenir,
  3) EN'ye ulasan gorevler kuyruga girer (ulasma aninda baglanti kopmussa gorev kaybolur),
  4) islemcisi bosalan EN siradaki gorevi secer: FIFO ya da bulanik oncelik skoru;
     son teslim zamani gecmis / yetisemeyecek gorevler kuyruktan dusurulur,
  5) islem bitince sonuc UN'ye geri gonderilir; baglanti kopmussa gorev basarisizdir.

Gorev, sonucu son teslim zamanindan once UN'ye ulasirsa "tamamlandi" sayilir.

Kullanim:
    from src.sim import SimConfig, run_simulation
    res = run_simulation("FUZZY", SimConfig(density=150), seed=1)
"""
from __future__ import annotations

import heapq
import time
import numpy as np

from src.fuzzy.fis import FuzzyPrioritySystem

from .channel import transfer
from .config import SimConfig
from .mobility import Highway
from .policies import make_policy
from .tasks import (COMPLETED, DROPPED, FAIL_LINK, FAIL_RESULT, FAIL_UPLOAD, LATE, PENDING,
                    STATE_NAMES, generate_tasks)  # noqa: F401


class Simulation:
    def __init__(self, method: str, cfg: SimConfig, seed: int,
                 fis: FuzzyPrioritySystem | None = None):
        self.cfg = cfg
        self.method = method
        # Ayri rastgele akislar: hareket ve gorevler yontemden bagimsiz (ortak rastgele sayilar)
        ss = np.random.SeedSequence(seed)
        r_mob, r_task, r_node, r_ch, r_dec = (np.random.default_rng(s) for s in ss.spawn(5))
        self.hw = Highway(cfg, r_mob)
        self.n = self.hw.n
        self.mips = r_node.choice(np.asarray(cfg.mips_levels), size=self.n, p=cfg.mips_probs)
        self.tasks = generate_tasks(cfg, self.n, r_task)
        self.rng_ch = r_ch
        self.rng_dec = r_dec
        # Olcum gurultusu icin ayri akis: diger akislari (hareket, gorev, kanal) degistirmez
        self.rng_noise = np.random.default_rng([seed, 7])
        self.fis = fis if fis is not None else FuzzyPrioritySystem()
        self.policy = make_policy(method, self)
        self.t = 0.0
        # EN durumlari
        self.queue: list[list[int]] = [[] for _ in range(self.n)]
        self.queued_mi = np.zeros(self.n)
        self.busy_task = np.full(self.n, -1)
        self.busy_until = np.zeros(self.n)
        self._cpu_events: list[tuple[float, int]] = []       # (bitis_zamani, arac)
        self._transit: list[tuple[float, int]] = []          # (varis_zamani, gorev)
        # istatistik
        self.n_neighbors_log: list[int] = []
        self.fis_calls = 0
        self.fis_time = 0.0

    # ---------- beacon bilgisi ----------
    def wait_time(self, idx=None) -> np.ndarray:
        """Bir gorevin EN'de islenmeye baslamadan once bekleyecegi tahmini sure (s)."""
        busy = np.maximum(self.busy_until - self.t, 0.0) * (self.busy_task >= 0)
        w = self.queued_mi / self.mips + busy
        return w if idx is None else w[idx]

    def noisy(self, x: np.ndarray) -> np.ndarray:
        """Beacon'dan okunan bulanik girdiye olcum gurultusu ekle (cfg.input_noise > 0 ise)."""
        s = self.cfg.input_noise
        if s <= 0:
            return x
        x = np.asarray(x, dtype=float)
        return np.maximum(x * (1.0 + self.rng_noise.normal(0.0, s, x.shape)), 0.0)

    # ---------- kuyruk islemleri ----------
    def _enqueue(self, j: int, task: int, t: float) -> None:
        self.tasks.arrive_t[task] = t
        self.queue[j].append(task)
        self.queued_mi[j] += self.tasks.mi[task]
        if self.busy_task[j] < 0:
            self._start_next(j, t)

    def _start_next(self, j: int, t: float) -> None:
        T = self.tasks
        q = self.queue[j]
        # Son teslim zamanina yetisemeyecek gorevleri dusur (tum yontemlerde ayni kural)
        keep = []
        for k in q:
            if t + T.mi[k] / self.mips[j] > T.deadline[k]:
                T.state[k] = DROPPED
                self.queued_mi[j] -= T.mi[k]
            else:
                keep.append(k)
        q[:] = keep
        if not q:
            self.busy_task[j] = -1
            return
        if self.policy.fuzzy_queue and len(q) > 1:
            pos = self._fuzzy_pick(j, q)
        else:
            pos = 0                                           # FIFO
        k = q.pop(pos)
        self.queued_mi[j] -= T.mi[k]
        T.start_t[k] = t
        fin = t + T.mi[k] / self.mips[j]
        self.busy_task[j] = k
        self.busy_until[j] = fin
        heapq.heappush(self._cpu_events, (fin, j))

    def _fuzzy_pick(self, j: int, q: list[int]) -> int:
        """EN kuyrugundaki gorevleri bulanik oncelik skoruna gore sirala, en yuksegi sec."""
        T = self.tasks
        idx = np.asarray(q)
        origins = T.origin[idx]
        dist = self.noisy(self.hw.dist(j, origins))
        rel_v = self.noisy(self.hw.rel_speed(j, origins))
        t0 = time.perf_counter()
        score = self.fis.evaluate(dist, rel_v, T.size[idx], T.priority[idx])
        self.fis_time += time.perf_counter() - t0
        self.fis_calls += len(idx)
        return int(np.argmax(score))   # esitlikte ilk gelen (FIFO'ya duser)

    def _finish(self, j: int, t: float) -> None:
        T = self.tasks
        k = self.busy_task[j]
        T.finish_t[k] = t
        i = T.origin[k]
        if i == j:                                            # yerel islem, sonuc iletimi yok
            T.delay[k] = t - T.gen_t[k]
        else:
            d = float(self.hw.dist(i, j))
            if d > self.cfg.comm_range:
                T.state[k] = FAIL_LINK
            else:
                ok, t_down = transfer(T.size[k] * self.cfg.result_ratio, d,
                                      self._n_neighbors(i), self.cfg, self.rng_ch)
                if not ok:
                    T.state[k] = FAIL_RESULT
                else:
                    T.delay[k] = t + t_down - T.gen_t[k]
        if T.state[k] == PENDING:
            T.state[k] = COMPLETED if T.gen_t[k] + T.delay[k] <= T.deadline[k] else LATE
        self.busy_task[j] = -1
        self._start_next(j, t)

    def _n_neighbors(self, i: int) -> int:
        return int((self.hw.dist(i) <= self.cfg.comm_range).sum() - 1)

    # ---------- yeni gorev ----------
    def _dispatch(self, task: int) -> None:
        T = self.tasks
        i = T.origin[task]
        d_all = self.hw.dist(i)
        mask = d_all <= self.cfg.comm_range
        mask[i] = False
        nb = np.flatnonzero(mask)
        self.n_neighbors_log.append(len(nb))
        if self.method == "LPA" or len(nb) == 0:
            j = i                                             # komsu yoksa yerelde isle
        else:
            j = self.policy.select(task, nb, d_all[nb])
        T.target[task] = j
        if j == i:
            self._enqueue(i, task, self.t)
            return
        ok, t_up = transfer(T.size[task], float(d_all[j]), len(nb), self.cfg, self.rng_ch)
        if not ok:
            T.state[task] = FAIL_UPLOAD
            T.delay[task] = np.nan
            return
        heapq.heappush(self._transit, (self.t + t_up, task))

    # ---------- ana dongu ----------
    def run(self) -> "Simulation":
        cfg, T = self.cfg, self.tasks
        n_steps = int(round(cfg.sim_time / cfg.dt))
        nxt = 0
        for step in range(1, n_steps + 1):
            self.t = step * cfg.dt
            self.hw.step(cfg.dt)
            # 1) yeni gorevler
            while nxt < len(T) and T.gen_t[nxt] <= self.t:
                self._dispatch(nxt)
                nxt += 1
            # 2) EN'ye varan gorevler
            while self._transit and self._transit[0][0] <= self.t:
                ta, k = heapq.heappop(self._transit)
                j = T.target[k]
                if float(self.hw.dist(T.origin[k], j)) > cfg.comm_range:
                    T.state[k] = FAIL_LINK                    # yukleme sirasinda menzilden cikti
                else:
                    self._enqueue(j, k, ta)
            # 3) islemi biten gorevler
            while self._cpu_events and self._cpu_events[0][0] <= self.t:
                tf, j = heapq.heappop(self._cpu_events)
                if self.busy_task[j] >= 0 and abs(self.busy_until[j] - tf) < 1e-9:
                    self._finish(j, tf)
        return self

    # ---------- metrikler ----------
    def metrics(self) -> dict:
        T, cfg = self.tasks, self.cfg
        sel = T.gen_t >= cfg.warmup
        st = T.state[sel]
        n = int(sel.sum())
        done = st == COMPLETED
        delays = T.delay[sel][done]
        offl = (T.target[sel] != T.origin[sel]) & (T.target[sel] >= 0)
        qwait = (T.start_t - T.arrive_t)[sel][done]
        # Son teslim sinirli gecikme: tamamlanamayan gorev, goreli son teslim suresiyle
        # (D = deadline - gen_t) cezalandirilir. Boylece cok gorev dusuren bir yontem
        # yalnizca "basarili gorevlerin gecikmesi" dusuk diye avantaj kazanmaz.
        rel_deadline = (T.deadline - T.gen_t)[sel]
        capped = np.where(done, np.minimum(T.delay[sel], rel_deadline), rel_deadline)
        out = {
            "method": self.method,
            "n_vehicles": self.n,
            "n_tasks": n,
            "completion_rate": float(done.mean()) if n else np.nan,
            "avg_delay": float(capped.mean()) if n else np.nan,
            "avg_delay_completed": float(delays.mean()) if done.any() else np.nan,
            "avg_queue_wait": float(np.nanmean(qwait)) if done.any() else np.nan,
            "offload_ratio": float(offl.mean()) if n else np.nan,
            "avg_neighbors": float(np.mean(self.n_neighbors_log)) if self.n_neighbors_log else 0.0,
            "fis_ms_per_eval": 1e3 * self.fis_time / self.fis_calls if self.fis_calls else np.nan,
        }
        # oncelige gore tamamlama: acil gorevler (p >= 0.7)
        urgent = T.priority[sel] >= 0.7
        out["completion_urgent"] = float(done[urgent].mean()) if urgent.any() else np.nan
        for code, name in STATE_NAMES.items():
            if code != COMPLETED:
                out[f"frac_{name}"] = float((st == code).mean()) if n else np.nan
        return out


def run_simulation(method: str, cfg: SimConfig | None = None, seed: int = 0,
                   fis: FuzzyPrioritySystem | None = None) -> dict:
    cfg = cfg or SimConfig()
    t0 = time.perf_counter()
    sim = Simulation(method, cfg, seed, fis=fis).run()
    m = sim.metrics()
    m.update(seed=seed, density=cfg.density, mean_speed=cfg.mean_speed,
             wall_s=time.perf_counter() - t0)
    return m


__all__ = ["Simulation", "run_simulation"]
