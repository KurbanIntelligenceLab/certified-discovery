# Methods note

A compact statement of what `certdisc` computes and the assumptions it relies on.
The manuscript (`paper/manuscript.pdf`) and its Supplementary Information contain
the full theory, proofs, and derivations.

## Setup

A screening campaign applies a model `f` to a candidate universe and reports the
flagged set `S = {i : f calls i stable}` of size `N`. Let `y_i ∈ {0,1}` indicate
true stability under the campaign's own DFT oracle (energy above the convex hull
`E_hull ≤ τ` at a stated threshold `τ`). The quantities of interest are the
**discovery precision** `π = (1/N) Σ_{i∈S} y_i`, the **discovery count** `Nπ`, and,
for model comparison, the **certified yield** `q_f` over a common pool.

The naive report — count every flagged candidate, or average predicted
stabilities over the pool — is the **imputation estimator** of prediction-powered
inference. It admits no valid confidence interval, and its error equals the
model's false-discovery behaviour on the very set the model selected, which is
exactly where a surrogate model is least trustworthy.

## The certified estimator

Reveal DFT labels for a uniform random subsample `L ⊂ S` of size `n`. The
prediction-powered point estimate is

```
π̂ = λ · mean(f over S)  +  (1/n) Σ_{i∈L} (y_i − λ f_i)
      \_______________/     \___________________________/
       model predictions        bias measured on the
       on all of S               verified sample
```

with the power-tuning coefficient `λ` chosen to minimise variance (PPI++). The
interval is a normal interval around `π̂` using the plug-in rectifier variance,
with an explicit **finite-population correction** because `S` is finite and
exhaustively enumerable. At `λ = 0` this reduces exactly to the classical
label-only estimator; the tuned interval is never asymptotically wider than the
classical one (equality only when predictions carry no signal).

## What the functions map to

| Function | Estimand |
|---|---|
| `classical_ci` | precision, labels only |
| `imputation_estimate` | naive precision (bias quantification; no interval) |
| `ppi_mean_ci` | certified precision on `S` |
| `ppi_count_ci` | certified count of stable materials in `S` |
| `ppi_yield_diff_ci` | certified difference in yield between two models (paired) |
| `required_budget` | closed-form `n` for a target interval half-width |
| `neyman_allocation` / `stratified_ppi_ci` | variance-optimal label allocation across strata |
| `simulate_campaign` / `budget_curve` | Monte Carlo coverage and width vs. budget |

## Assumptions and their limits

- **Selection-awareness.** All inference is conditional on the screened pool `S`.
  Labels must be sampled uniformly at random (or stratified-randomly) *from* `S`.
  Sampling labels from outside `S` and reusing them inside `S` is invalid and is
  deliberately unsupported by the code. Model selection of the pool does not bias
  the procedure because the estimand is defined on the selected pool and the
  verified subsample is drawn from that same pool; what is not permitted is
  recycling verifications acquired elsewhere.
- **Adaptive verification.** Campaigns whose verifications were chosen adaptively
  (e.g. verifying the most promising candidates first) cannot be certified
  retroactively by this construction, because the audited sample is no longer
  representative of the pool.
- **Small samples / rare positives.** When `n` is small or true positives are rare,
  the normal approximation degrades; the toolkit falls back to a Wilson score
  interval on the labelled proportion (see `wilson_ci`), conservative by design.
- **Oracle scope.** Certification is relative to the DFT settings that define the
  labels, not to experimental synthesizability. A certified-stable count is a
  statement about the computational hull.

## Reproducibility

`scripts/verify_results.py` recomputes every headline number in the manuscript
from the released `data/` CSVs and asserts agreement (28 checks). The full run of
record: notebook build `2026-07-03-optionB-colfix-r6`, `N_REP = 1000` Monte Carlo
replicates, `N_LABEL = 500`, base seed `0`, thresholds `τ ∈ {0, 0.05, 0.10}`
eV/atom, full and unique-prototype pools, 15 models. Every file carries an SHA-256
checksum in `data/run_metadata.json`.
