"""FIS gorsellestirme: uyelik fonksiyonlari ve kontrol yuzeyi.

Calistirma (repo kokunden):  python -m src.fuzzy.plot_fis
Ciktilar: results/figures/mf_inputs.png, mf_output.png, surface_distance_priority.png
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from src.fuzzy.fis import IN_TERMS, INPUTS, OUT_TERMS, UNIVERSE, FuzzyPrioritySystem  # noqa: E402

OUT_DIR = os.path.join("results", "figures")
LABELS = {"distance": "Mesafe (m)", "speed": "Bagil hiz (m/s)",
          "size": "Gorev boyutu (Mb)", "priority": "Gorev onceligi (0-1)"}
COLORS = ["#2a78b8", "#e08a1e", "#c2373b", "#5a9e4b", "#7a5bb0"]


def plot_inputs(fis: FuzzyPrioritySystem) -> str:
    fig, axes = plt.subplots(2, 2, figsize=(10, 6.5))
    for ax, name in zip(axes.ravel(), INPUTS):
        x = np.linspace(*UNIVERSE[name], 500)
        mu = fis.fuzzify(name, x)
        for k, term in enumerate(IN_TERMS):
            ax.plot(x, mu[:, k], color=COLORS[k], lw=2, label=term)
        ax.set_title(LABELS[name])
        ax.set_ylim(-0.05, 1.05)
        ax.set_ylabel("Uyelik derecesi")
        ax.grid(alpha=0.3)
    axes[0, 0].legend(loc="center right")
    fig.tight_layout()
    path = os.path.join(OUT_DIR, "mf_inputs.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_output(fis: FuzzyPrioritySystem) -> str:
    fig, ax = plt.subplots(figsize=(7, 3))
    for k, term in enumerate(OUT_TERMS):
        ax.plot(fis.y, fis.out_mf[k], color=COLORS[k], lw=2, label=term)
    ax.set_xlabel("Oncelik skoru")
    ax.set_ylabel("Uyelik derecesi")
    ax.legend(ncol=5, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, 1.25))
    ax.grid(alpha=0.3)
    fig.tight_layout()
    path = os.path.join(OUT_DIR, "mf_output.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_surface(fis: FuzzyPrioritySystem) -> str:
    d = np.linspace(*UNIVERSE["distance"], 60)
    p = np.linspace(*UNIVERSE["priority"], 60)
    D, P = np.meshgrid(d, p)
    Z = fis.evaluate(D.ravel(), np.full(D.size, 20.0), np.full(D.size, 5.0), P.ravel()).reshape(D.shape)
    fig = plt.figure(figsize=(7, 5))
    ax = fig.add_subplot(projection="3d")
    ax.plot_surface(D, P, Z, cmap="viridis", edgecolor="none")
    ax.set_xlabel("Mesafe (m)")
    ax.set_ylabel("Oncelik")
    ax.set_zlabel("Skor")
    ax.set_title("Kontrol yuzeyi (hiz=20 m/s, boyut=5 Mb)")
    fig.tight_layout()
    path = os.path.join(OUT_DIR, "surface_distance_priority.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    fis = FuzzyPrioritySystem()
    for p in (plot_inputs(fis), plot_output(fis), plot_surface(fis)):
        print("Kaydedildi:", p)
