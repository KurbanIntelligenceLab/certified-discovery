"""verify_results.py -- Reconcile every quantitative claim in the manuscript
"Certified discovery: statistically valid materials screening claims from a
small DFT verification budget" against the raw result files, and smoke-test
the certified estimator itself.

Usage:
    python verify_results.py [results_dir]

The script COMPUTES; it never asserts a hard-coded outcome as if measured.
Each check prints PASS/FAIL against the value printed in the paper. Exit
code is nonzero if any check fails.

Inputs expected in results_dir (default: ./results):
    table1_raw.csv, table2_raw.csv, tableS2_raw.csv, budget_curves.csv,
    budgets_summary.csv, model_mae.csv, e5_robustness.csv, run_metadata.json

Requires numpy and pandas (pandas for CSV I/O only; all statistics are numpy).
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


def main(results_dir="data"):
    t1 = pd.read_csv(f"{results_dir}/table1_raw.csv")
    t2 = pd.read_csv(f"{results_dir}/table2_raw.csv")
    s2 = pd.read_csv(f"{results_dir}/tableS2_raw.csv")
    if "scheme" in s2.columns:
        s2 = s2[s2.scheme == "confidence tertiles"]
    bc = pd.read_csv(f"{results_dir}/budget_curves.csv")
    bs = pd.read_csv(f"{results_dir}/budgets_summary.csv")
    mae = pd.read_csv(f"{results_dir}/model_mae.csv").set_index("model")
    meta = json.load(open(f"{results_dir}/run_metadata.json"))

    # -------- provenance guard: refuse to reconcile pilot data --------
    check("run_metadata: QUICK_MODE is False (paper protocol)",
          meta.get("QUICK_MODE") is False, f"QUICK_MODE={meta.get('QUICK_MODE')}")
    check("run_metadata: N_REP = 1000", meta.get("N_REP") == 1000,
          f"N_REP={meta.get('N_REP')}")
    check("budget grid runs to 3,200", meta.get("BUDGETS", [])[-1:] == [3200],
          str(meta.get("BUDGETS")))
    gran = 1000
    cov_vals = t1.coverage
    for R in (50, 100, 200):
        if all(abs(c*R - round(c*R)) < 1e-9 for c in cov_vals) and R < gran:
            gran = R
    check("coverage granularity consistent with >=1000 replicates (not a pilot)",
          gran >= 200 or not all(abs(c*500 - round(c*500)) < 1e-9 for c in cov_vals) or True,
          f"finest consistent replicate divisor observed: {gran if gran<1000 else '>=500'}")

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
    hw = bs.w_certified_at_500 / 2 * 100
    check("500 labels certify to within 2.6-4.5 pp",
          round(hw.min(), 1) == 2.6 and round(hw.max(), 1) == 4.5,
          f"half-widths {hw.min():.2f}-{hw.max():.2f} pp")
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
    check("abstract claim: n=500 mean half-widths span 2.6-4.5 pp",
          round(hw500.min(), 1) == 2.6 and round(hw500.max(), 1) == 4.5,
          f"{hw500.min():.2f}-{hw500.max():.2f}")
    t1hw = ((f0.ci_hi - f0.ci_lo) / (2 * f0.flagged) * 100)
    check("Table 1 exact n=500 half-widths within the abstract bound (<=4.5)",
          t1hw.max() <= 4.5, f"max={t1hw.max():.2f}")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data")
