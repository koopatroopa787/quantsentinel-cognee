"""Market data tool implementations."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import requests
import yfinance as yf

from tools.cache import get_cached, put


def fetch_ohlcv(
    ticker: str,
    start_date: str,
    end_date: str,
    interval: str = "1d",
) -> dict[str, Any]:
    """Fetch OHLCV data, cache it server-side, and return a compact summary.

    IMPORTANT FOR AGENTS: The full records are stored under cache_key.
    Do NOT include raw records in your response to the orchestrator — they are
    too large for LLM context.  Pass only the cache_key.  The next agent will
    call get_cached(cache_key) to retrieve the data.

    Direct Python callers (fallback pipeline) may use the records field directly.
    """
    dataframe = yf.download(
        ticker,
        start=start_date,
        end=end_date,
        interval=interval,
        auto_adjust=True,
        progress=False,
    )
    if dataframe.empty:
        return {
            "status": "error",
            "error_message": (
                f"No data returned for ticker {ticker} between {start_date} and {end_date}"
            ),
        }

    max_rows = int(os.getenv("MAX_BACKTEST_ROWS", "50000"))
    if len(dataframe) > max_rows:
        return {
            "status": "error",
            "error_message": f"Row count {len(dataframe)} exceeds MAX_BACKTEST_ROWS={max_rows}",
        }

    df = dataframe.reset_index()

    # Flatten MultiIndex columns (yfinance >= 0.2.40 behaviour)
    df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]

    column_map = {
        "Date": "date",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume",
    }
    df = df.rename(columns=column_map)
    if "date" not in df.columns:
        df["date"] = df.iloc[:, 0]
    df["date"] = df["date"].astype(str).str[:10]

    records = df[["date", "open", "high", "low", "close", "volume"]].to_dict(orient="records")
    cache_key = put(records, prefix="ohlcv")

    return {
        "status": "success",
        "ticker": ticker,
        "cache_key": cache_key,
        "record_count": len(records),
        "date_range": f"{records[0]['date']} to {records[-1]['date']}",
        # NOTE: raw records intentionally excluded — they are stored in the cache
        # under cache_key. The ADK session service persists every function response
        # verbatim; including thousands of OHLCV rows here causes context overflow.
        # Direct Python callers (fallback pipeline) must call cache.get(cache_key).
    }


# ---------------------------------------------------------------------------
# Hardcoded FOMC meeting dates (2005–2025) — used when FRED is unavailable.
# Source: Federal Reserve published meeting calendars.
# ---------------------------------------------------------------------------
_FOMC_DATES_FALLBACK: list[str] = [
    # 2005
    "2005-02-02","2005-03-22","2005-05-03","2005-06-30","2005-08-09",
    "2005-09-20","2005-11-01","2005-12-13",
    # 2006
    "2006-01-31","2006-03-28","2006-05-10","2006-06-29","2006-08-08",
    "2006-09-20","2006-10-25","2006-12-12",
    # 2007
    "2007-01-31","2007-03-21","2007-05-09","2007-06-28","2007-08-07",
    "2007-09-18","2007-10-31","2007-12-11",
    # 2008
    "2008-01-22","2008-01-30","2008-03-18","2008-04-30","2008-06-25",
    "2008-08-05","2008-09-16","2008-10-08","2008-10-29","2008-12-16",
    # 2009
    "2009-01-28","2009-03-18","2009-04-29","2009-06-24","2009-08-12",
    "2009-09-23","2009-11-04","2009-12-16",
    # 2010
    "2010-01-27","2010-03-16","2010-04-28","2010-06-23","2010-08-10",
    "2010-09-21","2010-11-03","2010-12-14",
    # 2011
    "2011-01-26","2011-03-15","2011-04-27","2011-06-22","2011-08-09",
    "2011-09-21","2011-11-02","2011-12-13",
    # 2012
    "2012-01-25","2012-03-13","2012-04-25","2012-06-20","2012-08-01",
    "2012-09-13","2012-10-24","2012-12-12",
    # 2013
    "2013-01-30","2013-03-20","2013-05-01","2013-06-19","2013-07-31",
    "2013-09-18","2013-10-30","2013-12-18",
    # 2014
    "2014-01-29","2014-03-19","2014-04-30","2014-06-18","2014-07-30",
    "2014-09-17","2014-10-29","2014-12-17",
    # 2015
    "2015-01-28","2015-03-18","2015-04-29","2015-06-17","2015-07-29",
    "2015-09-17","2015-10-28","2015-12-16",
    # 2016
    "2016-01-27","2016-03-16","2016-04-27","2016-06-15","2016-07-27",
    "2016-09-21","2016-11-02","2016-12-14",
    # 2017
    "2017-02-01","2017-03-15","2017-05-03","2017-06-14","2017-07-26",
    "2017-09-20","2017-11-01","2017-12-13",
    # 2018
    "2018-01-31","2018-03-21","2018-05-02","2018-06-13","2018-08-01",
    "2018-09-26","2018-11-08","2018-12-19",
    # 2019
    "2019-01-30","2019-03-20","2019-05-01","2019-06-19","2019-07-31",
    "2019-09-18","2019-10-30","2019-12-11",
    # 2020
    "2020-01-29","2020-03-03","2020-03-15","2020-04-29","2020-06-10",
    "2020-07-29","2020-09-16","2020-11-05","2020-12-16",
    # 2021
    "2021-01-27","2021-03-17","2021-04-28","2021-06-16","2021-07-28",
    "2021-09-22","2021-11-03","2021-12-15",
    # 2022
    "2022-01-26","2022-03-16","2022-05-04","2022-06-15","2022-07-27",
    "2022-09-21","2022-11-02","2022-12-14",
    # 2023
    "2023-02-01","2023-03-22","2023-05-03","2023-06-14","2023-07-26",
    "2023-09-20","2023-11-01","2023-12-13",
    # 2024
    "2024-01-31","2024-03-20","2024-05-01","2024-06-12","2024-07-31",
    "2024-09-18","2024-11-07","2024-12-18",
    # 2025
    "2025-01-29","2025-03-19","2025-05-07","2025-06-18","2025-07-30",
    "2025-09-17","2025-10-29","2025-12-10",
]


def fetch_fomc_dates(start_year: int = 2010, end_year: int = 2024) -> dict[str, Any]:
    """Fetch FOMC release dates from FRED and cache the result server-side.

    IMPORTANT FOR AGENTS: Returns a cache_key, not the raw date list.
    Pass the cache_key to the next agent; they will call get_cached(cache_key).

    Resilience strategy:
    - Retries the FRED API up to 3 times with 2-second back-off on 5xx errors.
    - Falls back to a hardcoded FOMC date table if FRED remains unavailable.
      The fallback covers 2005–2025 and is accurate for historical backtesting.
    """
    import time as _time  # noqa: PLC0415

    fred_key = os.getenv("FRED_API_KEY", "")

    filtered: list[str] | None = None  # will be set by FRED or fallback

    if fred_key:
        last_exc: Exception | None = None
        for attempt in range(3):
            try:
                response = requests.get(
                    "https://api.stlouisfed.org/fred/releases/dates",
                    params={"release_id": 82, "api_key": fred_key, "file_type": "json"},
                    timeout=30,
                )
                response.raise_for_status()
                payload = response.json()
                releases = payload.get("release_dates", [])
                filtered = []
                for item in releases:
                    date_str = item.get("date")
                    if not date_str:
                        continue
                    year = datetime.strptime(date_str, "%Y-%m-%d").year
                    if start_year <= year <= end_year:
                        filtered.append(date_str)
                break  # success — exit retry loop
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                if attempt < 2:
                    logger.warning(
                        "FRED fetch attempt %d/3 failed (%s) — retrying in 2s…",
                        attempt + 1, exc,
                    )
                    _time.sleep(2)
                else:
                    logger.warning(
                        "FRED API unavailable after 3 attempts (%s) — using hardcoded fallback.",
                        exc,
                    )
    else:
        logger.warning("FRED_API_KEY not configured — using hardcoded FOMC fallback.")

    # Use hardcoded fallback if FRED failed or key is missing
    if filtered is None:
        filtered = [
            d for d in _FOMC_DATES_FALLBACK
            if start_year <= int(d[:4]) <= end_year
        ]
        source = "fallback"
    else:
        source = "fred"

    cache_key = put(filtered, prefix="fomc")

    return {
        "status": "success",
        "cache_key": cache_key,
        "date_count": len(filtered),
        "year_range": f"{start_year}–{end_year}",
        "source": source,
        # NOTE: raw fomc_dates list intentionally excluded — stored in cache under
        # cache_key to prevent ADK session context bloat. Use cache.get(cache_key).
    }


# Re-export get_cached so agents only need to import from market_data
get_ohlcv_records = get_cached  # backward-compat alias used by data_agent / backtester_agent
