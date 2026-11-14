"""
Canli demo (Streamlit): bulanik gorev onceliklendirme + IoV gorev aktarim simulatoru.

Calistirma:  streamlit run app.py

Sekmeler
  1) Canli FIS        : girdi kaydiricilari -> uyelik dereceleri, ateslenen kurallar,
                        birlesik cikti kumesi ve skor (Elle FIS / GA-FIS / ablation turleri)
  2) Kontrol yuzeyi   : iki girdiye gore skor yuzeyi, Elle FIS ile secilen FIS yan yana
  3) Mini simulasyon  : yogunluk, hiz, gorev hizi ve seed secilerek yontemler karsilastirilir
  4) Deney sonuclari  : results/ altindaki Gun 3-4 tablo ve grafikleri
"""
from __future__ import annotations

import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from src.fuzzy.fis import (IN_TERMS, INPUTS, OUT_TERMS, OUT_UNIVERSE, UNIVERSE,  # noqa: E402
                           FuzzyPrioritySystem)
from src.fuzzy.ga_tuning import decode  # noqa: E402

ROOT = os.path.dirname(os.path.abspath(__file__))
GA_JSON = [os.path.join(ROOT, "results", "ga", n) for n in ("ga_selected.json", "ga_pilot_best.json")]
TERM_COLORS = ("#2a78d6", "#1baf7a", "#eb6834")
OUT_COLORS = ("#2a78d6", "#1baf7a", "#eda100", "#eb6834", "#e87ba4")
LABEL = {"distance": "Mesafe (m)", "speed": "Bağıl hız (m/s)", "size": "Görev boyutu (Mb)",
         "priority": "Uygulama önceliği (0–1)"}
METHOD_HELP = {"LPA": "yerelde işle", "RPA": "rastgele komşu", "CHGO": "merkezi açgözlü",
               "NF": "next fit (MIPS)", "FUZZY": "makaledeki yöntem", "FUZZY_FIFO": "bulanık seçim + FIFO kuyruk"}

st.set_page_config(page_title="Bulanık IoV görev aktarımı", layout="wide")


# ---------------------------------------------------------------- yardimcilar
@st.cache_data
def ga_genome():
    for p in GA_JSON:
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                j = json.load(f)
            return tuple(j["best_genome"]), os.path.basename(p)
    return None, None


def build_fis(kind: str) -> FuzzyPrioritySystem:
    g, _ = ga_genome()
    if kind == "GA-FIS" and g is not None:
        return FuzzyPrioritySystem(breakpoints=decode(np.array(g)))
    if kind == "Sugeno":
        return FuzzyPrioritySystem(inference="sugeno")
    if kind in ("Bisector", "MOM"):
        return FuzzyPrioritySystem(defuzz=kind.lower())
    return FuzzyPrioritySystem()


def style(ax):
    ax.grid(True, color="#e6e5e0", lw=0.8)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)


def mf_figure(fis: FuzzyPrioritySystem, x: dict, ref: FuzzyPrioritySystem | None = None):
    fig, axes = plt.subplots(1, 4, figsize=(14, 2.6), dpi=110)
    for ax, n in zip(axes, INPUTS):
        u = np.linspace(*UNIVERSE[n], 400)
        mu = fis.fuzzify(n, u)
        for t in range(3):
            ax.plot(u, mu[:, t], color=TERM_COLORS[t], lw=2, label=IN_TERMS[t])
            if ref is not None:
                ax.plot(u, ref.fuzzify(n, u)[:, t], color=TERM_COLORS[t], lw=1, ls=":")
        ax.axvline(x[n], color="#1f1f1f", lw=1.2)
        d = fis.fuzzify(n, np.array([x[n]]))[0]
        ax.set_title(f"{LABEL[n]}\n" + "  ".join(f"{IN_TERMS[t][0].upper()}={d[t]:.2f}" for t in range(3)),
                     fontsize=9, loc="left")
        ax.set_ylim(-0.03, 1.05)
        style(ax)
    axes[0].legend(frameon=False, fontsize=7)
    fig.tight_layout()
    return fig


def output_figure(fis: FuzzyPrioritySystem, e: dict):
    fig, ax = plt.subplots(figsize=(6.5, 2.8), dpi=110)
    for k in range(len(OUT_TERMS)):
        ax.plot(fis.y, fis.out_mf[k], color=OUT_COLORS[k], lw=1, ls=":")
        ax.fill_between(fis.y, np.minimum(e["alpha"][k], fis.out_mf[k]), color=OUT_COLORS[k], alpha=0.35,
                        label=f"{OUT_TERMS[k]} (α={e['alpha'][k]:.2f})")
    if fis.inference == "mamdani":
        ax.plot(fis.y, e["aggregated"], color="#1f1f1f", lw=1.6)
    ax.axvline(e["score"], color="#d03b3b", lw=2)
    ax.text(e["score"], 1.02, f" skor = {e['score']:.1f}", color="#d03b3b", fontsize=9)
    ax.set_xlim(*OUT_UNIVERSE)
    ax.set_ylim(0, 1.12)
    ax.set_xlabel("Öncelik skoru")
    style(ax)
    ax.legend(frameon=False, fontsize=7, loc="upper left")
    fig.tight_layout()
    return fig


@st.cache_data(show_spinner=False)
def surface(kind: str, a: str, b: str, fixed: tuple, n: int = 41):
    fis = build_fis(kind)
    ua, ub = np.linspace(*UNIVERSE[a], n), np.linspace(*UNIVERSE[b], n)
    A, B = np.meshgrid(ua, ub)
    vals = dict(zip(INPUTS, fixed))
    args = [A.ravel() if k == a else B.ravel() if k == b else np.full(A.size, vals[k]) for k in INPUTS]
    return ua, ub, fis.evaluate(*args).reshape(A.shape)


@st.cache_data(show_spinner=False)
def simulate(method: str, fis_kind: str, density: float, speed: float, rate: float, sim_time: float,
             seed: int, noise: float):
    from src.sim import SimConfig, run_simulation
    cfg = SimConfig(density=density, mean_speed=speed, task_rate=rate, sim_time=sim_time,
                    warmup=min(20.0, sim_time / 10), tail=min(30.0, sim_time / 8), input_noise=noise)
    fis = build_fis(fis_kind) if method.startswith("FUZZY") else None
    return run_simulation(method, cfg, seed, fis=fis)


# ---------------------------------------------------------------- arayuz
st.title("Bulanık mantık tabanlı görev aktarımı — IoV edge computing")
st.caption("Trabelsi, Ali ve Qayyum (2024), *Internet of Things* 28:101392 — yeniden gerçekleştirme ve "
           "GA ile ayarlanmış üyelik fonksiyonları (GA-FIS).")
g, gsrc = ga_genome()
with st.sidebar:
    st.header("Bulanık sistem")
    kinds = ["Elle FIS", "GA-FIS", "Sugeno", "Bisector", "MOM"] if g is not None else \
        ["Elle FIS", "Sugeno", "Bisector", "MOM"]
    kind = st.radio("FIS türü", kinds, help="Elle FIS: eşit aralıklı MF, Mamdani + centroid (baseline). "
                    "GA-FIS: MF kırılma noktaları Genetik Algoritma ile ayarlandı.")
    if kind == "GA-FIS":
        st.caption(f"Genom kaynağı: `results/ga/{gsrc}`")
    show_ref = st.checkbox("Elle FIS MF'lerini noktalı göster", value=kind == "GA-FIS")
    st.divider()
    st.header("Girdiler")
    x = {"distance": st.slider(LABEL["distance"], 0.0, 250.0, 180.0, 1.0),
         "speed": st.slider(LABEL["speed"], 0.0, 40.0, 12.0, 0.5),
         "size": st.slider(LABEL["size"], 0.0, 10.0, 3.0, 0.1),
         "priority": st.slider(LABEL["priority"], 0.0, 1.0, 0.8, 0.01)}

fis = build_fis(kind)
tab1, tab2, tab3, tab4 = st.tabs(["Canlı FIS", "Kontrol yüzeyi", "Mini simülasyon", "Deney sonuçları"])

with tab1:
    e = fis.explain(*(x[n] for n in INPUTS))
    c1, c2, c3 = st.columns(3)
    c1.metric("Öncelik skoru", f"{e['score']:.1f} / 100")
    if kind != "Elle FIS":
        base = FuzzyPrioritySystem().score(*(x[n] for n in INPUTS))
        c2.metric("Elle FIS skoru", f"{base:.1f}", delta=f"{e['score'] - base:+.1f}")
    c3.metric("Ateşlenen kural", f"{int((e['firing'] > 0).sum())} / {len(fis.rules)}")
    st.subheader("1 · Bulanıklaştırma")
    st.pyplot(mf_figure(fis, x, FuzzyPrioritySystem() if show_ref and kind != "Elle FIS" else None))
    left, right = st.columns([1.1, 1])
    with left:
        st.subheader("2 · Kural ateşleme (VE = min)")
        top = np.argsort(-e["firing"])[:8]
        rows = [{"güç": round(float(e["firing"][r]), 3),
                 **{n: IN_TERMS[fis.rules[r][i]] for i, n in enumerate(INPUTS)},
                 "→ skor": OUT_TERMS[fis.rule_out[r]]} for r in top if e["firing"][r] > 0]
        st.dataframe(pd.DataFrame(rows), hide_index=True)
    with right:
        st.subheader("3 · Birleştirme ve durulaştırma")
        st.pyplot(output_figure(fis, e))
        st.caption("Mamdani: her çıktı terimi α ile kırpılır (min), kümeler max ile birleşir, "
                   f"skor = {fis.defuzz if fis.inference == 'mamdani' else 'Sugeno ağırlıklı ortalama'}.")

with tab2:
    c1, c2 = st.columns(2)
    a = c1.selectbox("Yatay eksen", INPUTS, index=0, format_func=LABEL.get)
    b = c2.selectbox("Dikey eksen", [n for n in INPUTS if n != a], index=2, format_func=LABEL.get)
    fixed = tuple(x[n] for n in INPUTS)
    st.caption("Diğer iki girdi kenar çubuğundaki değerlerde sabit tutulur.")
    cols = st.columns(2)
    for col, k in zip(cols, ("Elle FIS", kind if kind != "Elle FIS" else ("GA-FIS" if g else "Sugeno"))):
        ua, ub, Z = surface(k, a, b, fixed)
        fig, ax = plt.subplots(figsize=(5.2, 4.0), dpi=110)
        im = ax.pcolormesh(ua, ub, Z, cmap="viridis", vmin=0, vmax=100, shading="auto")
        ax.plot(x[a], x[b], "o", color="#d03b3b", ms=7)
        ax.set_xlabel(LABEL[a])
        ax.set_ylabel(LABEL[b])
        ax.set_title(k, fontsize=10, loc="left")
        fig.colorbar(im, ax=ax, label="skor")
        fig.tight_layout()
        col.pyplot(fig)

with tab3:
    st.markdown("Aynı seed tüm yöntemlerde **aynı trafik ve görev akışını** üretir (ortak rastgele sayılar).")
    c1, c2, c3, c4 = st.columns(4)
    density = c1.slider("Yoğunluk (araç/km)", 50, 350, 150, 25)
    speed = c2.slider("Ortalama hız (m/s)", 10, 50, 30, 5)
    rate = c3.select_slider("Görev hızı (görev/s/araç)", [0.015, 0.025, 0.035, 0.045], 0.015)
    sim_time = c4.select_slider("Süre (s)", [60, 120, 200, 300], 120)
    c5, c6, c7 = st.columns([1, 1, 2])
    seed = c5.number_input("Seed", 1, 999, 1)
    noise = c6.select_slider("Girdi gürültüsü σ", [0.0, 0.05, 0.1, 0.2, 0.3], 0.0)
    methods = c7.multiselect("Yöntemler", list(METHOD_HELP), ["NF", "CHGO", "FUZZY", "FUZZY_FIFO"],
                             format_func=lambda m: f"{m} — {METHOD_HELP[m]}")
    if st.button("Simülasyonu çalıştır", type="primary"):
        rows = []
        prog = st.progress(0.0)
        for i, m in enumerate(methods):
            kinds_m = [kind] if m.startswith("FUZZY") else [None]
            if m == "FUZZY" and kind != "Elle FIS":
                kinds_m = ["Elle FIS", kind]
            for k in kinds_m:
                r = simulate(m, k or "Elle FIS", float(density), float(speed), rate, float(sim_time),
                             int(seed), noise)
                rows.append({"yöntem": m if k is None or len(kinds_m) == 1 else f"{m} ({k})", **r})
            prog.progress((i + 1) / len(methods))
        df = pd.DataFrame(rows)
        st.session_state["sim_df"] = df
    if "sim_df" in st.session_state:
        df = st.session_state["sim_df"]
        show = df[["yöntem", "n_tasks", "completion_rate", "completion_urgent", "avg_delay",
                   "avg_delay_completed", "offload_ratio", "wall_s"]].rename(columns={
                       "n_tasks": "görev", "completion_rate": "tamamlama", "completion_urgent": "acil tamamlama",
                       "avg_delay": "gecikme (s)", "avg_delay_completed": "gecikme, tamamlanan (s)",
                       "offload_ratio": "aktarım oranı", "wall_s": "süre (s)"})
        st.dataframe(show.round(4), hide_index=True)
        fig, axes = plt.subplots(1, 2, figsize=(11, 3.4), dpi=110)
        y = np.arange(len(df))
        for ax, m, lab in zip(axes, ("completion_rate", "completion_urgent"),
                              ("Tamamlama oranı", "Acil görev (p ≥ 0,7) tamamlama")):
            ax.barh(y, df[m], color="#2a78d6", height=0.6)
            for yi, v in zip(y, df[m]):
                ax.text(v + 0.01, yi, f"{v:.3f}", va="center", fontsize=8)
            ax.set_yticks(y, df["yöntem"])
            ax.set_xlim(0, 1.1)
            ax.set_xlabel(lab)
            ax.invert_yaxis()
            style(ax)
        fig.tight_layout()
        st.pyplot(fig)
        fail = [c for c in df.columns if c.startswith("frac_")]
        st.caption("Başarısızlık nedenleri (görev oranı)")
        st.dataframe(df[["yöntem", *fail]].round(4), hide_index=True)

with tab4:
    tdir, fdir = os.path.join(ROOT, "results", "tables"), os.path.join(ROOT, "results", "figures")
    for md, figs in (("ga_test_summary.md", ("ga_full_convergence.png", "ga_full_mf.png", "ga_test_load.png")),
                     ("robustness_summary.md", ("robustness_noise.png",)),
                     ("ablation_summary.md", ("ablation_urgent.png",)),
                     ("paper_comparison_r30.md", ("e1_density_completion_rate_r30.png",
                                                  "e2_speed_completion_rate_r30.png"))):
        p = os.path.join(tdir, md)
        if not os.path.exists(p):
            continue
        with st.expander(md, expanded=md == "ga_test_summary.md"):
            with open(p, encoding="utf-8") as f:
                st.markdown(f.read())
            cols = st.columns(len(figs))
            for c, fg in zip(cols, figs):
                fp = os.path.join(fdir, fg)
                if os.path.exists(fp):
                    c.image(fp)
