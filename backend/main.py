"""FastAPI server for QuantSentinel — ADK Runner wired into SSE /run endpoint."""

from tracing import setup_tracing  # must be first import

setup_tracing()

import asyncio
import json
import logging
import os
import uuid
from typing import Any, AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from pydantic import BaseModel, Field

from agents.orchestrator import quantsentinel_orchestrator
from config import settings
from tools.cognee_memory import forget as cognee_forget, recall as cognee_recall, setup as cognee_setup
from evals.evaluator import run_eval
from tools.backtest_runner import run_backtest
from tools.chart_tools import generate_equity_curve_chart
from tools.market_data import fetch_fomc_dates, fetch_ohlcv
from tools.phoenix_query_tool import extract_score_series, query_phoenix_traces
from tools.run_store import get_history, get_improvement_points, get_store_stats, save_run
from tools.signal_factory import describe_signal, generate_signal_code
from tools.suggestion_engine import generate_suggestion
from tools.stats_tools import bootstrap_ci, compute_sharpe, compute_t_test

logger = logging.getLogger(__name__)

ADK_TIMEOUT_SECS = int(os.getenv("ADK_TIMEOUT_SECS", "90"))   # per-attempt timeout; fallback fires after this
ADK_MAX_RETRIES  = int(os.getenv("ADK_MAX_RETRIES",  "2"))    # only retries on 429; timeouts go straight to fallback

# ---------------------------------------------------------------------------
# Default signal used in the fallback pipeline when ADK fails
# ---------------------------------------------------------------------------
_DEFAULT_SIGNAL_CODE = """
import numpy as np
import pandas as pd


def run(df: pd.DataFrame, fomc_dates):
    df = df.copy()
    if "close" not in df.columns:
        raise ValueError("close column is required")
    df["ret"] = df["close"].pct_change().fillna(0.0)
    # Simple 5-day rolling-mean mean-reversion signal
    df["signal"] = (df["ret"].rolling(5).mean().fillna(0.0) < 0).astype(int)
    strat_ret = df["signal"].shift(1).fillna(0) * df["ret"]
    equity_curve = (1 + strat_ret).cumprod().tolist()
    trades = df.index[df["signal"].diff().fillna(0) != 0].tolist()
    ec = np.array(equity_curve)
    running_max = np.maximum.accumulate(ec)
    max_dd = float(((running_max - ec) / (running_max + 1e-9)).max()) if len(ec) else 0.0
    # Win rate = profitable days / days the position was actually held
    held = df["signal"].shift(1).fillna(0) > 0
    active_days = int(held.sum())
    wins = int((strat_ret[held] > 0).sum())
    win_rate = float(wins / max(active_days, 1))
    n_trades = int(max(len(trades) // 2, 1))  # each trade = entry + exit = 2 signal changes
    return {
        "equity_curve": equity_curve,
        "returns": strat_ret.tolist(),
        "trades": [str(t) for t in trades],
        "total_return": float(ec[-1] - 1.0) if len(ec) else 0.0,
        "sharpe": float(
            strat_ret.mean() / (strat_ret.std() + 1e-9) * (252 ** 0.5)
        ),
        "max_drawdown": max_dd,
        "win_rate": win_rate,
        "num_trades": n_trades,
    }
"""

# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class RunRequest(BaseModel):
    """Request payload for a hypothesis research run."""

    hypothesis: str = Field(min_length=5)
    session_id: str = Field(min_length=1)


# ---------------------------------------------------------------------------
# SSE helpers
# ---------------------------------------------------------------------------


def _sse(event: str, payload: dict[str, Any]) -> str:
    """Serialise one server-sent event frame."""
    return f"event: {event}\ndata: {json.dumps(payload)}\n\n"


def _extract_memo_from_agent_output(text: str) -> str:
    """Return memo text or the raw text if the 8-section header is absent."""
    if "1. HYPOTHESIS" in text or "HYPOTHESIS" in text:
        return text.strip()
    return text.strip()


def _extract_chart_b64(text: str) -> str | None:
    """Heuristically pull a base64 PNG token from agent output text."""
    import re

    # Agents may output chart as: chart_base64: <value> or just a long b64 block
    match = re.search(r"chart_base64[\"']?\s*[:=]\s*[\"']?([A-Za-z0-9+/=\n]{200,})", text)
    if match:
        return match.group(1).replace("\n", "").strip()
    return None


# ---------------------------------------------------------------------------
# ADK-powered streaming pipeline
# ---------------------------------------------------------------------------


async def _run_adk_stream(payload: RunRequest) -> AsyncGenerator[str, None]:
    """Drive the ADK orchestrator and emit SSE events from agent steps."""
    run_id = str(uuid.uuid4())
    app_name = "quantsentinel"
    user_id = payload.session_id

    session_service = InMemorySessionService()
    runner = Runner(
        agent=quantsentinel_orchestrator,
        app_name=app_name,
        session_service=session_service,
    )

    session = await session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=run_id,
    )

    # ── Cognee memory recall ────────────────────────────────────────────────
    memories: list[dict] = []
    try:
        memories = await asyncio.get_event_loop().run_in_executor(
            None, cognee_recall, payload.hypothesis
        )
    except Exception as _mem_exc:
        logger.debug("cognee recall skipped: %s", _mem_exc)

    yield _sse("memory", {
        "found": len(memories),
        "memories": memories,
        "message": (
            f"Recalled {len(memories)} similar past research run(s) from cognee memory."
            if memories
            else "No similar past research in cognee memory — starting fresh."
        ),
    })
    # ── End cognee recall ───────────────────────────────────────────────────

    # Enrich the hypothesis with recalled context so the orchestrator starts informed
    memory_context = ""
    if memories:
        summaries = "\n".join(f"- {m.get('summary', str(m))}" for m in memories)
        memory_context = (
            f"\n\n[COGNEE MEMORY CONTEXT — {len(memories)} similar past run(s)]\n"
            f"{summaries}\n"
            f"Use this context to improve your research plan and avoid repeating failed approaches.\n"
        )

    user_message = Content(
        role="user",
        parts=[Part(text=payload.hypothesis + memory_context)],
    )

    # Emit plan event immediately so the UI feels responsive
    yield _sse("plan", {
        "hypothesis": payload.hypothesis,
        "status": "decomposing",
        "message": "Orchestrator is analysing the hypothesis…",
    })

    # Track what we've seen so we can emit step events for each agent
    seen_agents: set[str] = set()
    full_output_text = ""
    chart_b64: str | None = None
    memo_text = ""
    scores: dict[str, float] = {}

    import sys
    import time
    if sys.version_info >= (3, 11):
        from asyncio import timeout as _async_timeout
    else:
        from async_timeout import timeout as _async_timeout

    # Heartbeat queue: background task pushes progress pings here so we can
    # interleave them with real ADK events without blocking the generator.
    _hb_queue: asyncio.Queue[str] = asyncio.Queue()
    _active_agent: list[str] = ["orchestrator"]  # mutable cell
    _agent_start: list[float] = [time.monotonic()]

    _DATA_AGENT_MESSAGES = [
        "Connecting to Yahoo Finance…",
        "Downloading OHLCV bars…",
        "Waiting for market data response…",
        "Processing price data…",
        "Validating data frame…",
        "Building records for backtester…",
    ]

    async def _heartbeat_task() -> None:
        """Push periodic progress pings into the queue while agents are working."""
        tick = 0
        while True:
            await asyncio.sleep(5)
            elapsed = int(time.monotonic() - _agent_start[0])
            agent = _active_agent[0]
            if agent in ("data_agent",):
                msg = _DATA_AGENT_MESSAGES[tick % len(_DATA_AGENT_MESSAGES)]
            else:
                msg = f"Still working… ({elapsed}s)"
            await _hb_queue.put(_sse("heartbeat", {
                "agent": agent,
                "elapsed": elapsed,
                "message": msg,
            }))
            tick += 1

    hb_task = asyncio.create_task(_heartbeat_task())

    try:
        for attempt in range(ADK_MAX_RETRIES):
            try:
                async with _async_timeout(ADK_TIMEOUT_SECS):
                    async for event in runner.run_async(
                        user_id=user_id,
                        session_id=run_id,
                        new_message=user_message,
                    ):
                        # Drain any heartbeat pings accumulated while ADK was blocked
                        while not _hb_queue.empty():
                            yield await _hb_queue.get()

                        # ADK emits events with .author (agent name) and .content
                        author = getattr(event, "author", None) or "orchestrator"
                        is_final = getattr(event, "is_final_response", lambda: False)
                        if callable(is_final):
                            is_final = is_final()

                        # Emit per-agent step events (de-duplicate running → done)
                        if author not in seen_agents:
                            seen_agents.add(author)
                            yield _sse("step", {
                                "agent": author,
                                "status": "running",
                                "message": f"{author} is working…",
                            })

                        # Accumulate text content
                        content = getattr(event, "content", None)
                        if content is not None:
                            parts = getattr(content, "parts", []) or []
                            for part in parts:
                                part_text = getattr(part, "text", None)
                                if part_text:
                                    full_output_text += part_text
                                    # Emit the orchestrator's thought process
                                    yield _sse("agent_output", {"agent": author, "text": part_text})

                                    # Heuristic: extract chart if agent returns base64 block
                                    if chart_b64 is None:
                                        chart_b64 = _extract_chart_b64(part_text)
                                
                                if getattr(part, "function_call", None):
                                    tool_name = part.function_call.name
                                    args_dict = dict(part.function_call.args) if hasattr(part.function_call, "args") else {}
                                    # Strip huge data arrays from display (cache keys are sufficient)
                                    display_args = {
                                        k: v for k, v in args_dict.items()
                                        if k not in ("ohlcv_records", "records") and not (isinstance(v, list) and len(v) > 10)
                                    }
                                    if tool_name.endswith("_agent"):
                                        _active_agent[0] = tool_name
                                        _agent_start[0] = time.monotonic()
                                        yield _sse("step", {"agent": tool_name, "status": "running", "message": f"Delegated to {tool_name}…"})
                                        yield _sse("agent_output", {"agent": tool_name, "text": f"[Assigned Task]\n{json.dumps(display_args, indent=2)}\n\n[Model is processing — output will appear below as it streams]\n"})
                                    else:
                                        yield _sse("agent_output", {"agent": author, "text": f"\n[→ Tool call: {tool_name}]\n{json.dumps(display_args, indent=2)}\n"})

                                if getattr(part, "function_response", None):
                                    tool_name = part.function_response.name
                                    resp_dict = dict(part.function_response.response) if hasattr(part.function_response, "response") else {}
                                    # Strip huge arrays from display
                                    display_resp = {
                                        k: v for k, v in resp_dict.items()
                                        if k not in ("records", "equity_curve", "returns", "fomc_dates")
                                        and not (isinstance(v, list) and len(v) > 10)
                                    }
                                    if tool_name.endswith("_agent"):
                                        _active_agent[0] = author
                                        _agent_start[0] = time.monotonic()
                                        yield _sse("agent_output", {"agent": tool_name, "text": f"\n[← Result]\n{json.dumps(display_resp, indent=2)}\n"})
                                        yield _sse("step", {"agent": tool_name, "status": "done", "message": f"{tool_name} finished."})
                                    else:
                                        display_tool_resp = {
                                            k: v for k, v in resp_dict.items()
                                            if k not in ("records", "equity_curve", "returns", "fomc_dates")
                                            and not (isinstance(v, list) and len(v) > 10)
                                        }
                                        yield _sse("agent_output", {"agent": author, "text": f"\n[← {tool_name}]\n{json.dumps(display_tool_resp, indent=2)}\n"})

                        # On final response, emit done step
                        if is_final:
                            yield _sse("step", {
                                "agent": author,
                                "status": "done",
                                "message": f"{author} finished.",
                            })
                
                # If we made it through without error, break the retry loop
                break

            except Exception as e:
                err_str = str(e)
                is_rate_limit = "429" in err_str or "ResourceExhausted" in type(e).__name__
                is_timeout = isinstance(e, (asyncio.TimeoutError, TimeoutError))

                if is_timeout:
                    logger.warning("ADK run timed out after %ds on attempt %d — going straight to fallback", ADK_TIMEOUT_SECS, attempt + 1)
                    yield _sse("step", {
                        "agent": "system",
                        "status": "warning",
                        "message": f"ADK timed out after {ADK_TIMEOUT_SECS}s — running direct pipeline…",
                    })
                    raise  # no retry on timeout — fall through immediately to fallback
                elif is_rate_limit:
                    if attempt < ADK_MAX_RETRIES - 1:
                        wait = 30 * (attempt + 1)
                        logger.warning(f"429 hit — waiting {wait}s before retry {attempt + 2}/{max_retries}")
                        yield _sse("step", {
                            "agent": "system",
                            "status": "running",
                            "message": f"Rate limit hit. Retrying in {wait}s...",
                        })
                        await asyncio.sleep(wait)
                    else:
                        raise
                else:
                    raise

        # ----------------------------------------------------------------
        # Post-processing: extract memo, chart, scores
        # ----------------------------------------------------------------
        memo_text = _extract_memo_from_agent_output(full_output_text)

        # If the ADK run produced a chart base64, emit it
        if chart_b64:
            yield _sse("chart", {"image_base64": chart_b64})

        # If no chart was found in ADK output, generate one via fallback
        if not chart_b64:
            chart_b64 = await _generate_fallback_chart(payload.hypothesis)
            if chart_b64:
                yield _sse("chart", {"image_base64": chart_b64})

        # Calculate heuristic tokens since ADK does not surface them directly easily
        # ~1 token per 4 chars of output, base input prompt ~1500 tokens
        input_tokens = 1500 + (len(payload.hypothesis) // 4)
        output_tokens = len(full_output_text) // 4
        yield _sse("tokens", {"input": input_tokens, "output": output_tokens})

        yield _sse("memo", {"text": memo_text})

        # Run eval on the memo
        scores = run_eval(memo=memo_text, backtest_result={}, stat_summary={})
        yield _sse("scores", scores)

        trace_url = (
            f"{settings.PHOENIX_BASE_URL}/projects"
            f"/{settings.PHOENIX_PROJECT_NAME}/traces/{run_id}"
        )
        yield _sse("done", {"run_id": run_id, "phoenix_trace_url": trace_url})

    except (asyncio.TimeoutError, TimeoutError):
        # Do NOT yield an error SSE here — we already yielded the warning inside the inner
        # except, and we need this exception to propagate so _run_stream can trigger fallback.
        logger.warning("ADK stream timed out — propagating to trigger fallback pipeline.")
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("ADK run failed: %s", exc)
        yield _sse("error", {"message": str(exc) or repr(exc)})
    finally:
        hb_task.cancel()  # Always stop the heartbeat ticker to avoid resource leak


# ---------------------------------------------------------------------------
# Fallback pipeline — direct Python tool calls (no ADK Runner)
# ---------------------------------------------------------------------------


def _infer_signal_description(hypothesis: str) -> str:
    """Human-readable signal description for the memo's Methodology section.

    Delegates to signal_factory.describe_signal(), which is derived from the
    exact same detection and parameter-extraction logic used by
    generate_signal_code() — so this description can never disagree with the
    code that actually ran (previously this used separate, looser keyword
    checks and a hardcoded "14-day RSI", which could describe a different
    signal than the one whose results were reported).
    """
    return describe_signal(hypothesis)


def _build_conclusion(
    hypothesis: str,
    ticker: str,
    backtest_result: dict[str, Any],
    stats_summary: dict[str, Any],
) -> str:
    """Generate a specific, data-grounded conclusion for the hypothesis."""
    t = stats_summary["t_test"]
    b = stats_summary["bootstrap"]
    sig = t["significant_at_5pct"]
    sharpe = backtest_result.get("sharpe", 0.0)
    total_ret = backtest_result.get("total_return", 0.0)
    p_val = t["p_value"]
    ci_includes_zero = b["lower"] < 0 < b["upper"]

    # Confidence tier
    if sig and sharpe > 1.0:
        confidence = "high"
    elif sig or (sharpe > 0.5 and not ci_includes_zero):
        confidence = "medium"
    else:
        confidence = "low"

    verdict = (
        f"The backtest on {ticker} produced a total return of "
        f"{total_ret:.2%} with a Sharpe ratio of {sharpe:.4f}. "
    )
    if sig:
        verdict += (
            f"The Welch t-test (p={p_val:.4f}) rejects the null hypothesis at the 5% "
            f"significance level, providing statistical support for the hypothesis. "
        )
    else:
        verdict += (
            f"The Welch t-test (p={p_val:.4f}) fails to reject the null hypothesis — "
            f"the strategy returns are not statistically distinguishable from the benchmark "
            f"at the 5% significance level. "
        )
    if ci_includes_zero:
        verdict += (
            f"The 95% bootstrap CI [{b['lower']:.6f}, {b['upper']:.6f}] spans zero, "
            f"further undermining confidence in a persistent edge. "
        )
    else:
        verdict += (
            f"The 95% bootstrap CI [{b['lower']:.6f}, {b['upper']:.6f}] does not span zero, "
            f"suggesting a potentially consistent directional edge. "
        )
    verdict += f"\nOverall confidence level: **{confidence}**."
    return verdict


def _build_memo(
    hypothesis: str,
    ticker: str,
    start_date: str,
    end_date: str,
    backtest_result: dict[str, Any],
    stats_summary: dict[str, Any],
) -> str:
    """Build a structured, hypothesis-aware research memo from computed artefacts."""
    t = stats_summary["t_test"]
    b = stats_summary["bootstrap"]
    signal_desc = _infer_signal_description(hypothesis)
    conclusion = _build_conclusion(hypothesis, ticker, backtest_result, stats_summary)

    # Hypothesis-specific caveats
    h = hypothesis.lower()
    extra_caveat = ""
    if "fomc" in h or "fed" in h:
        extra_caveat = (
            "- FOMC-event risk: the fallback signal does not model FOMC dates directly; "
            "results do not constitute a true FOMC event study.\n"
        )
    elif "vix" in h or "volatility" in h:
        extra_caveat = (
            "- Volatility measurement: VIX is not traded directly; "
            "realised volatility proxies introduce tracking error.\n"
        )
    elif "golden cross" in h or "sma" in h:
        extra_caveat = (
            "- Look-ahead bias risk: SMA parameters (windows) were chosen based on "
            "the hypothesis statement, not discovered in-sample.\n"
        )

    return (
        f"1. HYPOTHESIS\n{hypothesis}\n\n"
        f"2. DATA SOURCES\nTicker: {ticker}\n"
        f"Date range: {start_date} to {end_date}\nProvider: yfinance (daily OHLCV) + FRED (FOMC dates)\n\n"
        f"3. METHODOLOGY\n{signal_desc}\n\n"
        f"4. RESULTS\n"
        f"total_return: {backtest_result.get('total_return', 0.0):.4f} "
        f"({backtest_result.get('total_return', 0.0):.2%})\n"
        f"sharpe: {backtest_result.get('sharpe', 0.0):.4f}\n"
        f"max_drawdown: {backtest_result.get('max_drawdown', 0.0):.4f} "
        f"({backtest_result.get('max_drawdown', 0.0):.2%} of peak)\n"
        f"win_rate: {backtest_result.get('win_rate', 0.0):.4f} "
        f"({backtest_result.get('win_rate', 0.0):.2%})\n"
        f"num_trades: {backtest_result.get('num_trades', 0)}\n\n"
        f"5. STATISTICAL ANALYSIS\n"
        f"t_statistic: {t['t_statistic']:.4f}\n"
        f"p_value: {t['p_value']:.4f}\n"
        f"significant_at_5pct: {t['significant_at_5pct']}\n"
        f"bootstrap_ci_95pct: [{b['lower']:.6f}, {b['upper']:.6f}]\n"
        f"bootstrap_mean: {b['mean']:.6f}\n\n"
        f"6. RISK CAVEATS\n"
        f"- Overfitting: the signal was not tested on out-of-sample data.\n"
        f"- Transaction costs and slippage are excluded from the simulation.\n"
        f"- Regime change: historical patterns may not persist in future markets.\n"
        f"- Data snooping bias: single signal tested without multiple-testing correction.\n"
        f"- Survivorship bias: index constituents may have changed over the backtest period.\n"
        f"{extra_caveat}\n"
        f"7. CONCLUSION\n{conclusion}\n\n"
        f"8. DISCLAIMER\n"
        f"For research purposes only. Not investment advice."
    )


async def _generate_fallback_chart(hypothesis: str) -> str | None:
    """Generate a simple chart using the fallback pipeline on SPY data."""
    try:
        from tools.cache import get as _cache_get  # noqa: PLC0415
        market = fetch_ohlcv("SPY", "2020-01-01", "2024-12-31")
        if market["status"] != "success":
            return None
        records = _cache_get(market["cache_key"]) or []
        if not records:
            return None
        backtest = run_backtest(signal_code=_DEFAULT_SIGNAL_CODE, ohlcv_records=records)
        if backtest["status"] != "success":
            return None
        full = backtest.get("_full", backtest)
        dates = [str(r["date"]) for r in records[: len(full["equity_curve"])]]
        return generate_equity_curve_chart(
            equity_curve=[float(v) for v in full["equity_curve"]],
            dates=dates,
            title="SPY Strategy Equity Curve",
        )
    except Exception:  # noqa: BLE001
        return None


async def _run_fallback_stream(payload: RunRequest) -> AsyncGenerator[str, None]:
    """
    Fallback streaming pipeline — calls tools directly when ADK is unavailable.
    Preserves the same SSE event contract as the ADK pipeline.
    """
    import re
    run_id = str(uuid.uuid4())

    # ── Cognee memory recall ────────────────────────────────────────────────
    # Query semantic memory for past research similar to this hypothesis.
    # The recalled context is injected into the suggestion engine so the agent
    # improves on what it already knows rather than repeating past mistakes.
    memories: list[dict] = []
    try:
        memories = await asyncio.get_event_loop().run_in_executor(
            None, cognee_recall, payload.hypothesis
        )
    except Exception as _mem_exc:
        logger.debug("cognee recall skipped: %s", _mem_exc)

    yield _sse("memory", {
        "found": len(memories),
        "memories": memories,
        "message": (
            f"Recalled {len(memories)} similar past research run(s) from cognee memory."
            if memories
            else "No similar past research in cognee memory — starting fresh."
        ),
    })
    # ── End cognee recall ───────────────────────────────────────────────────

    # Best-effort extract ticker and dates from the hypothesis text
    hypothesis_upper = payload.hypothesis.upper()
    # Match common 1-5 char tickers (prioritise known ones if present)
    # Note: deliberately avoid single-letter and ambiguous tickers (e.g. "T", "F",
    # "C", "V", "MA") that collide with common phrases like "t-test", "F-test" or
    # "moving average (MA)" and would otherwise hijack the ticker match.
    known = [
        "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "TSLA", "NVDA", "META", "NFLX",
        "AMD", "INTC", "CRM", "ORCL", "ADBE", "IBM", "CSCO", "QCOM", "AVGO",
        "JPM", "BAC", "WFC", "GS", "MS", "AXP",
        "JNJ", "PFE", "UNH", "MRK", "ABBV", "LLY",
        "XOM", "CVX", "COP", "BA", "CAT", "GE", "GM", "DIS", "KO", "PEP",
        "WMT", "HD", "NKE", "MCD", "PG", "VZ",
        "QQQ", "SPY", "DIA", "IWM", "VTI", "EFA", "EEM",
        "GLD", "SLV", "USO", "TLT", "HYG", "ARKK",
        "VIX", "UVXY", "BTC", "ETH",
    ]
    ticker = next((t for t in known if re.search(rf"\b{t}\b", hypothesis_upper)), "SPY")

    # Extract 4-digit years e.g. "2012" to "2024"
    years = re.findall(r"\b(20[0-2][0-9])\b", payload.hypothesis)
    start_date = f"{min(years)}-01-01" if len(years) >= 2 else "2015-01-01"
    end_date   = f"{max(years)}-12-31" if len(years) >= 2 else "2024-12-31"

    plan = {
        "required_tickers": [ticker],
        "start_date": start_date,
        "end_date": end_date,
        "signal_logic": "5-day mean-reversion proxy on negative rolling returns",
        "statistical_tests": ["welch_t_test", "bootstrap_ci", "sharpe"],
        "needs_fomc_dates": False,
    }
    yield _sse("plan", plan)

    yield _sse("step", {"agent": "data_agent", "status": "running", "message": "Fetching OHLCV data"})
    market = fetch_ohlcv(ticker=ticker, start_date=start_date, end_date=end_date)
    if market["status"] != "success":
        yield _sse("error", {"message": market.get("error_message", "Failed to fetch OHLCV data")})
        return
    # Records are stored in cache — fetch_ohlcv no longer embeds them inline
    from tools.cache import get as _cache_get  # noqa: PLC0415
    ohlcv_records: list[dict] = _cache_get(market["cache_key"]) or []
    if not ohlcv_records:
        yield _sse("error", {"message": "OHLCV cache miss after successful fetch — unexpected"})
        return
    fetch_fomc_dates(2015, 2024)  # pre-warm FOMC cache; never raises
    yield _sse("step", {"agent": "data_agent", "status": "done", "message": f"Market data fetched ({market['record_count']} bars)"})

    yield _sse("step", {"agent": "backtester_agent", "status": "running", "message": "Running sandboxed backtest"})
    from tools.signal_factory import _detect as _detect_sig_type  # noqa: PLC0415
    signal_code = generate_signal_code(payload.hypothesis)
    sig_type = _detect_sig_type(payload.hypothesis)
    logger.info("Fallback signal type: %s", sig_type)
    yield _sse("step", {"agent": "backtester_agent", "status": "running",
                        "message": f"Running {sig_type.replace('_', ' ')} signal"})
    backtest_result = run_backtest(signal_code=signal_code, ohlcv_records=ohlcv_records)
    if backtest_result["status"] != "success":
        yield _sse("error", {"message": backtest_result.get("stderr", "Backtest failed")})
        return
    yield _sse("step", {"agent": "backtester_agent", "status": "done", "message": "Backtest completed"})

    # Use the full result arrays (direct Python call — no LLM round-trip needed)
    full_backtest = backtest_result.get("_full", backtest_result)
    returns = [float(x) for x in full_backtest.get("returns", [])]
    closes = [float(rec["close"]) for rec in ohlcv_records]
    benchmark_returns = [
        (closes[i] - closes[i - 1]) / closes[i - 1] if closes[i - 1] else 0.0
        for i in range(1, len(closes))
    ]

    yield _sse("step", {"agent": "statistician_agent", "status": "running", "message": "Computing statistics"})
    t_test = compute_t_test(returns, benchmark_returns)
    boot = bootstrap_ci(returns)
    sharpe = compute_sharpe(returns)
    dates = [str(rec["date"]) for rec in ohlcv_records[: len(full_backtest.get("equity_curve", []))]]
    chart = generate_equity_curve_chart(
        equity_curve=[float(v) for v in full_backtest.get("equity_curve", [])],
        dates=dates,
        title=f"{ticker} Strategy Equity Curve",
    )
    stats_summary: dict[str, Any] = {"t_test": t_test, "bootstrap": boot, "sharpe": sharpe}
    yield _sse("step", {"agent": "statistician_agent", "status": "done", "message": "Statistics computed"})
    yield _sse("chart", {"image_base64": chart})

    # Build time-series for interactive charts (sample to ≤500 points for browser perf)
    equity_curve = [float(v) for v in full_backtest.get("equity_curve", [])]
    bench_curve: list[float] = []
    val = 1.0
    for r in benchmark_returns:
        val *= (1 + r)
        bench_curve.append(val)
    benchmark_total_return = float(bench_curve[-1] - 1.0) if bench_curve else 0.0
    strategy_total_return = float(full_backtest.get("total_return", 0.0))
    alpha = strategy_total_return - benchmark_total_return
    # Align lengths
    n = min(len(dates), len(equity_curve), len(bench_curve))
    step_size = max(1, n // 500)
    series = []
    running_max = 0.0
    for idx in range(0, n, step_size):
        eq = equity_curve[idx]
        running_max = max(running_max, eq)
        dd = (running_max - eq) / running_max if running_max > 0 else 0.0
        series.append({
            "date": dates[idx],
            "equity": round(eq, 4),
            "benchmark": round(bench_curve[idx], 4),
            "drawdown": round(-dd, 4),  # negative so it plots below zero
        })
    yield _sse("metrics", {
        "ticker": ticker,
        "start_date": start_date,
        "end_date": end_date,
        "total_return": round(strategy_total_return, 4),
        "benchmark_total_return": round(benchmark_total_return, 4),
        "alpha": round(alpha, 4),
        "sharpe": round(full_backtest.get("sharpe", 0.0), 4),
        "max_drawdown": round(full_backtest.get("max_drawdown", 0.0), 4),
        "win_rate": round(full_backtest.get("win_rate", 0.0), 4),
        "num_trades": full_backtest.get("num_trades", 0),
        "t_statistic": round(t_test["t_statistic"], 4),
        "p_value": round(t_test["p_value"], 4),
        "significant_at_5pct": t_test["significant_at_5pct"],
        "bootstrap_lower": round(boot["lower"], 6),
        "bootstrap_upper": round(boot["upper"], 6),
        "bootstrap_mean": round(boot["mean"], 6),
        "series": series,
    })

    # Augment backtest result with alpha/benchmark so evaluator + suggestion engine can use it
    eval_backtest = {**full_backtest, "alpha": alpha, "benchmark_total_return": benchmark_total_return}

    # Generate improvement suggestion.
    # Prepend the CURRENT run to history — save_run hasn't been called yet so the store
    # doesn't know this hypothesis was just tested. Without this, the engine re-suggests it.
    run_history = [{"hypothesis": payload.hypothesis, "score": 0}] + get_history(limit=50)
    suggestion = generate_suggestion(
        hypothesis=payload.hypothesis,
        backtest_result=eval_backtest,
        benchmark_total_return=benchmark_total_return,
        stat_summary=stats_summary,
        run_history=run_history,
    )
    yield _sse("suggestion", suggestion)

    yield _sse("step", {"agent": "critic_agent", "status": "running", "message": "Writing research memo"})
    memo = _build_memo(
        hypothesis=payload.hypothesis,
        ticker=ticker,
        start_date=start_date,
        end_date=end_date,
        backtest_result=full_backtest,
        stats_summary=stats_summary,
    )
    scores = run_eval(memo=memo, backtest_result=eval_backtest, stat_summary=stats_summary)
    save_run(run_id=run_id, hypothesis=payload.hypothesis, scores=scores, backtest_result=eval_backtest)

    input_tokens = 1500 + (len(payload.hypothesis) // 4)
    output_tokens = len(memo) // 4
    yield _sse("tokens", {"input": input_tokens, "output": output_tokens})

    yield _sse("memo", {"text": memo})
    yield _sse("scores", scores)
    yield _sse("step", {"agent": "critic_agent", "status": "done", "message": "Memo finalised"})

    trace_url = (
        f"{settings.PHOENIX_BASE_URL}/projects"
        f"/{settings.PHOENIX_PROJECT_NAME}/traces/{run_id}"
    )
    yield _sse("done", {"run_id": run_id, "phoenix_trace_url": trace_url})


# ---------------------------------------------------------------------------
# Unified stream dispatcher: ADK first, fallback on error
# ---------------------------------------------------------------------------


async def _run_stream(payload: RunRequest) -> AsyncGenerator[str, None]:
    """Attempt ADK pipeline; fall back to direct tool pipeline on failure."""
    use_adk = True
    try:
        _ = quantsentinel_orchestrator
    except Exception:  # noqa: BLE001
        use_adk = False

    adk_succeeded = False
    if use_adk:
        try:
            async for chunk in _run_adk_stream(payload):
                yield chunk
            adk_succeeded = True
        except (asyncio.TimeoutError, TimeoutError):
            # Timeout already emitted a warning SSE from inside _run_adk_stream;
            # just fall through to the fallback pipeline below.
            logger.warning("ADK pipeline timed out — running fallback pipeline.")
            yield _sse("step", {
                "agent": "system",
                "status": "running",
                "message": "Starting direct pipeline (no LLM overhead)…",
            })
        except Exception as exc:  # noqa: BLE001
            logger.warning("ADK stream failed (%s), falling back to direct pipeline.", exc)
            yield _sse("step", {
                "agent": "system",
                "status": "warning",
                "message": f"ADK runner failed: {exc!s}. Switching to direct pipeline.",
            })

    if not use_adk or not adk_succeeded:
        async for chunk in _run_fallback_stream(payload):
            yield chunk


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="QuantSentinel API",
    description=(
        "Self-improving quant research agent powered by Gemini and Arize Phoenix."
    ),
    version="1.0.0",
)

@app.on_event("startup")
async def _log_startup() -> None:
    orch_model = getattr(quantsentinel_orchestrator, "model", "unknown")
    stats = get_store_stats()
    logger.info("QuantSentinel started — orchestrator model: %s", orch_model)
    logger.info(
        "Run store: %s runs at %s",
        stats["count"], stats["path"],
    )
    logger.info(
        "ADK: timeout=%ss retries=%s (timeout→immediate fallback, 429→retry) | Fallback: always-on",
        ADK_TIMEOUT_SECS, ADK_MAX_RETRIES,
    )
    cognee_setup()  # Initialize cognee memory layer (non-blocking)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    """Return health probe response."""
    return {"status": "ok"}


@app.post("/run")
async def run_hypothesis(payload: RunRequest) -> StreamingResponse:
    """Accept a hypothesis, stream SSE events as agents process it."""
    return StreamingResponse(
        _run_stream(payload),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/history")
def history() -> dict[str, Any]:
    """Return recent runs — local store first, Phoenix as fallback."""
    local = get_history(limit=10)
    if local:
        return {"items": local}
    try:
        result = query_phoenix_traces(project_name=settings.PHOENIX_PROJECT_NAME, limit=20)
        return {"items": result.get("traces", [])}
    except Exception as exc:  # noqa: BLE001
        logger.warning("Phoenix unavailable for /history: %s", exc)
        return {"items": []}


@app.get("/golden-dataset")
def golden_dataset_endpoint() -> dict[str, Any]:
    """Return the golden evaluation dataset so the frontend can display it."""
    from evals.golden_dataset import GOLDEN_DATASET  # noqa: PLC0415
    return {
        "count": len(GOLDEN_DATASET),
        "hypotheses": [
            {
                "hypothesis": item["hypothesis"],
                "expected_verdict": item["expected_verdict"],
                "min_acceptable_score": item["min_acceptable_score"],
                "category": item["notes"][:80] + "…",
            }
            for item in GOLDEN_DATASET
        ],
    }


@app.post("/optimize")
async def trigger_optimizer() -> dict[str, Any]:
    """Trigger the nightly DSPy prompt optimizer on demand."""
    import asyncio  # noqa: PLC0415
    from optimizer.nightly_optimizer import main as _opt_main  # noqa: PLC0415

    loop = asyncio.get_event_loop()
    try:
        exit_code = await loop.run_in_executor(None, _opt_main)
        return {"status": "success" if exit_code == 0 else "failed", "exit_code": exit_code}
    except Exception as exc:  # noqa: BLE001
        logger.error("Optimizer failed: %s", exc)
        return {"status": "error", "message": str(exc)}


@app.post("/forget")
async def forget_memory(dataset: str | None = None) -> dict[str, Any]:
    """Clear cognee semantic memory for a dataset (default: quantsentinel_runs).

    Use this to reset the agent's memory between demo sessions or to remove
    stale research from the knowledge graph.
    """
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, cognee_forget, dataset)
    return {"status": "ok", "result": result}


@app.get("/improvement")
def improvement() -> dict[str, Any]:
    """Return eval score timeline — local store first, Phoenix as fallback."""
    local = get_improvement_points(limit=50)
    if local:
        return {"points": local}
    try:
        result = query_phoenix_traces(project_name=settings.PHOENIX_PROJECT_NAME, limit=50)
        timeline = extract_score_series(result.get("traces", []))
        return {"points": timeline}
    except Exception as exc:  # noqa: BLE001
        logger.warning("Phoenix unavailable for /improvement: %s", exc)
        return {"points": []}
