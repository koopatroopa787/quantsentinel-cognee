"""Cognee 1.0 semantic memory layer for QuantSentinel.

Uses the four native cognee primitives:
  cognee.remember  — store a completed research run in the graph
  cognee.recall    — retrieve past runs similar to the current hypothesis
  cognee.improve   — self-improve the memory graph every N runs
  cognee.forget    — (available for cleanup; called via /forget endpoint)

The JSONL run_store remains authoritative for metrics/charts.
Cognee is the semantic layer that lets the agent learn across sessions.
"""

from __future__ import annotations

import asyncio
import importlib.util
import logging
import os
import sys
import types
from concurrent.futures import ThreadPoolExecutor
from typing import Any

# mistralai ships as a namespace package (no __init__.py) in recent versions;
# instructor tries `from mistralai import Mistral` which fails without this shim.
def _patch_mistralai() -> None:
    try:
        import mistralai  # noqa: F401 — import to trigger namespace resolution
        if not hasattr(mistralai, "Mistral"):
            from mistralai.client import Mistral  # real class lives here
            mistralai.Mistral = Mistral
    except Exception:
        pass  # non-fatal — cognee will surface its own ImportError if needed

_patch_mistralai()

logger = logging.getLogger(__name__)

_DATASET = "quantsentinel_runs"
_RECALL_TOP_K = int(os.getenv("COGNEE_RECALL_TOP_K", "3"))
_IMPROVE_EVERY_N = int(os.getenv("COGNEE_IMPROVE_EVERY_N", "5"))
_run_count = 0

# Dedicated thread pool: cognee's async calls must run on their own event loop
# (FastAPI's loop is already running when save_run is called from a route handler)
_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="cognee")


def _run_async(coro) -> Any:
    """Submit a coroutine to a fresh event loop in a background thread."""
    future = _pool.submit(asyncio.run, coro)
    try:
        return future.result(timeout=30)
    except Exception as exc:
        logger.warning("cognee async call failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

async def _setup_async() -> None:
    try:
        import cognee
        logger.info("cognee %s ready — dataset: %s", cognee.get_cognee_version(), _DATASET)
    except ImportError:
        logger.warning("cognee not installed — memory features disabled. pip install cognee")
    except Exception as exc:
        logger.warning("cognee setup error (non-fatal): %s", exc)


def setup() -> None:
    """Initialize cognee at server startup (non-blocking)."""
    _run_async(_setup_async())


# ---------------------------------------------------------------------------
# Remember — store a completed run
# ---------------------------------------------------------------------------

async def _remember_async(
    run_id: str,
    hypothesis: str,
    scores: dict[str, Any],
    backtest_result: dict[str, Any] | None,
) -> None:
    global _run_count
    try:
        import cognee

        overall = scores.get("overall", 0.0)
        sharpe = (backtest_result or {}).get("sharpe", "N/A")
        total_return = (backtest_result or {}).get("total_return", "N/A")
        significant = (backtest_result or {}).get("significant_at_5pct", "unknown")
        alpha = (backtest_result or {}).get("alpha", "N/A")

        verdict = (
            "STRONG EDGE" if overall >= 70
            else "WEAK EDGE" if overall >= 50
            else "NO EDGE"
        )

        # Rich text that cognee will graph and embed for future recall
        memo = (
            f"QuantSentinel research run {run_id}.\n"
            f"Hypothesis tested: {hypothesis}\n"
            f"Verdict: {verdict} — overall score {overall:.1f}/100.\n"
            f"Scores: logic={scores.get('logic', 'N/A')}, "
            f"evidence={scores.get('evidence', 'N/A')}, "
            f"risk={scores.get('risk', 'N/A')}.\n"
            f"Backtest: sharpe={sharpe}, total_return={total_return}, "
            f"alpha_vs_SPY={alpha}, statistically_significant={significant}.\n"
        )

        result = await cognee.remember(memo, dataset_name=_DATASET)
        logger.info(
            "cognee.remember: stored run %s (score=%.1f, verdict=%s)",
            run_id[:8], overall, verdict,
        )

        # Self-improve the memory graph every N runs
        _run_count += 1
        if _run_count % _IMPROVE_EVERY_N == 0:
            logger.info("cognee.improve: triggering graph self-improvement (run #%d)", _run_count)
            await cognee.improve(dataset=_DATASET, run_in_background=True)

    except ImportError:
        pass
    except Exception as exc:
        logger.warning("cognee.remember failed (non-fatal): %s", exc)


def remember(
    run_id: str,
    hypothesis: str,
    scores: dict[str, Any],
    backtest_result: dict[str, Any] | None = None,
) -> None:
    """Fire-and-forget: store a completed run in cognee (never blocks the response)."""
    import threading
    t = threading.Thread(
        target=_run_async,
        args=(_remember_async(run_id, hypothesis, scores, backtest_result),),
        daemon=True,
        name=f"cognee-remember-{run_id[:8]}",
    )
    t.start()


# ---------------------------------------------------------------------------
# Recall — retrieve past research similar to the current hypothesis
# ---------------------------------------------------------------------------

async def _recall_async(hypothesis: str) -> list[dict[str, Any]]:
    try:
        import cognee

        query = f"Find past trading strategy research similar to: {hypothesis}"
        results = await cognee.recall(
            query_text=query,
            top_k=_RECALL_TOP_K,
        )
        if not results:
            return []

        items: list[dict[str, Any]] = []
        for r in results[:_RECALL_TOP_K]:
            # cognee.recall returns typed ResponseQAEntry / ResponseGraphEntry objects
            if hasattr(r, "answer"):
                items.append({"summary": r.answer})
            elif hasattr(r, "text"):
                items.append({"summary": r.text})
            elif isinstance(r, dict):
                items.append({"summary": r.get("answer") or r.get("text", str(r))})
            else:
                items.append({"summary": str(r)})
        return items

    except ImportError:
        return []
    except Exception as exc:
        logger.warning("cognee.recall failed (non-fatal): %s", exc)
        return []


def recall(hypothesis: str) -> list[dict[str, Any]]:
    """Return past research runs semantically similar to *hypothesis* (synchronous)."""
    return _run_async(_recall_async(hypothesis)) or []


# ---------------------------------------------------------------------------
# Forget — clean up a dataset (e.g. on /forget API call)
# ---------------------------------------------------------------------------

async def _forget_async(dataset: str | None = None, everything: bool = False) -> dict:
    try:
        import cognee
        result = await cognee.forget(
            dataset=dataset or _DATASET,
            everything=everything,
        )
        logger.info("cognee.forget: cleared dataset=%s everything=%s", dataset, everything)
        return result or {}
    except ImportError:
        return {}
    except Exception as exc:
        logger.warning("cognee.forget failed (non-fatal): %s", exc)
        return {}


def forget(dataset: str | None = None, everything: bool = False) -> dict:
    """Clear cognee memory for a dataset or everything (synchronous)."""
    return _run_async(_forget_async(dataset, everything)) or {}


# ---------------------------------------------------------------------------
# Recall as an ADK-compatible tool function
# ---------------------------------------------------------------------------

def recall_similar_runs(hypothesis: str) -> dict[str, Any]:
    """ADK tool: recall past QuantSentinel research runs semantically similar to this hypothesis.

    Call this as STEP 0, before planning. Use the returned memories to:
    - Avoid re-testing strategies that already scored low (< 50).
    - Build on strategies that scored high (>= 70).
    - Note any statistical findings (Sharpe, p-values, alpha) from past runs.

    Args:
        hypothesis: The trading hypothesis about to be researched.

    Returns:
        dict with 'found' (int), 'memories' (list of past run summaries), and 'note'.
    """
    memories = recall(hypothesis)
    return {
        "found": len(memories),
        "memories": memories,
        "note": (
            "Use these past results to inform your research plan. "
            "Prioritise untested signal types and avoid repeating low-scoring strategies."
            if memories
            else "No similar past research found in cognee memory — this is a fresh hypothesis."
        ),
    }
