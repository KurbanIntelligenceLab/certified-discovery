# API reference

Auto-generated from the docstrings in `src/certdisc/core.py`. Every interval-
returning function yields an `Interval` with `.estimate`, `.lower`, `.upper`,
`.width`, `.method`, `.alpha`, and `.n_labeled`.

## `classical_ci(y_labeled: 'np.ndarray', alpha: 'float' = 0.05, pool_size: 'int | None' = None) -> 'Interval'`

Label-only CI for a mean over the screened pool.

y_labeled : binary (or bounded) outcomes on a uniform random sample of
            the screened pool S.
pool_size : |S|; if given, applies the finite-population correction.

## `imputation_estimate(yhat_pool: 'np.ndarray') -> 'float'`

Naive 'trust the model' estimate: mean prediction over the pool.

This is the estimator implicit in headline claims of the form
'our model discovered N stable materials'. It carries the model's
full bias and admits no valid CI; returned for bias quantification only.

## `wilson_ci(successes: 'int', n: 'int', alpha: 'float' = 0.05) -> 'tuple[float, float]'`

Wilson score interval for a binomial proportion (no fpc; conservative).

## `ppi_mean_ci(y_labeled: 'np.ndarray', yhat_labeled: 'np.ndarray', yhat_pool: 'np.ndarray', alpha: 'float' = 0.05, power_tune: 'bool' = True, clip: 'tuple[float, float] | None' = (0.0, 1.0)) -> 'Interval'`

Prediction-powered CI for the mean outcome over a screened pool S.

Parameters
----------
y_labeled    : DFT labels on the labeled subsample of S (size n).
yhat_labeled : model predictions on that same subsample.
yhat_pool    : model predictions on ALL of S (size N), including the
               labeled subsample (finite-pool convention).
power_tune   : if True, uses the regression-slope coefficient lambda* = cov(y, yhat)/var(yhat)
               estimated on the labeled sample (Angelopoulos et al. 2023),
               which guarantees the interval is never asymptotically wider
               than the classical one.
clip         : clip the CI to this range (probabilities live in [0, 1];
               pass None for unbounded estimands such as counts / N).

Estimator: theta_hat = mean(yhat_pool)*lam + mean(y - lam*yhat on labeled)
which is unbiased for the pool mean of y for any fixed lam.

## `ppi_count_ci(y_labeled, yhat_labeled, yhat_pool, alpha: 'float' = 0.05, power_tune: 'bool' = True) -> 'Interval'`

CI for the COUNT of true positives (stable materials) in the screened
pool: count = |S| * precision. Wraps ppi_mean_ci and rescales.

## `ppi_yield_diff_ci(y_labeled, fA_l, fB_l, fA_pool, fB_pool, alpha: 'float' = 0.05) -> 'Interval'`

Paired CI for the difference in CERTIFIED YIELD between models A and B
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

## `required_budget(rect_var: 'float', pool_size: 'int', half_width: 'float', alpha: 'float' = 0.05) -> 'int'`

Closed-form certification budget (paper, Corollary 1).

Minimal n such that the (fixed-lambda) interval half-width
z * sqrt(S_r^2 (1/n - 1/N)) is at most `half_width`:
    n*(w) = ceil( N z^2 S_r^2 / (N w^2 + z^2 S_r^2) ),
clipped to [2, N]. As N -> infinity this recovers the classical
z^2 S_r^2 / w^2. `rect_var` is (a pilot estimate of) S_r^2 at the
working lambda; at the optimal lambda, S_r^2 = S_y^2 (1 - rho^2).

## `neyman_allocation(strata_sizes, strata_rect_sd, budget: 'int', min_per_stratum: 'int' = 2) -> 'np.ndarray'`

Variance-minimizing allocation of a DFT label budget across strata.

n_k proportional to N_k * sd_k (Neyman allocation), with a floor of
min_per_stratum labels per stratum and capping at stratum size.
strata_rect_sd should be a pilot estimate of the rectifier SD per stratum
(from a small uniform pilot); pass ones for proportional allocation.

## `stratified_ppi_ci(strata: 'list[dict]', alpha: 'float' = 0.05) -> 'Interval'`

Stratified PPI CI for the pool-level precision.

strata : list of dicts with keys
         'y' (labels in stratum sample), 'f_l' (predictions on sample),
         'f_pool' (predictions on the whole stratum).
The pool estimand is the size-weighted average of stratum means.

## `simulate_campaign(y_pool: 'np.ndarray', yhat_pool: 'np.ndarray', n_label: 'int', n_rep: 'int' = 1000, alpha: 'float' = 0.05, seed: 'int' = 0) -> 'dict'`

Monte-Carlo coverage/width study on a FULLY LABELED pool (e.g. WBM),
hiding all but n_label labels per replicate. Computes:
  - empirical coverage and mean width for classical vs PPI++,
  - the imputation (naive) bias,
against the true pool precision, which is known here by construction.

## `budget_curve(y_pool, yhat_pool, budgets, n_rep=500, alpha=0.05, seed=0)`

Mean CI width vs DFT budget, classical vs PPI++. Returns list of dicts.
