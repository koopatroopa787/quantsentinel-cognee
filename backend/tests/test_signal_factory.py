"""Unit tests for backend.tools.signal_factory.

These tests check that `generate_signal_code` routes each hypothesis to the
right strategy template and bakes the hypothesis-specific parameters (RSI
period/threshold, SMA windows, momentum lookback, ...) into the generated
code, plus that every generated snippet is syntactically valid Python.
"""

from __future__ import annotations

import ast

import pytest

from backend.tools.signal_factory import describe_signal, generate_signal_code


def _compiles(code: str) -> bool:
    ast.parse(code)
    return True


@pytest.mark.parametrize(
    "hypothesis",
    [
        "Does a 14-day RSI below 30 on SPY generate significant mean-reversion returns?",
        "Is there a golden cross signal when the 50-day SMA crosses the 200-day SMA?",
        "Does SPY outperform when price is above the 200-day SMA?",
        "Is SPY price above its 10-month SMA a reliable trend filter?",
        "Does 12-month momentum predict next-month returns?",
        "Do Bollinger Band breakouts on QQQ generate alpha?",
        "Does a MACD crossover on AAPL generate excess returns?",
        "Does SPY rally for 5 days following an FOMC rate decision?",
        "Does a low realised-volatility regime improve risk-adjusted returns?",
        "A completely generic hypothesis with no recognizable indicator",
    ],
)
def test_generated_code_is_valid_python(hypothesis):
    code = generate_signal_code(hypothesis)
    assert _compiles(code)
    # every template returns a dict with these keys
    for key in ("equity_curve", "returns", "sharpe", "max_drawdown", "win_rate", "num_trades"):
        assert f'"{key}"' in code


def test_rsi_hypothesis_bakes_in_period_and_threshold():
    code = generate_signal_code(
        "Does a 14-day RSI below 30 on SPY generate significant mean-reversion "
        "returns over 5 trading days?"
    )
    assert "rolling(14)" in code
    assert "rsi < 30" in code


def test_golden_cross_uses_detected_sma_windows():
    code = generate_signal_code(
        "Is there a golden cross signal when the 50-day SMA crosses above the 200-day SMA?"
    )
    assert "rolling(50)" in code
    assert "rolling(200)" in code


def test_price_vs_monthly_sma_converts_months_to_trading_days():
    code = generate_signal_code("Is SPY price above its 10-month SMA a reliable trend filter?")
    # 10 months -> 10 * 21 = 210 trading days
    assert "rolling(210)" in code
    assert "df['close'] > sma" in code


def test_price_vs_sma_below_uses_less_than_comparator():
    code = generate_signal_code("Does SPY underperform when price is below the 200-day SMA?")
    assert "rolling(200)" in code
    assert "df['close'] < sma" in code


def test_momentum_hypothesis_uses_lookback():
    code = generate_signal_code("Does 252-day momentum predict next-month returns?")
    assert "shift(252)" in code


def test_unrecognized_hypothesis_falls_back_to_mean_reversion():
    code = generate_signal_code("A completely generic hypothesis with no recognizable indicator")
    assert "5-day rolling mean-reversion" in code
    assert "rolling(5).mean()" in code


# ── Regression tests: short RSI periods / momentum lookbacks used to be ────
# silently discarded (or, worse, mixed up with the threshold/hold-days) by
# range-based positional extraction (e.g. RSI period had to be in 5..50, so
# "2-day RSI" fell through to a default of 14 and the leftover "2" was
# misassigned as the hold period).

def test_short_rsi_period_is_honored():
    code = generate_signal_code(
        "Does a 2-day RSI below 10 on AAPL generate mean-reversion returns "
        "over 3 trading days from 2018 to 2023?"
    )
    assert "rolling(2)" in code
    assert "rsi < 10" in code
    assert "rolling(3).max()" in code


def test_rsi_parenthetical_period_is_honored():
    code = generate_signal_code("Does RSI(2) below 5 on SPY generate mean reversion returns?")
    assert "rolling(2)" in code
    assert "rsi < 5" in code


def test_rsi_above_threshold_uses_greater_than_comparator():
    code = generate_signal_code("Is a 21-day RSI above 70 a good short-term overbought signal on QQQ?")
    assert "rolling(21)" in code
    assert "rsi > 70" in code


def test_short_momentum_lookback_is_honored():
    code = generate_signal_code("Does a 10-day momentum strategy on TSLA generate excess returns from 2019 to 2023?")
    assert "shift(10)" in code


def test_volatility_regime_routes_to_vix_filter():
    code = generate_signal_code("Does a low realised-volatility regime improve risk-adjusted returns?")
    assert "vol_20" in code and "vol_60" in code


# ── describe_signal: the memo's methodology text must match the generated ──
# code's actual parameters, not a separate hardcoded description.

def test_describe_signal_reflects_actual_rsi_period():
    hypothesis = "Does a 21-day RSI below 25 on AMZN generate mean-reversion returns over 10 trading days?"
    code = generate_signal_code(hypothesis)
    description = describe_signal(hypothesis)
    assert "rolling(21)" in code
    assert "21-day RSI" in description
    assert "10 trading days" in description


def test_describe_signal_for_macd_mentions_ema_not_sma():
    description = describe_signal("Does a MACD crossover on AAPL generate excess returns?")
    assert "MACD" in description
    assert "EMA" in description
    assert "SMA" not in description


def test_describe_signal_for_fomc_matches_event_study_code():
    hypothesis = "Does SPY rally for 5 days following an FOMC rate decision?"
    code = generate_signal_code(hypothesis)
    description = describe_signal(hypothesis)
    assert "fomc_dates" in code
    assert "FOMC" in description
    # Must not claim FOMC dates aren't used, since _fomc_signal does use them.
    assert "does not use FOMC" not in description


def test_describe_signal_for_momentum_matches_shift_based_code():
    hypothesis = "Does a 10-day momentum strategy on TSLA generate excess returns?"
    code = generate_signal_code(hypothesis)
    description = describe_signal(hypothesis)
    assert "shift(10)" in code
    assert "10 trading days ago" in description


def test_describe_signal_distinguishes_golden_cross_and_price_vs_sma():
    golden = describe_signal("Is there a golden cross signal when the 50-day SMA crosses the 200-day SMA?")
    price_vs_sma = describe_signal("Does NFLX outperform when price is above its 200-day SMA?")
    assert "crossover" in golden
    assert "crossover" not in price_vs_sma
    assert "Price-vs-SMA" in price_vs_sma
