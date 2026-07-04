# Contributing

Thanks for your interest in `certdisc`. This repository accompanies a research
paper, so contributions are welcome but scoped: the estimators must remain
statistically correct and match the published method.

## Ground rules

- **The code computes; it never asserts a fabricated outcome.** Any change that
  hard-codes a result, weakens an interval's validity, or bypasses the
  selection-aware sampling assumptions will be declined.
- **Tests must pass.** `pytest` runs coverage, bias, budget-monotonicity, and
  antisymmetry checks. New estimator behaviour needs a corresponding test.
- **Numbers must reconcile.** `python scripts/verify_results.py` must stay green;
  it re-derives every headline number in the paper from `data/`.

## Development setup

```bash
pip install -e ".[dev]"
pytest -q
python scripts/verify_results.py
```

## Pull requests

1. Open an issue describing the change first for anything beyond a typo.
2. Keep the core library numpy-only; put analysis-only dependencies behind the
   `analysis` extra.
3. Include a test and, if the change touches a reported quantity, update the
   relevant check in `scripts/verify_results.py`.
4. Do not commit regenerated figures or the matbench-discovery data cache; these
   are gitignored.

## Reporting issues

Please include your Python and numpy versions, a minimal reproducer, and the
expected vs. observed interval or number.
