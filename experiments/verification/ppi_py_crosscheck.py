import sys, numpy as np
sys.path.insert(0, "../../src")
from ppi_py import ppi_mean_pointestimate
import certdisc.core as pm
rng = np.random.default_rng(7); worst_pt = 0; lam_ratio = []
for t in range(200):
    N = int(rng.integers(2000, 20000)); n = int(rng.integers(100, 800))
    y = rng.integers(0, 2, N).astype(float); f = np.clip(y * 0.3 + rng.random(N) * 0.7, 0, 1)
    idx = rng.choice(N, n, replace=False)
    for lam in (0.0, 0.5, 1.0):
        ref = float(np.atleast_1d(ppi_mean_pointestimate(y[idx], f[idx], f, lam=lam))[0])
        mine = lam * f.mean() + (y[idx] - lam * f[idx]).mean()
        worst_pt = max(worst_pt, abs(ref - mine))
        if lam == 1.0:
            worst_pt = max(worst_pt, abs(pm.ppi_mean_ci(y[idx], f[idx], f, power_tune=False, clip=None).estimate - ref))
print(f"ppi_py vs toolkit/independent point estimates at fixed lambda: max abs diff {worst_pt:.2e}")
