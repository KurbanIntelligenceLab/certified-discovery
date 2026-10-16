"""verify_results.py -- Reconcile the quantitative claims of the manuscript
"Certified discovery: statistically valid materials screening claims from a
small DFT verification budget" against the archived result files.

Usage:
    python verify_results.py [results_dir] [experiments_results_dir]

results_dir (default: ./results) holds the run-of-record files (table1_raw.csv,
table2_raw.csv, tableS2_raw.csv, budget_curves.csv, budgets_summary.csv,
model_mae.csv, e5_robustness.csv, fig2_budget_curve_synthetic.csv,
run_metadata.json). If experiments_results_dir is given, the checks added in
revision round 1 (numbers introduced or corrected in the revised text, and the
independent re-execution files exp0_*, exp1_*, exp2_*, exp3_*, exp4_*, exp5_*)
are run as well.

The script COMPUTES; it never asserts a hard-coded outcome as if measured.
Each check prints PASS/FAIL against the value printed in the paper, and the exit
code is nonzero if any check fails. Requires numpy and pandas (pandas for CSV
I/O only; all statistics are numpy or the standard library).
"""
import json
import math
import sys

import numpy as np
import pandas as pd

FAILURES = []


def check(name, ok, detail=""):
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}" + (f"  ({detail})" if detail else ""))
    if not ok:
        FAILURES.append(name)


def main(results_dir="results"):
    t1 = pd.read_csv(f"{results_dir}/table1_raw.csv")
    t2 = pd.read_csv(f"{results_dir}/table2_raw.csv")
    s2 = pd.read_csv(f"{results_dir}/tableS2_raw.csv")
    if "scheme" in s2.columns:
        s2 = s2[s2.scheme == "confidence tertiles"]
    bs = pd.read_csv(f"{results_dir}/budgets_summary.csv")
    mae = pd.read_csv(f"{results_dir}/model_mae.csv").set_index("model")
    meta = json.load(open(f"{results_dir}/run_metadata.json"))

    # -------- provenance guard: refuse to reconcile pilot data --------
    check("run_metadata: QUICK_MODE is False (full protocol)",
          meta.get("QUICK_MODE") is False, f"QUICK_MODE={meta.get('QUICK_MODE')}")
    check("run_metadata: N_REP = 1000", meta.get("N_REP") == 1000,
          f"N_REP={meta.get('N_REP')}")
    check("budget grid runs to 3,200", meta.get("BUDGETS", [])[-1:] == [3200],
          str(meta.get("BUDGETS")))
    reps_ok = all(abs(c * 1000 - round(c * 1000)) < 1e-9 for c in t1.coverage)
    check("coverage values are multiples of 1/1000 (1,000 replicates per configuration)", reps_ok)

    # ---------------- Abstract / headline claims ----------------
    f0 = t1[(t1.pool == "full") & (t1.tau == 0.0)]
    check("90 (model, threshold, pool) configurations", len(t1) == 90, f"n={len(t1)}")
    check("15 models in the run", meta.get("models") and len(meta["models"]) == 15,
          f"n_models={len(meta.get('models', []))}")
    check("load path is the matbench-discovery package (Option B)",
          str(meta.get("load_path", "")).startswith("matbench"),
          f"load_path={meta.get('load_path')}")
    check("overstatement 10%-124% at tau=0 (full pool)",
          round(f0.overstate_pct.min()) == 10 and round(f0.overstate_pct.max()) == 124,
          f"min={f0.overstate_pct.min():.1f}, max={f0.overstate_pct.max():.1f}")
    # frontier vs classical split (the paper's sharpened message)
    frontier = ["EquiformerV3+DeNS-OAM", "eSEN-30M-OAM", "PET-OAM-XL", "GRACE-2L-OAM",
                "ORB v3", "SevenNet-MF-ompa", "MACE-MPA-0", "MatRIS-10M-OAM",
                "DPA3-v1-OpenLAM", "MatterSim v1 5M"]
    classical = ["CHGNet", "M3GNet", "ALIGNN", "MEGNet", "CGCNN"]
    hf = f0[f0.model.isin(frontier)].overstate_pct
    hc = f0[f0.model.isin(classical)].overstate_pct
    check("frontier models overstate 10-21% (mean ~14%)",
          9 <= hf.min() and hf.max() <= 21 and 12 <= hf.mean() <= 16,
          f"frontier {hf.min():.1f}-{hf.max():.1f}%, mean {hf.mean():.1f}%")
    check("classical models overstate 94-125%",
          93 <= hc.min() and hc.max() <= 125,
          f"classical {hc.min():.1f}-{hc.max():.1f}%")
    hwt = (f0.ci_hi - f0.ci_lo) / (2 * f0.flagged) * 100
    check("revised abstract: n=500 half-widths 2.5-4.3 pp (Table 1, measured)",
          round(hwt.min(), 1) == 2.5 and round(hwt.max(), 1) == 4.3, f"{hwt.min():.2f}-{hwt.max():.2f} pp")
    band = 3 * math.sqrt(0.95 * 0.05 / meta["N_REP"])
    cov = t1.coverage
    n_below = int((cov < 0.95 - band).sum())
    check("coverages below the 3-MC-sigma floor are rare and all at tau=0.10",
          n_below <= 5 and bool((t1[cov < 0.95 - band].tau == 0.10).all()),
          f"{n_below} below {0.95-band:.3f}, all at tau=0.10")
    check("coverage min/median/max = 0.924/0.945/0.967",
          (round(cov.min(), 3), round(cov.median(), 3), round(cov.max(), 3))
          == (0.924, 0.945, 0.967),
          f"{cov.min():.3f}/{cov.median():.3f}/{cov.max():.3f}")

    # ---------------- Table 1 (tau=0, full pool) ----------------
    paper_t1 = {
        'PET-OAM-XL': (0.018, 42619, 38664, 37614, 39714, 10.2, 0.093, 0.944),
        'EquiformerV3+DeNS-OAM': (0.017, 43437, 39364, 38332, 40479, 10.3, 0.094, 0.931),
        'eSEN-30M-OAM': (0.018, 42814, 38722, 37689, 39815, 10.6, 0.096, 0.946),
        'MatRIS-10M-OAM': (0.019, 42958, 38783, 37708, 39867, 10.8, 0.097, 0.955),
        'ORB v3': (0.023, 43497, 38305, 37192, 39545, 13.6, 0.119, 0.956),
        'MatterSim v1 5M': (0.024, 39624, 34700, 33640, 35826, 14.2, 0.124, 0.951),
        'SevenNet-MF-ompa': (0.021, 44484, 38556, 37373, 39883, 15.4, 0.133, 0.955),
        'GRACE-2L-OAM': (0.023, 42859, 36960, 35771, 38214, 16.0, 0.138, 0.953),
        'DPA3-v1-OpenLAM': (0.023, 43638, 37329, 36057, 38579, 16.9, 0.145, 0.942),
        'MACE-MPA-0': (0.028, 43477, 36055, 34709, 37407, 20.6, 0.171, 0.952),
        'CHGNet': (0.061, 62153, 32012, 29530, 34421, 94.2, 0.485, 0.953),
        'ALIGNN': (0.092, 56632, 28060, 25649, 30494, 101.8, 0.505, 0.946),
        'MEGNet': (0.128, 54380, 24811, 22427, 27144, 119.2, 0.544, 0.963),
        'M3GNet': (0.072, 75829, 33967, 30820, 36925, 123.2, 0.552, 0.952),
        'CGCNN': (0.135, 57037, 25411, 23095, 27889, 124.5, 0.554, 0.934),
    }
    idx = f0.set_index("model")
    ok = True
    for m, (pm, fl, tr, lo, hi, ov, pg, cv) in paper_t1.items():
        r = idx.loc[m]
        row_ok = (round(mae.loc[m, "mae_eV_per_atom"], 3) == pm and r.flagged == fl
                  and r["true"] == tr and r.ci_lo == lo and r.ci_hi == hi
                  and round(r.overstate_pct, 1) == ov
                  and round(r.precision_gap, 3) == pg and round(r.coverage, 3) == cv)
        if not row_ok:
            ok = False
            print("  Table 1 mismatch:", m)
    check("Table 1: all 15 rows match table1_raw.csv", ok)
    best = idx.loc["EquiformerV3+DeNS-OAM"]
    check("EquiformerV3 phantom count 4,073",
          best.flagged - best["true"] == 4073,
          f"{int(best.flagged - best['true'])}")
    weakest = [m for m in paper_t1 if idx.loc[m, "flagged"] - idx.loc[m, "true"] > idx.loc[m, "true"]]
    check("weakest models announce more false than true (M3GNet/MEGNet/ALIGNN/CGCNN)",
          set(weakest) == {"M3GNet", "MEGNet", "ALIGNN", "CGCNN"}, str(weakest))

    # Robustness ranges quoted in Results
    u0 = t1[(t1.pool == "uniq_protos") & (t1.tau == 0.0)]
    check("unique-prototype overstatement 7.8%-130.2%",
          round(u0.overstate_pct.min(), 1) == 7.8 and round(u0.overstate_pct.max(), 1) == 130.2,
          f"{u0.overstate_pct.min():.1f}-{u0.overstate_pct.max():.1f}")
    for tau, lo_hi in [(0.05, (5.2, 54.2)), (0.1, (4.0, 31.0))]:
        ff = t1[(t1.pool == "full") & (t1.tau == tau)]
        check(f"tau={tau} overstatement {lo_hi[0]}%-{lo_hi[1]}%",
              round(ff.overstate_pct.min(), 1) == lo_hi[0]
              and round(ff.overstate_pct.max(), 1) == lo_hi[1],
              f"{ff.overstate_pct.min():.1f}-{ff.overstate_pct.max():.1f}")

    # ---------------- Budget claims (Fig 3a,b) ----------------
    frac = bs.n_empirical_pm2pct / bs.pool_N * 100
    check("budgets are under 6% of pool", frac.max() <= 6.0,
          f"{frac.min():.1f}%-{frac.max():.1f}%")
    grid = meta["BUDGETS"]
    inside = []
    for _, r in bs.iterrows():
        i = grid.index(r.n_empirical_pm2pct)
        lo = grid[i - 1] if i > 0 else 0
        inside.append(lo <= r.n_pred_pm2pct <= r.n_empirical_pm2pct)
    check("closed-form budget inside bracket for 12/15 models",
          sum(inside) == 12, f"{sum(inside)}/15 inside")
    # Directional audit of the 3 off-bracket models (guards the Fig 3b caption wording).
    opt, pess = [], []
    for _, r in bs.iterrows():
        i = grid.index(r.n_empirical_pm2pct); lo = grid[i - 1] if i > 0 else 0
        if r.n_pred_pm2pct < lo:
            opt.append(r.model)                    # predicts too few labels (optimistic)
        elif r.n_pred_pm2pct > r.n_empirical_pm2pct:
            pess.append(r.model)                   # predicts too many labels (pessimistic)
    check("off-bracket direction: 1 optimistic (ORB v3), 2 high (EquiformerV3, MatRIS)",
          set(opt) == {"ORB v3"}
          and set(pess) == {"EquiformerV3+DeNS-OAM", "MatRIS-10M-OAM"},
          f"optimistic={opt}, one-step-high={pess}")

    # ---------------- Table 2 (paired rankings) ----------------
    n_sig = int((t2.p_holm < 0.05).sum())
    check("4 of 14 pairs Holm-significant", n_sig == 4 and len(t2) == 14,
          f"{n_sig}/{len(t2)}")
    sig_agree = bool((t2[t2.p_holm < 0.05].agrees == "yes").all())
    check("every Holm-significant pair agrees with MAE order", sig_agree)
    raw_flip = t2[t2.agrees == "NO (flip)"]
    check("2 raw-CI reversals, none survive Holm correction",
          len(raw_flip) == 2 and not (raw_flip.p_holm < 0.05).any(),
          f"{len(raw_flip)} raw flips, {(raw_flip.p_holm<0.05).sum()} Holm-sig")

    # ---------------- Supplementary tables ----------------
    check("Supp Table 2 confidence-tertile max gain 8% (GRACE-2L-OAM)",
          round((1 - s2[s2.scheme == 'confidence tertiles'].width_ratio.min()) * 100) == 8,
          f"max gain {(1-s2.width_ratio.min())*100:.1f}%")
    hw500 = (bs.w_certified_at_500 / 2 * 100)
    print(f"  note: budgets_summary.w_certified_at_500 is linearly interpolated between n=400 and n=800 "
          f"({hw500.min():.2f}-{hw500.max():.2f} pp); the manuscript no longer quotes it")
    t1hw = ((f0.ci_hi - f0.ci_lo) / (2 * f0.flagged) * 100)
    check("Table 1 exact n=500 half-widths within the abstract bound (<=4.5)",
          t1hw.max() <= 4.5, f"max={t1hw.max():.2f}")

def revision_checks(results_dir, exp_dir):
    """Checks added in revision round 1 (numbers introduced or corrected in the revised text)."""
    from math import comb
    t1 = pd.read_csv(f"{results_dir}/table1_raw.csv"); bc = pd.read_csv(f"{results_dir}/budget_curves.csv")
    bs = pd.read_csv(f"{results_dir}/budgets_summary.csv"); syn = pd.read_csv(f"{results_dir}/fig2_budget_curve_synthetic.csv")
    cov = t1.coverage
    check("coverage median 0.945 and mean 0.9445", round(cov.median(), 3) == 0.945 and round(cov.mean(), 4) == 0.9445,
          f"{cov.median():.4f} / {cov.mean():.5f}")
    mt = t1.groupby("tau").coverage.mean().round(4).to_dict()
    check("per-threshold mean coverage 0.9475 / 0.9427 / 0.9435 (0.7 pp below nominal at tau>=0.05)",
          [mt[0.0], mt[0.05], mt[0.1]] == [0.9475, 0.9427, 0.9435], str(mt))
    k, n = int(round((cov * 1000).sum())), 90 * 1000
    z = (k / n - 0.95) / math.sqrt(0.95 * 0.05 / n)
    p = math.erfc(abs(z) / math.sqrt(2))
    check("pooled binomial test of nominal coverage: p < 1e-12 (normal approximation)", p < 1e-12, f"z={z:.2f}, p={p:.1e}")
    check("SI Table 1: classical coverage range in budget sweep 0.860-0.976",
          (round(bc.coverage_classical.min(), 3), round(bc.coverage_classical.max(), 3)) == (0.86, 0.976))
    check("SI Table 1: certified coverage range in budget sweep 0.916-0.988",
          (round(bc.coverage_certified.min(), 3), round(bc.coverage_certified.max(), 3)) == (0.916, 0.988))
    dev = (bs.ratio_n400 - np.sqrt(1 - bs.rho_pool ** 2)).abs().max()
    check("Fig 2d: real campaigns within 0.002 of sqrt(1-rho^2)", dev < 0.002, f"max dev {dev:.4f}")
    red = (1 - bs.ratio_n400) * 100
    check("real-data width reduction 0.4%-9.8%, rho 0.07-0.43",
          round(red.min(), 1) == 0.4 and round(red.max(), 1) == 9.8 and round(bs.rho_pool.min(), 2) == 0.07
          and round(bs.rho_pool.max(), 2) == 0.43, f"{red.min():.2f}-{red.max():.2f}%")
    check("synthetic width reduction 6.5%-8.1% across budgets",
          round(syn.width_reduction.min() * 100, 1) == 6.5 and round(syn.width_reduction.max() * 100, 1) == 8.1)
    ob = pd.read_csv(f"{exp_dir}/exp1_oracle_budgets.csv")
    check("oracle budgets: +-5pp 123-377, +-2pp 754-2271, +-1pp 2861-8071",
          (ob.n_pm5pp.min(), ob.n_pm5pp.max(), ob.n_pm2pp.min(), ob.n_pm2pp.max(), ob.n_pm1pp.min(), ob.n_pm1pp.max())
          == (123, 377, 754, 2271, 2861, 8071))
    check("oracle half-width at n=500 2.46-4.33 pp; labels saved at +-2pp 12-415",
          (round(ob.hw500_certified_pp.min(), 2), round(ob.hw500_certified_pp.max(), 2)) == (2.46, 4.33)
          and ((ob.n_pm2pp_classical - ob.n_pm2pp).min(), (ob.n_pm2pp_classical - ob.n_pm2pp).max()) == (12, 415))
    check("finite-N effect on n*(+-2pp) at most 4.2%", round((1 - ob.n_pm2pp / ob.n_pm2pp_infiniteN).max() * 100, 1) == 4.2)
    a = pd.read_csv(f"{exp_dir}/exp2_benchmark_transfer_arity.csv"); r = pd.read_csv(f"{exp_dir}/exp2_benchmark_transfer.csv")
    b = a[a.arity == "binary"].transfer_error_pp
    check("transfer: binaries overestimated by 9.4-12.5 pp; 9/15 beyond half-width; rounds max 5.9 pp",
          round(b.min(), 1) == 9.4 and round(b.max(), 1) == 12.5 and int(a.exceeds_halfwidth.sum()) == 9
          and round(r.transfer_error_pp.abs().max(), 1) == 5.9)
    sh = pd.read_csv(f"{exp_dir}/exp4_shared_budget.csv").set_index(["design", "total_labels", "pair"])
    order = ["CHGNet vs M3GNet", "M3GNet vs ALIGNN", "ALIGNN vs MEGNet", "MEGNet vs CGCNN"]
    s2 = [round(sh.loc[("shared", 2000, q)].holm_power * 100) for q in order]
    pp = [round(sh.loc[("perpair", 2000, q)].holm_power * 100) for q in order]
    check("shared 2,000: 84/100/99/14%; per-pair 4x500: 34/98/68/5%", s2 == [84, 100, 99, 14] and pp == [34, 98, 68, 5], f"{s2} {pp}")
    s5 = [sh.loc[("shared", 500, q)].holm_power for q in order]; sp5 = [sh.loc[("split", 500, q)].holm_power for q in order]
    covr = pd.read_csv(f"{exp_dir}/exp4_shared_budget.csv").coverage
    check("shared 500 beats split 500 for every pair; coverage 0.936-0.965",
          all(x > y for x, y in zip(s5, sp5)) and (round(covr.min(), 3), round(covr.max(), 3)) == (0.936, 0.965))
    c = pd.read_csv(f"{exp_dir}/exp3_cost_proxy.csv")
    l, cu = c[c.proxy == "n_sites^1"], c[c.proxy == "n_sites^3"]
    check("cost proxy: linear within +-4%; cubic 95% range ~0.7-2.8x",
          l.q025.min() >= 0.96 and l.q975.max() <= 1.04 and round(cu.q025.min(), 1) == 0.7 and round(cu.q975.max(), 1) == 2.8)
    e0 = pd.read_csv(f"{exp_dir}/exp0_census_reproduction.csv")
    check("independent census reproduction (five earlier models): 30/30", bool(e0.match.all()) and len(e0) == 30)
    e5 = pd.read_csv(f"{exp_dir}/exp5_e1_reproduction.csv"); e3 = pd.read_csv(f"{exp_dir}/exp5_e3_reproduction.csv")
    ok1 = ((e5.coverage == e5.paper_coverage) & (e5.ci_lo == e5.paper_lo) & (e5.ci_hi == e5.paper_hi)).all()
    check("independent re-execution: E1 30/30 and E3 8/8 identical to the run of record", bool(ok1) and bool(e3.identical.all()))
    fr = t1[(t1.pool == "full") & (t1.tau == 0.0) & ~t1.model.isin(["CHGNet", "M3GNet", "ALIGNN", "MEGNet", "CGCNN"])]
    def pfb(N, K, n=50):  # exact hypergeometric P(min class count < 10)
        tot = comb(N, n); lo = sum(comb(K, j) * comb(N - K, n - j) for j in range(0, 10))
        hi = sum(comb(K, j) * comb(N - K, n - j) for j in range(n - 9, n + 1)); return (lo + hi) / tot
    pr = [pfb(int(r.flagged), int(r["true"])) for _, r in fr.iterrows()]
    check("SI Note 3: fallback probability at n=50 is 0.65-0.98 (exact)", (round(min(pr), 2), round(max(pr), 2)) == (0.65, 0.98),
          f"{min(pr):.3f}-{max(pr):.3f}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:]]
    results_dir = args[0] if args else "results"
    main(results_dir)
    if len(args) > 1:
        revision_checks(results_dir, args[1])
    print(f"\n{len(FAILURES)} check(s) failed" if FAILURES else "\nall checks passed")
    sys.exit(1 if FAILURES else 0)
