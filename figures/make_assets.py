#!/usr/bin/env python3
"""Build the branded README assets: the hero banner, the method diagram, and the
headline overstatement figure.

Outputs are written to docs/assets/. The overstatement figure reads the released
result files in results/; the hero and method diagram are self-contained. Run from
the repository root:

    python figures/make_assets.py
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mc
from matplotlib.patches import Circle, FancyBboxPatch
from matplotlib.lines import Line2D

ASSETS = "docs/assets"
DATA = "results"
os.makedirs(ASSETS, exist_ok=True)

# Shared palette (Okabe-Ito derived), used across every asset.
OKB, OKV, OKG = "#0072B2", "#D55E00", "#009E73"
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Liberation Sans", "Arial", "DejaVu Sans"],
})


def _tint(hexc, amt=0.11):
    r, g, b = mc.to_rgb(hexc)
    return (1 - (1 - r) * amt, 1 - (1 - g) * amt, 1 - (1 - b) * amt)


def build_hero(path=f"{ASSETS}/hero.png"):
    """Dark branded header with the count-to-interval story card."""
    HB, CARD, TXT, SUB = "#0072B2", "#1b2740", "#e8eef5", "#8fa3bd"
    fig = plt.figure(figsize=(12, 3.4), dpi=200)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 3.4)
    ax.axis("off")
    for yy in np.linspace(0, 3.4, 120):
        t = yy / 3.4
        ax.add_patch(plt.Rectangle((0, yy), 12, 3.4 / 120 + 0.02,
                                   facecolor=(0.051 + 0.03 * t, 0.078 + 0.04 * t, 0.141 + 0.06 * t),
                                   lw=0, zorder=0))
    rng = np.random.default_rng(7)
    for _ in range(110):
        ax.add_patch(Circle((rng.uniform(0.2, 7.3), rng.uniform(0.2, 3.2)), 0.02,
                            color="white", alpha=rng.uniform(0.02, 0.10), zorder=1))
    ax.text(0.6, 2.42, "Certified Discovery", fontsize=37, fontweight="bold", color=TXT, zorder=5)
    ax.plot([0.63, 5.05], [2.02, 2.02], color=HB, lw=3, zorder=5, solid_capstyle="round")
    ax.text(0.64, 1.56, "Statistically valid materials-screening claims", fontsize=13.5, color=SUB, zorder=5)
    ax.text(0.64, 1.18, "from a small DFT verification budget", fontsize=13.5, color=SUB, zorder=5)
    cx = 0.64
    for ch in ["prediction-powered inference", "15 models", "~257k candidates", "numpy-only"]:
        w = 0.125 * len(ch) + 0.35
        ax.add_patch(FancyBboxPatch((cx, 0.36), w, 0.44, boxstyle="round,pad=0.02,rounding_size=0.18",
                                    facecolor=CARD, edgecolor=HB, lw=0.8, zorder=4))
        ax.text(cx + w / 2, 0.58, ch, fontsize=8.6, color=HB, ha="center", va="center", fontweight="bold", zorder=5)
        cx += w + 0.22
    px, py, pw, ph = 8.45, 1.02, 3.20, 2.10
    ax.add_patch(FancyBboxPatch((px, py), pw, ph, boxstyle="round,pad=0.02,rounding_size=0.18",
                                facecolor=CARD, edgecolor="#2b3a58", lw=1.0, zorder=3))
    midx = px + pw / 2
    ax.text(midx, py + ph - 0.26, "one campaign, two answers", fontsize=8.3, color=SUB, ha="center", zorder=5)
    ax.text(px + 0.82, py + ph - 0.66, "naive count", fontsize=7.6, color=SUB, ha="center", zorder=5)
    ax.text(px + 0.82, py + ph - 1.04, "62,153", fontsize=18, color=OKV, ha="center", fontweight="bold", zorder=5)
    ax.text(px + 0.82, py + ph - 1.34, "a prediction", fontsize=6.8, color=SUB, ha="center", zorder=5)
    ax.annotate("", xy=(px + 1.95, py + ph - 0.98), xytext=(px + 1.50, py + ph - 0.98),
                arrowprops=dict(arrowstyle="-|>", color=TXT, lw=1.8), zorder=5)
    icx = px + 2.45
    ax.text(icx, py + ph - 0.66, "certified 95%", fontsize=7.6, color=SUB, ha="center", zorder=5)
    ax.plot([icx - 0.52, icx + 0.52], [py + ph - 1.02] * 2, color=HB, lw=3.2, zorder=5, solid_capstyle="round")
    for xx in (icx - 0.52, icx + 0.52):
        ax.plot([xx, xx], [py + ph - 1.13, py + ph - 0.91], color=HB, lw=2.0, zorder=5)
    ax.plot([icx], [py + ph - 1.02], "o", ms=4.5, color=TXT, zorder=6)
    ax.text(icx, py + ph - 1.34, "[29,530 - 34,421]", fontsize=8.6, color=HB, ha="center", fontweight="bold", zorder=5)
    ax.text(midx, py + 0.20, "true count 32,012 . inside the interval", fontsize=7.0, color=OKG, ha="center", zorder=5)
    fig.savefig(path, dpi=200, facecolor="#0d1424")
    plt.close(fig)
    print(f"  wrote {path}")


def build_method(path=f"{ASSETS}/method.png"):
    """Four-step certification pipeline with the estimator equation."""
    INK, GREY = "#2b3a58", "#7a8aa0"
    fig, ax = plt.subplots(figsize=(10, 2.9), dpi=200)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 2.9)
    ax.axis("off")

    def box(x, y, w, h, num, title, sub, color):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.14",
                                    linewidth=1.6, edgecolor=color, facecolor=_tint(color, 0.11), zorder=2))
        ax.add_patch(plt.Circle((x + 0.32, y + h - 0.30), 0.17, facecolor=color, zorder=3))
        ax.text(x + 0.32, y + h - 0.30, num, fontsize=8.5, fontweight="bold", ha="center", va="center", color="white", zorder=4)
        ax.text(x + 0.60, y + h - 0.30, title, fontsize=10, fontweight="bold", ha="left", va="center", color=color, zorder=3)
        ax.text(x + w / 2, y + h / 2 - 0.28, sub, fontsize=7.4, ha="center", va="center", color="#48566b", zorder=3)

    y, h, w = 0.95, 1.05, 2.15
    xs = [0.15, 2.65, 5.15, 7.65]
    data = [("1", "Screen", "model flags N\ncandidates (pool S)", OKV),
            ("2", "Verify", "reveal DFT labels for\nn random items of S", OKG),
            ("3", "Certify", "prediction-powered\ninterval for the count", OKB),
            ("4", "Budget", "closed-form n for a\ntarget precision", INK)]
    for x, (n, t, s, c) in zip(xs, data):
        box(x, y, w, h, n, t, s, c)
    for i in range(3):
        ax.annotate("", xy=(xs[i + 1] - 0.05, y + h / 2), xytext=(xs[i] + w + 0.05, y + h / 2),
                    arrowprops=dict(arrowstyle="-|>", color=GREY, lw=1.8), zorder=2)
    ax.text(0.15, 2.58, "How certification works", fontsize=12.5, fontweight="bold", color="#1a2540")
    ax.text(0.16, 2.28, "labels sampled uniformly from the screened pool   .   interval never wider than label-only   .   numpy-only",
            fontsize=7.6, color=GREY)
    ax.text(5.0, 0.44, r"$\hat\pi = \lambda\,\bar f \;+\; \dfrac{1}{n}\sum_{i\in\mathcal{L}}(y_i-\lambda f_i)$",
            fontsize=13, ha="center", color=OKB)
    ax.text(5.0, 0.05, "predictions on all of S   +   bias measured on the verified sample",
            fontsize=7.4, ha="center", color=GREY)
    fig.savefig(path, dpi=200, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {path}")


def build_overstatement(path=f"{ASSETS}/overstatement.png"):
    """Headline: overstatement versus model accuracy, from results/."""
    t1 = pd.read_csv(f"{DATA}/table1_raw.csv")
    mae = pd.read_csv(f"{DATA}/model_mae.csv").set_index("model")
    f0 = t1[(t1.pool == "full") & (t1.tau == 0.0)].set_index("model")
    FR = ["EquiformerV3+DeNS-OAM", "eSEN-30M-OAM", "PET-OAM-XL", "GRACE-2L-OAM", "ORB v3",
          "SevenNet-MF-ompa", "MACE-MPA-0", "MatRIS-10M-OAM", "DPA3-v1-OpenLAM", "MatterSim v1 5M"]
    CL = ["CHGNet", "M3GNet", "ALIGNN", "MEGNet", "CGCNN"]
    plt.rcParams.update({"font.size": 8.5, "axes.linewidth": 0.7,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "xtick.major.width": 0.7, "ytick.major.width": 0.7})
    fig, ax = plt.subplots(figsize=(6.6, 3.3))
    ax.axhspan(0, 25, color=OKB, alpha=0.06, lw=0)
    ax.axhspan(90, 130, color=OKV, alpha=0.06, lw=0)
    for m in FR:
        ax.scatter(mae.loc[m, "mae_eV_per_atom"], f0.loc[m, "overstate_pct"], s=46, color=OKB, edgecolor="white", lw=0.7, zorder=3)
    for m in CL:
        ax.scatter(mae.loc[m, "mae_eV_per_atom"], f0.loc[m, "overstate_pct"], s=46, color=OKV, edgecolor="white", lw=0.7, zorder=3)
    best = "EquiformerV3+DeNS-OAM"
    phantom = int(f0.loc[best, "flagged"] - f0.loc[best, "true"])
    ax.annotate(f"EquiformerV3+DeNS-OAM\nmost accurate 2026 model\nstill {f0.loc[best,'overstate_pct']:.1f}% ({phantom:,} phantom)",
                xy=(mae.loc[best, "mae_eV_per_atom"], f0.loc[best, "overstate_pct"]),
                xytext=(0.036, 33), fontsize=7.0, color=OKB,
                arrowprops=dict(arrowstyle="->", color=OKB, lw=0.8, connectionstyle="arc3,rad=-0.2"))
    ax.annotate(f"CGCNN\n{f0.loc['CGCNN','overstate_pct']:.1f}%",
                xy=(mae.loc["CGCNN", "mae_eV_per_atom"], f0.loc["CGCNN", "overstate_pct"]),
                xytext=(0.128, 100), fontsize=7.0, color=OKV, ha="center",
                arrowprops=dict(arrowstyle="->", color=OKV, lw=0.8))
    ax.text(0.088, 15, "frontier models\n10-21% (mean 14%)", color=OKB, fontsize=7.8, fontweight="bold", ha="left", va="center")
    ax.text(0.020, 112, "earlier graph networks 94-124%", color=OKV, fontsize=7.8, fontweight="bold", ha="left", va="center")
    ax.set_xlabel("formation-energy MAE (eV/atom)", fontsize=8.5)
    ax.set_ylabel("overstatement of true\ndiscoveries (%)", fontsize=8.5)
    ax.set_xlim(0.012, 0.145)
    ax.set_ylim(0, 132)
    ax.set_title("Naive counts overstate discoveries at every accuracy level", loc="left", fontsize=9.2, fontweight="bold", pad=8)
    leg = [Line2D([], [], marker="o", ls="none", color=OKB, mec="white", mew=0.7, ms=7, label="current generation (10 models)"),
           Line2D([], [], marker="o", ls="none", color=OKV, mec="white", mew=0.7, ms=7, label="earlier graph networks (5 models)")]
    ax.legend(handles=leg, fontsize=7.0, loc="center left", bbox_to_anchor=(0.30, 0.60), frameon=False, handletextpad=0.4)
    fig.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {path}")


if __name__ == "__main__":
    print("Building README assets into docs/assets/ ...")
    build_hero()
    build_method()
    build_overstatement()
    print("done")
