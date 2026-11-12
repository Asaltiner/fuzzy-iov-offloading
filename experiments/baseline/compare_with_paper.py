"""
Yeniden uretim sonuclarini (E1/E2, 30 tekrar) referans makaleyle karsilastirir.

Uc katman:
  1) EGILIM: her yontem icin metrik ~ x (yogunluk/hiz) Spearman rho ve p-degeri
     (kosu duzeyinde, 30 tekrar x nokta). Isaret makaledeki egilim yonuyle karsilastirilir.
  2) SIRALAMA ve ISTATISTIK: her x noktasinda yontem siralamasi; FUZZY ile en iyi
     baseline arasinda Wilcoxon isaretli sira testi (ayni seed = ortak rastgele sayilar
     -> eslestirilmis orneklem).
  3) SAYISAL: data/paper_digitized/*.csv doluysa (WebPlotDigitizer), her yontemin egrisi
     icin bizim ortalamalarimiz ile makale degerleri arasinda Spearman rho (egri sekli)
     ve her x noktasinda yontemler arasi Spearman rho (siralama uyumu). CSV bossa atlanir.

Makaledeki iddialar yalnizca metinde/sekillerde acikca gorulenlerdir (docs/01, docs/04 Bolum 6).

Calistirma:  python -m experiments.baseline.compare_with_paper --reps 30
Cikti:       results/tables/paper_comparison_r30.md (+ .csv), results/figures/rank_heatmap_r30.png
"""
from __future__ import annotations

import argparse
import os

import numpy as np
import pandas as pd
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TAB = os.path.join(ROOT, "results", "tables")
FIG = os.path.join(ROOT, "results", "figures")
PAPER = os.path.join(ROOT, "data", "paper_digitized")
BASELINES = ["LPA", "RPA", "CHGO", "NF"]
CORE = BASELINES + ["FUZZY"]
HIGHER_BETTER = {"completion_rate": True, "completion_urgent": True, "avg_delay": False}


def load(tag, reps):
    raw = pd.read_csv(os.path.join(TAB, f"{tag}_raw_r{reps}.csv"))
    sm = pd.read_csv(os.path.join(TAB, f"{tag}_summary_r{reps}.csv"))
    return raw, sm


def trend_table(raw, param, metrics):
    rows = []
    for m in CORE + ["FUZZY_FIFO"]:
        g = raw[raw.method == m]
        if g.empty:
            continue
        for met in metrics:
            rho, p = stats.spearmanr(g[param], g[met], nan_policy="omit")
            means = g.groupby(param)[met].mean()
            rows.append({"method": m, "metric": met, "rho": rho, "p": p,
                         "first": means.iloc[0], "last": means.iloc[-1],
                         "change": means.iloc[-1] - means.iloc[0]})
    return pd.DataFrame(rows)


def ranking(sm, param, metric):
    piv = sm.pivot(index=param, columns="method", values=f"{metric}_mean")[CORE]
    asc = not HIGHER_BETTER[metric]
    return piv.rank(axis=1, ascending=asc).astype(int)   # 1 = en iyi


def fuzzy_vs_best_baseline(raw, sm, param, metric):
    """Her noktada FUZZY ile o noktadaki en iyi baseline arasinda eslestirilmis Wilcoxon."""
    rows = []
    hb = HIGHER_BETTER[metric]
    for x, g in raw.groupby(param):
        means = g[g.method.isin(BASELINES)].groupby("method")[metric].mean()
        best = means.idxmax() if hb else means.idxmin()
        a = g[g.method == "FUZZY"].set_index("seed")[metric]
        b = g[g.method == best].set_index("seed")[metric]
        idx = a.index.intersection(b.index)
        diff = a[idx] - b[idx]
        p = stats.wilcoxon(a[idx], b[idx]).pvalue if (diff != 0).any() else 1.0
        rows.append({"param": param, "x": x, "metric": metric, "best_baseline": best,
                     "fuzzy_mean": a[idx].mean(), "baseline_mean": b[idx].mean(),
                     "diff": diff.mean(), "wilcoxon_p": p,
                     "fuzzy_better": bool((diff.mean() > 0) == hb and diff.mean() != 0)})
    return pd.DataFrame(rows)


def paper_numeric(sm, param, metric, fname):
    p = os.path.join(PAPER, fname)
    if not os.path.exists(p):
        return None
    pp = pd.read_csv(p)
    if pp.empty:
        return None
    xcol = pp.columns[0]
    ours = sm.pivot(index=param, columns="method", values=f"{metric}_mean")
    # makaledeki x degerlerini bizim noktalarimiza eslestir (en yakin)
    pp["_x"] = [ours.index[np.argmin(np.abs(ours.index.values - v))] for v in pp[xcol]]
    pp = pp.groupby("_x").mean(numeric_only=True)
    rows = []
    for m in CORE:
        if m in pp.columns and pp[m].notna().sum() >= 3:
            common = pp.index.intersection(ours.index)
            r, pv = stats.spearmanr(ours.loc[common, m], pp.loc[common, m])
            rows.append({"level": "eğri şekli", "key": m, "rho": r, "p": pv, "n": len(common)})
    for x in pp.index.intersection(ours.index):
        cols = [m for m in CORE if m in pp.columns and pd.notna(pp.loc[x, m])]
        if len(cols) >= 3:
            r, pv = stats.spearmanr(ours.loc[x, cols], pp.loc[x, cols])
            rows.append({"level": "sıralama", "key": f"{param}={x}", "rho": r, "p": pv, "n": len(cols)})
    return pd.DataFrame(rows) if rows else None


def claims(e1_raw, e1_sm, e2_raw, e2_sm):
    """Makaledeki nitel iddialari otomatik kontrol et. (iddia, kaynak, bizim sonuc, durum)"""
    out = []
    r_e1c, r_e1d, r_e2c = (ranking(e1_sm, "density", "completion_rate"),
                           ranking(e1_sm, "density", "avg_delay"),
                           ranking(e2_sm, "mean_speed", "completion_rate"))
    tr1 = trend_table(e1_raw, "density", ["avg_delay", "completion_rate"]).set_index(["method", "metric"])
    tr2 = trend_table(e2_raw, "mean_speed", ["completion_rate"]).set_index(["method", "metric"])

    n = (r_e1d["FUZZY"] == 1).sum()
    out.append(("Önerilen yöntem tüm yoğunluklarda en düşük gecikme", "Şek. 9",
                f"{n}/{len(r_e1d)} noktada 1.", n == len(r_e1d)))
    n = (r_e1c["FUZZY"] == 1).sum() + (r_e2c["FUZZY"] == 1).sum()
    tot = len(r_e1c) + len(r_e2c)
    out.append(("Önerilen yöntem tüm yoğunluk ve hızlarda en yüksek tamamlama", "Şek. 11–12",
                f"{n}/{tot} noktada 1.", n == tot))
    ok = [m for m in CORE if tr1.loc[(m, "avg_delay"), "rho"] > 0 and tr1.loc[(m, "avg_delay"), "p"] < 0.05]
    out.append(("Yoğunluk ↑ → gecikme ↑", "Şek. 9",
                f"anlamlı artış (ρ>0, p<0,05): {', '.join(ok) or 'yok'}", len(ok) >= 3))
    rho = tr2.loc[("CHGO", "completion_rate"), "rho"]
    out.append(("CHGO hıza karşı tutarlı", "Şek. 12", f"CHGO ρ(hız, tamamlama) = {rho:+.2f}",
                abs(rho) < 0.3))
    rho = tr1.loc[("CHGO", "completion_rate"), "rho"]
    out.append(("CHGO yoğun ağda zayıf", "Şek. 11", f"CHGO ρ(yoğunluk, tamamlama) = {rho:+.2f}", rho < 0))
    ch = {m: abs(tr1.loc[(m, "completion_rate"), "change"]) for m in BASELINES if m != "LPA"}
    out.append(("NF yoğun bölgelerde güçlü/kararlı", "Şek. 11",
                "|Δ tamamlama| 50→350: " + ", ".join(f"{k} {v:.3f}" for k, v in ch.items()),
                min(ch, key=ch.get) == "NF"))
    n = (r_e1c["LPA"] == 5).sum() + (r_e2c["LPA"] == 5).sum()
    worst = pd.concat([r_e1c, r_e2c]).idxmax(axis=1).value_counts().to_dict()
    out.append(("LPA en kötü yöntem", "Şek. 11–12",
                f"LPA {n}/{tot} noktada son; en kötü: {worst}", n == tot))
    hi = e1_sm[e1_sm.density == e1_sm.density.max()].set_index("method")["completion_rate_mean"]
    out.append(("Yüksek yoğunlukta RPA > LPA", "Şek. 11",
                f"350 araç/km: RPA {hi['RPA']:.3f}, LPA {hi['LPA']:.3f}", hi["RPA"] > hi["LPA"]))
    return pd.DataFrame(out, columns=["iddia", "kaynak", "bizim sonuç", "uyumlu"])


def plot_rank_heatmap(ranks: dict[str, pd.DataFrame], path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, len(ranks), figsize=(4.2 * len(ranks), 3.2), dpi=150)
    for ax, (title, r) in zip(np.atleast_1d(axes), ranks.items()):
        im = ax.imshow(r.T.values, cmap="Blues_r", vmin=1, vmax=5, aspect="auto")
        ax.set_yticks(range(len(r.columns)), r.columns)
        ax.set_xticks(range(len(r.index)), [f"{v:g}" for v in r.index], fontsize=7)
        for (i, j), v in np.ndenumerate(r.T.values):
            ax.text(j, i, int(v), ha="center", va="center", fontsize=7,
                    color="white" if v <= 2 else "#0b0b0b")
        ax.set_title(title, fontsize=9, loc="left")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def md(df, floatfmt=".3f"):
    return df.to_markdown(index=False, floatfmt=floatfmt)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=30)
    a = ap.parse_args()
    e1_raw, e1_sm = load("e1_density", a.reps)
    e2_raw, e2_sm = load("e2_speed", a.reps)

    cl = claims(e1_raw, e1_sm, e2_raw, e2_sm)
    tr = pd.concat([trend_table(e1_raw, "density", ["avg_delay", "completion_rate"]).assign(exp="E1 yoğunluk"),
                    trend_table(e2_raw, "mean_speed", ["completion_rate"]).assign(exp="E2 hız")])
    wx = pd.concat([fuzzy_vs_best_baseline(e1_raw, e1_sm, "density", "completion_rate"),
                    fuzzy_vs_best_baseline(e1_raw, e1_sm, "density", "avg_delay"),
                    fuzzy_vs_best_baseline(e2_raw, e2_sm, "mean_speed", "completion_rate")])
    ranks = {"E1 tamamlama (1 = en iyi)": ranking(e1_sm, "density", "completion_rate"),
             "E1 gecikme": ranking(e1_sm, "density", "avg_delay"),
             "E2 tamamlama": ranking(e2_sm, "mean_speed", "completion_rate")}
    plot_rank_heatmap(ranks, os.path.join(FIG, f"rank_heatmap_r{a.reps}.png"))

    num = [x for x in (paper_numeric(e1_sm, "density", "avg_delay", "fig9_delay_vs_density.csv"),
                       paper_numeric(e1_sm, "density", "completion_rate", "fig11_completion_vs_density.csv"),
                       paper_numeric(e2_sm, "mean_speed", "completion_rate", "fig12_completion_vs_speed.csv"))
           if x is not None]

    cl.to_csv(os.path.join(TAB, f"paper_claims_r{a.reps}.csv"), index=False)
    tr.to_csv(os.path.join(TAB, f"trend_spearman_r{a.reps}.csv"), index=False)
    wx.to_csv(os.path.join(TAB, f"fuzzy_vs_best_wilcoxon_r{a.reps}.csv"), index=False)

    lines = [f"# Makaleyle karşılaştırma ({a.reps} tekrar)\n",
             "## 1. Nitel iddialar\n", md(cl.assign(uyumlu=cl.uyumlu.map({True: "✅", False: "❌"}))),
             f"\nUyum: **{int(cl.uyumlu.sum())}/{len(cl)}**\n",
             "## 2. Eğilim (Spearman ρ, koşu düzeyinde)\n",
             md(tr[["exp", "method", "metric", "rho", "p", "first", "last", "change"]], ".3g"),
             "\n## 3. FUZZY vs. en iyi baseline (eşleştirilmiş Wilcoxon)\n",
             md(wx, ".3g")]
    for name, r in ranks.items():
        lines += [f"\n## Sıralama — {name}\n", r.reset_index().to_markdown(index=False)]
    if num:
        lines += ["\n## 4. Sayısallaştırılmış şekillerle Spearman\n", md(pd.concat(num), ".3f")]
    else:
        lines += ["\n## 4. Sayısallaştırılmış şekiller\n",
                  "`data/paper_digitized/*.csv` boş olduğu için sayısal Spearman karşılaştırması "
                  "yapılamadı. CSV'ler doldurulduğunda bu betik yeniden çalıştırılınca bölüm otomatik oluşur."]
    with open(os.path.join(TAB, f"paper_comparison_r{a.reps}.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(md(cl))
    print(f"\nUyum: {int(cl.uyumlu.sum())}/{len(cl)}")


if __name__ == "__main__":
    main()
