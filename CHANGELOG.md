# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/).

## [1.1.1] - 2026-10-14
### Changed
- Documentation rewritten (README, methods note, contributing guide, data dictionary); new
  `docs/VERIFICATION.md` and `Makefile`; figure-reproduction claim qualified by matplotlib
  version, with the rendering environment recorded in `figures/output/ENVIRONMENT.txt`;
  `LICENSE-DATA` names the directories it covers; project URLs added to `pyproject.toml`.
### Added
- `.github/workflows/reproduce.yml`: re-runs the experiments from the public inputs on a hosted
  runner, requires byte-identical outputs, and re-executes the run of record for all fifteen
  models from the figshare-hosted files.
- `requirements-lock.txt`: exact versions of the environment that rendered the figures; the
  notebook now writes to `results_rerun/` instead of overwriting `results/`; `make notebook`
  and `make experiments-all` targets.
- `WBM_DATA_SOURCE=url`: every experiment input can be streamed from its public URL into
  memory with checksum or size verification and no file written to disk.

## [1.1.0] - 2026-10-14
### Changed
- `scripts/verify_results.py`: removed a check that could never fail; the script now exits
  nonzero on any failure; 15 checks added for the numbers introduced or corrected in the
  revised manuscript (45 checks in total, run as `python scripts/verify_results.py results experiments/results`).
- `figures/build_figures.py`: now reproduces the manuscript's Figure 3 (log width axis,
  per-threshold mean coverage in panel c, no overlapping labels); descriptive panel titles;
  generated outputs tracked under `figures/output/` with the rendering environment recorded in `figures/output/ENVIRONMENT.txt`.
- `notebooks/analysis.ipynb`: removed a hard-coded working directory and a stale embedded
  copy of the toolkit; imports `certdisc`; starts from the repository root or `notebooks/`;
  stale "/9 pairs" and "ten models" strings fixed; outputs cleared.
- `src/certdisc/core.py`: header documents the cross-check against `ppi_py` and the relation
  of the tuned coefficient to PPI++.
- Repository URL corrected to KurbanIntelligenceLab/certified-discovery.
### Added
- `experiments/`: independent re-implementation of the data pipeline (`wbm_data.py`) and
  the revision experiments: census and run-of-record reproduction (EXP-0, EXP-5), oracle
  budgets (EXP-1), benchmark-precision transfer (EXP-2), cost proxy (EXP-3), shared-sample
  model comparison (EXP-4), with their result files; `fetch_data.sh` (pinned, checksummed
  inputs) and `fetch_frontier.sh` with `frontier_pred_files.json` for the ten frontier
  models; a `MODELS=all` fifteen-model mode.
- `experiments/verification/`: exact-enumeration checks of Theorem 1, Lemma 1, Corollary 1
  and Propositions 2-3, and the `ppi_py` cross-check.
- `tests/test_theory.py`: the exact-enumeration checks as unit tests.

## [1.0.0] - 2026-07-04
### Added
- Initial public release accompanying the manuscript "Certified discovery:
  statistically valid materials screening claims from a small DFT verification
  budget."
- `certdisc` estimator library (numpy-only): classical and prediction-powered
  intervals for discovery precision, stable-material counts, and paired model
  comparisons; closed-form budget rule; stratified PPI with Neyman allocation;
  coverage and budget-curve harnesses.
- `scripts/verify_results.py` - independent re-derivation of every headline
  number in the paper (28 checks).
- `figures/build_figures.py` - regenerates Figures 2 and 3 (vector PDF + 600 dpi PNG).
- `figures/make_assets.py` - regenerates the README visuals (hero, method diagram, headline figure).
- `results/` - per-figure and per-table source data with an SHA-256 manifest.
- Full test suite, CI, and API/methods documentation.
