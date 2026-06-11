"""General-purpose in-process data cache.

Large tool outputs (OHLCV records, backtest equity curves, FOMC date lists)
must NOT be passed raw through LLM context — each hop costs thousands of tokens
and causes agent timeouts.  Instead, every tool stores its result here and
returns only a compact summary + cache_key.  Agents pass cache_keys between
steps; the receiving agent calls get_cached(cache_key) to retrieve the data
without involving the LLM in the transfer.
"""

from __future__ import annotations

import uuid
from typing import Any

_STORE: dict[str, Any] = {}


def put(data: Any, prefix: str = "") -> str:
    """Store *data* and return a short cache key."""
    key = f"{prefix}_{uuid.uuid4().hex[:10]}" if prefix else uuid.uuid4().hex[:10]
    _STORE[key] = data
    return key


def get(cache_key: str) -> Any | None:
    """Return stored data or None if the key is missing."""
    return _STORE.get(cache_key)


def get_cached(cache_key: str) -> dict[str, Any]:
    """ADK tool: retrieve any previously cached payload by key.

    Use this when another agent has passed you a cache_key instead of raw data.
    Works for OHLCV records, FOMC dates, backtest results, or any other payload.
    """
    data = _STORE.get(cache_key)
    if data is None:
        return {
            "status": "error",
            "error_message": (
                f"Cache key '{cache_key}' not found. "
                "Ensure the producing tool was called first in this session."
            ),
        }
    # Return a type hint so the agent knows what it got back
    data_type = type(data).__name__
    if isinstance(data, list):
        return {"status": "success", "cache_key": cache_key, "type": data_type, "count": len(data), "data": data}
    if isinstance(data, dict):
        return {"status": "success", "cache_key": cache_key, "type": data_type, "data": data}
    return {"status": "success", "cache_key": cache_key, "type": data_type, "data": data}
