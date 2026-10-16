"""Exact checks of the paper's finite-population results on small pools (Theorem 1, Lemma 1,
Corollary 1, Propositions 2 and 3), independent of the Monte Carlo harness."""
import itertools

import numpy as np

from certdisc.core import _z, required_budget, wilson_ci


def _pop_var(x):
    return x.var(ddof=1)


def _pop_cov(x, y):
    return np.cov(x, y, ddof=1)[0, 1]


def test_theorem1_and_lemma1_by_exact_enumeration():
    rng = np.random.default_rng(0)
    for trial in range(40):
        N = int(rng.integers(5, 9)); n = int(rng.integers(2, N + 1))
        y = rng.integers(0, 2, N).astype(float)
        f = rng.random(N) if trial % 2 else rng.integers(0, 2, N).astype(float)
        lam = float(rng.normal())
        pi, fbar = y.mean(), f.mean()
        ests, vhats = [], []
        for L in itertools.combinations(range(N), n):
            L = list(L); r = y[L] - lam * f[L]
            ests.append(lam * fbar + r.mean())
            vhats.append(r.var(ddof=1) / n * (1 - n / N) + lam ** 2 * _pop_var(f) / N)
        ests = np.array(ests)
        Sr2 = _pop_var(y) - 2 * lam * _pop_cov(y, f) + lam ** 2 * _pop_var(f)
        assert abs(ests.mean() - pi) < 1e-12                                   # (i) unbiased
        assert abs(ests.var(ddof=0) - Sr2 / n * (1 - n / N)) < 1e-12           # (ii) exact variance
        assert abs(np.mean(vhats) - (Sr2 / n * (1 - n / N) + lam ** 2 * _pop_var(f) / N)) < 1e-12  # Lemma 1


def test_corollary1_budget_is_minimal():
    z = _z(0.05)
    for S2 in (0.01, 0.1, 0.25):
        for N in (500, 43437):
            for w in (0.01, 0.02, 0.05):
                n = required_budget(S2, N, w)
                hw = lambda k: z * np.sqrt(S2 * (1 / k - 1 / N))
                assert hw(n) <= w + 1e-12
                assert n == 2 or hw(n - 1) > w


def test_proposition2_wilson_lower_limit_exceeds_half():
    z = _z(0.05)
    for n in range(4, 2000):
        lo, _ = wilson_ci(n, n)
        assert abs(lo - n / (n + z * z)) < 1e-12 and lo > 0.5


def test_proposition3_pairing_dominates_for_any_covariance_sign():
    rng = np.random.default_rng(1)
    for t in range(20000):
        M = int(rng.integers(4, 40)); n = 2 * int(rng.integers(1, M // 2 + 1))
        y = rng.integers(0, 2, M).astype(float)
        fA = rng.random(M); fB = (1 - fA + rng.normal(0, 0.1, M)).clip(0, 1) if t % 3 == 0 else rng.random(M)
        lam = float(rng.normal())
        rA, rB = y * fA - lam * fA, y * fB - lam * fB
        SA, SB, SAB = _pop_var(rA), _pop_var(rB), _pop_cov(rA, rB)
        if SA + SB <= 0:
            continue
        vp = (1 / n) * (1 - n / M) * (SA + SB - 2 * SAB)
        vs = (2 / n) * (1 - n / (2 * M)) * (SA + SB)
        assert vp < vs
