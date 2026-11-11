"""
Checkpoint 3 - ilk sonuclar: tek senaryo (150 arac/km, 30 m/s), tum yontemler, 10 seed.

Calistirma:  python -m experiments.baseline.cp3_first_results [--seeds 10]
Ciktilar:    results/tables/cp3_first_results_raw.csv
             results/tables/cp3_first_results_summary.csv
             results/figures/cp3_completion.png, cp3_outcomes.png
"""
from __future__ import annotations

import argparse
import os

import numpy as np
import pandas as pd

from src.sim import METHODS, SimConfig
from src.sim.experiment import STYLE, run_grid, summarize

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TAB = os.path.join(ROOT, "results", "tables")
FIG = os.path.join(ROOT, "results", "figures")
METRICS = ["completion_rate", "completion_urgent", "avg_delay", "avg_delay_completed",
           "avg_queue_wait", "offload_ratio", "frac_fail_upload", "frac_fail_link",
           "frac_dropped_queue", "frac_late", "frac_fail_result", "wall_s"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--density", type=float, default=150)
    ap.add_argument("--speed", type=float, default=30)
    a = ap.parse_args()
    base = SimConfig(density=a.density, mean_speed=a.speed)
    df = run_grid("density", [a.density], METHODS, range(1, a.seeds + 1), base)
    os.makedirs(TAB, exist_ok=True)
    df.to_csv(os.path.join(TAB, "cp3_first_results_raw.csv"), index=False)
    sm = summarize(df, ["method"], METRICS).set_index("method").loc[list(METHODS)].reset_index()
    sm.to_csv(os.path.join(TAB, "cp3_first_results_summary.csv"), index=False)

    show = pd.DataFrame({
        "Yöntem": sm.method,
        "Tamamlama": [f"{m:.3f} ± {c:.3f}" for m, c in zip(sm.completion_rate_mean, sm.completion_rate_ci95)],
        "Acil tamamlama": [f"{m:.3f}" for m in sm.completion_urgent_mean],
        "Gecikme (s)": [f"{m:.2f} ± {c:.2f}" for m, c in zip(sm.avg_delay_mean, sm.avg_delay_ci95)],
        "Gecikme-tamamlanan (s)": [f"{m:.2f}" for m in sm.avg_delay_completed_mean],
        "Kuyruk bekleme (s)": [f"{m:.2f}" for m in sm.avg_queue_wait_mean],
        "Bağlantı kopması": [f"{m:.3f}" for m in sm.frac_fail_link_mean],
        "Kuyruktan düşen": [f"{m:.3f}" for m in sm.frac_dropped_queue_mean],
    })
    md = show.to_markdown(index=False)
    with open(os.path.join(TAB, "cp3_first_results_summary.md"), "w", encoding="utf-8") as f:
        f.write(f"Senaryo: {a.density:g} araç/km, {a.speed:g} m/s, {a.seeds} seed, "
                f"değerler ortalama ± %95 GA\n\n{md}\n")
    print(md)
    _plots(sm)


def _plots(sm: pd.DataFrame):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    os.makedirs(FIG, exist_ok=True)
    order = sm.sort_values("completion_rate_mean")
    fig, ax = plt.subplots(figsize=(6.4, 3.4), dpi=150)
    y = np.arange(len(order))
    ax.barh(y, order.completion_rate_mean, xerr=order.completion_rate_ci95, height=0.6,
            color=[STYLE[m]["color"] for m in order.method], capsize=3,
            error_kw=dict(elinewidth=1, ecolor="#52514e"))
    for yi, v in zip(y, order.completion_rate_mean):
        ax.text(v + 0.02, yi, f"{v:.2f}", va="center", fontsize=8, color="#0b0b0b")
    ax.set_yticks(y, order.method)
    ax.set_xlim(0, 1.08)
    ax.set_xlabel("Görev tamamlama oranı (ortalama ± %95 GA)")
    ax.set_title("CP3 ilk sonuçlar: 150 araç/km, 30 m/s", fontsize=10, loc="left")
    ax.grid(True, axis="x", color="#e6e5e0", lw=0.8)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "cp3_completion.png"))
    plt.close(fig)

    # Gorev sonuc dagilimi: neden basarisiz oluyor?
    parts = [("completion_rate", "Tamamlandı", "#2a78d6"),
             ("frac_dropped_queue", "Kuyrukta süre doldu", "#eda100"),
             ("frac_fail_link", "Bağlantı koptu", "#eb6834"),
             ("frac_fail_upload", "Yükleme başarısız", "#6250d6"),
             ("frac_late", "Geç teslim", "#e87ba4"),
             ("frac_fail_result", "Sonuç iletilemedi", "#1baf7a")]
    sm2 = sm.set_index("method").loc[list(METHODS)]
    fig, ax = plt.subplots(figsize=(6.8, 3.6), dpi=150)
    left = np.zeros(len(sm2))
    y = np.arange(len(sm2))[::-1]
    for col, lab, colr in parts:
        v = sm2[f"{col}_mean"].to_numpy()
        ax.barh(y, v, left=left, height=0.6, color=colr, label=lab,
                edgecolor="#fcfcfb", linewidth=1.5)
        left += v
    ax.set_yticks(y, sm2.index)
    ax.set_xlim(0, 1)
    ax.set_xlabel("Görevlerin payı")
    ax.set_title("Görev sonuçlarının dağılımı (150 araç/km, 30 m/s)", fontsize=10, loc="left")
    ax.legend(frameon=False, fontsize=7, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.22))
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "cp3_outcomes.png"))
    plt.close(fig)


if __name__ == "__main__":
    main()
