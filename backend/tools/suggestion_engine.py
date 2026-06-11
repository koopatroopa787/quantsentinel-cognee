"""Alpha suggestion engine — memory-aware.

Generates an actionable improved hypothesis after each backtest run.
Reads the full run history so it never re-suggests a strategy that
has already been tested, and escalates appropriately.
"""

from __future__ import annotations

import re
from typing import Any

from evals.golden_dataset import GOLDEN_DATASET


# ── Helpers ───────────────────────────────────────────────────────────────

def _detect_signal_type(hypothesis: str) -> str:
    h = hypothesis.lower()
    if re.search(r'\b(rsi|relative strength)', h):
        return "rsi"
    if re.search(r'golden cross|death cross', h):
        return "golden_cross"
    if re.search(r'(above|below).{0,20}(200|50|100).{0,10}(sma|ma|moving)', h):
        return "price_vs_sma"
    if re.search(r'(sma|ema|moving average).{0,20}(above|cross|below)', h):
        return "sma_cross"
    if re.search(r'\b(fomc|fed|rate decision)', h):
        return "fomc_event"
    if re.search(r'\b(momentum|52.week|breakout)', h):
        return "momentum"
    if re.search(r'\b(bollinger|bb band)', h):
        return "bollinger"
    if re.search(r'\b(macd)\b', h):
        return "macd"
    return "mean_reversion"


def _extract_ticker(hypothesis: str) -> str:
    known = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META",
             "QQQ", "SPY", "IWM", "GLD", "TLT"]
    for t in known:
        if re.search(rf"\b{t}\b", hypothesis.upper()):
            return t
    return "SPY"


def _extract_years(hypothesis: str) -> tuple[str, str]:
    years = re.findall(r"\b(20[0-2][0-9])\b", hypothesis)
    return (min(years), max(years)) if len(years) >= 2 else ("2015", "2024")


def _already_tested(candidate: str, history: list[dict[str, Any]]) -> bool:
    """Check if a candidate hypothesis is semantically close to an already-tested one."""
    cand_lower = candidate.lower().strip()
    for item in history:
        prev = item.get("hypothesis", "").lower().strip()
        if not prev:
            continue
        # Exact match
        if prev == cand_lower:
            return True
        # High overlap: same ticker + same signal keywords
        ticker = _extract_ticker(candidate)
        if ticker.lower() in prev and _detect_signal_type(candidate) == _detect_signal_type(prev):
            return True
    return False


def _tested_signal_types(ticker: str, history: list[dict[str, Any]]) -> set[str]:
    """Return all signal types already tested on a given ticker."""
    tested: set[str] = set()
    for item in history:
        h = item.get("hypothesis", "")
        if ticker.upper() in h.upper():
            tested.add(_detect_signal_type(h))
    return tested


def _best_score_for_ticker(ticker: str, history: list[dict[str, Any]]) -> float:
    best = 0.0
    for item in history:
        if ticker.upper() in item.get("hypothesis", "").upper():
            s = float(item.get("score", 0))
            if s > best:
                best = s
    return best


# ── Candidate pool ─────────────────────────────────────────────────────────
# Each entry is a function (ticker, start_y, end_y) → dict

def _candidates(ticker: str, start_y: str, end_y: str) -> list[dict[str, Any]]:
    """Ordered list of strategies to try, from simple to sophisticated."""
    alt = "QQQ" if ticker == "SPY" else ("SPY" if ticker != "QQQ" else "QQQ")
    return [
        # Level 1: simple trend filter
        {
            "sig": "price_vs_sma",
            "title": "Price > 200-day SMA Trend Filter",
            "rationale": (
                "Hold the asset only when it is above its 200-day moving average. "
                "This eliminates bear-market periods and has historically reduced drawdowns "
                "by 30–50% with minimal impact on compound returns."
            ),
            "new_hypothesis": f"Does holding {ticker} only when its price is above the 200-day SMA outperform buy-and-hold from {start_y} to {end_y}?",
            "priority": "high",
        },
        # Level 2: MACD for cleaner entries
        {
            "sig": "macd",
            "title": "MACD Crossover — Cleaner Entry Signal",
            "rationale": (
                "MACD uses exponential rather than simple moving averages, "
                "so it responds faster to price changes and produces fewer whipsaws "
                "than SMA crossovers. Long when MACD line > signal line."
            ),
            "new_hypothesis": f"Does a MACD crossover strategy on {ticker} outperform buy-and-hold from {start_y} to {end_y}?",
            "priority": "high",
        },
        # Level 3: RSI dip-buying with trend filter
        {
            "sig": "rsi",
            "title": "RSI Dip-Buying + Trend Filter",
            "rationale": (
                "Pure RSI dip-buying often catches falling knives in bear markets. "
                "Combining RSI < 30 with price > 200-day SMA ensures you only buy "
                "dips in trending markets, dramatically improving the hit rate."
            ),
            "new_hypothesis": f"Does buying {ticker} when 14-day RSI < 30 AND price is above the 200-day SMA generate significant mean-reversion returns from {start_y} to {end_y}?",
            "priority": "medium",
        },
        # Level 4: Momentum lookback
        {
            "sig": "momentum",
            "title": "12-Month Momentum",
            "rationale": (
                "12-month price momentum (buy if today > price 252 trading days ago) "
                "is one of the most robustly documented factor premia in academic finance, "
                "with positive Sharpe ratios across asset classes and time periods."
            ),
            "new_hypothesis": f"Does buying {ticker} when its 252-day momentum is positive outperform buy-and-hold from {start_y} to {end_y}?",
            "priority": "medium",
        },
        # Level 5: Bollinger Band squeeze
        {
            "sig": "bollinger",
            "title": "Bollinger Band Mean-Reversion",
            "rationale": (
                "Buying when price closes below the lower Bollinger Band (2 std devs) "
                "captures extreme short-term oversold conditions. Works well on liquid "
                "index ETFs where mean-reversion is structurally present."
            ),
            "new_hypothesis": f"Does buying {ticker} when it closes below the lower Bollinger Band (20-day, 2σ) generate significant 5-day mean-reversion returns from {start_y} to {end_y}?",
            "priority": "low",
        },
        # Level 6: cross-asset momentum
        {
            "sig": "momentum_cross",
            "title": f"Try {alt} — Cross-Asset Momentum",
            "rationale": (
                f"After exhausting {ticker} signals, testing the same momentum framework "
                f"on {alt} provides an independent out-of-sample validation. "
                "Different volatility regimes often make one ETF more amenable to "
                "trend-following than the other."
            ),
            "new_hypothesis": f"Does buying {alt} when its 252-day momentum is positive outperform buy-and-hold from {start_y} to {end_y}?",
            "priority": "low",
        },
    ]


# ── Main entry point ───────────────────────────────────────────────────────

def generate_suggestion(
    hypothesis: str,
    backtest_result: dict[str, Any],
    benchmark_total_return: float,
    stat_summary: dict[str, Any],
    run_history: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return the next best hypothesis to test, accounting for what has already been run."""

    history = run_history or []
    ticker = _extract_ticker(hypothesis)
    start_y, end_y = _extract_years(hypothesis)

    total_return = backtest_result.get("total_return", 0.0)
    sharpe = backtest_result.get("sharpe", 0.0)
    max_dd = backtest_result.get("max_drawdown", 0.0)
    alpha = total_return - benchmark_total_return
    p_value = stat_summary.get("t_test", {}).get("p_value", 1.0)
    significant = stat_summary.get("t_test", {}).get("significant_at_5pct", False)

    tested_types = _tested_signal_types(ticker, history)

    # Work through the candidate pool in order, skipping already-tested types
    pool = _candidates(ticker, start_y, end_y)
    for candidate in pool:
        if candidate["sig"] in tested_types:
            continue
        if _already_tested(candidate["new_hypothesis"], history):
            continue
        # Found an untested candidate — add context about why we're suggesting it
        result = dict(candidate)

        # Append a "what we learned" note if multiple strategies have already been tested
        if len(tested_types) >= 2:
            best = _best_score_for_ticker(ticker, history)
            result["rationale"] = (
                f"You've now tested {len(tested_types)} strategies on {ticker} "
                f"(best score so far: {best:.2f}). " + result["rationale"]
            )
        elif alpha < -0.3:
            result["rationale"] = (
                f"Current strategy: alpha = {alpha:.1%}, Sharpe = {sharpe:.2f}. "
                + result["rationale"]
            )
        return result

    # All standard candidates exhausted — graduate to academically-validated golden hypotheses
    tested_hyps = {item.get("hypothesis", "").lower().strip() for item in history}
    for golden in GOLDEN_DATASET:
        hyp = golden["hypothesis"]
        if hyp.lower().strip() in tested_hyps:
            continue
        if _already_tested(hyp, history):
            continue
        return {
            "title": f"Graduate to Academically-Validated Research: {golden['expected_verdict'].replace('_', ' ').title()}",
            "rationale": (
                f"You've exhausted standard single-stock signals on {ticker}. "
                f"This hypothesis is drawn from the golden eval dataset — grounded in peer-reviewed finance research. "
                f"Expected verdict: {golden['expected_verdict'].replace('_', ' ')}. "
                f"Academic basis: {golden['notes'][:200]}…"
            ),
            "new_hypothesis": golden["hypothesis"],
            "priority": "medium",
        }

    # Truly exhausted — suggest extending the period
    all_tested = ", ".join(sorted(tested_types))
    best = _best_score_for_ticker(ticker, history)
    start_ext = str(int(start_y) - 5)
    return {
        "title": "Full Research Programme Complete — Try Walk-Forward Validation",
        "rationale": (
            f"You've tested all standard signals ({all_tested}) on {ticker} and worked through the "
            f"golden hypothesis set. Best score: {best:.2f}. "
            f"The final step is walk-forward validation: split {start_y}–{end_y} into in-sample "
            f"(training) and out-of-sample (test) windows. Any edge that survives OOS is likely real."
        ),
        "new_hypothesis": (
            f"Does the best-performing strategy on {ticker} remain profitable on out-of-sample data "
            f"from {start_ext} to {end_y} using walk-forward validation?"
        ),
        "priority": "low",
    }
