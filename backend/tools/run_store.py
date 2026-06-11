"""Lightweight file-backed store for completed research runs.

Persists each run as a JSON-lines entry so the improvement chart and history
sidebar show real data even when Phoenix is offline or empty.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_STORE_PATH = Path(os.getenv("RUN_STORE_PATH", Path(__file__).parent.parent / "run_store.jsonl"))


def _is_valid_record(r: dict[str, Any]) -> bool:
    """Filter out stale Phoenix-format or corrupt records."""
    return (
        isinstance(r.get("hypothesis"), str)
        and r["hypothesis"] not in ("unknown", "")
        and isinstance(r.get("scores"), dict)
        and isinstance(r["scores"].get("overall"), (int, float))
    )


def _load_all() -> list[dict[str, Any]]:
    if not _STORE_PATH.exists():
        return []
    runs: list[dict[str, Any]] = []
    try:
        for line in _STORE_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    r = json.loads(line)
                    if _is_valid_record(r):
                        runs.append(r)
                except json.JSONDecodeError:
                    pass
    except Exception:
        pass
    return runs


_OPTIMIZE_EVERY_N = int(os.getenv("OPTIMIZE_EVERY_N_RUNS", "5"))


def save_run(
    run_id: str,
    hypothesis: str,
    scores: dict[str, float],
    backtest_result: dict[str, Any] | None = None,
) -> None:
    """Append a completed run record and auto-trigger the DSPy optimizer every N runs."""
    record = {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hypothesis": hypothesis,
        "scores": scores,
        "metrics": {
            k: backtest_result.get(k)
            for k in ("total_return", "sharpe", "max_drawdown", "win_rate", "num_trades")
            if backtest_result and k in backtest_result
        },
    }
    try:
        _STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _STORE_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
        count = len(_load_all())
        logger.info("Run saved to store: %s (overall=%.3f) — store now has %d runs", run_id[:8], scores.get("overall", 0), count)

        # Auto-trigger optimizer every N runs in a background thread
        if count % _OPTIMIZE_EVERY_N == 0:
            _trigger_optimizer_background()
    except Exception as exc:
        logger.warning("Failed to save run to store: %s", exc)


def _trigger_optimizer_background() -> None:
    """Spawn the nightly optimizer in a daemon thread so it doesn't block the response.

    Uses a lock file to prevent duplicate runs when uvicorn --reload restarts the
    worker process mid-optimization (daemon threads are killed on process exit).
    """
    import threading  # noqa: PLC0415
    import tempfile  # noqa: PLC0415
    from pathlib import Path  # noqa: PLC0415

    lock_path = Path(tempfile.gettempdir()) / "quantsentinel_optimizer.lock"

    def _run() -> None:
        # Prevent concurrent runs (e.g. two requests hitting count==N simultaneously)
        if lock_path.exists():
            logger.info("Optimizer lock file exists — skipping duplicate trigger.")
            return
        try:
            lock_path.touch()
            logger.info("Auto-triggering DSPy optimizer (background)…")
            print("[OPTIMIZER] Starting background DSPy optimization run…", flush=True)
            from optimizer.nightly_optimizer import main as _opt_main  # noqa: PLC0415
            exit_code = _opt_main()
            logger.info("Optimizer finished with exit_code=%s", exit_code)
            print(f"[OPTIMIZER] Finished — exit_code={exit_code}", flush=True)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Background optimizer failed: %s", exc)
            print(f"[OPTIMIZER] FAILED: {exc}", flush=True)
        finally:
            lock_path.unlink(missing_ok=True)

    t = threading.Thread(target=_run, daemon=True, name="nightly-optimizer")
    t.start()


def get_store_stats() -> dict[str, Any]:
    """Return summary stats about the store (used in startup log)."""
    runs = _load_all()
    return {
        "path": str(_STORE_PATH),
        "count": len(runs),
        "latest": runs[-1]["timestamp"] if runs else None,
    }


def get_history(limit: int = 10) -> list[dict[str, Any]]:
    """Return the most recent runs for the history sidebar."""
    runs = _load_all()
    runs.sort(key=lambda r: r.get("timestamp", ""), reverse=True)
    return [
        {
            "hypothesis": r["hypothesis"],
            "score": r["scores"].get("overall", 0.0),
            "timestamp": r["timestamp"],
        }
        for r in runs[:limit]
    ]


def get_improvement_points(limit: int = 50) -> list[dict[str, Any]]:
    """Return chronological eval score series for the improvement chart."""
    runs = _load_all()
    runs.sort(key=lambda r: r.get("timestamp", ""))
    return [
        {"timestamp": r["timestamp"], "overall": r["scores"].get("overall", 0.0)}
        for r in runs[-limit:]
    ]
