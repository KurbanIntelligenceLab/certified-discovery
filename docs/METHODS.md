# Methods note

A compact statement of what `certdisc` computes and of the assumptions it relies on.
The manuscript and its Supplementary Information contain the full theory, proofs and
derivations.

## Setup

A screening campaign applies a model `f` to a candidate universe and reports the flagged
set `S = {i : f calls i stable}` of size `N`. Let `y_i ∈ {0, 1}` indicate true stability
under the campaign's own DFT oracle (energy above the convex hull `E_hull ≤ τ` at a stated
threshold `τ`). The quantities of interest are the discovery precision
`π = (1/N) Σ_{i∈S} y_i`, the discovery count `Nπ`, and, for model comparison, the
discovery yield `q_f = (1/|U|) Σ_{i∈U} y_i f_i` over a common pool `U`, whose difference
between two models, multiplied by `|U|`, is the difference in their true discovery counts.

The naive report, which counts every flagged candidate or averages predicted stabilities
over the pool, is the imputation estimator of prediction-powered inference. It admits no
valid confidence interval, and its error equals the model's false-discovery behavior on
the set the model selected, where surrogate errors are known to concentrate.

## The certified estimator

Reveal DFT labels for a uniform random subsample `L ⊂ S` of size `n`. The point estimate
is

```
π̂ = λ · mean(f over S)  +  (1/n) Σ_{i∈L} (y_i − λ f_i)
      \_______________/     \___________________________/
       model predictions        bias measured on the
       on all of S               verified sample
```

The coefficient `λ` is estimated as the regression slope of the verified labels on the
predictions within the verified sample. This is the finite-population counterpart of
PPI++ power tuning; PPI++ shrinks the same slope by `1/(1 + n/N_u)` for a separate
unlabeled sample of size `N_u`, whereas on a flagged pool the predictions are known for
every member and the unshrunk slope minimizes the variance. The interval is a normal
interval around `π̂` with the plug-in rectifier variance and an explicit finite-population
correction, because `S` is finite and fully enumerable. At `λ = 0` the estimator reduces
exactly to the classical label-only estimator; the tuned interval is never
asymptotically wider than the classical one, with equality only when the predictions
carry no signal. Unbiasedness and the variance formula hold exactly at every `n`;
interval coverage is asymptotic in `n`.

## What the functions compute

| Function | Quantity |
|---|---|
| `classical_ci` | precision, labels only |
| `imputation_estimate` | naive precision (no interval; used to quantify bias) |
| `ppi_mean_ci` | certified precision on `S` |
| `ppi_count_ci` | certified count of stable materials in `S` |
| `ppi_yield_diff_ci` | certified difference in discovery yield between two models (paired, one shared sample) |
| `required_budget` | closed-form `n` for a target interval half-width |
| `neyman_allocation`, `stratified_ppi_ci` | variance-optimal label allocation across strata and the stratified interval |
| `simulate_campaign`, `budget_curve` | Monte Carlo coverage and width against budget |
| `wilson_ci` | score interval used in the rare-class fallback |

## Assumptions and their limits

- **Selection awareness.** All inference is conditional on the flagged pool `S`. Labels
  must be sampled uniformly at random, or stratified-randomly, from `S`. Reusing labels
  acquired outside `S` is invalid and is not supported by the code. Model selection of the
  pool does not bias the procedure, because the estimand is defined on the selected pool
  and the verified subsample is drawn from that same pool.
- **Adaptive verification.** Campaigns whose verifications were chosen in a
  deterministic, informative order, for example the most promising candidates first,
  cannot be certified retroactively by this construction, because the audited sample is
  no longer representative of the pool. Randomized adaptive designs with known inclusion
  probabilities remain certifiable with inverse-probability weighting; this library does
  not implement them.
- **Small samples and rare classes.** When `n` is small or one class is rare in the
  verified sample (fewer than ten members), the normal approximation degrades and the
  toolkit falls back to a Wilson score interval on the labeled proportion. The fallback
  omits the finite-population correction and is therefore wider.
- **Finite-sample coverage.** On the WBM campaigns at `n = 500`, empirical coverage of
  the nominal 95% intervals is 0.924 to 0.967 across 90 configurations (mean 0.9445),
  about 0.7 percentage points below nominal at the two looser thresholds.
- **Oracle scope.** Certification is relative to the DFT settings that define the labels,
  not to experimental synthesizability. A certified count is a statement about the
  computational hull.

## Reproducibility

`scripts/verify_results.py results experiments/results` recomputes the headline numbers
and tables of the manuscript from the released result files and reports 45 checks, with a
nonzero exit code on any failure. The run of record is `notebooks/analysis.ipynb`, build
`2026-07-03-optionB-colfix-r6`: 1,000 Monte Carlo replicates, 500 labels per campaign,
base seed 0, thresholds `τ ∈ {0, 0.05, 0.10}` eV/atom, full and unique-prototype pools,
fifteen models. Every result file carries an SHA-256 checksum in
`results/run_metadata.json`. `experiments/` re-executes the pipeline independently of
the notebook; see `docs/VERIFICATION.md` for what has been reproduced and to what
precision.
