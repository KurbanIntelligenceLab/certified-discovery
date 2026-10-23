# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/).

## [1.1.1] - 2026-10-14
### Added (results)
- `experiments/results/*_15models.csv`: the fifteen-model re-execution (90/90 and 28/28 identical to the
  run of record) and the shared-sample comparison on the fifteen-model union, with five checks in
  `verify_results.py` (50 in total).
### Fixed
- `scripts/compare_results.py` (and `make compare`): numerical comparison of re-executed outputs
  with the committed files, replacing a byte-identity check that fails across CPU architectures.
- `experiments/fetch_frontier.sh` and the streamed loader used figshare's landing URLs
  (`figshare.com/files/<id>`), and the `ndownloader` form answers a plain HTTP client with
  status 202 and an empty body; both now use the figshare API endpoint
  (`api.figshare.com/v2/file/download/<id>`, recorded as `download_url` in
  `frontier_pred_files.json`), which redirects to the file, and send a User-Agent header. A failed download is deleted
  rather than left as an empty file.
### Changed
- Documentation rewritten (README, methods note, contributing guide, data dictionary); new
  `docs/VERIFICATION.md` and `Makefile`; figure-reproduction claim qualified by matplotlib
  version, with the rendering environment recorded in `figures/output/ENVIRONMENT.txt`;
  `LICENSE-DATA` names the directories it covers; project URLs added to `pyproject.toml`.
### Added
- `.github/workflows/reproduce.yml`: re-runs the experiments from the public inputs on a hosted
  runner, requires byte-identical outputs, and re-executes the run of record for all fifteen
  models from the figshare-hosted files.
- `notebooks/experiments.ipynb`: the re-execution and revision experiments as a notebook, with every
  input streamed from its public URL (no data download).
- `notebooks/analysis.ipynb`: drafting-workflow remarks removed from its markdown and messages.
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
