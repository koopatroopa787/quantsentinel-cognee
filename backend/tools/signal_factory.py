"""Signal factory — generate hypothesis-specific Python signal code for the fallback pipeline.

The fallback pipeline used to run the same 5-day mean-reversion signal for every
hypothesis.  This module detects what the hypothesis is actually asking and returns
appropriate, runnable signal code so the backtest results are meaningful.
"""

from __future__ import annotations

import re


# ── Shared boilerplate (appended to every signal) ─────────────────────────

_STATS_BLOCK = """
    ec = np.array(equity_curve)
    if len(ec) == 0:
        ec = np.array([1.0])
        equity_curve = [1.0]
    running_max = np.maximum.accumulate(ec)
    max_dd = float(((running_max - ec) / (running_max + 1e-9)).max())
    held = position.shift(1).fillna(0) > 0
    active_days = int(held.sum())
    wins = int((strat_ret[held] > 0).sum())
    win_rate = float(wins / max(active_days, 1))
    trades = df.index[position.diff().fillna(0) != 0].tolist()
    return {
        "equity_curve": equity_curve,
        "returns": strat_ret.tolist(),
        "trades": [str(t) for t in trades],
        "total_return": float(ec[-1] - 1.0),
        "sharpe": float(strat_ret.mean() / (strat_ret.std() + 1e-9) * (252 ** 0.5)),
        "max_drawdown": max_dd,
        "win_rate": win_rate,
        "num_trades": int(max(len(trades) // 2, 1)),
    }
"""

_HEADER = "import numpy as np\nimport pandas as pd\n\n\ndef run(df: pd.DataFrame, fomc_dates):\n    df = df.copy()\n    df['ret'] = df['close'].pct_change().fillna(0.0)\n"


# ── Detectors ─────────────────────────────────────────────────────────────

def _extract_numbers(hypothesis: str) -> list[int]:
    return [int(n) for n in re.findall(r'\b(\d+)\b', hypothesis)]


def _detect(h: str) -> str:
    """Return a signal-type tag."""
    hl = h.lower()
    if re.search(r'\b(rsi|relative strength)', hl):
        return "rsi"
    if re.search(r'golden cross|death cross', hl):
        return "golden_cross"
    # "above the 10-month / 200-day SMA" — any period, monthly or daily
    if re.search(r'(above|below).{0,30}(sma|moving average|ma\b)', hl):
        return "price_vs_sma"
    if re.search(r'(above|below).{0,20}(200|50|100|10).{0,10}(sma|ma|moving|month)', hl):
        return "price_vs_sma"
    if re.search(r'(sma|ema|moving average).{0,20}(above|cross|below)', hl):
        return "sma_cross"
    if re.search(r'\b(fomc|fed|rate decision|interest rate)', hl):
        return "fomc"
    # "12-month return is positive", "trailing 12-month", "252-day momentum"
    if re.search(r'(trailing|12.month|12-month).{0,20}(return|momentum)', hl):
        return "momentum"
    if re.search(r'\b(momentum|52.week|breakout|rate of change|roc)\b', hl):
        return "momentum"
    if re.search(r'\b(vix|volatility)\b', hl):
        return "vix_filter"
    if re.search(r'\b(bollinger|bb|band)\b', hl):
        return "bollinger"
    if re.search(r'\b(macd)\b', hl):
        return "macd"
    return "mean_reversion"


# ── Parameter extraction ───────────────────────────────────────────────────
# Shared by the *_signal code generators below and by describe_signal(), so
# the memo's methodology text can never disagree with the code that actually
# ran. These prefer phrasing anchored to the indicator name (e.g. "2-day RSI",
# "RSI(2)", "below 10", "10-day momentum") over blind positional/range-based
# number extraction, which used to silently discard or mix up parameters that
# fell outside hardcoded ranges (e.g. an RSI period < 5 or a momentum lookback
# < 20 would be dropped and a default substituted instead).

def _rsi_params(hypothesis: str) -> tuple[int, int, int, str]:
    """Return (period, threshold, hold_days, comparator) for an RSI signal."""
    h = hypothesis.lower()
    nums = _extract_numbers(hypothesis)

    period_match = re.search(r'(\d+)[\s-]*(?:day|days|period)?[\s-]*rsi', h) or \
        re.search(r'rsi[\s(]*(\d+)', h)
    period = int(period_match.group(1)) if period_match else next((n for n in nums if 5 <= n <= 50), 14)

    below_match = re.search(r'(?:below|under|less than)\s*(\d+)', h)
    above_match = re.search(r'(?:above|over|greater than|exceed\w*)\s*(\d+)', h)
    if below_match:
        threshold, comparator = int(below_match.group(1)), "<"
    elif above_match:
        threshold, comparator = int(above_match.group(1)), ">"
    else:
        threshold, comparator = next((n for n in nums if 10 <= n <= 90 and n != period), 30), "<"

    hold_match = re.search(r'(?:hold(?:ing)?(?:\s*for)?|over|for)\s*(\d+)\s*(?:trading\s*)?days?', h)
    if hold_match:
        hold_days = int(hold_match.group(1))
    else:
        hold_days = next((n for n in nums if 1 <= n <= 20 and n not in (period, threshold)), 5)

    return period, threshold, hold_days, comparator


def _golden_cross_params(hypothesis: str) -> tuple[int, int]:
    """Return (short_window, long_window) for a golden/death-cross signal."""
    nums = _extract_numbers(hypothesis)
    sma_nums = sorted({n for n in nums if 5 <= n <= 500})
    short_w = sma_nums[0] if len(sma_nums) >= 1 else 50
    long_w = sma_nums[1] if len(sma_nums) >= 2 else 200
    return short_w, long_w


def _price_vs_sma_params(hypothesis: str) -> tuple[int, str, str]:
    """Return (window_days, direction, comparator) for a price-vs-SMA signal."""
    nums = _extract_numbers(hypothesis)
    hl = hypothesis.lower()
    direction = "below" if "below" in hl else "above"
    cmp = "<" if direction == "below" else ">"
    if "month" in hl:
        months = next((n for n in nums if 1 <= n <= 24), 10)
        period = months * 21  # ~21 trading days per month
    else:
        period = next((n for n in nums if 20 <= n <= 500), 200)
    return period, direction, cmp


def _momentum_lookback(hypothesis: str) -> int:
    """Return the lookback window (in trading days) for a momentum signal."""
    h = hypothesis.lower()
    nums = _extract_numbers(hypothesis)

    month_match = re.search(r'(\d+)[\s-]*month', h)
    if month_match:
        return int(month_match.group(1)) * 21  # ~21 trading days per month

    day_match = re.search(r'(\d+)[\s-]*(?:day|days)?[\s-]*momentum', h) or \
        re.search(r'momentum[\s(]*(\d+)', h)
    if day_match:
        return int(day_match.group(1))

    return next((n for n in nums if 5 <= n <= 500), 252)


def _bollinger_period(hypothesis: str) -> int:
    """Return the rolling window for a Bollinger Band signal."""
    nums = _extract_numbers(hypothesis)
    return next((n for n in nums if 5 <= n <= 100), 20)


def _fomc_hold(hypothesis: str) -> int:
    """Return the holding period (in trading days) for an FOMC event-study signal."""
    nums = _extract_numbers(hypothesis)
    return next((n for n in nums if 1 <= n <= 20), 5)


# ── Signal implementations ─────────────────────────────────────────────────

def _rsi_signal(hypothesis: str) -> str:
    period, threshold, hold_days, comparator = _rsi_params(hypothesis)
    direction = "below" if comparator == "<" else "above"
    return f"""{_HEADER}
    # RSI mean-reversion: go long when {period}-day RSI is {direction} {threshold}, hold for {hold_days} days
    delta = df['close'].diff()
    gain = delta.clip(lower=0).rolling({period}).mean()
    loss = (-delta.clip(upper=0)).rolling({period}).mean()
    rsi = 100 - (100 / (1 + gain / (loss + 1e-9)))
    signal_raw = (rsi {comparator} {threshold}).astype(int)
    # Hold for {hold_days} days after signal fires
    position = signal_raw.rolling({hold_days}).max().fillna(0)
    strat_ret = position.shift(1).fillna(0) * df['ret']
    equity_curve = (1 + strat_ret).cumprod().tolist()
{_STATS_BLOCK}"""


def _golden_cross_signal(hypothesis: str) -> str:
    short_w, long_w = _golden_cross_params(hypothesis)
    return f"""{_HEADER}
    # Golden cross: long when {short_w}-day SMA > {long_w}-day SMA
    sma_short = df['close'].rolling({short_w}).mean()
    sma_long = df['close'].rolling({long_w}).mean()
    position = (sma_short > sma_long).astype(int)
    strat_ret = position.shift(1).fillna(0) * df['ret']
    equity_curve = (1 + strat_ret).cumprod().tolist()
{_STATS_BLOCK}"""


def _price_vs_sma_signal(hypothesis: str) -> str:
    period, direction, cmp = _price_vs_sma_params(hypothesis)
    # "10-month" → 210 trading days; "200-day" → 200
    if "month" in hypothesis.lower():
        label = f"{period // 21}-month ({period}-day) SMA"
    else:
        label = f"{period}-day SMA"
    return f"""{_HEADER}
    # Hold when price is {direction} the {label}
    sma = df['close'].rolling({period}).mean()
    position = (df['close'] {cmp} sma).astype(int)
    strat_ret = position.shift(1).fillna(0) * df['ret']
    equity_curve = (1 + strat_ret).cumprod().tolist()
{_STATS_BLOCK}"""


def _vix_filter_signal() -> str:
    """VIX regime filter — hold SPY when VIX is low (calm markets), cash when high.
    Since we only have the target ticker's OHLCV, we proxy VIX regime using
    the target asset's own 20-day realised volatility: invest when vol < long-run median.
    """
    return f"""{_HEADER}
    # Volatility regime filter: long when 20-day realised vol < 60-day median vol
    log_ret = np.log(df['close'] / df['close'].shift(1)).fillna(0)
    vol_20  = log_ret.rolling(20).std() * np.sqrt(252)
    vol_60  = log_ret.rolling(60).std() * np.sqrt(252)
    # Low-vol regime = 20-day vol below 60-day vol (calm, trending up)
    position = (vol_20 < vol_60).astype(int)
    strat_ret = position.shift(1).fillna(0) * df['ret']
    equity_curve = (1 + strat_ret).cumprod().tolist()
{_STATS_BLOCK}"""


def _momentum_signal(hypothesis: str) -> str:
    lookback = _momentum_lookback(hypothesis)
    return f"""{_HEADER}
    # Momentum: long when today's close > close {lookback} days ago
    position = (df['close'] > df['close'].shift({lookback})).astype(int)
    strat_ret = position.shift(1).fillna(0) * df['ret']
    equity_curve = (1 + strat_ret).cumprod().tolist()
{_STATS_BLOCK}"""


def _bollinger_signal(hypothesis: str) -> str:
    period = _bollinger_period(hypothesis)
    return f"""{_HEADER}
    # Bollinger Band mean-reversion: long when price < lower band
    mid = df['close'].rolling({period}).mean()
    std = df['close'].rolling({period}).std()
    lower = mid - 2 * std
    position = (df['close'] < lower).astype(int).rolling(5).max().fillna(0)
    strat_ret = position.shift(1).fillna(0) * df['ret']
    equity_curve = (1 + strat_ret).cumprod().tolist()
{_STATS_BLOCK}"""


def _macd_signal(hypothesis: str) -> str:
    return f"""{_HEADER}
    # MACD crossover: long when MACD line crosses above signal line
    ema12 = df['close'].ewm(span=12, adjust=False).mean()
    ema26 = df['close'].ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal_line = macd.ewm(span=9, adjust=False).mean()
    position = (macd > signal_line).astype(int)
    strat_ret = position.shift(1).fillna(0) * df['ret']
    equity_curve = (1 + strat_ret).cumprod().tolist()
{_STATS_BLOCK}"""


def _fomc_signal(hypothesis: str) -> str:
    hold = _fomc_hold(hypothesis)
    return f"""{_HEADER}
    # FOMC event study: long for {hold} days starting on each FOMC date
    import datetime
    fomc_set = set(fomc_dates or [])
    df['date_str'] = df['close'].index.astype(str) if not hasattr(df.index, 'strftime') else [d.strftime('%Y-%m-%d') for d in df.index]
    # If date column exists
    if 'date' in df.columns:
        df['date_str'] = df['date'].astype(str).str[:10]
    position = pd.Series(0, index=df.index)
    for i, row in enumerate(df['date_str']):
        if row in fomc_set:
            position.iloc[i:i+{hold}] = 1
    strat_ret = position.shift(1).fillna(0) * df['ret']
    equity_curve = (1 + strat_ret).cumprod().tolist()
{_STATS_BLOCK}"""


def _mean_reversion_signal() -> str:
    """Default fallback."""
    return f"""{_HEADER}
    # 5-day rolling mean-reversion: go long after 5 consecutive down days
    position = (df['ret'].rolling(5).mean().fillna(0.0) < 0).astype(int)
    strat_ret = position.shift(1).fillna(0) * df['ret']
    equity_curve = (1 + strat_ret).cumprod().tolist()
{_STATS_BLOCK}"""


# ── Public API ─────────────────────────────────────────────────────────────

def generate_signal_code(hypothesis: str) -> str:
    """Return runnable signal code tailored to the given hypothesis string."""
    sig_type = _detect(hypothesis)
    if sig_type == "rsi":
        return _rsi_signal(hypothesis)
    if sig_type == "golden_cross":
        return _golden_cross_signal(hypothesis)
    if sig_type == "price_vs_sma":
        return _price_vs_sma_signal(hypothesis)
    if sig_type == "sma_cross":
        return _golden_cross_signal(hypothesis)
    if sig_type == "momentum":
        return _momentum_signal(hypothesis)
    if sig_type == "bollinger":
        return _bollinger_signal(hypothesis)
    if sig_type == "macd":
        return _macd_signal(hypothesis)
    if sig_type == "fomc":
        return _fomc_signal(hypothesis)
    if sig_type == "vix_filter":
        return _vix_filter_signal()
    return _mean_reversion_signal()


def describe_signal(hypothesis: str) -> str:
    """Human-readable description of the signal `generate_signal_code` produces.

    Built from the same detection and parameter-extraction logic as the code
    generators above, so this description can never disagree with the code
    that actually runs (e.g. it won't say "14-day RSI" when the generated
    code uses a 21-day window, or describe a moving-average crossover for a
    hypothesis that actually ran an FOMC event study).
    """
    sig_type = _detect(hypothesis)
    if sig_type == "rsi":
        period, threshold, hold_days, comparator = _rsi_params(hypothesis)
        zone = "oversold" if comparator == "<" else "overbought"
        day_word = "day" if hold_days == 1 else "days"
        return (
            f"RSI mean-reversion signal: long when the {period}-day RSI is "
            f"{'below' if comparator == '<' else 'above'} {threshold} ({zone}), "
            f"holding the position for {hold_days} trading {day_word}, flat otherwise."
        )
    if sig_type in ("golden_cross", "sma_cross"):
        short_w, long_w = _golden_cross_params(hypothesis)
        return (
            f"Moving-average crossover signal: long when the {short_w}-day SMA is "
            f"above the {long_w}-day SMA, flat otherwise."
        )
    if sig_type == "price_vs_sma":
        period, direction, _cmp = _price_vs_sma_params(hypothesis)
        return (
            f"Price-vs-SMA signal: long while price is {direction} its {period}-day "
            f"SMA, flat otherwise."
        )
    if sig_type == "momentum":
        lookback = _momentum_lookback(hypothesis)
        return (
            f"Momentum signal: long when today's close is above the close from "
            f"{lookback} trading days ago, flat otherwise."
        )
    if sig_type == "bollinger":
        period = _bollinger_period(hypothesis)
        return (
            f"Bollinger Band mean-reversion signal: long when price closes below "
            f"the lower {period}-day (2 std-dev) band, holding for up to 5 days, "
            f"flat otherwise."
        )
    if sig_type == "macd":
        return (
            "MACD crossover signal: long when the MACD line (12-day EMA minus "
            "26-day EMA) is above its 9-day EMA signal line, flat otherwise."
        )
    if sig_type == "fomc":
        hold = _fomc_hold(hypothesis)
        return (
            f"FOMC event-study signal: long for {hold} trading days starting on "
            f"each FOMC announcement date, flat otherwise."
        )
    if sig_type == "vix_filter":
        return (
            "Volatility-regime signal: long when 20-day realised volatility is "
            "below 60-day realised volatility (a calm regime), flat otherwise."
        )
    return (
        "5-day rolling mean-reversion signal: long after the 5-day rolling mean "
        "daily return turns negative, flat otherwise."
    )
