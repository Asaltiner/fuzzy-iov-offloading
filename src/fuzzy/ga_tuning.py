"""
Ozgun katki (Checkpoint 4): Genetik Algoritma ile uyelik fonksiyonu (MF) ayari -> GA-FIS.

Ne degisiyor?
  Elle tasarlanmis FIS'te her girdinin MF kirilma noktalari esit aralikli
  (0.25, 0.5, 0.5, 0.75). GA-FIS'te bu 4 girdi x 4 nokta = 16 gen, simulasyondaki
  performansa gore Genetik Algoritma ile ayarlanir. Kural tabani (81 kural), cikarim
  (Mamdani min/max) ve durulastirma (centroid) DEGISMEZ; yalnizca MF sekli degisir.
  Boylece gozlenen fark yalnizca MF ayarina atfedilebilir.

Neden?
  * Makale, MF ve kurallarin GA/DRL ile otomatik ayarini gelecek calisma olarak oneriyor.
  * Makale MF parametrelerini vermiyor; bizim esit aralikli secimimiz keyfi bir varsayim.
  * Mesafe ve hiz MF'leri hem edge seciminde (com_score) hem EN kuyrugunda kullaniliyor;
    MF sekli iki asamayi birlikte etkiliyor.

Kromozom (gercek kodlu, normalize [0, 1]):
  [d1 d2 d3 d4 | v1 v2 v3 v4 | s1 s2 s3 s4 | p1 p2 p3 p4]
  sira = fis.INPUTS (distance, speed, size, priority). Her girdi icin:
    low = yamuk(0, 0, b1, b2), medium = ucgen(b1, (b2+b3)/2, b4), high = yamuk(b3, b4, 1, 1)
  Onarim (repair): her 4'lu grup siralanir, [MARGIN, 1-MARGIN] araligina kirpilir ve
  ardisik noktalar arasinda en az MIN_GAP birakilir -> MF'ler her zaman gecerli.

Uygunluk (fitness), egitim senaryolari x egitim seed'leri ortalamasi:
  F = CR + lambda_u * CR_acil - lambda_d * (gecikme / D_ort)
    CR       : gorev tamamlama orani
    CR_acil  : p >= 0.7 olan acil gorevlerin tamamlama orani (bulanik kuyrugun asil etkisi)
    gecikme  : son teslim sinirli ortalama gecikme, D_ort ortalama goreli son teslim suresi
  Ayni seed'ler tum bireylerde kullanilir (ortak rastgele sayilar) -> bireyler arasi fark
  rastgelelikten degil MF'lerden gelir.

Asiri uyumu (overfitting) onlemek icin EGITIM seed'leri (101...) ile Gun 4'teki TEST
seed'leri (1...30) ayridir. GA test seed'lerini hic gormez.

GA operatorleri: turnuva secimi (k=3), BLX-alpha caprazlama, Gauss mutasyonu,
elitizm (en iyi 2 birey aynen aktarilir). Baslangic populasyonuna elle tasarlanmis
FIS de eklenir (seeding): GA en kotu ihtimalle baseline'i korur.

Kullanim:
  python -m src.fuzzy.ga_tuning --smoke                 # ~1 dk, kod kontrolu
  python -m src.fuzzy.ga_tuning --pop 16 --gens 12 --tag ga_pilot   # Gun 3 pilot
  python -m src.fuzzy.ga_tuning --pop 24 --gens 20 --seeds 101 102 103 104 105 \
         --adaptive --ga-seed 1 --tag ga_full_s1                      # Gun 4 tam kosu
Ciktilar: results/ga/<tag>_history.csv, <tag>_best.json, results/figures/<tag>_*.png
"""
from __future__ import annotations

import argparse
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass, field

import numpy as np

from .fis import INPUTS, FuzzyPrioritySystem, default_breakpoints

N_GENES = 4 * len(INPUTS)
MARGIN = 0.02     # kirilma noktasi evren kenarina bu kadar yaklasabilir
MIN_GAP = 0.02    # ardisik kirilma noktalari arasi en kucuk fark


# ---------------------------------------------------------------- kodlama
def default_genome() -> np.ndarray:
    bp = default_breakpoints()
    return np.concatenate([bp[k] for k in INPUTS])


def repair(genome: np.ndarray) -> np.ndarray:
    """Her girdinin 4 genini sirala, sinirla ve rampalara en az MIN_GAP genislik birak.

    b1<b2 (low'un inen rampasi) ve b3<b4 (high'in cikan rampasi) icin MIN_GAP zorunlu;
    b2 == b3 serbest (medium ucgeninin tepesi (b2+b3)/2). Varsayilan genom
    (0.25, 0.5, 0.5, 0.75) onarimdan degismeden gecer.
    """
    g = np.clip(np.asarray(genome, dtype=float).copy(), 0.0, 1.0)
    gaps = (MIN_GAP, 0.0, MIN_GAP)
    for i in range(len(INPUTS)):
        b = np.sort(g[4 * i:4 * i + 4])
        b = np.clip(b, MARGIN, 1.0 - MARGIN - 2 * MIN_GAP)
        for k in range(1, 4):
            b[k] = max(b[k], b[k - 1] + gaps[k - 1])
        g[4 * i:4 * i + 4] = b
    return g


def decode(genome: np.ndarray) -> dict[str, np.ndarray]:
    g = repair(genome)
    return {k: g[4 * i:4 * i + 4].copy() for i, k in enumerate(INPUTS)}


def make_fis(genome: np.ndarray | None) -> FuzzyPrioritySystem:
    if genome is None:
        return FuzzyPrioritySystem()
    return FuzzyPrioritySystem(breakpoints=decode(genome))


# ---------------------------------------------------------------- uygunluk
def train_scenarios(sim_time: float = 200.0) -> dict:
    """Egitim senaryolari: normal yuk (CP3 noktasi) + yuksek yuk (docs/04 Bolum 7)."""
    from src.sim import SimConfig
    return {
        "normal": SimConfig(density=150.0, mean_speed=30.0, sim_time=sim_time),
        "highload": SimConfig(density=100.0, mean_speed=30.0, task_rate=0.035, sim_time=sim_time),
    }


@dataclass
class FitnessWeights:
    lambda_urgent: float = 0.5
    lambda_delay: float = 0.2


def mean_rel_deadline(cfg) -> float:
    """Ortalama goreli son teslim suresi D = base + per_mb*E[S] + urgency*E[1-p]."""
    return (cfg.deadline_base + cfg.deadline_per_mb * (cfg.size_min + cfg.size_max) / 2
            + cfg.deadline_urgency * 0.5)


def run_metrics(metrics: dict, cfg, w: FitnessWeights) -> float:
    """Tek bir simulasyon kosusunun uygunluk katkisi."""
    return (metrics["completion_rate"] + w.lambda_urgent * metrics["completion_urgent"]
            - w.lambda_delay * metrics["avg_delay"] / mean_rel_deadline(cfg))


def _eval_job(args):
    genome, cfg, seed, method = args
    from src.sim import run_simulation
    return run_simulation(method, cfg, seed, fis=make_fis(genome))


# ---------------------------------------------------------------- GA
@dataclass
class GAConfig:
    pop_size: int = 16
    generations: int = 12
    elite: int = 2
    tournament: int = 3
    cx_prob: float = 0.9
    blx_alpha: float = 0.3
    mut_prob: float = 1.0 / N_GENES * 2      # gen basina; birey basina ort. 2 gen
    mut_sigma: float = 0.08
    train_seeds: tuple = (101, 102, 103)
    sim_time: float = 200.0
    method: str = "FUZZY"
    seed: int = 2026                          # GA'nin kendi rastgeleligi
    # Uyarlanabilir mutasyon (Gun 4): en iyi birey `stall_gens` nesil iyilesmezse
    # sigma `sigma_up` katina cikar (en fazla `sigma_max`); iyilesince taban degere doner.
    adaptive: bool = False
    stall_gens: int = 3
    sigma_up: float = 1.5
    sigma_max: float = 0.25
    weights: FitnessWeights = field(default_factory=FitnessWeights)


class GeneticTuner:
    def __init__(self, cfg: GAConfig, workers: int | None = None, scenarios: dict | None = None):
        self.cfg = cfg
        self.rng = np.random.default_rng(cfg.seed)
        self.workers = workers or os.cpu_count() or 1
        self.scenarios = scenarios or train_scenarios(cfg.sim_time)
        self.cache: dict[tuple, dict] = {}
        self.history: list[dict] = []
        self.n_sims = 0
        self.sigma = cfg.mut_sigma

    # ---- toplu degerlendirme (paralel, onbellekli)
    @staticmethod
    def _key(g: np.ndarray) -> tuple:
        return tuple(np.round(repair(g), 4))

    def evaluate(self, pop: list[np.ndarray]) -> np.ndarray:
        todo = []
        for g in pop:
            k = self._key(g)
            if k not in self.cache and k not in [t[0] for t in todo]:
                todo.append((k, repair(g)))
        jobs, owners = [], []
        for k, g in todo:
            for name, sc in self.scenarios.items():
                for s in self.cfg.train_seeds:
                    jobs.append((g, sc, s, self.cfg.method))
                    owners.append((k, name))
        if jobs:
            if self.workers == 1:
                res = [_eval_job(j) for j in jobs]
            else:
                with ProcessPoolExecutor(max_workers=self.workers) as ex:
                    res = list(ex.map(_eval_job, jobs, chunksize=1))
            self.n_sims += len(jobs)
            per: dict[tuple, dict[str, list]] = {}
            for (k, name), m in zip(owners, res):
                per.setdefault(k, {}).setdefault(name, []).append(m)
            for k, d in per.items():
                self.cache[k] = self._aggregate(d)
        return np.array([self.cache[self._key(g)]["fitness"] for g in pop])

    def _aggregate(self, per_scen: dict[str, list]) -> dict:
        w = self.cfg.weights
        out, fits = {}, []
        for name, runs in per_scen.items():
            sc = self.scenarios[name]
            f = [run_metrics(m, sc, w) for m in runs]
            fits.extend(f)
            out[f"{name}_fitness"] = float(np.mean(f))
            for met in ("completion_rate", "completion_urgent", "avg_delay"):
                out[f"{name}_{met}"] = float(np.mean([m[met] for m in runs]))
        out["fitness"] = float(np.mean(fits))
        return out

    # ---- operatorler
    def _tournament(self, pop, fit) -> np.ndarray:
        idx = self.rng.choice(len(pop), size=self.cfg.tournament, replace=False)
        return pop[idx[np.argmax(fit[idx])]]

    def _crossover(self, a, b):
        if self.rng.random() > self.cfg.cx_prob:
            return a.copy(), b.copy()
        lo, hi = np.minimum(a, b), np.maximum(a, b)
        span = hi - lo
        al = self.cfg.blx_alpha
        c1 = self.rng.uniform(lo - al * span, hi + al * span)
        c2 = self.rng.uniform(lo - al * span, hi + al * span)
        return c1, c2

    def _mutate(self, g):
        m = self.rng.random(N_GENES) < self.cfg.mut_prob
        g = g.copy()
        g[m] += self.rng.normal(0.0, self.sigma, m.sum())
        return repair(g)

    def initial_population(self) -> list[np.ndarray]:
        pop = [default_genome()]                                   # seeding: elle tasarim
        while len(pop) < self.cfg.pop_size:
            pop.append(repair(self.rng.random(N_GENES)))
        return pop

    # ---- ana dongu
    def run(self, log=print) -> dict:
        c = self.cfg
        pop = self.initial_population()
        t0 = time.time()
        base_key = self._key(default_genome())
        best_so_far, stall = -np.inf, 0
        for gen in range(c.generations + 1):
            fit = self.evaluate(pop)
            order = np.argsort(-fit)
            best = pop[order[0]]
            if fit[order[0]] > best_so_far + 1e-9:
                best_so_far, stall = float(fit[order[0]]), 0
                self.sigma = c.mut_sigma
            else:
                stall += 1
                if c.adaptive and stall >= c.stall_gens:
                    self.sigma = min(self.sigma * c.sigma_up, c.sigma_max)
            rec = {"generation": gen, "best": float(fit[order[0]]), "mean": float(fit.mean()),
                   "std": float(fit.std()), "baseline": self.cache[base_key]["fitness"],
                   "n_sims": self.n_sims, "elapsed_s": time.time() - t0,
                   "sigma": self.sigma,
                   "best_genome": json.dumps([round(x, 4) for x in repair(best)])}
            self.history.append(rec)
            log(f"nesil {gen:2d}  en iyi {rec['best']:.4f}  ort {rec['mean']:.4f}  "
                f"baseline {rec['baseline']:.4f}  sigma {self.sigma:.3f}  "
                f"({rec['elapsed_s']:.0f} s, {self.n_sims} sim)")
            if gen == c.generations:
                break
            P = np.array(pop)
            new = [P[i].copy() for i in order[:c.elite]]              # elitizm
            while len(new) < c.pop_size:
                a, b = self._tournament(P, fit), self._tournament(P, fit)
                for ch in self._crossover(a, b):
                    if len(new) < c.pop_size:
                        new.append(self._mutate(ch))
            pop = new
        best_g = repair(pop[int(np.argmax(self.evaluate(pop)))])
        return {"best_genome": best_g.tolist(),
                "best_breakpoints": {k: v.tolist() for k, v in decode(best_g).items()},
                "best_detail": self.cache[self._key(best_g)],
                "baseline_detail": self.cache[base_key],
                "config": {**asdict(c), "weights": asdict(c.weights)},
                "n_sims": self.n_sims, "elapsed_s": time.time() - t0}


# ---------------------------------------------------------------- grafikler
def plot_history(history: list[dict], path: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    g = [h["generation"] for h in history]
    fig, ax = plt.subplots(figsize=(6.4, 4.0), dpi=150)
    ax.plot(g, [h["best"] for h in history], color="#2a78d6", marker="o", lw=2, label="En iyi birey")
    ax.plot(g, [h["mean"] for h in history], color="#1baf7a", marker="^", lw=2, label="Popülasyon ortalaması")
    ax.axhline(history[0]["baseline"], color="#52514e", ls="--", lw=1.2, label="Elle tasarlanmış FIS")
    ax.set_xlabel("Nesil")
    ax.set_ylabel("Uygunluk (eğitim seed'leri)")
    ax.grid(True, color="#e6e5e0", lw=0.8)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig.savefig(path)
    plt.close(fig)


def plot_mf_comparison(genome: np.ndarray, path: str) -> None:
    """Elle tasarlanmis ve GA ile ayarlanmis MF'leri yan yana ciz."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from .fis import IN_TERMS, UNIVERSE
    base, ga = make_fis(None), make_fis(genome)
    colors = ("#2a78d6", "#1baf7a", "#eb6834")
    fig, axes = plt.subplots(2, 2, figsize=(9, 6), dpi=150)
    for ax, name in zip(axes.ravel(), INPUTS):
        x = np.linspace(*UNIVERSE[name], 400)
        mb, mg = base.fuzzify(name, x), ga.fuzzify(name, x)
        for t in range(3):
            ax.plot(x, mb[:, t], color=colors[t], ls=":", lw=1.3)
            ax.plot(x, mg[:, t], color=colors[t], lw=2, label=IN_TERMS[t])
        ax.set_title(name, fontsize=10, loc="left")
        ax.set_ylim(-0.03, 1.05)
        ax.grid(True, color="#e6e5e0", lw=0.8)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
    axes[0, 0].legend(frameon=False, fontsize=8, title="düz: GA-FIS, noktalı: elle", title_fontsize=7)
    fig.tight_layout()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig.savefig(path)
    plt.close(fig)


# ---------------------------------------------------------------- CLI
def main():
    ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ap = argparse.ArgumentParser(description="GA ile MF kirilma noktasi optimizasyonu")
    ap.add_argument("--pop", type=int, default=16)
    ap.add_argument("--gens", type=int, default=12)
    ap.add_argument("--seeds", type=int, nargs="+", default=[101, 102, 103])
    ap.add_argument("--sim-time", type=float, default=200.0)
    ap.add_argument("--workers", type=int, default=None)
    ap.add_argument("--tag", default=None)
    ap.add_argument("--ga-seed", type=int, default=2026, help="GA'nin kendi rastgelelik seed'i")
    ap.add_argument("--adaptive", action="store_true", help="uyarlanabilir mutasyon")
    ap.add_argument("--smoke", action="store_true", help="kucuk ayarlarla hizli kontrol")
    a = ap.parse_args()
    import functools
    global print
    print = functools.partial(print, flush=True)  # noqa: A001  arka plan loglari icin
    if a.smoke:
        a.pop, a.gens, a.seeds, a.sim_time = 6, 2, [101], 80.0
    tag = a.tag or ("ga_smoke" if a.smoke else f"ga_p{a.pop}_g{a.gens}")
    cfg = GAConfig(pop_size=a.pop, generations=a.gens, train_seeds=tuple(a.seeds),
                   sim_time=a.sim_time, seed=a.ga_seed, adaptive=a.adaptive)
    tuner = GeneticTuner(cfg, workers=a.workers)
    out = tuner.run()
    gdir = os.path.join(ROOT, "results", "ga")
    os.makedirs(gdir, exist_ok=True)
    import pandas as pd
    pd.DataFrame(tuner.history).to_csv(os.path.join(gdir, f"{tag}_history.csv"), index=False)
    with open(os.path.join(gdir, f"{tag}_best.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    fdir = os.path.join(ROOT, "results", "figures")
    plot_history(tuner.history, os.path.join(fdir, f"{tag}_convergence.png"))
    plot_mf_comparison(np.array(out["best_genome"]), os.path.join(fdir, f"{tag}_mf.png"))
    b, d = out["baseline_detail"], out["best_detail"]
    print(f"\nElle FIS uygunluk {b['fitness']:.4f} -> GA-FIS {d['fitness']:.4f} "
          f"({out['n_sims']} simulasyon, {out['elapsed_s']:.0f} s)")
    print("En iyi kirilma noktalari:")
    for k, v in out["best_breakpoints"].items():
        print(f"  {k:9s} {np.round(v, 3)}")


if __name__ == "__main__":
    main()
