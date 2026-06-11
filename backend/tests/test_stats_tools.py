"""Unit tests for backend.tools.stats_tools."""

from __future__ import annotations

import math

from backend.tools.stats_tools import bootstrap_ci, compute_sharpe, compute_t_test


class TestComputeTTest:
    def test_empty_inputs_return_neutral_result(self):
        result = compute_t_test([], [])
        assert result == {
            "t_statistic": 0.0,
            "p_value": 1.0,
            "significant_at_5pct": False,
        }

    def test_empty_returns_only(self):
        result = compute_t_test([], [0.01, 0.02])
        assert result["significant_at_5pct"] is False

    def test_identical_distributions_are_not_significant(self):
        returns = [0.01, 0.02, -0.01, 0.005, 0.0]
        result = compute_t_test(returns, returns)
        assert result["t_statistic"] == 0.0
        assert result["p_value"] == 1.0
        assert result["significant_at_5pct"] is False

    def test_clearly_different_distributions_are_significant(self):
        strategy = [0.05] * 30
        benchmark = [-0.05] * 30
        result = compute_t_test(strategy, benchmark)
        assert result["significant_at_5pct"] is True
        assert result["p_value"] < 0.05

    def test_no_nan_in_output(self):
        result = compute_t_test([0.01], [0.02])
        assert not math.isnan(result["t_statistic"])
        assert not math.isnan(result["p_value"])


class TestBootstrapCi:
    def test_empty_returns_zeroed_result(self):
        result = bootstrap_ci([])
        assert result == {"lower": 0.0, "upper": 0.0, "mean": 0.0}

    def test_constant_returns_have_zero_width_interval(self):
        result = bootstrap_ci([0.01] * 50, n_iterations=200)
        assert result["lower"] == result["upper"] == result["mean"]
        assert result["mean"] == 0.01

    def test_interval_brackets_the_mean(self):
        returns = [0.01, 0.02, -0.01, 0.03, -0.02, 0.015]
        result = bootstrap_ci(returns, n_iterations=500)
        assert result["lower"] <= result["mean"] <= result["upper"]

    def test_wider_ci_produces_wider_interval(self):
        returns = [0.01, -0.03, 0.02, -0.01, 0.04, -0.02, 0.0, 0.015]
        narrow = bootstrap_ci(returns, n_iterations=500, ci=0.5)
        wide = bootstrap_ci(returns, n_iterations=500, ci=0.99)
        narrow_width = narrow["upper"] - narrow["lower"]
        wide_width = wide["upper"] - wide["lower"]
        assert wide_width >= narrow_width


class TestComputeSharpe:
    def test_empty_returns_zero(self):
        assert compute_sharpe([]) == 0.0

    def test_zero_variance_returns_zero(self):
        assert compute_sharpe([0.0] * 10) == 0.0

    def test_positive_returns_yield_positive_sharpe(self):
        returns = [0.002, 0.001, 0.003, 0.0015, 0.0025] * 10
        sharpe = compute_sharpe(returns)
        assert sharpe > 0

    def test_negative_returns_yield_negative_sharpe(self):
        returns = [-0.002, -0.001, -0.003, -0.0015, -0.0025] * 10
        sharpe = compute_sharpe(returns)
        assert sharpe < 0

    def test_higher_risk_free_rate_lowers_sharpe(self):
        returns = [0.002, 0.001, 0.003, 0.0015, 0.0025, -0.001] * 5
        low_rf = compute_sharpe(returns, risk_free_annual=0.0)
        high_rf = compute_sharpe(returns, risk_free_annual=0.20)
        assert high_rf < low_rf
