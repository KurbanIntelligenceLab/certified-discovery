"""EXP-5: exact re-execution of the paper's E1 (coverage, Table 1/SI Table 1) and E3 (Table 2, SI Table 4)
protocols for the five earlier-generation models, using the independent loader in wbm_data.py and the
released estimator code. Same seeds as the run of record (BASE_SEED=0; E3 uses BASE_SEED+2)."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "../src")
from certdisc.core import ppi_mean_ci, ppi_yield_diff_ci, classical_ci
from wbm_data import load, campaign
import os
MODE = os.environ.get("MODELS", "five"); SUF = "_15models" if MODE == "all" else ""
wbm, EP = load(MODE); SD = "../results/"
t1 = pd.read_csv(SD + "table1_raw.csv")
rows = []
for m in EP:
    for pool in ("full", "uniq_protos"):
        for tau in (0.0, 0.05, 0.1):
            _, y, f = campaign(wbm, EP[m], tau, uniq=(pool == "uniq_protos"))
            N, truth = len(y), y.mean(); rng = np.random.default_rng(0)
            cov = cov_c = 0; lo, hi = [], []
            for _ in range(1000):
                idx = rng.choice(N, 500, replace=False)
                ci = ppi_mean_ci(y[idx], f[idx], f); cc = classical_ci(y[idx], pool_size=N)
                cov += ci.lower <= truth <= ci.upper; cov_c += cc.lower <= truth <= cc.upper
                lo.append(ci.lower * N); hi.append(ci.upper * N)
            ref = t1[(t1.model == m) & (t1.pool == pool) & (t1.tau == tau)].iloc[0]
            rows.append(dict(model=m, pool=pool, tau=tau, coverage=cov / 1000, paper_coverage=ref.coverage,
                             ci_lo=round(np.median(lo)), ci_hi=round(np.median(hi)), paper_lo=ref.ci_lo,
                             paper_hi=ref.ci_hi, classical_coverage=cov_c / 1000))
e1 = pd.DataFrame(rows); e1.to_csv(f"results/exp5_e1_reproduction{SUF}.csv", index=False)
m1 = ((e1.coverage == e1.paper_coverage) & (e1.ci_lo == e1.paper_lo) & (e1.ci_hi == e1.paper_hi)).sum()
print(f"E1 re-execution: {m1}/{len(e1)} configs identical (coverage and median CI) to table1_raw.csv")
print(f"  classical coverage at n=500 (same draws): {e1.classical_coverage.min():.3f}-{e1.classical_coverage.max():.3f}")

def holm(p):
    p = np.asarray(p, float); o = np.argsort(p); adj = np.empty(len(p)); run = 0.0
    for r, i in enumerate(o):
        run = max(run, (len(p) - r) * p[i]); adj[i] = min(run, 1.0)
    return adj
mae = pd.read_csv(SD + "model_mae.csv").set_index("model").mae_eV_per_atom
order = sorted(EP, key=mae.get); pairs = list(zip(order[:-1], order[1:]))
y_all = (wbm["e_above_hull_mp2020_corrected_ppd_mp"] <= 0).to_numpy(float)
t2 = pd.read_csv(SD + "table2_raw.csv").set_index("pair"); t2b = pd.read_csv(SD + "table2_budget_sensitivity.csv").set_index("pair")
out = []
for budget, ref in ((500, t2), (2000, t2b)):
    for A, B in pairs:
        ok = (EP[A].notna() & EP[B].notna() & wbm["e_above_hull_mp2020_corrected_ppd_mp"].notna()).to_numpy()
        fA = (EP[A].to_numpy() <= 0)[ok].astype(float); fB = (EP[B].to_numpy() <= 0)[ok].astype(float); y = y_all[ok]
        u = (fA + fB) > 0; yu, fAu, fBu = y[u], fA[u], fB[u]; M = len(yu); rng = np.random.default_rng(2)
        e = []
        for _ in range(200):
            idx = rng.choice(M, min(budget, M // 2), replace=False)
            ci = ppi_yield_diff_ci(yu[idx], fAu[idx], fBu[idx], fAu, fBu); e.append((ci.estimate, ci.lower, ci.upper))
        est, lo, hi = (float(np.median([x[k] for x in e])) for k in range(3))
        r = ref.loc[f"{A} vs {B}"]
        out.append(dict(budget=budget, pair=f"{A} vs {B}", dq=est, lo=lo, hi=hi,
                        identical=bool(np.isclose([est, lo, hi], [r.dq, r.lo, r.hi], atol=1e-12).all())))
e3 = pd.DataFrame(out); e3.to_csv(f"results/exp5_e3_reproduction{SUF}.csv", index=False)
print(f"E3 re-execution: {int(e3.identical.sum())}/{len(e3)} rows identical to table2_raw / table2_budget_sensitivity")
