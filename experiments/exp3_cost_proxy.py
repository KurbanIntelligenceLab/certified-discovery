"""EXP-3 (R2.3, R1.3): what a verification budget of n labels costs when per-structure DFT cost varies.
Exact identity: under uniform sampling without replacement every pool member has inclusion probability n/N,
so the expected total cost of the verified sample is (n/N) x (total cost of verifying the whole pool),
whatever the cost distribution. Spread of the realized cost is measured by simulation with a size proxy
c_i = n_sites^p, p in {1, 3} (sensitivity bracket for plane-wave DFT; a proxy, not a measured cost)."""
import numpy as np, pandas as pd
from wbm_data import load, campaign
wbm, EP = load(); rng = np.random.default_rng(11); rows = []
ns_all = wbm["n_sites"].to_numpy(float)
for m in EP:
    idx, y, _ = campaign(wbm, EP[m], 0.0); ns = wbm.loc[idx, "n_sites"].to_numpy(float); N = len(ns)
    for p in (1, 3):
        c = ns ** p; exp_cost = 500 / N * c.sum()
        real = np.array([c[rng.choice(N, 500, replace=False)].sum() for _ in range(10000)]) / exp_cost
        rows.append(dict(model=m, N=N, proxy=f"n_sites^{p}", median_sites=np.median(ns), p95_sites=np.percentile(ns, 95),
                         cv_per_structure=c.std() / c.mean(), mean_realized_over_expected=real.mean(),
                         q025=np.quantile(real, 0.025), q975=np.quantile(real, 0.975), sample_fraction_pct=100 * 500 / N))
d = pd.DataFrame(rows); d.to_csv("results/exp3_cost_proxy.csv", index=False)
print(d.round(3).to_string(index=False))
print(f"WBM universe n_sites: median {np.median(ns_all):.0f}, 95th pct {np.percentile(ns_all,95):.0f}, max {ns_all.max():.0f}")
