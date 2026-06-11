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
    if re.search(r'\b(vix|volatility spike)\b', hl):
        return "vix_filter"
    if re.search(r'\b(bollinger|bb|band)\b', hl):
        return "bollinger"
    if re.search(r'\b(macd)\b', hl):
        return "macd"
    return "mean_reversion"


# ── Signal implementations ─────────────────────────────────────────────────

def _rsi_signal(hypothesis: str) -> str:
    nums = _extract_numbers(hypothesis)
    period = next((n for n in nums if 5 <= n <= 50), 14)
    threshold = next((n for n in nums if 10 <= n <= 45 and n != period), 30)
    hold_days = next((n for n in nums if 1 <= n <= 20 and n not in (period, threshold)), 5)
    return f"""{_HEADER}
    # RSI mean-reversion: go long when RSI < {threshold}, hold for {hold_days} days
    delta = df['close'].diff()
    gain = delta.clip(lower=0).rolling({period}).mean()
    loss = (-delta.clip(upper=0)).rolling({period}).mean()
    rsi = 100 - (100 / (1 + gain / (loss + 1e-9)))
    signal_raw = (rsi < {threshold}).astype(int)
    # Hold for {hold_days} days after signal fires
    position = signal_raw.rolling({hold_days}).max().fillna(0)
    strat_ret = position.shift(1).fillna(0) * df['ret']
    equity_curve = (1 + strat_ret).cumprod().tolist()
{_STATS_BLOCK}"""


def _golden_cross_signal(hypothesis: str) -> str:
    nums = _extract_numbers(hypothesis)
    sma_nums = sorted([n for n in nums if 5 <= n <= 500])
    short_w = sma_nums[0] if len(sma_nums) >= 1 else 50
    long_w = sma_nums[1] if len(sma_nums) >= 2 else 200
    return f"""{_HEADER}
    # Golden cross: long when {short_w}-day SMA > {long_w}-day SMA
    sma_short = df['close'].rolling({short_w}).mean()
    sma_long = df['close'].rolling({long_w}).mean()
    position = (sma_short > sma_long).astype(int)
    strat_ret = position.shift(1).fillna(0) * df['ret']
    equity_curve = (1 + strat_ret).cumprod().tolist()
{_STATS_BLOCK}"""


def _price_vs_sma_signal(hypothesis: str) -> str:
    nums = _extract_numbers(hypothesis)
    hl = hypothesis.lower()
    direction = "below" if "below" in hl else "above"
    cmp = "<" if direction == "below" else ">"
    # Detect monthly vs daily and pick window accordingly
    # "10-month" → 210 trading days; "200-day" → 200; default 200
    if "month" in hl:
        months = next((n for n in nums if 1 <= n <= 24), 10)
        period = months * 21  # ~21 trading days per month
        label = f"{months}-month ({period}-day) SMA"
    else:
        period = next((n for n in nums if 20 <= n <= 500), 200)
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
    nums = _extract_numbers(hypothesis)
    lookback = next((n for n in nums if 20 <= n <= 500), 252)
    return f"""{_HEADER}
    # Momentum: long when today's close > close {lookback} days ago
    position = (df['close'] > df['close'].shift({lookback})).astype(int)
    strat_ret = position.shift(1).fillna(0) * df['ret']
    equity_curve = (1 + strat_ret).cumprod().tolist()
{_STATS_BLOCK}"""


def _bollinger_signal(hypothesis: str) -> str:
    nums = _extract_numbers(hypothesis)
    period = next((n for n in nums if 5 <= n <= 100), 20)
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
    nums = _extract_numbers(hypothesis)
    hold = next((n for n in nums if 1 <= n <= 20), 5)
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
