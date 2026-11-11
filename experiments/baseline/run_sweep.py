"""
Yeniden uretim deneyleri E1 (yogunluk) ve E2 (hiz).

  E1: yogunluk {50,...,350} arac/km, hiz 30 m/s  -> Sek. 9 (gecikme), Sek. 11 (tamamlama)
  E2: ortalama hiz {10,...,50} m/s, 150 arac/km  -> Sek. 12 (tamamlama)

Calistirma:
  python -m experiments.baseline.run_sweep --exp density --reps 30
  python -m experiments.baseline.run_sweep --exp speed   --reps 30
Gun 2'de on sonuc icin --reps 5 ile calistirildi; Gun 3'te 30 tekrar kosulacak.
"""
from __future__ import annotations

import argparse
import os
import time

import pandas as pd

from src.sim import METHODS, SimConfig
from src.sim.experiment import plot_metric, run_grid, summarize

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TAB = os.path.join(ROOT, "results", "tables")
FIG = os.path.join(ROOT, "results", "figures")
PAPER = os.path.join(ROOT, "data", "paper_digitized")
METRICS = ["completion_rate", "completion_urgent", "avg_delay", "avg_delay_completed",
           "avg_queue_wait", "frac_fail_link", "frac_dropped_queue", "avg_neighbors", "wall_s"]

EXPS = {
    "density": dict(param="density", values=[50, 100, 150, 200, 250, 300, 350],
                    base=SimConfig(mean_speed=30.0), tag="e1_density",
                    figs=[("avg_delay", "fig9_delay_vs_density.csv", "Sek. 9 karşılığı"),
                          ("completion_rate", "fig11_completion_vs_density.csv", "Sek. 11 karşılığı")]),
    "speed": dict(param="mean_speed", values=[10, 20, 30, 40, 50],
                  base=SimConfig(density=150.0), tag="e2_speed",
                  figs=[("completion_rate", "fig12_completion_vs_speed.csv", "Sek. 12 karşılığı")]),
}


def _paper(fname):
    p = os.path.join(PAPER, fname)
    if not os.path.exists(p):
        return None
    df = pd.read_csv(p)
    return df if len(df) else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exp", choices=list(EXPS), required=True)
    ap.add_argument("--reps", type=int, default=30)
    ap.add_argument("--workers", type=int, default=None)
    a = ap.parse_args()
    e = EXPS[a.exp]
    t0 = time.time()
    df = run_grid(e["param"], e["values"], METHODS, range(1, a.reps + 1), e["base"], a.workers)
    os.makedirs(TAB, exist_ok=True)
    suffix = f"_r{a.reps}"
    df.to_csv(os.path.join(TAB, f"{e['tag']}_raw{suffix}.csv"), index=False)
    sm = summarize(df, ["method", e["param"]], METRICS)
    sm.to_csv(os.path.join(TAB, f"{e['tag']}_summary{suffix}.csv"), index=False)
    for metric, paper_csv, title in e["figs"]:
        plot_metric(sm, e["param"], metric,
                    os.path.join(FIG, f"{e['tag']}_{metric}{suffix}.png"),
                    title=f"{title} — {a.reps} tekrar, ortalama ± %95 GA",
                    paper=_paper(paper_csv))
    # tamlik icin acil gorev tamamlama grafigi
    plot_metric(sm, e["param"], "completion_urgent",
                os.path.join(FIG, f"{e['tag']}_completion_urgent{suffix}.png"),
                title=f"Acil görevler — {a.reps} tekrar")
    piv = sm.pivot(index="method", columns=e["param"], values="completion_rate_mean").loc[list(METHODS)]
    print(piv.round(3).to_string())
    print(f"{len(df)} koşu, {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
