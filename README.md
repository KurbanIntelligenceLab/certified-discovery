<div align="center">

# Certified Discovery

**Statistically valid materials screening claims from a small DFT verification budget**

[![CI](https://github.com/hasankurban/certified-discovery/actions/workflows/verify.yml/badge.svg)](https://github.com/hasankurban/certified-discovery/actions/workflows/verify.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Code license: MIT](https://img.shields.io/badge/code-MIT-green.svg)](LICENSE)
[![Data license: CC BY 4.0](https://img.shields.io/badge/data-CC%20BY%204.0-lightgrey.svg)](LICENSE-DATA)

*Turn a headline discovery count into a confidence interval you can defend.*

</div>

---

## What this is

Machine-learning models now screen millions of candidate crystals and report how
many new stable materials they found. Those counts are **model predictions
presented as measurements**: they inherit the model's unknown bias on the very set
the model selected, and they carry no statistical guarantee.

`certdisc` adapts **prediction-powered inference** to model-selected candidate
pools. With a small, uniformly random sample of DFT verifications, it returns a
valid confidence interval for the precision of a flagged set, the count of truly
stable materials, and the difference between two models, plus a closed-form rule
for how large the verification budget must be.

Emulating certification campaigns for **15 public energy models** on the
exhaustively labelled ~257,000-candidate WBM corpus, naive counts overstate true
discoveries by **10% to 124%** at the exact-hull threshold. The overstatement
shrinks with model accuracy but does not vanish: even the single most accurate
2026 model still announces roughly **one phantom discovery in ten**. Five hundred
verifications certify discovery rates to within **2.6–4.5 percentage points** at
nominal 95% coverage.

## Install

```bash
git clone https://github.com/hasankurban/certified-discovery.git
cd certified-discovery
pip install -e .                 # core estimators, numpy only
pip install -e ".[analysis]"     # + pandas/matplotlib/matbench-discovery to reproduce the paper
```

The core library depends on **numpy alone**. `matbench-discovery`, `pandas`, and
`matplotlib` are needed only to reproduce the full study.

## Quickstart

```python
import numpy as np
from certdisc import ppi_count_ci, imputation_estimate, required_budget

# A model flagged N candidates as stable. You can afford to DFT-verify n of them,
# drawn uniformly at random from the flagged set.
N = 62_153                         # size of the flagged set S
rng = np.random.default_rng(0)

# ground truth is hidden in practice; here we simulate a biased screener
y_true = (rng.random(N) < 0.515).astype(float)     # true stability of flagged items
f_pred = np.ones(N)                                # the model called all of them stable

# reveal labels for a random subsample of size n
n = 500
idx = rng.choice(N, size=n, replace=False)

naive = imputation_estimate(f_pred) * N            # what a naive campaign announces
iv = ppi_count_ci(y_true[idx], f_pred[idx], f_pred, alpha=0.05)   # certified interval

print(f"naive announced count : {naive:,.0f}")
print(f"certified 95% interval: [{iv.lower:,.0f}, {iv.upper:,.0f}]  (point {iv.estimate:,.0f})")

# how many labels would a +/-2% interval need? (from the rectifier variance)
rect_var = float(np.var(y_true[idx] - f_pred[idx], ddof=1))
print("budget for +/-2%:", required_budget(rect_var=rect_var, pool_size=N, half_width=0.02))
```

Every interval is an `Interval` object with `.lower`, `.upper`, `.estimate`, and
`.width`. See [`notebooks/analysis.ipynb`](notebooks/analysis.ipynb) for the full
study and [`docs/API.md`](docs/API.md) for every function.

## Reproduce the paper

Every number in the manuscript is recomputed from the released result files by an
independent script:

```bash
python scripts/verify_results.py        # reconciles all headline numbers; prints PASS/FAIL
python scripts/build_figures.py         # regenerates Figures 2 and 3 (vector PDF + 600 dpi PNG)
```

`verify_results.py` recomputes counts, intervals, coverage, budget predictions,
and the paired-comparison outcomes from the CSVs in [`data/`](data/) and asserts
they match the paper (**28 checks, all pass**). The full run of record used
notebook build `2026-07-03-optionB-colfix-r6`, `N_REP = 1000` Monte Carlo
replicates, `N_LABEL = 500`, base seed `0`, thresholds τ ∈ {0, 0.05, 0.10} eV/atom,
and both the full and unique-prototype pools; every file in `data/` carries an
SHA-256 checksum in [`data/run_metadata.json`](data/run_metadata.json).

To regenerate the results themselves (downloads ~200 MB of public WBM/leaderboard
data on first run):

```bash
jupyter nbconvert --to notebook --execute notebooks/analysis.ipynb
```

## Repository layout

```
certified-discovery/
├── src/certdisc/         # the estimator library (numpy-only)
│   ├── __init__.py       #   public API
│   └── core.py           #   PPI/PPI++, counts, paired diffs, budget rule, stratified PPI
├── scripts/
│   ├── verify_results.py #   independent re-derivation of every headline number (28/28)
│   └── build_figures.py  #   regenerates Figures 2 & 3 from data/
├── notebooks/
│   └── analysis.ipynb    #   the full study, end to end
├── data/                 # per-figure / per-table source data + SHA-256 manifest
├── tests/                # unit tests + smoke test (run with pytest)
└── docs/                 # API reference and methods notes
```

The manuscript itself is not distributed in this repository. It is available from
Nature Computational Science on publication (and the preprint from arXiv); the
figures are regenerated from `data/` by `scripts/build_figures.py`.

## Data and methods, in one paragraph

Labels are DFT-verified binary stability indicators (energy above the convex hull
≤ τ). Predictions are a model's binary stability calls on the same pool. All
inference is **conditional on the screened pool** S, and labels must be sampled
uniformly at random (or stratified-randomly) *from* S — sampling elsewhere and
reusing labels inside S is invalid and is deliberately unsupported. Because
screening pools are finite and exhaustively enumerable, the finite-population
correction is applied explicitly. See [`docs/METHODS.md`](docs/METHODS.md).

## Citing

If you use this software or the certified-discovery protocol, please cite the
paper and the software (see [`CITATION.cff`](CITATION.cff)). A `BibTeX` entry will
be added on publication; the archived release will carry a Zenodo DOI.

## License

Code is released under the [MIT License](LICENSE). The data files in `data/` are
released under [CC BY 4.0](LICENSE-DATA). The underlying WBM corpus and Matbench
Discovery prediction files are the property of their respective authors and are
redistributed here only as derived per-figure source data; see their original
licenses.

## A note on scope

Certification is relative to the DFT oracle used to define stability, not to
experimental synthesizability. The estimators are domain-generic, but the
empirical magnitudes reported here are specific to inorganic-crystal stability on
the WBM corpus. The library computes; it never asserts a fabricated outcome.
