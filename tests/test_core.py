"""Unit and smoke tests for the certdisc estimators.

These exercise the guarantees the paper relies on: the classical and PPI
intervals cover the truth at the nominal rate, the naive imputation estimator is
biased on a biased screener, PPI is not wider than classical on average with an
informative predictor, budgets are monotone, and paired differences are
antisymmetric. They compute; none asserts a fabricated outcome.
"""
import numpy as np
import pytest

from certdisc import (
    classical_ci,
    imputation_estimate,
    wilson_ci,
    ppi_mean_ci,
    ppi_count_ci,
    ppi_yield_diff_ci,
    required_budget,
    budget_curve,
)


def make_pool(N, precision, rho, seed):
    """N items with a given true precision and a predictor whose agreement with
    the labels is controlled by rho (0 = coin flip, 1 = perfect)."""
    rng = np.random.default_rng(seed)
    y = (rng.random(N) < precision).astype(float)
    flip = rng.random(N) > (0.5 + rho / 2)
    f = np.where(flip, 1 - y, y).astype(float)
    return y, f


def test_imputation_is_biased_on_biased_screener():
    N = 20_000
    y, _ = make_pool(N, precision=0.375, rho=0.4, seed=1)
    naive = imputation_estimate(np.ones(N))          # screener calls all stable
    assert naive == pytest.approx(1.0)
    assert naive - y.mean() > 0.5                     # large positive bias vs 0.375


def test_classical_ci_covers_truth():
    N, n, reps = 20_000, 500, 300
    y, _ = make_pool(N, precision=0.5, rho=0.3, seed=2)
    truth = y.mean()
    rng = np.random.default_rng(0)
    hits = sum(
        (lambda iv: iv.lower <= truth <= iv.upper)(
            classical_ci(y[rng.choice(N, n, replace=False)], pool_size=N))
        for _ in range(reps))
    assert hits / reps >= 0.90


def test_ppi_mean_ci_covers_truth():
    N, n, reps = 20_000, 500, 300
    y, f = make_pool(N, precision=0.5, rho=0.45, seed=3)
    truth = y.mean()
    rng = np.random.default_rng(0)
    hits = 0
    for _ in range(reps):
        idx = rng.choice(N, n, replace=False)
        iv = ppi_mean_ci(y[idx], f[idx], f)
        hits += iv.lower <= truth <= iv.upper
    assert hits / reps >= 0.90


def test_ppi_not_wider_than_classical_on_average():
    N, n, reps = 20_000, 500, 200
    y, f = make_pool(N, precision=0.5, rho=0.6, seed=4)
    rng = np.random.default_rng(0)
    wc, wp = [], []
    for _ in range(reps):
        idx = rng.choice(N, n, replace=False)
        wc.append(classical_ci(y[idx], pool_size=N).width)
        wp.append(ppi_mean_ci(y[idx], f[idx], f).width)
    assert np.mean(wp) <= np.mean(wc) + 1e-3


def test_count_ci_contains_true_count():
    N, n = 20_000, 800
    y, f = make_pool(N, precision=0.6, rho=0.4, seed=5)
    true_count = y.sum()
    rng = np.random.default_rng(0)
    covered = 0
    for _ in range(200):
        idx = rng.choice(N, n, replace=False)
        iv = ppi_count_ci(y[idx], f[idx], f)
        covered += iv.lower <= true_count <= iv.upper
    assert covered / 200 >= 0.88


def test_required_budget_monotone_in_target():
    # a tighter target (smaller half-width) needs at least as many labels
    n_loose = required_budget(rect_var=0.1, pool_size=20_000, half_width=0.04)
    n_tight = required_budget(rect_var=0.1, pool_size=20_000, half_width=0.02)
    assert n_tight >= n_loose


def test_wilson_ci_valid_range():
    lo, hi = wilson_ci(successes=3, n=50)
    assert 0.0 <= lo <= hi <= 1.0


def test_budget_curve_decreasing():
    N = 20_000
    y, f = make_pool(N, precision=0.5, rho=0.4, seed=7)
    budgets = [50, 100, 200, 400, 800]
    out = budget_curve(y, f, budgets, n_rep=50, seed=0)
    # budget_curve returns one summary dict per budget; certified width should
    # not grow as the budget grows (monotone non-increasing, with MC slack)
    w = [row["mean_width_ppi"] for row in out]
    for a, b in zip(w, w[1:]):
        assert b <= a + 5e-3


def test_yield_diff_ci_antisymmetric():
    N, n = 20_000, 500
    y, fa = make_pool(N, precision=0.5, rho=0.6, seed=8)
    _, fb = make_pool(N, precision=0.5, rho=0.3, seed=9)
    rng = np.random.default_rng(0)
    idx = rng.choice(N, n, replace=False)
    ab = ppi_yield_diff_ci(y[idx], fa[idx], fb[idx], fa, fb)
    ba = ppi_yield_diff_ci(y[idx], fb[idx], fa[idx], fb, fa)
    assert ab.estimate == pytest.approx(-ba.estimate, abs=1e-9)
    assert ab.lower == pytest.approx(-ba.upper, abs=1e-6)
