"""
GA pilot sonucunun genellenip genellenmedigini hizlica kontrol eder (CP4 on kontrolu).

Elle tasarlanmis FIS ile results/ga/<tag>_best.json'daki GA-FIS, GA'nin hic gormedigi
TEST seed'leriyle (varsayilan 1-10) ve tam sure (300 s) ile her iki egitim senaryosunda
kosturulur. Gun 4'teki asil karsilastirma 30 test seed'i + Wilcoxon ile yapilacak.

Calistirma: python -m experiments.proposed.ga_pilot_holdout --tag ga_pilot --seeds 10
"""
from __future__ import annotations

import argparse
import json
import os
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

from src.fuzzy.ga_tuning import (FitnessWeights, _eval_job, default_genome, run_metrics,
                                 train_scenarios)

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="ga_pilot")
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--workers", type=int, default=None)
    a = ap.parse_args()
    with open(os.path.join(ROOT, "results", "ga", f"{a.tag}_best.json"), encoding="utf-8") as f:
        best = np.array(json.load(f)["best_genome"])
    sc = train_scenarios(300.0)
    seeds = range(1, a.seeds + 1)
    variants = {"Elle FIS": default_genome(), "GA-FIS": best}
    keys = [(v, n, s) for v in variants for n in sc for s in seeds]
    jobs = [(variants[v], sc[n], s, "FUZZY") for v, n, s in keys]
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        res = list(ex.map(_eval_job, jobs))
    w = FitnessWeights()
    rows = [{"variant": v, "scenario": n, "seed": s, "fitness": run_metrics(m, sc[n], w),
             **{k: m[k] for k in ("completion_rate", "completion_urgent", "avg_delay")}}
            for (v, n, s), m in zip(keys, res)]
    df = pd.DataFrame(rows)
    out = os.path.join(ROOT, "results", "tables", f"{a.tag}_holdout_s{a.seeds}.csv")
    df.to_csv(out, index=False)
    sm = df.groupby(["scenario", "variant"])[["fitness", "completion_rate", "completion_urgent",
                                             "avg_delay"]].mean()
    print(sm.round(4).to_string())


if __name__ == "__main__":
    main()
