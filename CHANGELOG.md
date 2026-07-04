# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/).

## [1.0.0] — 2026-07-04
### Added
- Initial public release accompanying the manuscript "Certified discovery:
  statistically valid materials screening claims from a small DFT verification
  budget."
- `certdisc` estimator library (numpy-only): classical and prediction-powered
  intervals for discovery precision, stable-material counts, and paired model
  comparisons; closed-form budget rule; stratified PPI with Neyman allocation;
  coverage and budget-curve harnesses.
- `scripts/verify_results.py` — independent re-derivation of every headline
  number in the paper (28 checks).
- `figures/build_figures.py` — regenerates Figures 2 and 3 (vector PDF + 600 dpi PNG).
- `figures/make_assets.py` — regenerates the README visuals (hero, method diagram, headline figure).
- `results/` — per-figure and per-table source data with an SHA-256 manifest.
- Full test suite, CI, and API/methods documentation.
