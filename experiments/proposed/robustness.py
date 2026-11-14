"""
Gun 4 / CP5 - Gurultu (robustness) analizi.

Soru: Beacon'dan okunan mesafe ve bagil hiz olcumleri gurultuluyse bulanik yontem ve
GA-FIS ne kadar bozulur? GA-FIS'in dik (keskin) MF gecisleri onu gurultuye karsi daha
kirilgan yapar mi?

Gurultu modeli: x_olculen = x * (1 + N(0, sigma)), sigma in {0, 0.05, 0.10, 0.20, 0.30}.
Yalnizca bulanik girdiler (edge secimindeki MF_dist/MF_speed ve EN kuyrugundaki FIS)
etkilenir; hareket, gorevler ve kanal ayni kalir. NF gurultuden etkilenmez, referans cizgisi.

Calistirma: python -m experiments.proposed.robustness   (~4 dk, 2 cekirdek)
"""
from __future__ import annotations

import argparse
import os

import numpy as np
import pandas as pd

from src.sim import SimConfig

from .common import (COLORS, FIGURES, TEST_SEEDS, Variant, ci95, fmt_p, paired_test, run_jobs,
                     save, selected_genome, style_axes)

NOISE = (0.0, 0.05, 0.10, 0.20, 0.30)
SCEN = {"normal": SimConfig(density=150.0), "highload": SimConfig(density=100.0, task_rate=0.035)}
TITLE = {"normal": "Normal yük", "highload": "Yüksek yük"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=len(TEST_SEEDS))
    ap.add_argument("--workers", type=int, default=None)
    a = ap.parse_args()
    seeds = TEST_SEEDS[:a.seeds]
    variants = [Variant("Elle FIS"), Variant("GA-FIS", genome=selected_genome())]
    jobs = [(v, c.with_(input_noise=n), s, {"scenario": k, "noise": n})
            for v in variants for k, c in SCEN.items() for n in NOISE for s in seeds]
    jobs += [(Variant("NF", method="NF"), c, s, {"scenario": k, "noise": 0.0})
             for k, c in SCEN.items() for s in seeds]
    df = run_jobs(jobs, a.workers)
    save(df, "robustness_raw.csv")

    # Her varyantin kendi gurultusuz haline gore bozulmasi + GA-Elle farki
    fz = df[df.variant != "NF"]
    rows = []
    for (k, v, n), g in fz.groupby(["scenario", "variant", "noise"]):
        base = fz[(fz.scenario == k) & (fz.variant == v) & (fz.noise == 0)].set_index("seed")
        gg = g.set_index("seed")
        r = {"scenario": k, "variant": v, "noise": n}
        for m in ("completion_rate", "completion_urgent", "avg_delay"):
            r[f"{m}_mean"], r[f"{m}_ci95"] = gg[m].mean(), ci95(gg[m])
            r[f"{m}_drop"] = (gg[m] - base[m]).mean()
        rows.append(r)
    sm = pd.DataFrame(rows)
    save(sm, "robustness_summary.csv")
    tests = pd.concat([paired_test(fz, "Elle FIS", "GA-FIS", m, ["scenario", "noise"])
                       for m in ("completion_rate", "completion_urgent")], ignore_index=True)
    save(tests, "robustness_wilcoxon.csv")

    md = ["# Gürültü analizi (test seed'leri 1–%d)" % len(seeds), "",
          "| Senaryo | σ | Elle FIS CR | GA-FIS CR | Δ (GA−elle) | p (Holm) | Elle acil | GA acil | Δ acil | p |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for k in SCEN:
        for n in NOISE:
            e = sm[(sm.scenario == k) & (sm.variant == "Elle FIS") & (sm.noise == n)].iloc[0]
            g = sm[(sm.scenario == k) & (sm.variant == "GA-FIS") & (sm.noise == n)].iloc[0]
            t1 = tests[(tests.scenario == k) & (tests.noise == n) & (tests.metric == "completion_rate")].iloc[0]
            t2 = tests[(tests.scenario == k) & (tests.noise == n) & (tests.metric == "completion_urgent")].iloc[0]
            md.append(f"| {TITLE[k]} | {n:.2f} | {e.completion_rate_mean:.4f} | {g.completion_rate_mean:.4f} | "
                      f"{t1.diff_mean:+.4f} | {fmt_p(t1.p_holm)} | {e.completion_urgent_mean:.4f} | "
                      f"{g.completion_urgent_mean:.4f} | {t2.diff_mean:+.4f} | {fmt_p(t2.p_holm)} |")
    nf = df[df.variant == "NF"].groupby("scenario").completion_rate.mean()
    md += ["", "NF (gürültüden etkilenmez) tamamlama oranı: " +
           ", ".join(f"{TITLE[k]} {nf[k]:.4f}" for k in SCEN)]
    with open(os.path.join(os.path.dirname(FIGURES), "tables", "robustness_summary.md"), "w",
              encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    print("\n".join(md))

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 2, figsize=(9, 6.4), dpi=150, sharex=True)
    for col, k in enumerate(SCEN):
        for row, m in enumerate(("completion_rate", "completion_urgent")):
            ax = axes[row, col]
            for v, mk in (("Elle FIS", "o"), ("GA-FIS", "s")):
                s = sm[(sm.scenario == k) & (sm.variant == v)].sort_values("noise")
                ax.errorbar(s.noise, s[f"{m}_mean"], yerr=s[f"{m}_ci95"], color=COLORS[v],
                            marker=mk, lw=2, capsize=3, label=v)
            nfv = df[(df.variant == "NF") & (df.scenario == k)][m].mean()
            ax.axhline(nfv, color=COLORS["NF"], ls="--", lw=1.3, label="NF (referans)")
            ax.set_title(TITLE[k], fontsize=10, loc="left")
            ax.set_ylabel("Tamamlama oranı" if m == "completion_rate" else "Acil görev tamamlama")
            if row == 1:
                ax.set_xlabel("Girdi gürültüsü σ (göreli)")
            style_axes(ax)
    axes[0, 0].legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES, "robustness_noise.png"))
    plt.close(fig)


if __name__ == "__main__":
    main()
