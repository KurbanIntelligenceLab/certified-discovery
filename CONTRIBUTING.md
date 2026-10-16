# Contributing

Thanks for your interest in `certdisc`. This repository accompanies a research
paper, so contributions are welcome but scoped: the estimators must remain
statistically correct and match the published method.

## Ground rules

- **No hard-coded results.** Any change that hard-codes a reported value, weakens an
  interval's validity, or bypasses the selection-aware sampling assumptions will be
  declined.
- **Tests must pass.** `pytest` runs coverage, bias, budget-monotonicity, and
  antisymmetry checks, and exact checks of the theorems. New estimator behavior needs a
  corresponding test.
- **Numbers must reconcile.** `python scripts/verify_results.py results experiments/results`
  must keep passing; it recomputes the headline numbers and tables of the paper from the
  result files.

## Development setup

```bash
pip install -e ".[dev]"
pytest -q
python scripts/verify_results.py results experiments/results
python -m pyflakes src/certdisc scripts experiments
```

## Pull requests

1. Open an issue describing the change first for anything beyond a typo.
2. Keep the core library numpy-only; put analysis-only dependencies behind the
   `analysis` extra.
3. Include a test and, if the change touches a reported quantity, update the
   relevant check in `scripts/verify_results.py`.
4. Do not commit the data cache or fetched inputs; they are ignored. Regenerated figures
   belong in `figures/output/` only when the result files change.

## Reporting issues

Please include your Python and numpy versions, a minimal reproducer, and the
expected vs. observed interval or number.
