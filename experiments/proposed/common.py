"""Gun 4 (CP5) deneyleri icin ortak yardimcilar: varyant tanimi, paralel kosu, istatistik, grafik.

Varyant = (yontem, genom, FIS secenekleri). Ayni seed tum varyantlarda ayni trafik ve gorev
akisini urettigi icin (ortak rastgele sayilar) karsilastirmalar seed duzeyinde ESLESTIRILMISTIR.
"""
from __future__ import annotations

import json
import os
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TABLES = os.path.join(ROOT, "results", "tables")
FIGURES = os.path.join(ROOT, "results", "figures")
GA_DIR = os.path.join(ROOT, "results", "ga")

TEST_SEEDS = tuple(range(1, 31))       # GA'nin hic gormedigi test seed'leri
VAL_SEEDS = tuple(range(201, 211))     # GA seed'i secimi icin dogrulama seed'leri
METRICS = ("completion_rate", "completion_urgent", "avg_delay", "avg_delay_completed",
           "fis_ms_per_eval", "wall_s")

# dataviz referans paleti (src/sim/experiment.py ile ayni). Elle FIS = mavi, GA-FIS = turuncu.
COLORS = {"Elle FIS": "#2a78d6", "GA-FIS": "#eb6834", "NF": "#1baf7a", "FIFO kuyruk": "#6250d6",
          "Bisector": "#eda100", "MOM": "#e87ba4", "Sugeno": "#52514e"}
GRID = "#e6e5e0"


@dataclass(frozen=True)
class Variant:
    name: str
    method: str = "FUZZY"
    genome: tuple | None = None                 # None -> elle tasarlanmis MF'ler
    fis_kw: dict = field(default_factory=dict)  # inference / defuzz

    def make_fis(self):
        from src.fuzzy.fis import FuzzyPrioritySystem
        from src.fuzzy.ga_tuning import decode
        bp = decode(np.asarray(self.genome)) if self.genome is not None else None
        return FuzzyPrioritySystem(**({"breakpoints": bp} if bp else {}), **self.fis_kw)


def load_genome(tag: str) -> tuple:
    with open(os.path.join(GA_DIR, f"{tag}_best.json"), encoding="utf-8") as f:
        return tuple(json.load(f)["best_genome"])


def selected_genome() -> tuple:
    """ga_evaluate.py'nin dogrulama seed'leriyle sectigi GA-FIS genomu."""
    with open(os.path.join(GA_DIR, "ga_selected.json"), encoding="utf-8") as f:
        return tuple(json.load(f)["best_genome"])


def _job(args):
    variant, cfg, seed, extra = args
    from src.sim import run_simulation
    m = run_simulation(variant.method, cfg, seed, fis=variant.make_fis())
    m.update(variant=variant.name, **extra)
    return m


def run_jobs(jobs: list[tuple], workers: int | None = None) -> pd.DataFrame:
    """jobs: (Variant, SimConfig, seed, ekstra_sutunlar) listesi -> ham sonuc tablosu."""
    workers = workers or os.cpu_count() or 1
    if workers == 1:
        rows = [_job(j) for j in jobs]
    else:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            rows = list(ex.map(_job, jobs, chunksize=2))
    return pd.DataFrame(rows)


def fitness(df: pd.DataFrame, cfg) -> pd.Series:
    """GA'nin uygunluk fonksiyonunun (F) test verisinde hesaplanmasi."""
    from src.fuzzy.ga_tuning import FitnessWeights, mean_rel_deadline
    w = FitnessWeights()
    return (df.completion_rate + w.lambda_urgent * df.completion_urgent
            - w.lambda_delay * df.avg_delay / mean_rel_deadline(cfg))


def ci95(x) -> float:
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    if len(x) < 2:
        return np.nan
    return float(stats.t.ppf(0.975, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x)))


def paired_test(df: pd.DataFrame, a: str, b: str, metric: str, by: list[str]) -> pd.DataFrame:
    """Her grup icin b - a farki (seed bazinda eslestirilmis) ve iki yanli Wilcoxon testi.

    Holm-Bonferroni duzeltmesi grup sayisi uzerinden yapilir (coklu karsilastirma).
    """
    out = []
    for key, g in df.groupby(by):
        pa = g[g.variant == a].set_index("seed")[metric]
        pb = g[g.variant == b].set_index("seed")[metric]
        common = pa.index.intersection(pb.index)
        d = (pb[common] - pa[common]).to_numpy()
        row = dict(zip(by, key if isinstance(key, tuple) else (key,)))
        row.update({"metric": metric, "n": len(d), f"{a}_mean": pa[common].mean(),
                    f"{b}_mean": pb[common].mean(), "diff_mean": d.mean(), "diff_ci95": ci95(d),
                    "wins": int((d > 1e-12).sum()), "ties": int((np.abs(d) <= 1e-12).sum()),
                    "losses": int((d < -1e-12).sum())})
        if np.allclose(d, 0):
            row["p_wilcoxon"] = 1.0
        else:
            row["p_wilcoxon"] = float(stats.wilcoxon(d, zero_method="wilcox").pvalue)
        out.append(row)
    res = pd.DataFrame(out)
    # Holm-Bonferroni
    p = res.p_wilcoxon.to_numpy()
    order = np.argsort(p)
    m = len(p)
    adj = np.empty(m)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * p[i]))
        adj[i] = running
    res["p_holm"] = adj
    res["significant"] = res.p_holm < 0.05
    return res


def style_axes(ax):
    ax.grid(True, color=GRID, lw=0.8)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)


def fmt_p(p: float) -> str:
    return f"{p:.1e}" if p < 1e-3 else f"{p:.3f}"


def save(df: pd.DataFrame, name: str) -> str:
    os.makedirs(TABLES, exist_ok=True)
    path = os.path.join(TABLES, name)
    df.to_csv(path, index=False)
    return path
