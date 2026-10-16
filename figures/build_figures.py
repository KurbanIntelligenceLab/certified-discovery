#!/usr/bin/env python3
"""
Build Figures 2 and 3 for the manuscript at publication resolution.

Emits, for each figure, a high-DPI PNG and a vector PDF, both drawn from the
run's persisted, sha-verified CSVs. Layouts are the collision-audited final
versions. Resolution is set in one place (DPI below).

Usage:  python build_figures.py [results_dir] [--dpi N]
"""
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import FixedLocator, FixedFormatter

DPI = 600  # PNG raster resolution; PDF is vector regardless
RES = "results"
_args = sys.argv[1:]
_skip = False
for _i, a in enumerate(_args):
    if _skip:
        _skip = False
        continue
    if a.startswith("--dpi"):
        if "=" in a:
            DPI = int(a.split("=")[1])
        else:
            DPI = int(_args[_i + 1])
            _skip = True  # consume the value so it is not read as the data dir
    elif not a.startswith("--"):
        RES = a

OKB, OKG, OKV, OKGR = "#0072B2", "#009E73", "#D55E00", "#7F7F7F"
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Liberation Sans", "Arial", "DejaVu Sans"],
    "font.size": 7.0, "axes.linewidth": 0.6,
    "axes.spines.top": False, "axes.spines.right": False,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "xtick.major.size": 2.5, "ytick.major.size": 2.5,
    "legend.frameon": False, "axes.titlesize": 7.6,
    "pdf.fonttype": 42, "ps.fonttype": 42,  # embed real fonts (TrueType) in the PDF, not paths
    "svg.fonttype": "none",
})


def save(fig, stem):
    fig.savefig(f"{stem}.png", dpi=DPI, bbox_inches="tight")
    fig.savefig(f"{stem}.pdf", bbox_inches="tight")  # vector
    print(f"  wrote {stem}.png ({DPI} dpi) and {stem}.pdf (vector)")


# ============================ FIGURE 2 ============================
def figure2():
    S = pd.read_csv(f"{RES}/fig2_synthetic_summary.csv")
    g = lambda sec, key: float(S[(S.section == sec) & (S.key == key)].value.iloc[0])
    truth, naive = g("panel_a", "true_precision"), g("panel_a", "naive_estimate")
    cl_lo, cl_e, cl_hi = g("panel_a", "classical_lo"), g("panel_a", "classical_est"), g("panel_a", "classical_hi")
    pp_lo, pp_e, pp_hi = g("panel_a", "certified_lo"), g("panel_a", "certified_est"), g("panel_a", "certified_hi")
    C = pd.read_csv(f"{RES}/fig2_budget_curve_synthetic.csv")
    budgets = C.n_label.tolist()
    covc, covp = C.coverage_classical.values, C.coverage_ppi.values
    wc, wp = C.mean_width_classical.values, C.mean_width_ppi.values

    def sweep(sec):
        d = S[S.section == sec]; sig = [0.02, 0.25, 0.6, 1.0, 1.8, 3.5]
        return ([float(d[d.key == f"rho@sigma={s}"].value.iloc[0]) for s in sig],
                [float(d[d.key == f"ratio@sigma={s}"].value.iloc[0]) for s in sig])
    rb, qb = sweep("panel_d_binary"); rm, qm = sweep("panel_d_margins")
    BS = pd.read_csv(f"{RES}/budgets_summary.csv")

    fig, axes = plt.subplots(2, 2, figsize=(7.09, 5.05))
    (a, b), (c, d) = axes

    a.axhline(truth, color="k", lw=0.9, ls=(0, (4, 3)), zorder=1)
    a.text(3.68, truth - 0.012, "true precision\n(hidden from all methods)", va="top", ha="right", fontsize=6.2, color="0.25")
    a.errorbar([1], [cl_e], yerr=[[cl_e - cl_lo], [cl_hi - cl_e]], fmt="o", color=OKGR, ms=4.5, capsize=3.5, lw=1.4, capthick=1.4, zorder=3)
    a.text(1, cl_hi + 0.010, f"width\n{cl_hi - cl_lo:.3f}", ha="center", va="bottom", fontsize=5.8, color=OKGR)
    a.errorbar([2], [pp_e], yerr=[[pp_e - pp_lo], [pp_hi - pp_e]], fmt="o", color=OKB, ms=4.5, capsize=3.5, lw=1.4, capthick=1.4, zorder=3)
    a.text(2, pp_hi + 0.010, f"width\n{pp_hi - pp_lo:.3f}", ha="center", va="bottom", fontsize=5.8, color=OKB)
    a.plot([3], [naive], "s", color=OKV, ms=6, zorder=3)
    a.annotate("", xy=(3, naive - 0.007), xytext=(3, truth + 0.005), arrowprops=dict(arrowstyle="-|>", color=OKV, lw=1.2, mutation_scale=9))
    a.text(2.86, (naive + truth) / 2, f"+{naive - truth:.2f}\nbias", color=OKV, fontsize=6.4, ha="right", va="center", fontweight="bold")
    a.text(3.13, naive, "no interval\nat all", ha="left", va="center", color=OKV, fontsize=6.2)
    a.set_xticks([1, 2, 3]); a.set_xticklabels(["classical\n(labels only)", "certified\n(this work)", "naive\n(trust model)"], fontsize=6.6)
    a.set_xlim(0.45, 3.85); a.set_ylim(cl_lo - 0.038, naive + 0.038); a.set_ylabel("estimated precision")
    a.set_title("One campaign, three answers  (n = 300 labels)", loc="left")

    mc = 1.96 * np.sqrt(0.95 * 0.05 / 500)
    b.axhspan(0.95 - mc, 0.95 + mc, color="k", alpha=0.07, lw=0)
    b.axhline(0.95, color="k", lw=0.9, ls=(0, (4, 3)))
    b.plot(budgets, covc, "o-", color=OKGR, ms=3.6, lw=1.2)
    b.plot(budgets, covp, "o-", color=OKB, ms=3.6, lw=1.2)
    b.text(budgets[-1], 0.95 + mc + 0.006, "nominal 0.95  (band: Monte-Carlo error)", ha="right", va="bottom", fontsize=6.0, color="0.25")
    b.text(52, 0.917, "classical", color=OKGR, fontsize=6.8, fontweight="bold")
    b.text(52, 0.904, "certified", color=OKB, fontsize=6.8, fontweight="bold")
    b.set_xscale("log"); b.set_ylim(0.875, 1.005)
    b.set_xlabel("DFT verification budget $n$"); b.set_ylabel("empirical coverage")
    b.set_title("Coverage across budgets (nominal 0.95)", loc="left")

    c.fill_between(budgets, wp, wc, color=OKB, alpha=0.16, lw=0)
    c.plot(budgets, wc, "o-", color=OKGR, ms=3.6, lw=1.2)
    c.plot(budgets, wp, "o-", color=OKB, ms=3.6, lw=1.2)
    c.text(300, np.interp(np.log(300), np.log(budgets), wc) + 0.020, "classical", color=OKGR, fontsize=6.8, fontweight="bold", ha="center")
    c.text(300, np.interp(np.log(300), np.log(budgets), wp) - 0.026, "certified", color=OKB, fontsize=6.8, fontweight="bold", ha="center")
    c.legend(handles=[Patch(facecolor=OKB, alpha=0.16, label="prediction gain:\nwidth bought by the model\nat the same budget")],
             loc="upper right", fontsize=6.0, handlelength=1.6, borderaxespad=0.4)
    c.set_xscale("log"); c.set_xlim(45, 1900); c.set_ylim(0.03, 0.29)
    c.set_xlabel("DFT verification budget $n$"); c.set_ylabel("mean 95% CI width")
    c.set_title("Interval width against budget", loc="left")

    gridr = np.linspace(0, 0.995, 300)
    d.plot(gridr, np.sqrt(1 - gridr ** 2), "k-", lw=1.2, zorder=2)
    d.plot(rb, qb, "o", color=OKB, ms=4.0, zorder=3)
    d.plot(rm, qm, "s", mfc="none", mec=OKG, mew=1.2, ms=4.8, zorder=4)
    d.plot(BS.rho_pool, BS.ratio_n400, "D", color=OKV, ms=4.6, mec="white", mew=0.6, zorder=5)
    handles = [Line2D([], [], color="k", lw=1.2, label=r"$\sqrt{1-\rho^{2}}$, Theorem 1 (no fit)"),
               Line2D([], [], marker="D", ls="none", color=OKV, mec="white", mew=0.6, ms=4.6, label="15 real WBM campaigns (Table 1)"),
               Line2D([], [], marker="o", ls="none", color=OKB, ms=4.0, label="synthetic, binary stability calls"),
               Line2D([], [], marker="s", ls="none", mfc="none", mec=OKG, mew=1.2, ms=4.8, label="synthetic, continuous margins")]
    d.legend(handles=handles, loc="lower left", fontsize=6.0, handletextpad=0.5, labelspacing=0.5, borderaxespad=0.35, bbox_to_anchor=(0.015, 0.02))
    d.set_xlim(0, 1); d.set_ylim(0.5, 1.05)
    d.set_xlabel(r"prediction–label correlation $\rho$ on the pool")
    d.set_ylabel("width ratio, certified / classical")
    d.set_title(r"Width ratio against $\rho$: the $\sqrt{1-\rho^{2}}$ law", loc="left")

    for ax, letter in zip([a, b, c, d], "abcd"):
        ax.text(-0.155, 1.09, letter, transform=ax.transAxes, fontsize=11, fontweight="bold")
    fig.tight_layout(w_pad=2.4, h_pad=2.6)
    save(fig, "fig2_synthetic_validation")
    plt.close(fig)


# ============================ FIGURE 3 ============================
def figure3():
    df = pd.read_csv(f"{RES}/budget_curves.csv"); bs = pd.read_csv(f"{RES}/budgets_summary.csv")
    t1 = pd.read_csv(f"{RES}/table1_raw.csv")
    FR = ["EquiformerV3+DeNS-OAM", "eSEN-30M-OAM", "PET-OAM-XL", "GRACE-2L-OAM", "ORB v3",
          "SevenNet-MF-ompa", "MACE-MPA-0", "MatRIS-10M-OAM", "DPA3-v1-OpenLAM", "MatterSim v1 5M"]
    CL = ["CHGNet", "M3GNet", "ALIGNN", "MEGNet", "CGCNN"]

    fig = plt.figure(figsize=(7.09, 2.75))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.12, 1.18, 0.95], wspace=0.50)
    axa, axb, axc = [fig.add_subplot(gs[i]) for i in range(3)]

    for m in FR:
        dd = df[df.model == m].sort_values("n"); axa.plot(dd.n, dd.w_certified, "-", lw=0.7, color=OKB, alpha=0.40)
    for m in CL:
        dd = df[df.model == m].sort_values("n"); axa.plot(dd.n, dd.w_certified, "-", lw=0.7, color=OKV, alpha=0.40)
    piv = df.pivot_table(index="n", columns="model", values="w_certified")
    axa.plot(piv.index, piv[FR].mean(axis=1), "o-", color=OKB, lw=1.8, ms=3.4, zorder=4)
    axa.plot(piv.index, piv[CL].mean(axis=1), "o-", color=OKV, lw=1.8, ms=3.4, zorder=4)
    axa.axhline(0.04, ls=(0, (4, 3)), color="k", lw=0.8)
    axa.text(52, 0.0455, r"$\pm2\%$ target", ha="left", va="bottom", fontsize=6.0, color="0.2")
    handles = [Line2D([], [], color=OKV, lw=1.8, label="5 earlier graph networks\n(MAE 0.06–0.14 eV/atom)"),
               Line2D([], [], color=OKB, lw=1.8, label="10 frontier models\n(MAE $\\approx$ 0.02 eV/atom)")]
    axa.legend(handles=handles, loc="upper right", fontsize=6.0, handlelength=1.5, labelspacing=0.7, borderaxespad=0.25)
    axa.set_xscale("log"); axa.set_yscale("log"); axa.set_xlabel("DFT verification budget $n$")
    axa.yaxis.set_major_locator(FixedLocator([0.02, 0.05, 0.10, 0.15, 0.20, 0.25])); axa.yaxis.set_major_formatter(FixedFormatter(["0.02", "0.05", "0.10", "0.15", "0.20", "0.25"]))
    axa.yaxis.set_minor_locator(FixedLocator([])); axa.set_ylim(0.017, 0.30)
    axa.set_ylabel("mean certified 95% CI width")
    axa.set_title("Width against budget", loc="left")

    grid = [50, 100, 200, 400, 800, 1600, 3200]
    order = bs.sort_values(["n_empirical_pm2pct", "n_pred_pm2pct"]).reset_index(drop=True)
    for i, r in order.iterrows():
        emp = int(r.n_empirical_pm2pct); j = grid.index(emp); lo = grid[j - 1]
        axb.plot([lo, emp], [i, i], color="0.80", lw=3.4, solid_capstyle="butt", zorder=1)
        inside = lo <= r.n_pred_pm2pct <= emp
        axb.plot(r.n_pred_pm2pct, i, "o", ms=3.8, zorder=3, color=(OKB if inside else OKV), mec="white", mew=0.4)
    axb.set_yticks(range(len(order))); axb.set_yticklabels(order.model, fontsize=4.9)
    axb.set_ylim(-0.7, len(order) - 0.3); axb.set_xscale("log")
    axb.xaxis.set_major_locator(FixedLocator([400, 800, 1600, 3200]))
    axb.xaxis.set_major_formatter(FixedFormatter(["400", "800", "1,600", "3,200"]))
    axb.xaxis.set_minor_locator(FixedLocator([])); axb.tick_params(axis="x", labelsize=6)
    axb.set_xlabel("labels required for $\\pm2\\%$")
    axb.set_title("Budget rule versus empirical need", loc="left")
    axb.plot([], [], color="0.80", lw=3.4, label="empirical bracket")
    axb.plot([], [], "o", color=OKB, ms=3.8, label="pilot inside (12/15)")
    axb.plot([], [], "o", color=OKV, ms=3.8, label="one step off (3/15)")
    leg = axb.legend(fontsize=5.0, loc="upper left", handlelength=1.2, handletextpad=0.45, borderaxespad=0.2, labelspacing=0.35)
    fig.canvas.draw()
    inv = axb.transData.inverted()
    for t in leg.get_texts():
        xend = inv.transform((t.get_window_extent().x1, t.get_window_extent().y1))[0]
        assert xend < 1500, f"legend line '{t.get_text()}' reaches the bars (x={xend:.0f})"

    mc3 = 3 * np.sqrt(0.95 * 0.05 / 1000)
    axc.axhspan(0.95 - mc3, 0.95 + mc3, color="k", alpha=0.07, lw=0)
    axc.axhline(0.95, ls=(0, (4, 3)), color="k", lw=0.8)
    rng = np.random.default_rng(1)
    for k, tau in enumerate([0.0, 0.05, 0.10]):
        cv = t1[t1.tau == tau].coverage.values
        xj = k + rng.uniform(-0.22, 0.22, len(cv)); low = cv < 0.95 - mc3
        axc.plot(xj[~low], cv[~low], "o", ms=2.5, color=OKB, alpha=0.75)
        axc.plot(xj[low], cv[low], "o", ms=3.2, color=OKV, zorder=4)
    axc.set_xticks([0, 1, 2]); axc.set_xticklabels(["0", "0.05", "0.10"], fontsize=6.6)
    axc.set_xlabel(r"stability threshold $\tau$ (eV/atom)", fontsize=6.6)
    axc.set_xlim(-0.6, 2.6); axc.set_ylim(0.905, 0.985)
    # explicit two-decimal y ticks: the auto-formatter drops the leading "0." at this range,
    # which would misread a coverage of 0.95 as "95". Force 0.91..0.98.
    yt = [0.91, 0.92, 0.93, 0.94, 0.95, 0.96, 0.97, 0.98]
    axc.set_yticks(yt); axc.set_yticklabels([f"{v:.2f}" for v in yt], fontsize=6.4)
    axc.set_ylabel("empirical coverage")
    axc.text(1.0, 0.9505 + mc3 + 0.003, "nominal 0.95  (3 MC s.e. band)", ha="center", fontsize=5.9, color="0.25")
    # arrow must reach the low cluster (min coverage 0.924); tip just under it, small shrink
    for k, tau in enumerate([0.0, 0.05, 0.10]):
        mu = t1[t1.tau == tau].coverage.mean()
        axc.plot([k - 0.30, k + 0.30], [mu, mu], color="k", lw=1.1, zorder=5)
    axc.annotate("4 of 90 below the band, all at $\\tau=0.10$;\nblack bars: mean per threshold", xy=(2.02, 0.9235), xytext=(0.30, 0.9125),
                 fontsize=5.8, color=OKV, ha="left",
                 arrowprops=dict(arrowstyle="->", color=OKV, lw=0.7, shrinkA=2, shrinkB=2))
    axc.set_title("Coverage, 90 configurations", loc="left")

    for ax, letter in zip([axa, axb, axc], "abc"):
        ax.text(-0.20, 1.10, letter, transform=ax.transAxes, fontsize=11, fontweight="bold")
    save(fig, "fig3_budget_real")
    plt.close(fig)


if __name__ == "__main__":
    print(f"Building figures at {DPI} dpi (PNG) + vector PDF, from {RES}/")
    figure2()
    figure3()
    print("done")
