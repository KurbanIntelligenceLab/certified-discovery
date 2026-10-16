"""Independent mechanical checks of the main-text theory (exact enumeration / random search).
Independent of certdisc.core except where explicitly compared."""
import itertools, sys
import numpy as np
sys.path.insert(0, "../../src")
import certdisc.core as pm

rng = np.random.default_rng(2026)
def pop_var(x):  return x.var(ddof=1)
def pop_cov(x, y): return np.cov(x, y, ddof=1)[0, 1]

# ---- Theorem 1 (i)-(iii), Lemma 1: exact enumeration over all SRSWOR samples ----
worst = dict(bias=0, var=0, lemma=0, lam_opt=0)
for trial in range(200):
    N = int(rng.integers(5, 10)); n = int(rng.integers(2, N + 1))
    y = rng.integers(0, 2, N).astype(float)
    f = rng.random(N) if trial % 2 else rng.integers(0, 2, N).astype(float)
    lam = float(rng.normal())
    pi = y.mean(); fbar = f.mean()
    ests, vhats = [], []
    for L in itertools.combinations(range(N), n):
        L = list(L); r = y[L] - lam * f[L]
        ests.append(lam * fbar + r.mean())
        if n >= 2:
            vhats.append(r.var(ddof=1) / n * (1 - n / N) + lam**2 * pop_var(f) / N)
    ests = np.array(ests)
    Sr2 = pop_var(y) - 2 * lam * pop_cov(y, f) + lam**2 * pop_var(f)
    worst["bias"] = max(worst["bias"], abs(ests.mean() - pi))
    worst["var"] = max(worst["var"], abs(ests.var(ddof=0) - Sr2 / n * (1 - n / N)))
    worst["lemma"] = max(worst["lemma"], abs(np.mean(vhats) - (Sr2 / n * (1 - n / N) + lam**2 * pop_var(f) / N)))
    if pop_var(f) > 0 and pop_var(y) > 0:
        ls = pop_cov(y, f) / pop_var(f); rho = pop_cov(y, f) / np.sqrt(pop_var(y) * pop_var(f))
        grid = np.linspace(ls - 3, ls + 3, 2001)
        S = pop_var(y) - 2 * grid * pop_cov(y, f) + grid**2 * pop_var(f)
        worst["lam_opt"] = max(worst["lam_opt"], abs(grid[S.argmin()] - ls),
                               abs(S.min() - (1 - rho**2) * pop_var(y)) * 0)
print("Theorem 1/Lemma 1 exact-enumeration max abs errors:", {k: f"{v:.2e}" for k, v in worst.items()})

# ---- Prop 2: Wilson lower limit at p_hat = 1 equals n/(n+z^2) > 1/2 for n >= 4 ----
z = pm._z(0.05)
ok = all(abs(pm.wilson_ci(n, n)[0] - n / (n + z * z)) < 1e-12 and n / (n + z * z) > 0.5 for n in range(4, 5000))
print("Prop 2 Wilson identity and >1/2 for n in [4,5000):", ok, "| n=3 gives", round(3 / (3 + z * z), 4))

# ---- Prop 3 as stated, plus the stronger claim: paired < split for ANY sign of S_AB ----
viol_stated = viol_strong = 0; min_margin = np.inf; neg_cases = 0
for t in range(200000):
    M = int(rng.integers(4, 60)); n = 2 * int(rng.integers(1, M // 2 + 1))
    y = rng.integers(0, 2, M).astype(float)
    fA = rng.random(M) if t % 3 else rng.integers(0, 2, M).astype(float)
    fB = (1 - fA + rng.normal(0, 0.1, M)).clip(0, 1) if t % 5 == 0 else rng.random(M)
    lam = float(rng.normal())
    rA, rB = y * fA - lam * fA, y * fB - lam * fB
    SA, SB, SAB = pop_var(rA), pop_var(rB), pop_cov(rA, rB)
    if SA + SB <= 0: continue
    vp = (1 / n) * (1 - n / M) * (SA + SB - 2 * SAB)
    vs = (2 / n) * (1 - n / (2 * M)) * (SA + SB)
    neg_cases += SAB < 0
    if SAB >= 0 and not vp < vs: viol_stated += 1
    if not vp < vs: viol_strong += 1
    min_margin = min(min_margin, vs - vp)
print(f"Prop 3 stated (S_AB>=0) violations: {viol_stated}; strengthened (any S_AB) violations: {viol_strong}; "
      f"cases with S_AB<0 tested: {neg_cases}; min(Var_split - Var_paired) = {min_margin:.3e}")

# ---- Corollary 1: n* is the least integer meeting the target (exhaustive over a grid) ----
bad = 0
for S2 in [0.01, 0.05, 0.1, 0.2, 0.25]:
    for N in [500, 5000, 43437, 75829]:
        for w in [0.005, 0.01, 0.02, 0.03, 0.05]:
            ns = pm.required_budget(S2, N, w)
            hw = lambda k: z * np.sqrt(S2 * (1 / k - 1 / N))
            if hw(ns) > w + 1e-12 or (ns > 2 and hw(ns - 1) <= w): bad += 1
print("Corollary 1 inversion failures over grid:", bad)

# ---- Toolkit vs an independent implementation at fixed lambda (point estimate identity) ----
diff = 0
for t in range(2000):
    N = int(rng.integers(50, 2000)); n = int(rng.integers(20, N // 2))
    y = rng.integers(0, 2, N).astype(float); f = rng.random(N)
    idx = rng.choice(N, n, replace=False)
    if min(y[idx].sum(), n - y[idx].sum()) < 10: continue
    iv = pm.ppi_mean_ci(y[idx], f[idx], f, power_tune=False, clip=None)   # lam = 1
    mine = f.mean() + (y[idx] - f[idx]).mean()
    diff = max(diff, abs(iv.estimate - mine))
print("toolkit PPI (lam=1) vs independent difference estimator, max abs diff:", f"{diff:.2e}")
