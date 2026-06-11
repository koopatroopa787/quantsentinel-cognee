"""Statistical helper tools for backtest analysis."""

from __future__ import annotations

from math import sqrt
from typing import Any

import numpy as np
from scipy import stats


def compute_t_test(returns: list[float], benchmark_returns: list[float]) -> dict[str, Any]:
    """Compute Welch's t-test for strategy vs benchmark returns."""
    if not returns or not benchmark_returns:
        return {"t_statistic": 0.0, "p_value": 1.0, "significant_at_5pct": False}
    t_statistic, p_value = stats.ttest_ind(returns, benchmark_returns, equal_var=False)
    t_val = float(0.0 if np.isnan(t_statistic) else t_statistic)
    p_val = float(1.0 if np.isnan(p_value) else p_value)
    return {"t_statistic": t_val, "p_value": p_val, "significant_at_5pct": p_val < 0.05}


def bootstrap_ci(
    returns: list[float],
    n_iterations: int = 1000,
    ci: float = 0.95,
) -> dict[str, float]:
    """Compute bootstrap confidence interval for mean returns."""
    if not returns:
        return {"lower": 0.0, "upper": 0.0, "mean": 0.0}
    arr = np.array(returns, dtype=float)
    means = []
    for _ in range(n_iterations):
        sample = np.random.choice(arr, size=len(arr), replace=True)
        means.append(float(np.mean(sample)))
    alpha = 1.0 - ci
    lower = float(np.quantile(means, alpha / 2))
    upper = float(np.quantile(means, 1 - alpha / 2))
    return {"lower": lower, "upper": upper, "mean": float(np.mean(arr))}


def compute_sharpe(returns: list[float], risk_free_annual: float = 0.05) -> float:
    """Compute annualized Sharpe ratio from daily returns."""
    if not returns:
        return 0.0
    arr = np.array(returns, dtype=float)
    daily_rf = risk_free_annual / 252
    std = float(np.std(arr))
    if std == 0.0:
        return 0.0
    return float((np.mean(arr) - daily_rf) / std * sqrt(252))

