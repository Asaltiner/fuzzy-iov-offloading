"""
Gun 4 / CP5 - GA-FIS'in elle tasarlanmis FIS ile kontrollu karsilastirmasi.

Asamalar (veri sizintisi olmamasi icin uc ayri seed kumesi):
  1) EGITIM  (101-105): GA bunlarla calisti (src/fuzzy/ga_tuning.py, 3 GA seed'i).
  2) DOGRULAMA (201-210): 3 GA kosusunun en iyi bireylerinden biri SECILIR.
     Test seed'lerine bakarak secim yapmak iyimser sonuc verirdi.
  3) TEST (1-30): secilen GA-FIS ile elle FIS karsilastirilir; eslestirilmis Wilcoxon +
     Holm duzeltmesi.

Test deneyleri:
  T1 ana senaryolar   : normal (150 arac/km, 0.015) ve yuksek yuk (100 arac/km, 0.035)
                        + referans olarak en iyi baseline NF + 3 GA seed'inin hepsi
  T2 yogunluk taramasi: 50-350 arac/km, normal yuk (E1 ile ayni kosullar)
  T3 yuk taramasi     : 100 arac/km, gorev hizi 0.015-0.045 gorev/s/arac (yeni senaryo)

Calistirma:
  python -m experiments.proposed.ga_evaluate               # ~6 dk (2 cekirdek)
  python -m experiments.proposed.ga_evaluate --quick       # 5 seed, kod kontrolu
"""
from __future__ import annotations

import argparse
import json
import os

import numpy as np
import pandas as pd

from src.fuzzy.ga_tuning import decode, plot_mf_comparison
from src.sim import SimConfig

from .common import (COLORS, FIGURES, GA_DIR, TEST_SEEDS, VAL_SEEDS, Variant, ci95, fitness,
                     fmt_p, load_genome, paired_test, run_jobs, save, style_axes)

GA_TAGS = ("ga_full_s1", "ga_full_s2", "ga_full_s3")
NORMAL = SimConfig(density=150.0, mean_speed=30.0)
HIGHLOAD = SimConfig(density=100.0, mean_speed=30.0, task_rate=0.035)
DENSITIES = (50, 100, 150, 200, 250, 300, 350)
LOADS = (0.015, 0.025, 0.035, 0.045)
COMPARE = ("completion_rate", "completion_urgent", "avg_delay", "fitness")
LABEL = {"completion_rate": "Tamamlama oranı", "completion_urgent": "Acil görev tamamlama",
         "avg_delay": "Gecikme (s)", "fitness": "Uygunluk F", "fis_ms_per_eval": "FIS süresi (ms/görev)"}


def add_fitness(df: pd.DataFrame, cfgs: dict) -> pd.DataFrame:
    df["fitness"] = np.nan
    for key, cfg in cfgs.items():
        m = df.scenario == key
        df.loc[m, "fitness"] = fitness(df[m], cfg)
    return df


# ---------------------------------------------------------------- 1) dogrulama
def validate(seeds, workers) -> dict:
    genomes = {t: load_genome(t) for t in GA_TAGS}
    variants = [Variant("Elle FIS")] + [Variant(t, genome=g) for t, g in genomes.items()]
    cfgs = {"normal": NORMAL, "highload": HIGHLOAD}
    jobs = [(v, c, s, {"scenario": k}) for v in variants for k, c in cfgs.items() for s in seeds]
    df = add_fitness(run_jobs(jobs, workers), cfgs)
    save(df, "ga_validation_raw.csv")
    sm = df.groupby("variant")[["fitness", "completion_rate", "completion_urgent"]].mean()
    train = {}
    for t in GA_TAGS:
        with open(os.path.join(GA_DIR, f"{t}_best.json"), encoding="utf-8") as f:
            j = json.load(f)
        train[t] = (j["best_detail"]["fitness"], j["baseline_detail"]["fitness"])
    sm["train_fitness"] = [train.get(v, (np.nan, np.nan))[0] if v in train else
                           next(iter(train.values()))[1] for v in sm.index]
    save(sm.reset_index(), "ga_validation_summary.csv")
    best_tag = sm.loc[list(GA_TAGS), "fitness"].idxmax()
    sel = {"selected_tag": best_tag, "best_genome": list(genomes[best_tag]),
           "best_breakpoints": {k: v.tolist() for k, v in decode(np.array(genomes[best_tag])).items()},
           "validation_seeds": list(seeds),
           "validation_fitness": sm["fitness"].to_dict(),
           "train_fitness": sm["train_fitness"].to_dict()}
    with open(os.path.join(GA_DIR, "ga_selected.json"), "w", encoding="utf-8") as f:
        json.dump(sel, f, indent=2, ensure_ascii=False)
    print("Dogrulama (seed %d-%d):" % (seeds[0], seeds[-1]))
    print(sm.round(4).to_string())
    print(f"-> secilen GA kosusu: {best_tag}")
    return sel


# ---------------------------------------------------------------- 2) test
def test(sel: dict, seeds, workers) -> dict[str, pd.DataFrame]:
    ga = Variant("GA-FIS", genome=tuple(sel["best_genome"]))
    elle = Variant("Elle FIS")
    others = [Variant(t, genome=load_genome(t)) for t in GA_TAGS]
    nf = Variant("NF", method="NF")
    out = {}

    # T1 ana senaryolar
    cfgs = {"normal": NORMAL, "highload": HIGHLOAD}
    jobs = [(v, c, s, {"scenario": k}) for v in [elle, ga, nf, *others]
            for k, c in cfgs.items() for s in seeds]
    out["main"] = add_fitness(run_jobs(jobs, workers), cfgs)

    # T2 yogunluk, T3 yuk
    cfgs2 = {f"d{d}": NORMAL.with_(density=float(d)) for d in DENSITIES}
    cfgs3 = {f"l{l}": HIGHLOAD.with_(task_rate=l) for l in LOADS}
    jobs = [(v, c, s, {"scenario": k, "x": float(k[1:])}) for v in (elle, ga)
            for k, c in {**cfgs2, **cfgs3}.items() for s in seeds]
    df = add_fitness(run_jobs(jobs, workers), {**cfgs2, **cfgs3})
    out["density"] = df[df.scenario.str.startswith("d")].copy()
    out["load"] = df[df.scenario.str.startswith("l")].copy()
    for k, d in out.items():
        save(d, f"ga_test_{k}_raw.csv")
    return out


def summarize(res: dict[str, pd.DataFrame], sel: dict) -> None:
    # ---- ana tablo: ortalama +- %95 GA
    main = res["main"]
    rows = []
    for (sc, v), g in main.groupby(["scenario", "variant"]):
        r = {"scenario": sc, "variant": v}
        for m in (*COMPARE, "avg_delay_completed", "fis_ms_per_eval", "wall_s"):
            r[f"{m}_mean"], r[f"{m}_ci95"] = g[m].mean(), ci95(g[m])
        rows.append(r)
    save(pd.DataFrame(rows), "ga_test_main_summary.csv")

    # ---- eslestirilmis testler (GA-FIS - Elle FIS)
    tests = []
    for exp, df, by in (("main", main, ["scenario"]), ("density", res["density"], ["x"]),
                        ("load", res["load"], ["x"])):
        for m in COMPARE:
            t = paired_test(df[df.variant.isin(["Elle FIS", "GA-FIS"])], "Elle FIS", "GA-FIS", m, by)
            t.insert(0, "experiment", exp)
            tests.append(t)
    tests = pd.concat(tests, ignore_index=True)
    save(tests, "ga_test_wilcoxon.csv")

    # ---- GA seed'ine duyarlilik (3 kosunun test performansi)
    rob = main[main.variant.str.startswith("ga_full")].groupby(["variant", "scenario"])[
        ["fitness", "completion_rate", "completion_urgent"]].mean().unstack("scenario")
    rob.columns = [f"{a}_{b}" for a, b in rob.columns]
    save(rob.reset_index(), "ga_seed_sensitivity.csv")

    # ---- Baseline / Gelistirilen / Degisim tablosu (yonerge 6.2)
    md = ["# GA-FIS ve elle tasarlanmış FIS: test seed'leri 1–30 (eşleştirilmiş Wilcoxon, Holm)",
          "", f"Seçilen GA koşusu: `{sel['selected_tag']}` (doğrulama seed'leri 201–210).", ""]
    for sc, name in (("normal", "Normal yük (150 araç/km, 0,015 görev/s)"),
                     ("highload", "Yüksek yük (100 araç/km, 0,035 görev/s)")):
        g = main[main.scenario == sc]
        md += [f"## {name}", "", "| Ölçüt | Elle FIS (baseline) | GA-FIS | Değişim | p (Holm) | K/B/E |",
               "|---|---|---|---|---|---|"]
        for m in (*COMPARE, "fis_ms_per_eval"):
            a = g[g.variant == "Elle FIS"][m]
            b = g[g.variant == "GA-FIS"][m]
            if m == "fis_ms_per_eval":
                md.append(f"| {LABEL[m]} | {a.mean():.4f} | {b.mean():.4f} | "
                          f"{(b.mean() / a.mean() - 1) * 100:+.1f} % | – | – |")
                continue
            t = tests[(tests.experiment == "main") & (tests.scenario == sc) & (tests.metric == m)].iloc[0]
            md.append(f"| {LABEL[m]} | {a.mean():.4f} ± {ci95(a):.4f} | {b.mean():.4f} ± {ci95(b):.4f} | "
                      f"{t.diff_mean:+.4f} ± {t.diff_ci95:.4f} | {fmt_p(t.p_holm)}"
                      f"{' *' if t.significant else ''} | {t.wins}/{t.ties}/{t.losses} |")
        md.append("")
    md += ["K/B/E: GA-FIS'in elle FIS'ten iyi / eşit / kötü olduğu seed sayısı "
           "(gecikmede 'iyi' = artış; yorumlarken işarete dikkat). * : p_Holm < 0,05.", "",
           "## Yoğunluk ve yük taramaları (GA-FIS − Elle FIS)", "",
           "| Deney | x | ΔTamamlama | p | ΔAcil | p | ΔGecikme (s) | p |", "|---|---|---|---|---|---|---|---|"]
    for exp in ("density", "load"):
        t = tests[tests.experiment == exp]
        for x in sorted(t.x.unique()):
            r = {m: t[(t.x == x) & (t.metric == m)].iloc[0] for m in COMPARE}
            cells = " | ".join(f"{r[m].diff_mean:+.4f} | {fmt_p(r[m].p_holm)}{'*' if r[m].significant else ''}"
                               for m in ("completion_rate", "completion_urgent", "avg_delay"))
            md.append(f"| {'yoğunluk' if exp == 'density' else 'görev hızı'} | {x:g} | {cells} |")
    md += ["", "## GA seed'ine duyarlılık (test seed'leri, ortalama uygunluk)", "",
           "| Koşu | Eğitim F | Doğrulama F | Test F normal | Test F yüksek yük |", "|---|---|---|---|---|"]
    for v in GA_TAGS:
        md.append(f"| {v} | {sel['train_fitness'][v]:.4f} | {sel['validation_fitness'][v]:.4f} | "
                  f"{rob.loc[v, 'fitness_normal']:.4f} | {rob.loc[v, 'fitness_highload']:.4f} |")
    e = main[main.variant == "Elle FIS"].groupby("scenario").fitness.mean()
    md.append(f"| Elle FIS | {sel['train_fitness']['Elle FIS']:.4f} | "
              f"{sel['validation_fitness']['Elle FIS']:.4f} | {e['normal']:.4f} | {e['highload']:.4f} |")
    with open(os.path.join(os.path.dirname(FIGURES), "tables", "ga_test_summary.md"), "w",
              encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    print("\n".join(md))


# ---------------------------------------------------------------- grafikler
def plots(res: dict[str, pd.DataFrame], sel: dict) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    os.makedirs(FIGURES, exist_ok=True)

    # (a) yakinsama: 3 GA seed'i
    fig, ax = plt.subplots(figsize=(6.4, 4.0), dpi=150)
    shades = ("#2a78d6", "#eb6834", "#1baf7a")
    for t, c in zip(GA_TAGS, shades):
        h = pd.read_csv(os.path.join(GA_DIR, f"{t}_history.csv"))
        ax.plot(h.generation, h.best, color=c, lw=2, marker="o", ms=3, label=f"{t[-2:]} en iyi")
        ax.plot(h.generation, h["mean"], color=c, lw=1.2, ls="--", label=f"{t[-2:]} ortalama")
    ax.axhline(h.baseline.iloc[0], color="#52514e", ls=":", lw=1.3, label="Elle FIS")
    ax.set_xlabel("Nesil")
    ax.set_ylabel("Uygunluk F (eğitim seed'leri 101–105)")
    style_axes(ax)
    ax.legend(frameon=False, fontsize=7, ncol=2)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES, "ga_full_convergence.png"))
    plt.close(fig)

    plot_mf_comparison(np.array(sel["best_genome"]), os.path.join(FIGURES, "ga_full_mf.png"))

    # (b) taramalarda fark (GA - Elle) +- %95 GA
    for exp, xlabel in (("density", "Araç yoğunluğu (araç/km)"),
                        ("load", "Görev hızı (görev/s/araç), 100 araç/km")):
        df = res[exp]
        fig, axes = plt.subplots(1, 2, figsize=(9, 3.6), dpi=150)
        for ax, m in zip(axes, ("completion_rate", "completion_urgent")):
            p = df.pivot_table(index=["x", "seed"], columns="variant", values=m)
            d = (p["GA-FIS"] - p["Elle FIS"]).groupby("x")
            xs = np.array(sorted(df.x.unique()))
            mu = d.mean().reindex(xs)
            ci = d.apply(ci95).reindex(xs)
            ax.axhline(0, color="#52514e", lw=1)
            ax.errorbar(xs, mu, yerr=ci, color=COLORS["GA-FIS"], marker="o", lw=2, capsize=3)
            ax.set_xlabel(xlabel)
            ax.set_ylabel(f"Δ {LABEL[m].lower()} (GA − elle)")
            style_axes(ax)
        fig.tight_layout()
        fig.savefig(os.path.join(FIGURES, f"ga_test_{exp}_diff.png"))
        plt.close(fig)

    # (c) yuk taramasinda mutlak degerler
    df = res["load"]
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.6), dpi=150)
    for ax, m in zip(axes, ("completion_rate", "completion_urgent")):
        for v, mk in (("Elle FIS", "o"), ("GA-FIS", "s")):
            g = df[df.variant == v].groupby("x")[m]
            ax.errorbar(g.mean().index, g.mean(), yerr=g.apply(ci95), color=COLORS[v], marker=mk,
                        lw=2, capsize=3, label=v)
        ax.set_xlabel("Görev hızı (görev/s/araç)")
        ax.set_ylabel(LABEL[m])
        style_axes(ax)
    axes[0].legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES, "ga_test_load.png"))
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="5 test / 3 dogrulama seed'i")
    ap.add_argument("--workers", type=int, default=None)
    a = ap.parse_args()
    seeds = TEST_SEEDS[:5] if a.quick else TEST_SEEDS
    val = VAL_SEEDS[:3] if a.quick else VAL_SEEDS
    sel = validate(val, a.workers)
    res = test(sel, seeds, a.workers)
    summarize(res, sel)
    plots(res, sel)


if __name__ == "__main__":
    main()
