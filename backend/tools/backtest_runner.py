"""Sandboxed backtest execution tool."""

from __future__ import annotations

import ast
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


def _sanitize(obj: Any) -> Any:
    """Recursively replace NaN/Inf floats with 0.0 — NaN is invalid JSON and rejected by Gemini API."""
    if isinstance(obj, float):
        return 0.0 if (math.isnan(obj) or math.isinf(obj)) else obj
    if isinstance(obj, list):
        return [_sanitize(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    return obj

from tools.cache import get_cached, put


BACKTEST_SIGNAL_TEMPLATE = """
The signal code must define:
    run(df: pd.DataFrame, fomc_dates: list | None) -> dict

The result dict must include:
{
  "equity_curve": [...],
  "returns": [...],
  "trades": [...],
  "total_return": float,
  "sharpe": float,
  "max_drawdown": float,
  "win_rate": float,
  "num_trades": int
}
"""

_ALLOWED_IMPORTS = {"pandas", "numpy", "scipy", "datetime", "json", "math", "statistics"}


def _is_allowed_module(module: str) -> bool:
    if module in _ALLOWED_IMPORTS:
        return True
    return any(module == pkg or module.startswith(pkg + ".") for pkg in _ALLOWED_IMPORTS)


def _validate_signal_code(signal_code: str) -> None:
    """Validate that signal code only imports allowlisted modules."""
    tree = ast.parse(signal_code)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if not _is_allowed_module(alias.name):
                    raise ValueError(f"Disallowed import: {alias.name}")
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if not _is_allowed_module(module):
                raise ValueError(f"Disallowed import: {module}")


def run_backtest(
    signal_code: str,
    ohlcv_cache_key: str | None = None,
    ohlcv_records: list[dict[str, Any]] | None = None,
    fomc_cache_key: str | None = None,
    fomc_dates: list[str] | None = None,
) -> dict[str, Any]:
    """Run validated signal code in a constrained subprocess and return a compact summary.

    Data can be supplied two ways (prefer cache keys to avoid huge LLM context):
      - ohlcv_cache_key: key returned by fetch_ohlcv / get_cached  (preferred for agents)
      - ohlcv_records:   raw list of OHLCV dicts                   (used by fallback pipeline)

    FOMC dates follow the same pattern via fomc_cache_key or fomc_dates.

    Returns a compact summary with a result_cache_key.  The full equity_curve /
    returns arrays are stored under that key — retrieve with get_cached(result_cache_key).
    The summary scalars (total_return, sharpe, max_drawdown, win_rate, num_trades) are
    included directly so agents can reason about results without a second tool call.
    """
    # Resolve OHLCV records
    records: list[dict[str, Any]] | None = ohlcv_records
    if records is None and ohlcv_cache_key:
        cached = get_cached(ohlcv_cache_key)
        if cached.get("status") == "error":
            return {"status": "error", "stderr": cached["error_message"]}
        records = cached.get("data") or cached.get("records")
    if not records:
        return {"status": "error", "stderr": "No OHLCV data provided. Pass ohlcv_cache_key or ohlcv_records."}

    # Resolve FOMC dates
    dates: list[str] = fomc_dates or []
    if not dates and fomc_cache_key:
        cached = get_cached(fomc_cache_key)
        if cached.get("status") == "success":
            raw = cached.get("data")
            if isinstance(raw, list):
                dates = raw

    try:
        _validate_signal_code(signal_code)
    except Exception as exc:
        return {"status": "error", "stderr": f"Signal validation failed: {exc}"}

    workdir = Path(tempfile.mkdtemp(prefix="backtest_"))
    signal_path = workdir / "signal_impl.py"
    runner_path = workdir / "runner.py"
    input_path = workdir / "input.json"

    try:
        signal_path.write_text(signal_code, encoding="utf-8")
        input_path.write_text(json.dumps({"ohlcv_records": records, "fomc_dates": dates}), encoding="utf-8")

        runner_code = """import json
import math
import pandas as pd
from signal_impl import run

def _sanitize(obj):
    \"\"\"Replace NaN/Inf with 0.0 so json.dumps produces valid JSON.\"\"\"
    if isinstance(obj, float):
        return 0.0 if (math.isnan(obj) or math.isinf(obj)) else obj
    if isinstance(obj, list):
        return [_sanitize(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    return obj

with open("input.json", "r", encoding="utf-8") as f:
    payload = json.load(f)

df = pd.DataFrame(payload["ohlcv_records"])
result = _sanitize(run(df, payload.get("fomc_dates")))
print(json.dumps(result))
"""
        runner_path.write_text(runner_code, encoding="utf-8")

        # Inherit full env so Python can initialise on Windows (needs SYSTEMROOT etc.)
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        # 60s — pandas/numpy import on Windows with AV scanning can take 20-30s alone
        proc = subprocess.run(
            [sys.executable, str(runner_path)],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(workdir),
            env=env,
            check=False,
        )
        if proc.returncode != 0:
            detail = proc.stderr.strip() or proc.stdout.strip() or f"exit code {proc.returncode}"
            return {"status": "error", "stderr": detail}

        full_result: dict[str, Any] = _sanitize(json.loads(proc.stdout.strip()))
        full_result["status"] = "success"

        # Cache the full arrays (equity_curve + returns can be thousands of floats)
        result_cache_key = put(full_result, prefix="backtest")

        # Return only scalar summary + cache_key — agents must not forward raw arrays
        return {
            "status": "success",
            "result_cache_key": result_cache_key,
            "total_return": full_result.get("total_return", 0.0),
            "sharpe": full_result.get("sharpe", 0.0),
            "max_drawdown": full_result.get("max_drawdown", 0.0),
            "win_rate": full_result.get("win_rate", 0.0),
            "num_trades": full_result.get("num_trades", 0),
            # Full result included for direct Python callers (fallback pipeline)
            "_full": full_result,
        }
    except subprocess.TimeoutExpired:
        return {"status": "error", "stderr": "Backtest timed out after 30 seconds"}
    except json.JSONDecodeError as exc:
        return {"status": "error", "stderr": f"Backtest output was not valid JSON: {exc}"}
    except Exception as exc:
        return {"status": "error", "stderr": str(exc)}
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
