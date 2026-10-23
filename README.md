<div align="center">

<img src="docs/assets/hero.png" alt="Certified discovery" width="100%"/>

<br/>

[![CI](https://github.com/KurbanIntelligenceLab/certified-discovery/actions/workflows/verify.yml/badge.svg)](https://github.com/KurbanIntelligenceLab/certified-discovery/actions/workflows/verify.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Code license: MIT](https://img.shields.io/badge/code-MIT-green.svg)](LICENSE)
[![Data license: CC BY 4.0](https://img.shields.io/badge/data-CC%20BY%204.0-lightgrey.svg)](LICENSE-DATA)
[![Core: numpy only](https://img.shields.io/badge/core-numpy--only-orange.svg)](pyproject.toml)
[![Verification: 50 checks](https://img.shields.io/badge/verification-50%20checks-brightgreen.svg)](scripts/verify_results.py)

**Confidence intervals for machine-learning materials discovery counts from a small DFT verification budget.**

[Overview](#overview) · [Key result](#key-result) · [Method](#method) · [Installation](#installation) · [Quickstart](#quickstart) · [Reproducing the paper](#reproducing-the-paper) · [Experiments](#experiments) · [API](docs/API.md) · [Methods](docs/METHODS.md) · [Verification](docs/VERIFICATION.md)

</div>

---

## Overview

Machine-learning energy models screen millions of candidate crystals and report how many
new stable materials they found. Those counts are model predictions presented as
measurements: they inherit the model's unknown bias on the set the model itself selected,
and they carry no statistical guarantee.

`certdisc` certifies such counts. Given a uniformly random sample of DFT verifications
drawn from the flagged set, it returns a confidence interval for the precision of the set
(the fraction of flagged candidates that are truly stable), for the count of truly stable
materials, and for the difference in true discovery counts between two models, together
with a closed-form rule for the number of verifications a target half-width requires. The
estimator is the finite-population form of prediction-powered inference; its validity comes
from the randomized verification design, and the model's predictions narrow the interval
by a factor of sqrt(1 - rho^2), where rho is the correlation between predictions and labels
on the pool. Interval coverage is asymptotic; finite-sample coverage is reported in the
paper and reproduced by the code in this repository.

This repository accompanies the manuscript *Certified discovery: statistically valid
materials screening claims from a small DFT verification budget* (Kurban and Kurban,
under review at *Digital Discovery*). It contains the estimator library, the analysis
notebook that produced every number in the paper, the result files, the scripts that
reconcile the paper's numbers with those files and regenerate its figures, and an
independent re-execution of the pipeline.

## Key result

Emulating certification campaigns for fifteen public energy models on the exhaustively
DFT-labeled WBM corpus (about 257,000 candidates), naive counts overstate true discoveries
by 10% to 124% at the exact-hull threshold. The overstatement shrinks with model accuracy
but does not disappear: nearly one in ten candidates flagged by the most accurate model is
a false discovery.

<div align="center">
<img src="docs/assets/overstatement.png" alt="Overstatement against model accuracy" width="82%"/>
</div>

| | Overstatement at τ = 0 | Certified half-width at n = 500 | Empirical coverage at n = 500 |
|---|:---:|:---:|:---:|
| Ten current-generation models | 10% to 21% (mean 14%) | 2.5 to 3.1 percentage points | |
| Five earlier graph networks | 94% to 124% | 3.9 to 4.3 percentage points | |
| All 90 configurations | | | 0.924 to 0.967 (median 0.945, mean 0.9445) |

Five hundred verifications, about 1% of a flagged pool, certify discovery precision to
within 2.5 to 4.3 percentage points at nominal 95% confidence. Empirical coverage is close
to nominal at τ = 0 (mean 0.9475) and about 0.7 percentage points below nominal at
τ = 0.05 and 0.10 (0.9427 and 0.9435), a finite-sample effect of the normal
approximation that the paper reports as such. On these pools the predictions narrow the
interval by 0.4% to 9.8% relative to the label-only interval.

## Method

<div align="center">
<img src="docs/assets/method.png" alt="Certification pipeline" width="92%"/>
</div>

All inference is conditional on the flagged pool `S`, and the verified labels must be a
uniform random sample drawn from `S`. The point estimate combines the model's predictions
on all of `S` with the bias measured on the verified sample; at `λ = 0` it reduces to the
classical label-only estimator, and with the variance-optimal coefficient its interval is
never asymptotically wider than the classical one. Unbiasedness and the variance formula
are exact at every budget because the pool is finite and fully enumerable. See
[`docs/METHODS.md`](docs/METHODS.md) for the statement of the estimator, its assumptions
and their limits.

## Installation

```bash
git clone https://github.com/KurbanIntelligenceLab/certified-discovery.git
cd certified-discovery
pip install -e .                 # estimator library (numpy only)
pip install -e ".[analysis]"     # adds pandas, matplotlib, jupyter, nbclient, scipy and matbench-discovery
pip install -e ".[dev]"          # adds pytest
```

Python 3.9 or later. The estimator library depends on numpy alone.

## Quickstart

```python
import numpy as np
from certdisc import ppi_count_ci, imputation_estimate, required_budget

# A model flagged N candidates as stable; n of them can be verified with DFT,
# drawn uniformly at random from the flagged set.
N = 62_153
rng = np.random.default_rng(0)

# In practice the labels are hidden; here a biased screener is simulated.
y_true = (rng.random(N) < 0.515).astype(float)     # true stability of the flagged items
f_pred = np.ones(N)                                # binary calls: the model flagged all of them

n = 500
idx = rng.choice(N, size=n, replace=False)          # the verified sample

naive = imputation_estimate(f_pred) * N            # what an unverified campaign announces
iv = ppi_count_ci(y_true[idx], f_pred[idx], f_pred, alpha=0.05)

print(f"naive announced count : {naive:,.0f}")
print(f"certified 95% interval: [{iv.lower:,.0f}, {iv.upper:,.0f}]  (point {iv.estimate:,.0f})")

# Verifications needed for a +/-2 percentage-point half-width, from the rectifier variance
rect_var = float(np.var(y_true[idx] - f_pred[idx], ddof=1))
print("budget for +/-2 points:", required_budget(rect_var=rect_var, pool_size=N, half_width=0.02))
```

```text
naive announced count : 62,153
certified 95% interval: [30,856, 36,270]  (point 33,563)
budget for +/-2 points: 2302
```

Inside a single flagged set every binary call equals 1, so the certified interval above
coincides with the label-only interval. Passing continuous stability margins as `f_pred`
(for example a monotone transform of the predicted energy above the hull) lets the
predictions narrow the interval; the analysis notebook does this for the real campaigns.
Every interval is an `Interval` with `.lower`, `.upper`, `.estimate` and `.width`. The
public functions are documented in [`docs/API.md`](docs/API.md).

## Reproducing the paper

Three commands reconcile the paper with the files in this repository:

```bash
python scripts/verify_results.py results experiments/results   # 50 checks against the result files; nonzero exit on any failure
python figures/build_figures.py results                         # regenerates Figures 2 and 3 (vector PDF and 600 dpi PNG)
pytest -q                                                       # unit tests, including exact checks of the theorems
```

`make verify`, `make figures`, `make test` and `make lint` run the same steps; `make all` runs them all.

- **Run of record.** `notebooks/analysis.ipynb` produced every number in the paper:
  build `2026-07-03-optionB-colfix-r6`, 1,000 Monte Carlo replicates, 500 labels per
  campaign, base seed 0, thresholds τ ∈ {0, 0.05, 0.10} eV/atom, full and unique-prototype
  pools, fifteen models. Each file in [`results/`](results/) carries an SHA-256 checksum in
  [`results/run_metadata.json`](results/run_metadata.json), and
  [`results/README.md`](results/README.md) is the data dictionary.
- **Re-running the notebook.** `make notebook`, or open `notebooks/analysis.ipynb` from the
  repository root (or from `notebooks/`) with the `analysis` extra installed. Outputs go to
  `results_rerun/` (override with `CERTDISC_OUT`); the run of record in `results/` is never
  overwritten. With an importable `matbench-discovery` package the notebook runs the fifteen
  models of the paper; otherwise it falls back to the GitHub-hosted v1.3.1 prediction files
  (ten models of that generation). Note that the package is moving quickly: its PyPI release
  1.3.1 does not ship the model metadata, and its current GitHub main requires Python 3.14,
  so for the fifteen-model re-execution use the package-free route in `experiments/`
  (`MODELS=all`), which reads the prediction files directly.
- **Experiments in a notebook, without downloading data.** `notebooks/experiments.ipynb`
  runs the independent re-execution and the revision experiments with every input streamed
  from its public URL into memory (`WBM_DATA_SOURCE=url`); set `MODELS` in its first cell to
  `"five"` or `"all"`. Only the result CSVs under `experiments/results/` are written.
- **Figures.** `figures/output/` holds the figures used in the manuscript;
  `figures/build_figures.py` reproduces them from `results/`. They are pixel-identical in the
  environment of `requirements-lock.txt` (matplotlib 3.10.8; `pip install -r
  requirements-lock.txt -e .`), and visually identical with sub-pixel differences in text
  layout under other matplotlib versions.
- **Continuous integration.** `verify.yml` runs static analysis, the 50 checks and the tests
  on every push. `reproduce.yml` (on request, and monthly) fetches the public inputs on a
  GitHub-hosted runner, re-runs the experiments, requires the outputs to match the committed
  files within floating-point tolerance, and then fetches the ten frontier prediction files from figshare
  and re-executes the run of record for all fifteen models, requiring 90 of 90 Table 1
  configurations and 28 of 28 pair rows to match.

## Experiments

`experiments/` contains an independent re-implementation of the data pipeline and the
analyses added in revision, each writing a result file under `experiments/results/`:

| Script | Purpose |
|---|---|
| `exp0_census_reproduction.py` | Reproduces the census columns of Table 1 from the public prediction files |
| `exp5_reproduce_e1_e3.py` | Re-executes the coverage campaigns and the paired comparisons with the run-of-record seeds and compares every value with `results/` |
| `exp1_oracle_budgets.py` | Minimal verification budgets for target half-widths (Corollary 1 at census values) |
| `exp2_benchmark_transfer.py` | Whether benchmark precision transfers to chemically restricted pools |
| `exp3_cost_proxy.py` | Realized DFT cost of a verification sample under per-structure cost proxies |
| `exp4_shared_budget.py` | One shared verification sample certifying several model comparisons |
| `verification/math_checks.py` | Theorem 1, Lemma 1, Corollary 1 and Propositions 2 and 3 by exact enumeration and random search |
| `verification/ppi_py_crosscheck.py` | Point estimates against the reference implementation `ppi_py` |

Inputs are fetched with checksums (`make data`, or `experiments/fetch_data.sh` for the WBM
summary and the five earlier models and `experiments/fetch_frontier.sh` for the ten
current-generation models), or streamed from their public URLs with `WBM_DATA_SOURCE=url`
without writing to disk. `make experiments` re-runs the five-model pipeline and `make compare` checks its outputs
against the committed files numerically (byte identity of the CSVs holds on the reference
platform but not across CPU architectures, where the last floating-point digits can differ);
`make experiments-all` (or `MODELS=all`) extends the re-execution to all fifteen models. See
[`experiments/README.md`](experiments/README.md).

## Repository layout

```
certified-discovery/
├── src/certdisc/              estimator library (numpy only): core.py and the public API
├── scripts/verify_results.py  reconciles the paper's numbers and tables with the result files
├── figures/                   build_figures.py (Figures 2 and 3), output/ (manuscript figures), make_assets.py (README visuals)
├── notebooks/                 analysis.ipynb (the full study, run of record) and experiments.ipynb (streamed re-execution)
├── results/                   result files behind every figure and table, with an SHA-256 manifest
├── experiments/               independent re-execution, revision experiments, verification scripts, result files
├── data/                      fetched inputs (not tracked) and data/frontier/ for the current-generation prediction files
├── tests/                     unit tests, including exact checks of the theorems
├── docs/                      API reference, methods note, verification summary, figure assets
├── Makefile                   verify, figures, test, lint, experiments, experiments-all, notebook
└── requirements-lock.txt      exact versions of the environment that rendered the figures
```

The manuscript and its Supplementary Information are not distributed in this repository.

## Scope and limitations

Certification is relative to the DFT oracle that defines stability (energy above the
MP2020-corrected convex hull at a stated threshold), not to experimental synthesizability.
Labels must be sampled uniformly at random from the flagged pool; verifications selected
adaptively, for example the most promising candidates first, cannot be certified
retroactively by this construction. Interval validity is asymptotic in the number of
labels; for small samples or rare classes the toolkit falls back to a Wilson score
interval. The estimators are domain-generic; the empirical magnitudes reported here are
specific to inorganic-crystal stability on the WBM corpus.

## Citation

If you use this software or the protocol, please cite the paper and the software. Citation
metadata is in [`CITATION.cff`](CITATION.cff).

## License

Code is released under the [MIT License](LICENSE). The result files in `results/` and
`experiments/results/` are released under [CC BY 4.0](LICENSE-DATA). The WBM corpus and
the Matbench Discovery prediction files remain the work of their respective authors and
should be cited when used.
