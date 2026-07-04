"""certdisc: certified discovery for AI-driven materials screening.

Prediction-powered confidence intervals for discovery precision, stable-material
counts, and model comparisons, from a small randomly sampled DFT verification
budget. Implements the estimators of the paper "Certified discovery: statistically
valid materials screening claims from a small DFT verification budget."

Public API
----------
classical_ci            Label-only (classical) confidence interval.
imputation_estimate     Naive "trust the model" point estimate (no interval).
wilson_ci               Wilson score interval (small-sample fallback).
ppi_mean_ci             PPI/PPI++ interval for discovery precision.
ppi_count_ci            PPI/PPI++ interval for the count of stable materials.
ppi_yield_diff_ci       Paired PPI interval for a difference between two models.
required_budget         Closed-form DFT budget for a target interval width.
neyman_allocation       Variance-optimal per-stratum label allocation.
stratified_ppi_ci       Stratified PPI interval with Neyman allocation.
simulate_campaign       One Monte Carlo certification campaign.
budget_curve            Interval width as a function of the verification budget.
"""

from .core import (
    classical_ci,
    imputation_estimate,
    wilson_ci,
    ppi_mean_ci,
    ppi_count_ci,
    ppi_yield_diff_ci,
    required_budget,
    neyman_allocation,
    stratified_ppi_ci,
    simulate_campaign,
    budget_curve,
)

__all__ = [
    "classical_ci",
    "imputation_estimate",
    "wilson_ci",
    "ppi_mean_ci",
    "ppi_count_ci",
    "ppi_yield_diff_ci",
    "required_budget",
    "neyman_allocation",
    "stratified_ppi_ci",
    "simulate_campaign",
    "budget_curve",
]

__version__ = "1.0.0"
