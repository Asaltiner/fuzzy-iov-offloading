"""Deney yardimcilari: parametre taramasi (paralel), ozet istatistik ve grafik."""
from __future__ import annotations

import os
from concurrent.futures import ProcessPoolExecutor
from itertools import product

import numpy as np
import pandas as pd
from scipy import stats

from .config import SimConfig
from .policies import METHODS
from .simulator import run_simulation

# dataviz referans paleti (validate_palette.js ile acik zeminde kontrol edildi).
# Renk yontemi takip eder (siraya gore degismez); her yontemin ayrica isaretcisi var.
STYLE = {
    "FUZZY":      dict(color="#2a78d6", marker="o", ls="-"),
    "CHGO":       dict(color="#eb6834", marker="s", ls="-"),
    "NF":         dict(color="#1baf7a", marker="^", ls="-"),
    "RPA":        dict(color="#eda100", marker="D", ls="-"),
    "LPA":        dict(color="#e87ba4", marker="v", ls="-"),
    "FUZZY_FIFO": dict(color="#6250d6", marker="o", ls="--"),
}
METRIC_LABEL = {
    "completion_rate": "Görev tamamlama oranı",
    "avg_delay": "Ortalama gecikme (s, son teslim sınırlı)",
    "avg_delay_completed": "Ortalama gecikme (s, yalnız tamamlanan)",
    "completion_urgent": "Acil görev (p ≥ 0.7) tamamlama oranı",
}
AXIS_LABEL = {"density": "Araç yoğunluğu (araç/km)", "mean_speed": "Ortalama hız (m/s)"}


def _job(args):
    method, cfg, seed = args
    return run_simulation(method, cfg, seed)


def run_grid(param: str, values, methods=METHODS, seeds=range(1, 6),
             base: SimConfig | None = None, workers: int | None = None) -> pd.DataFrame:
    """param in {'density', 'mean_speed', ...}; her (deger, yontem, seed) icin bir kosu."""
    base = base or SimConfig()
    jobs = [(m, base.with_(**{param: v}), s) for v, m, s in product(values, methods, seeds)]
    workers = workers or os.cpu_count() or 1
    if workers == 1:
        rows = [_job(j) for j in jobs]
    else:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            rows = list(ex.map(_job, jobs, chunksize=2))
    df = pd.DataFrame(rows)
    df[param] = [getattr(cfg, param) for _, cfg, _ in jobs]   # taranan parametre sutunu
    return df


def summarize(df: pd.DataFrame, by: list[str], metrics: list[str]) -> pd.DataFrame:
    """Ortalama, standart sapma ve %95 guven araligi yari genisligi (t dagilimi)."""
    out = []
    for key, g in df.groupby(by):
        row = dict(zip(by, key if isinstance(key, tuple) else (key,)))
        row["n_runs"] = len(g)
        for m in metrics:
            x = g[m].dropna().to_numpy()
            n = len(x)
            mean = x.mean() if n else np.nan
            sd = x.std(ddof=1) if n > 1 else np.nan
            half = stats.t.ppf(0.975, n - 1) * sd / np.sqrt(n) if n > 1 else np.nan
            row.update({f"{m}_mean": mean, f"{m}_std": sd, f"{m}_ci95": half})
        out.append(row)
    return pd.DataFrame(out)


def plot_metric(summary: pd.DataFrame, param: str, metric: str, path: str,
                methods=METHODS, title: str | None = None, paper: pd.DataFrame | None = None):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6.4, 4.2), dpi=150)
    for m in methods:
        s = summary[summary.method == m].sort_values(param)
        if s.empty:
            continue
        st = STYLE[m]
        ax.errorbar(s[param], s[f"{metric}_mean"], yerr=s[f"{metric}_ci95"], label=m,
                    color=st["color"], marker=st["marker"], ls=st["ls"], lw=2, ms=6,
                    capsize=3, elinewidth=1)
        if paper is not None and m in paper.columns and paper[m].notna().any():
            ax.plot(paper[paper.columns[0]], paper[m], color=st["color"], ls=":", lw=1.2,
                    marker=st["marker"], ms=4, mfc="none", alpha=0.8)
    ax.set_xlabel(AXIS_LABEL.get(param, param))
    ax.set_ylabel(METRIC_LABEL.get(metric, metric))
    if title:
        ax.set_title(title, fontsize=10, loc="left")
    ax.grid(True, color="#e6e5e0", lw=0.8)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.legend(frameon=False, fontsize=8, ncol=3, loc="best")
    if paper is not None and paper.drop(columns=paper.columns[0]).notna().any().any():
        ax.text(0.99, 0.01, "noktalı: makale (sayısallaştırılmış)", transform=ax.transAxes,
                ha="right", va="bottom", fontsize=7, color="#52514e")
    fig.tight_layout()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig.savefig(path)
    plt.close(fig)
