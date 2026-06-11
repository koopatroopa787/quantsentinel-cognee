"""Data agent — fetches OHLCV market data and FOMC dates."""

from __future__ import annotations

from google.adk.agents import Agent

from tools.cache import get_cached
from tools.market_data import fetch_fomc_dates, fetch_ohlcv


DATA_AGENT_INSTRUCTION = """
You are the Data Agent for QuantSentinel. Your sole responsibility is data
acquisition. Given a research plan, execute the following:

1. Call fetch_ohlcv for EACH ticker in the required tickers list, using the
   specified start_date and end_date. Always use interval="1d" unless told
   otherwise.

   IMPORTANT: fetch_ohlcv stores the data server-side and returns a compact
   summary including a "cache_key". Do NOT include the raw records in your
   response — they are too large. Instead return:
     - status: "success"
     - For each ticker: { "cache_key": <key>, "record_count": <n>, "date_range": <range> }
     - fomc_cache_key (if fetched)

2. If FOMC dates are required, call fetch_fomc_dates with the appropriate
   start_year and end_year derived from the date range.

   IMPORTANT: fetch_fomc_dates always returns status "success" — it uses a
   hardcoded fallback table when FRED is unavailable. The response includes a
   "source" field ("fred" or "fallback") — both are equally valid. NEVER
   treat a "fallback" source as an error. Always pass the cache_key forward.

3. Return a concise JSON response with the cache_keys (NOT the raw records).
   The backtester will use get_cached(cache_key) to retrieve the data.

If fetch_ohlcv fails, report the error clearly and stop.
"""

# Gemini Flash — fast, cheap, sufficient for data fetching
data_agent = Agent(
    name="data_agent",
    model="gemini-2.5-flash",
    description="Fetches OHLCV market data and FOMC dates for a research plan.",
    tools=[fetch_ohlcv, fetch_fomc_dates, get_cached],
    instruction=DATA_AGENT_INSTRUCTION,
)
