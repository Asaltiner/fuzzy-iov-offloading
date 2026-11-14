"""
Gun 4 / CP5 - Ablation: bulanik sistemin hangi bileseni sonucu ne kadar etkiliyor?

Varyantlar (hepsi ayni edge secimi ve ayni test seed'leri 1-30):
  Elle FIS    : Mamdani min/max + centroid (baseline)
  Bisector    : durulastirma = alanin ortaortayi (bisector)
  MOM         : durulastirma = maksimumlarin ortalamasi
  Sugeno      : sifirinci derece Sugeno (sabit cikti 0/25/50/75/100, agirlikli ortalama)
  FIFO kuyruk : EN kuyrugunda bulanik siralama kapali (FUZZY_FIFO)
  GA-FIS      : GA ile ayarlanmis MF'ler (Mamdani + centroid)

Ayrica hesaplama maliyeti: her FIS turu icin degerlendirme suresi (tek gorev ve 50'lik
kuyruk) ve scikit-fuzzy ile ayni sistemin suresi.

Calistirma: python -m experiments.proposed.ablation   (~3 dk, 2 cekirdek)
"""
from __future__ import annotations

import argparse
import os
import sys
import time

import numpy as np
import pandas as pd

from src.fuzzy.fis import INPUTS, UNIVERSE
from src.sim import SimConfig

from .common import (COLORS, FIGURES, TEST_SEEDS, Variant, ci95, fmt_p, paired_test, run_jobs,
                     save, selected_genome, style_axes)

SCEN = {"normal": SimConfig(density=150.0), "highload": SimConfig(density=100.0, task_rate=0.035)}
TITLE = {"normal": "Normal yük", "highload": "Yüksek yük"}


def variants():
    return [Variant("Elle FIS"), Variant("Bisector", fis_kw={"defuzz": "bisector"}),
            Variant("MOM", fis_kw={"defuzz": "mom"}), Variant("Sugeno", fis_kw={"inference": "sugeno"}),
            Variant("FIFO kuyruk", method="FUZZY_FIFO"), Variant("GA-FIS", genome=selected_genome())]


def timing(reps: int = 300) -> pd.DataFrame:
    """FIS degerlendirme suresi (ms). Tek is parcacigi, sicak calistirma sonrasi medyan."""
    rng = np.random.default_rng(0)
    rows = []
    for v in variants():
        if v.method != "FUZZY":
            continue
        fis = v.make_fis()
        for n in (1, 50):
            x = [rng.uniform(*UNIVERSE[k], n) for k in INPUTS]
            fis.evaluate(*x)
            t = []
            for _ in range(reps):
                t0 = time.perf_counter()
                fis.evaluate(*x)
                t.append(time.perf_counter() - t0)
            rows.append({"variant": v.name, "batch": n, "ms_per_call": 1e3 * np.median(t),
                         "ms_per_task": 1e3 * np.median(t) / n})
    try:   # scikit-fuzzy referansi (yalniz tek gorev; vektorlu arayuzu yok)
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
        from skfuzzy import control as ctrl

        from src.fuzzy.fis import FuzzyPrioritySystem
        from tests.test_fis import build_skfuzzy
        system = build_skfuzzy(FuzzyPrioritySystem())
        t = []
        for _ in range(max(20, reps // 10)):
            x = [rng.uniform(*UNIVERSE[k]) for k in INPUTS]
            sim = ctrl.ControlSystemSimulation(system)
            t0 = time.perf_counter()
            for k, val in zip(INPUTS, x):
                sim.input[k] = val
            sim.compute()
            t.append(time.perf_counter() - t0)
        rows.append({"variant": "scikit-fuzzy (Elle FIS)", "batch": 1, "ms_per_call": 1e3 * np.median(t),
                     "ms_per_task": 1e3 * np.median(t)})
    except Exception as e:  # pragma: no cover
        print("scikit-fuzzy zamanlamasi atlandi:", e)
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=len(TEST_SEEDS))
    ap.add_argument("--workers", type=int, default=None)
    a = ap.parse_args()
    seeds = TEST_SEEDS[:a.seeds]
    vs = variants()
    jobs = [(v, c, s, {"scenario": k}) for v in vs for k, c in SCEN.items() for s in seeds]
    df = run_jobs(jobs, a.workers)
    save(df, "ablation_raw.csv")
    tm = timing()
    save(tm, "fis_timing.csv")

    others = [v.name for v in vs if v.name != "Elle FIS"]
    tests = pd.concat([paired_test(df[df.variant.isin(["Elle FIS", o])], "Elle FIS", o, m, ["scenario"])
                       .assign(variant=o) for o in others
                       for m in ("completion_rate", "completion_urgent", "avg_delay")], ignore_index=True)
    # Holm duzeltmesini tum ablation karsilastirmalari uzerinden yeniden yap
    p = tests.p_wilcoxon.to_numpy()
    order, m_ = np.argsort(p), len(p)
    adj, run = np.empty(m_), 0.0
    for rank, i in enumerate(order):
        run = max(run, min(1.0, (m_ - rank) * p[i]))
        adj[i] = run
    tests["p_holm"], tests["significant"] = adj, adj < 0.05
    save(tests, "ablation_wilcoxon.csv")

    md = [f"# Ablation (test seed'leri 1–{len(seeds)}; fark = varyant − elle FIS, Holm düzeltmeli)", ""]
    for k in SCEN:
        g = df[df.scenario == k]
        md += [f"## {TITLE[k]}", "", "| Varyant | Tamamlama | Δ | p | Acil | Δ | p | Gecikme (s) | Δ | p | FIS ms/görev |",
               "|---|---|---|---|---|---|---|---|---|---|---|"]
        for v in vs:
            gv = g[g.variant == v.name]
            cells = []
            for m in ("completion_rate", "completion_urgent", "avg_delay"):
                cells.append(f"{gv[m].mean():.4f}")
                if v.name == "Elle FIS":
                    cells += ["–", "–"]
                else:
                    t = tests[(tests.scenario == k) & (tests.variant == v.name) & (tests.metric == m)].iloc[0]
                    cells += [f"{t.diff_mean:+.4f}", fmt_p(t.p_holm) + ("*" if t.significant else "")]
            fis_ms = gv.fis_ms_per_eval.mean()
            cells.append("–" if np.isnan(fis_ms) else f"{fis_ms:.4f}")
            md.append(f"| {v.name} | " + " | ".join(cells) + " |")
        md.append("")
    md += ["## FIS değerlendirme süresi (medyan, tek çekirdek)", "", "| FIS | Parti | ms/çağrı | ms/görev |",
           "|---|---|---|---|"]
    md += [f"| {r.variant} | {r.batch} | {r.ms_per_call:.4f} | {r.ms_per_task:.4f} |" for r in tm.itertuples()]
    with open(os.path.join(os.path.dirname(FIGURES), "tables", "ablation_summary.md"), "w",
              encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    print("\n".join(md))

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 3.8), dpi=150, sharey=True)
    names = [v.name for v in vs if v.name != "Elle FIS"]
    for ax, k in zip(axes, SCEN):
        t = tests[(tests.scenario == k) & (tests.metric == "completion_urgent")].set_index("variant").loc[names]
        y = np.arange(len(names))
        ax.barh(y, t.diff_mean, xerr=t.diff_ci95, color=[COLORS[n] for n in names], height=0.6,
                capsize=3)
        ax.axvline(0, color="#52514e", lw=1)
        ax.set_yticks(y, names)
        ax.set_title(TITLE[k], fontsize=10, loc="left")
        ax.set_xlabel("Δ acil görev tamamlama (varyant − elle FIS)")
        style_axes(ax)
    axes[0].invert_yaxis()
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES, "ablation_urgent.png"))
    plt.close(fig)


if __name__ == "__main__":
    main()
