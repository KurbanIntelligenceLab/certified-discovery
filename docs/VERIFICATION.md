# Verification summary

What has been verified about the code, the result files and the figures in this
repository, by which means, and with what limitations. Numbers refer to the state of the
repository at version 1.1.1.

## Automated checks

| Check | Command | Outcome |
|---|---|---|
| Reconciliation of the paper's numbers and tables with `results/` and `experiments/results/` | `python scripts/verify_results.py results experiments/results` | 45 checks pass; exit code is nonzero on any failure |
| Re-executed experiment outputs against the committed files | `python scripts/compare_results.py experiments/results` | numerical comparison (rtol 1e-9); byte identity holds on the reference platform (x86-64 Linux) but the last floating-point digits can differ on other CPU architectures |
| Unit tests, including exact-enumeration checks of Theorem 1, Lemma 1, Corollary 1 and Propositions 2 and 3 | `pytest -q` | 13 pass |
| Static analysis of the library, scripts and experiments | `python -m pyflakes src/certdisc scripts experiments` | clean |
| Figure regeneration | `python figures/build_figures.py results` | reproduces `figures/output/`; pixel-identical in the `requirements-lock.txt` environment (verified in a fresh virtual environment), sub-pixel text-layout differences under other matplotlib versions |

The continuous-integration workflow (`.github/workflows/verify.yml`) runs the first three
on every push.

## Independent re-execution

`experiments/wbm_data.py` re-implements the data pipeline (hull convention, error filter,
flagged pools, margin transform) without reference to the notebook. With it:

- **Census (EXP-0).** All 30 Table 1 configurations of the five earlier graph networks
  (CHGNet, M3GNet, ALIGNN, MEGNet, CGCNN) are reproduced exactly from the public
  Matbench Discovery v1.3.1 prediction files, as are the models' formation-energy errors.
- **Run of record (EXP-5).** Re-executing the coverage campaigns and the paired
  comparisons with the run-of-record seeds reproduces, for these five models, every
  coverage value and median interval of Table 1 and Supplementary Table 1 (30 of 30
  configurations) and every row of Table 2 and Supplementary Table 4 involving only these
  models (8 of 8).
- **Notebook.** `notebooks/analysis.ipynb` executes end to end from a clean checkout
  without the `matbench-discovery` package, using the GitHub-hosted fallback files; for
  the five earlier models it reproduces the Table 1, budget-sweep and seed-robustness
  values of the run of record to machine precision (differences at most 4e-15, from
  floating-point formatting).
- **Theory.** `experiments/verification/math_checks.py` confirms Theorem 1 and Lemma 1
  by exact enumeration over all samples of small random pools (maximum error 4e-16),
  Corollary 1 by exhaustive inversion, Proposition 2 by identity, and Proposition 3 on
  200,000 random pools including 38,683 with negative residual covariance (no violation).
- **Reference implementation.** `experiments/verification/ppi_py_crosscheck.py` shows that
  the toolkit's point estimates coincide with `ppi_py` 0.2.3 at fixed coefficient.

## Fresh-environment reproduction

The whole chain was repeated in a fresh virtual environment built from
`pip install -e ".[analysis,dev]"` (numpy 2.5.4, pandas 3.0.6, matplotlib 3.11.2): static
analysis clean, 13 tests, 45 checks, all eight experiment result files byte-identical to
the committed ones, the notebook executed end to end with overlapping values identical to
the run of record, and the streamed data path (`WBM_DATA_SOURCE=url`) reproducing the
census with no file written to disk. The only version-dependent artifact is figure
rendering, as noted above.

## Fifteen-model re-execution

The ten current-generation models' prediction files are distributed by Matbench Discovery
through figshare and were fetched through its API endpoint. Running `MODELS=all` on an
Apple Silicon machine (macOS 26, Python 3.12.15, numpy 2.5.4, pandas 3.1.0) reproduced the
run of record exactly: all 90 Table 1 configurations (`exp5_e1_reproduction_15models.csv`)
and all 28 pair rows (`exp5_e3_reproduction_15models.csv`), and ran the shared-sample
comparison on the fifteen-model union (`exp4_shared_budget_15models.csv`). These files are
committed under `experiments/results/`, and `verify_results.py` checks them when present.
The `reproduce` workflow repeats this on a GitHub-hosted runner.

## Scope of the verification

All checks were performed with the authors' tooling; no independent third party has
repeated them. Verification establishes that the reported
numbers follow from the released files and code; it does not by itself establish the
scientific assumptions behind them, which the paper states and discusses.
