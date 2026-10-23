"""
certdisc.core
=============
Prediction-powered inference (PPI) for AI-driven materials discovery.

Implements the paper's core quantities:
  * Classical (label-only) confidence intervals for discovery precision / yield.
  * Imputation ("trust the model") point estimates, to quantify naive bias.
  * PPI and PPI++ (power-tuned) confidence intervals for:
      - discovery precision on a screened (predicted-stable) candidate set,
      - the total count of stable materials in a candidate pool,
      - differences in precision between two models (paired comparison).
  * Stratified PPI with Neyman-style variance-optimal DFT budget allocation.
  * Bootstrap utilities and a coverage simulation harness.

Design notes
------------
- numpy-only. No fabricated outcomes: every function COMPUTES from inputs.
- Estimands are means of indicator variables over a finite screened pool, so
  PPI for the mean (Angelopoulos et al., Science 2023) and PPI++ power tuning
  (Angelopoulos, Duchi, Zrnic 2023) apply directly; we implement the
  finite-population correction explicitly because screening pools are finite.
- "Labels" are DFT-verified binary stability indicators (E_above_hull <= tau).
  "Predictions" are model-derived binary stability calls on the same pool.
- Selection-awareness: all inference is conditional on the screened pool S
  (the set the model flagged stable). Labels must be sampled uniformly at
  random (or stratified-randomly) FROM S; the functions assume and document
  this sampling design. Sampling labels from outside S and reusing them
  inside S is invalid and is deliberately not supported.

Cross-check: at fixed lambda the point estimate coincides with the reference
implementation ppi_py 0.2.3 (ppi_mean_pointestimate with the whole pool passed as the
unlabeled set); see experiments/verification/ppi_py_crosscheck.py. The tuned
coefficient is the finite-population regression slope Cov/Var, whereas the PPI++
default is Cov/((1 + n/N_u) Var) for a separate unlabeled sample of size N_u.
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass

Z_TABLE = {0.90: 1.6448536269514722, 0.95: 1.959963984540054, 0.99: 2.5758293035489004}


def _z(alpha: float) -> float:
    """Two-sided normal quantile for confidence level 1 - alpha."""
    conf = 1.0 - alpha
    if conf in Z_TABLE:
        return Z_TABLE[conf]
    # Acklam-style rational approximation of the normal inverse CDF.
    p = 1.0 - alpha / 2.0
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    plow, phigh = 0.02425, 1 - 0.02425
    if p < plow:
        q = np.sqrt(-2 * np.log(p))
        return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p > phigh:
        q = np.sqrt(-2 * np.log(1 - p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    q = p - 0.5
    r = q * q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)


@dataclass
class Interval:
    """A point estimate with a two-sided confidence interval."""
    estimate: float
    lower: float
    upper: float
    alpha: float
    n_labeled: int
    method: str

    @property
    def width(self) -> float:
        return self.upper - self.lower

    def __str__(self) -> str:
        return (f"{self.method}: {self.estimate:.4f} "
                f"[{self.lower:.4f}, {self.upper:.4f}] "
                f"(1-alpha={1-self.alpha:.2f}, n={self.n_labeled})")


# ---------------------------------------------------------------------------
# Classical and imputation baselines
# ---------------------------------------------------------------------------

def classical_ci(y_labeled: np.ndarray, alpha: float = 0.05,
                 pool_size: int | None = None) -> Interval:
    """Label-only CI for a mean over the screened pool.

    y_labeled : binary (or bounded) outcomes on a uniform random sample of
                the screened pool S.
    pool_size : |S|; if given, applies the finite-population correction.
    """
    y = np.asarray(y_labeled, dtype=float)
    n = y.size
    mu = y.mean()
    var = y.var(ddof=1) if n > 1 else 0.0
    fpc = 1.0 if pool_size is None else max(0.0, (pool_size - n) / max(pool_size - 1, 1))
    se = np.sqrt(var / n * fpc)
    z = _z(alpha)
    return Interval(mu, max(0.0, mu - z * se), min(1.0, mu + z * se), alpha, n, "classical")


def imputation_estimate(yhat_pool: np.ndarray) -> float:
    """Naive 'trust the model' estimate: mean prediction over the pool.

    This is the estimator implicit in headline claims of the form
    'our model discovered N stable materials'. It carries the model's
    full bias and admits no valid CI; returned for bias quantification only.
    """
    return float(np.asarray(yhat_pool, dtype=float).mean())


def wilson_ci(successes: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion (no fpc; conservative)."""
    z = _z(alpha)
    if n == 0:
        return 0.0, 1.0
    p = successes / n
    denom = 1.0 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, center - half), min(1.0, center + half)


SMALL_SAMPLE_MIN_CLASS_COUNT = 10  # threshold documented in the paper (A2)


# ---------------------------------------------------------------------------
# PPI and PPI++ for a mean over a finite screened pool
# ---------------------------------------------------------------------------

def ppi_mean_ci(y_labeled: np.ndarray, yhat_labeled: np.ndarray,
                yhat_pool: np.ndarray, alpha: float = 0.05,
                power_tune: bool = True, clip: tuple[float, float] | None = (0.0, 1.0)
                ) -> Interval:
    """Prediction-powered CI for the mean outcome over a screened pool S.

    Parameters
    ----------
    y_labeled    : DFT labels on the labeled subsample of S (size n).
    yhat_labeled : model predictions on that same subsample.
    yhat_pool    : model predictions on ALL of S (size N), including the
                   labeled subsample (finite-pool convention).
    power_tune   : if True, uses the PPI++ tuning lambda* = cov(y, yhat)/var(yhat)
                   estimated on the labeled sample (Angelopoulos et al. 2023),
                   which guarantees the interval is never asymptotically wider
                   than the classical one.
    clip         : clip the CI to this range (probabilities live in [0, 1];
                   pass None for unbounded estimands such as counts / N).

    Estimator: theta_hat = mean(yhat_pool)*lam + mean(y - lam*yhat on labeled)
    which is unbiased for the pool mean of y for any fixed lam.
    """
    y = np.asarray(y_labeled, dtype=float)
    f_l = np.asarray(yhat_labeled, dtype=float)
    f_p = np.asarray(yhat_pool, dtype=float)
    n, N = y.size, f_p.size
    if n < 2:
        raise ValueError("need at least 2 labeled points")

    # Small-sample / rare-positive fallback (paper, Assumption A2 and
    # Supplementary Note 3): if either labeled class has fewer than
    # SMALL_SAMPLE_MIN_CLASS_COUNT members, the normal approximation for the
    # rectifier is unreliable; fall back to lambda = 0 (the classical
    # estimator) with a Wilson score interval, which is conservative here
    # because it omits the finite-population correction.
    if set(np.unique(y)).issubset({0.0, 1.0}):
        pos = int(y.sum())
        if min(pos, n - pos) < SMALL_SAMPLE_MIN_CLASS_COUNT:
            lo, hi = wilson_ci(pos, n, alpha)
            return Interval(pos / n, lo, hi, alpha, n,
                            "Wilson (small-sample fallback, lambda=0)")

    if power_tune:
        vf = f_l.var(ddof=1)
        # Variance-optimal coefficient (Theorem 1(iii)): the pool regression
        # slope Cov_S(y,f)/Var_S(f), estimated on the labeled sample. No
        # budget-dependent shrinkage: sigma_r^2(lam) does not depend on n,
        # and at n = N the estimator equals the census mean for every lam.
        lam = float(np.cov(y, f_l, ddof=1)[0, 1] / vf) if vf > 0 else 0.0
    else:
        lam = 1.0

    rect = y - lam * f_l                      # rectifier terms on labeled sample
    theta = lam * f_p.mean() + rect.mean()    # PPI point estimate

    var_rect = rect.var(ddof=1)
    var_f = f_p.var(ddof=1) if N > 1 else 0.0
    # Exact SRSWOR variance (Theorem 1(ii)): S_r^2/n * (1 - n/N) with the
    # (n-1)-normalized sample variance; plus a deliberately conservative
    # lam^2 * Var(f)/N term absorbing plug-in variability of lam (see paper).
    fpc = max(0.0, 1.0 - n / N)
    se = np.sqrt(var_rect / n * fpc + lam ** 2 * var_f / N)

    z = _z(alpha)
    lo, hi = theta - z * se, theta + z * se
    if clip is not None:
        lo, hi = max(clip[0], lo), min(clip[1], hi)
        theta = min(max(theta, clip[0]), clip[1])
    return Interval(theta, lo, hi, alpha, n, "PPI++" if power_tune else "PPI")


def ppi_count_ci(y_labeled, yhat_labeled, yhat_pool, alpha: float = 0.05,
                 power_tune: bool = True) -> Interval:
    """CI for the COUNT of true positives (stable materials) in the screened
    pool: count = |S| * precision. Wraps ppi_mean_ci and rescales."""
    N = np.asarray(yhat_pool).size
    iv = ppi_mean_ci(y_labeled, yhat_labeled, yhat_pool, alpha, power_tune, clip=(0.0, 1.0))
    return Interval(iv.estimate * N, iv.lower * N, iv.upper * N, alpha,
                    iv.n_labeled, iv.method + " (count)")


def ppi_yield_diff_ci(y_labeled, fA_l, fB_l, fA_pool, fB_pool,
                      alpha: float = 0.05) -> Interval:
    """Paired CI for the difference in CERTIFIED YIELD between models A and B
    over a COMMON candidate pool U.

    Certified yield of model M is the fraction of U that is both flagged
    stable by M and truly stable: q_M = mean_i[ y_i * f_M(i) ]. The paired
    difference q_A - q_B is estimable with ONE label sample drawn uniformly
    from U (one DFT budget serves all models).

    Note: a *precision* difference across two different screened pools is not
    a paired estimand; estimate each precision with ppi_mean_ci on its own
    pool-sampled labels and difference the intervals conservatively instead.

    y_labeled : DFT labels on a uniform sample of U (size n).
    fA_l/fB_l : each model's binary calls on that sample.
    fA_pool/fB_pool : each model's calls on all of U (size N).
    """
    y = np.asarray(y_labeled, float)
    fA_l = np.asarray(fA_l, float); fB_l = np.asarray(fB_l, float)
    fA_p = np.asarray(fA_pool, float); fB_p = np.asarray(fB_pool, float)
    if not (y.size == fA_l.size == fB_l.size):
        raise ValueError("labeled arrays must be aligned")
    if fA_p.size != fB_p.size:
        raise ValueError("paired comparison requires a common pool")
    n, N = y.size, fA_p.size
    d_y = y * (fA_l - fB_l)            # per-item outcome difference
    d_f = fA_l - fB_l                  # its model-computable proxy
    vf = d_f.var(ddof=1)
    lam = float(np.cov(d_y, d_f, ddof=1)[0, 1] / vf) if vf > 0 else 0.0
    rect = d_y - lam * d_f                    # (y - lam) * (fA - fB) per item
    theta = lam * (fA_p.mean() - fB_p.mean()) + rect.mean()
    fpc = max(0.0, 1.0 - n / N)
    se = np.sqrt(rect.var(ddof=1) / n * fpc +
                 lam ** 2 * (fA_p - fB_p).var(ddof=1) / N)
    z = _z(alpha)
    return Interval(theta, theta - z * se, theta + z * se, alpha, n,
                    "PPI++ yield diff (paired)")


def required_budget(rect_var: float, pool_size: int, half_width: float,
                    alpha: float = 0.05) -> int:
    """Closed-form certification budget (paper, Corollary 1).

    Minimal n such that the (fixed-lambda) interval half-width
    z * sqrt(S_r^2 (1/n - 1/N)) is at most `half_width`:
        n*(w) = ceil( N z^2 S_r^2 / (N w^2 + z^2 S_r^2) ),
    clipped to [2, N]. As N -> infinity this recovers the classical
    z^2 S_r^2 / w^2. `rect_var` is (a pilot estimate of) S_r^2 at the
    working lambda; at the optimal lambda, S_r^2 = S_y^2 (1 - rho^2).
    """
    N, z, S2, w = pool_size, _z(alpha), float(rect_var), float(half_width)
    if S2 <= 0:
        return 2
    n = int(np.ceil(N * z * z * S2 / (N * w * w + z * z * S2)))
    return int(min(max(n, 2), N))


# ---------------------------------------------------------------------------
# Stratified PPI with variance-optimal DFT budget allocation
# ---------------------------------------------------------------------------

def neyman_allocation(strata_sizes, strata_rect_sd, budget: int,
                      min_per_stratum: int = 2) -> np.ndarray:
    """Variance-minimizing allocation of a DFT label budget across strata.

    n_k proportional to N_k * sd_k (Neyman allocation), with a floor of
    min_per_stratum labels per stratum and capping at stratum size.
    strata_rect_sd should be a pilot estimate of the rectifier SD per stratum
    (from a small uniform pilot); pass ones for proportional allocation.
    """
    N = np.asarray(strata_sizes, dtype=float)
    s = np.asarray(strata_rect_sd, dtype=float)
    K = N.size
    if budget < K * min_per_stratum:
        raise ValueError("budget too small for the requested per-stratum floor")
    w = N * np.maximum(s, 1e-12)
    n = np.maximum(min_per_stratum, np.floor(budget * w / w.sum()).astype(int))
    n = np.minimum(n, N.astype(int))
    # greedy fix-up to hit the budget exactly
    while n.sum() > budget:
        k = int(np.argmax(n - min_per_stratum))
        if n[k] <= min_per_stratum:
            break
        n[k] -= 1
    while n.sum() < budget:
        deficit_gain = w / np.maximum(n, 1)
        deficit_gain[n >= N] = -np.inf
        k = int(np.argmax(deficit_gain))
        if not np.isfinite(deficit_gain[k]):
            break
        n[k] += 1
    return n


def stratified_ppi_ci(strata: list[dict], alpha: float = 0.05) -> Interval:
    """Stratified PPI CI for the pool-level precision.

    strata : list of dicts with keys
             'y' (labels in stratum sample), 'f_l' (predictions on sample),
             'f_pool' (predictions on the whole stratum).
    The pool estimand is the size-weighted average of stratum means.
    """
    total_N = sum(np.asarray(s["f_pool"]).size for s in strata)
    est, var = 0.0, 0.0
    n_total = 0
    for s in strata:
        Nk = np.asarray(s["f_pool"]).size
        wk = Nk / total_N
        iv = ppi_mean_ci(s["y"], s["f_l"], s["f_pool"], alpha, power_tune=True)
        sek = (iv.upper - iv.lower) / (2 * _z(alpha))
        est += wk * iv.estimate
        var += (wk * sek) ** 2
        n_total += iv.n_labeled
    z = _z(alpha)
    se = np.sqrt(var)
    return Interval(est, max(0.0, est - z * se), min(1.0, est + z * se),
                    alpha, n_total, "stratified PPI++")


# ---------------------------------------------------------------------------
# Evaluation harness: coverage and width, given a fully labeled pool
# ---------------------------------------------------------------------------

def simulate_campaign(y_pool: np.ndarray, yhat_pool: np.ndarray, n_label: int,
                      n_rep: int = 1000, alpha: float = 0.05,
                      seed: int = 0) -> dict:
    """Monte-Carlo coverage/width study on a FULLY LABELED pool (e.g. WBM),
    hiding all but n_label labels per replicate. Computes:
      - empirical coverage and mean width for classical vs PPI++,
      - the imputation (naive) bias,
    against the true pool precision, which is known here by construction.
    """
    rng = np.random.default_rng(seed)
    y_pool = np.asarray(y_pool, float)
    f_pool = np.asarray(yhat_pool, float)
    N = y_pool.size
    truth = y_pool.mean()
    cover = {"classical": 0, "ppi": 0}
    width = {"classical": [], "ppi": []}
    for _ in range(n_rep):
        idx = rng.choice(N, size=n_label, replace=False)
        y_l, f_l = y_pool[idx], f_pool[idx]
        c = classical_ci(y_l, alpha, pool_size=N)
        p = ppi_mean_ci(y_l, f_l, f_pool, alpha)
        cover["classical"] += (c.lower <= truth <= c.upper)
        cover["ppi"] += (p.lower <= truth <= p.upper)
        width["classical"].append(c.width)
        width["ppi"].append(p.width)
    return {
        "truth": truth,
        "imputation_estimate": imputation_estimate(f_pool),
        "imputation_bias": imputation_estimate(f_pool) - truth,
        "coverage_classical": cover["classical"] / n_rep,
        "coverage_ppi": cover["ppi"] / n_rep,
        "mean_width_classical": float(np.mean(width["classical"])),
        "mean_width_ppi": float(np.mean(width["ppi"])),
        "width_reduction": 1.0 - float(np.mean(width["ppi"])) / float(np.mean(width["classical"])),
        "n_label": n_label, "n_rep": n_rep, "alpha": alpha,
    }


def budget_curve(y_pool, yhat_pool, budgets, n_rep=500, alpha=0.05, seed=0):
    """Mean CI width vs DFT budget, classical vs PPI++. Returns list of dicts."""
    return [simulate_campaign(y_pool, yhat_pool, b, n_rep, alpha, seed + i)
            for i, b in enumerate(budgets)]


# ---------------------------------------------------------------------------
# Smoke test on synthetic data (demonstrates EXPECTED BEHAVIOR, not results)
# ---------------------------------------------------------------------------

def _smoke_test():
    rng = np.random.default_rng(42)
    # Synthetic screened pool: N candidates the model called "stable".
    # True stability correlates with a latent score; the model's binary call
    # is imperfect and optimistically biased, mimicking uMLIP screening.
    N = 20000
    latent = rng.normal(0, 1, N)
    p_true = 1 / (1 + np.exp(-(latent - 0.4) * 2.2))     # true P(stable)
    y = rng.binomial(1, p_true).astype(float)             # DFT ground truth
    noise = rng.normal(0, 0.9, N)
    yhat = ((latent + noise) > -0.25).astype(float)       # optimistic model call

    truth = y.mean()
    naive = imputation_estimate(yhat)
    print(f"true pool precision      : {truth:.4f}")
    print(f"naive/imputation estimate: {naive:.4f}  (bias {naive-truth:+.4f})")

    res = simulate_campaign(y, yhat, n_label=300, n_rep=400, alpha=0.05, seed=1)
    print(f"coverage  classical={res['coverage_classical']:.3f}  "
          f"PPI++={res['coverage_ppi']:.3f}  (target 0.95)")
    print(f"mean width classical={res['mean_width_classical']:.4f}  "
          f"PPI++={res['mean_width_ppi']:.4f}  "
          f"(reduction {res['width_reduction']*100:.1f}%)")

    # Checks: both methods must cover near 1-alpha; PPI must not be wider.
    assert res["coverage_classical"] >= 0.90, "classical coverage broken"
    assert res["coverage_ppi"] >= 0.90, "PPI coverage broken"
    assert res["mean_width_ppi"] <= res["mean_width_classical"] * 1.02, \
        "PPI++ should never be materially wider than classical"

    # Paired model comparison: model B strictly noisier than A, so A's
    # certified yield over the common pool should exceed B's.
    yhatB = ((latent + rng.normal(0, 1.6, N)) > -0.25).astype(float)
    idx = rng.choice(N, 400, replace=False)
    d = ppi_yield_diff_ci(y[idx], yhat[idx], yhatB[idx], yhat, yhatB)
    true_diff = (y * yhat).mean() - (y * yhatB).mean()
    print(f"paired yield diff A-B: {d}  (truth {true_diff:+.4f})")
    assert d.lower <= true_diff <= d.upper, "paired diff CI missed the truth"

    # Stratified + Neyman allocation sanity check.
    strata_id = (latent > 0).astype(int)
    sizes = [int((strata_id == k).sum()) for k in (0, 1)]
    pilot_idx = rng.choice(N, 100, replace=False)
    sds = []
    for k in (0, 1):
        m = strata_id[pilot_idx] == k
        r = y[pilot_idx][m] - yhat[pilot_idx][m]
        sds.append(r.std(ddof=1) if m.sum() > 1 else 1.0)
    alloc = neyman_allocation(sizes, sds, budget=300)
    print(f"Neyman allocation over strata sizes {sizes}: {alloc.tolist()}")
    strata = []
    for k in (0, 1):
        mask = strata_id == k
        ids = rng.choice(np.where(mask)[0], alloc[k], replace=False)
        strata.append({"y": y[ids], "f_l": yhat[ids], "f_pool": yhat[mask]})
    s = stratified_ppi_ci(strata)
    print("stratified PPI++:", s)
    assert s.lower <= truth <= s.upper or abs(s.estimate - truth) < 0.05
    # Small-sample fallback: with n=15 labels and rare positives the
    # estimator must return the Wilson fallback and still cover plausibly.
    idx_small = rng.choice(N, 15, replace=False)
    tiny = ppi_mean_ci(y[idx_small], yhat[idx_small], yhat)
    assert "Wilson" in tiny.method or min(int(y[idx_small].sum()),
                                          15 - int(y[idx_small].sum())) >= 10
    print("small-sample fallback check:", tiny.method)

    # Budget rule (Corollary 1): algebraic inversion check. The width
    # implied by the formula at n_req must meet the target, and at n_req - 1
    # must miss it (whenever n_req > 2), using the same S_r^2.
    S2 = float((y - yhat * 0.5).var(ddof=1))  # any working-lambda rectifier
    z95 = 1.959963984540054
    for w in (0.05, 0.02, 0.01):
        n_req = required_budget(S2, N, w)
        def half_width(n):
            return z95 * np.sqrt(S2 * (1.0 / n - 1.0 / N))
        assert half_width(n_req) <= w + 1e-12
        if n_req > 2:
            assert half_width(n_req - 1) > w
    print("budget-rule inversion check passed")
    print("SMOKE TEST PASSED")


if __name__ == "__main__":
    _smoke_test()
