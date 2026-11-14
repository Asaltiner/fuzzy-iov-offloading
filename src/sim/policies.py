"""
Gorev aktarim (offloading) yontemleri: edge secimi + kuyruk disiplini.

| Yontem      | Edge secimi                                         | EN kuyrugu   |
|-------------|-----------------------------------------------------|--------------|
| LPA         | yok, gorev yerelde islenir                          | FIFO         |
| RPA         | menzildeki rastgele arac                            | FIFO         |
| CHGO        | merkezi acgozlu: tahmini (bekleme+islem) en kucuk   | FIFO         |
| NF          | MIPS'e gore sirali listede "next fit"               | FIFO         |
| FUZZY       | beacon tabanli bulanik com_score (Denk. 5-9) + LET  | bulanik skor |
| FUZZY_FIFO  | FUZZY ile ayni secim, FIFO kuyruk (ablation)        | FIFO         |

Tum yontemler ayni bilgiye (beacon: konum, hiz, MIPS, kuyruk yuku) erisir; CHGO
ise merkezi denetleyicinin `chgo_update` saniyede bir guncelledigi eski (stale)
anlik goruntuyu kullanir.
"""
from __future__ import annotations

import numpy as np

from .channel import effective_rate, link_success_prob

METHODS = ("LPA", "RPA", "CHGO", "NF", "FUZZY", "FUZZY_FIFO")


class Policy:
    name = "BASE"
    fuzzy_queue = False

    def __init__(self, sim):
        self.sim = sim

    def select(self, task: int, nb: np.ndarray, d: np.ndarray) -> int:  # pragma: no cover
        raise NotImplementedError


class LPA(Policy):
    name = "LPA"

    def select(self, task, nb, d):
        return int(self.sim.tasks.origin[task])


class RPA(Policy):
    name = "RPA"

    def select(self, task, nb, d):
        return int(self.sim.rng_dec.choice(nb))


class CHGO(Policy):
    """Merkezi acgozlu (centralized greedy): islem gecikmesi en dusuk dugum.

    Hareketliligi ve kanal kalitesini dikkate almaz; durum bilgisi periyodik guncellenir.
    """
    name = "CHGO"

    def __init__(self, sim):
        super().__init__(sim)
        self.snapshot = np.zeros(sim.n)
        self.last_update = -np.inf

    def select(self, task, nb, d):
        s = self.sim
        if s.t - self.last_update >= s.cfg.chgo_update - 1e-9:
            self.snapshot = s.wait_time()
            self.last_update = s.t
        est = self.snapshot[nb] + s.tasks.mi[task] / s.mips[nb]
        return int(nb[np.argmin(est)])


class NF(Policy):
    """Next Fit: komsular MIPS'e gore azalan siralanir; son kullanilan EN'den itibaren
    kapasitesi uygun (bekleme < esik) ilk dugum secilir."""
    name = "NF"

    def __init__(self, sim):
        super().__init__(sim)
        self.last = np.full(sim.n, -1)

    def select(self, task, nb, d):
        s = self.sim
        i = s.tasks.origin[task]
        order = nb[np.lexsort((d, -s.mips[nb]))]          # MIPS azalan, esitlikte yakin olan
        wait = s.wait_time(order)
        start = 0
        if self.last[i] in order:
            start = int(np.where(order == self.last[i])[0][0])
        k = len(order)
        for off in range(k):
            idx = (start + off) % k
            if wait[idx] < s.cfg.nf_max_wait:
                self.last[i] = order[idx]
                return int(order[idx])
        self.last[i] = order[0]
        return int(order[0])


class FuzzySelect(Policy):
    """Makaledeki edge secimi (Bolum 2.2, Denk. 3-9) yorumu.

    Aday j icin uyelik dereceleri (0-1):
      MF_dist  : mesafe "low" (+0.5*"medium") -> yakin aday uzun sure menzilde kalir
      MF_speed : bagil hiz (Denk. 4) "low" (+0.5*"medium") -> benzer hizla ayni yonde
      MF_cpu   : MIPS seviyesi poor/average/good -> 0 / 0.5 / 1
      MF_load  : beacon'daki kuyruk beklemesinin kalan sureye orani dusukse 1
    com_score = sum(w_x * MF_x), w_x = I_x / sum(I)   (Denk. 5-9)
    Gorev boyutu ve onceligi tum adaylar icin ayni oldugundan secimi degistirmez;
    bu iki terim EN kuyrugundaki bulanik siralamada kullanilir.
    Ek olarak, tahmini toplam sure baglanti kopma suresinden (LET) ve son teslim
    zamanindan kisa olan adaylar tercih edilir ("baglanti suresi uzun + kaynak yeterli").
    """
    name = "FUZZY_FIFO"

    def __init__(self, sim):
        super().__init__(sim)
        w = sim.cfg.selection_weights
        tot = sum(w.values())
        self.w = {k: v / tot for k, v in w.items()}
        self.fis = sim.fis
        lv = np.asarray(sim.cfg.mips_levels)
        self.cpu_mf = {m: k / (len(lv) - 1) for k, m in enumerate(lv)}

    def scores(self, task, nb, d):
        s = self.sim
        T = s.tasks
        i = T.origin[task]
        mu_d = self.fis.fuzzify("distance", s.noisy(d))
        mu_v = self.fis.fuzzify("speed", s.noisy(s.hw.rel_speed(i, nb)))
        mf_dist = mu_d[:, 0] + 0.5 * mu_d[:, 1]
        mf_speed = mu_v[:, 0] + 0.5 * mu_v[:, 1]
        mf_cpu = np.array([self.cpu_mf[m] for m in s.mips[nb]])
        remaining = max(T.deadline[task] - s.t, 1e-3)
        wait = s.wait_time(nb)
        mf_load = np.clip(1.0 - wait / remaining, 0.0, 1.0)
        com = (self.w["distance"] * mf_dist + self.w["speed"] * mf_speed
               + self.w["cpu"] * mf_cpu + self.w["load"] * mf_load)
        # Tahmini sure ve fizibilite
        rate = effective_rate(len(nb), s.cfg)
        p = np.maximum(link_success_prob(d, s.cfg), 1e-3)
        est = T.size[task] / rate / p + wait + T.mi[task] / s.mips[nb]
        let = s.hw.link_expiration(i, nb)
        feasible = (let > est) & (s.t + est <= T.deadline[task])
        return com, feasible

    def select(self, task, nb, d):
        com, feasible = self.scores(task, nb, d)
        if feasible.any():
            com = np.where(feasible, com, -np.inf)
        return int(nb[np.argmax(com)])


class FuzzyFull(FuzzySelect):
    name = "FUZZY"
    fuzzy_queue = True


_REGISTRY = {"LPA": LPA, "RPA": RPA, "CHGO": CHGO, "NF": NF,
             "FUZZY": FuzzyFull, "FUZZY_FIFO": FuzzySelect}


def make_policy(name: str, sim) -> Policy:
    if name not in _REGISTRY:
        raise ValueError(f"Bilinmeyen yontem: {name}. Secenekler: {METHODS}")
    return _REGISTRY[name](sim)

