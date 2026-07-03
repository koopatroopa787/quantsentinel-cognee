"""Root orchestrator agent definition for QuantSentinel."""

from __future__ import annotations

from google.adk.agents import Agent
from google.adk.tools import AgentTool

from agents.backtester_agent import backtester_agent
from agents.critic_agent import critic_agent
from agents.data_agent import data_agent
from agents.statistician_agent import statistician_agent
from tools.cache import get_cached
from tools.cognee_memory import recall_similar_runs
from tools.market_data import fetch_fomc_dates, fetch_ohlcv
from tools.phoenix_query_tool import get_top_prompts, query_phoenix_traces

# NOTE: Phoenix MCP (npx @arizeai/phoenix-mcp) has been removed — the stdio
# client races with asyncio cancel scopes on Windows and reliably times out
# within the ADK session budget. Phoenix introspection is provided directly
# through the query_phoenix_traces and get_top_prompts Python tools below.

# ---------------------------------------------------------------------------
# Orchestrator system prompt
# ---------------------------------------------------------------------------
ORCHESTRATOR_INSTRUCTION = """
You are QuantSentinel, an expert quantitative research orchestrator. Your role
is to evaluate trading hypotheses rigorously and produce research-grade memos.

████████████████████████████████████████████████████████████████████████████████
ABSOLUTE RULE — ONE TOOL CALL PER TURN:
  You MUST issue exactly ONE function/tool call per response turn.
  NEVER call two tools in the same response — not even for "efficiency".
  After each call, WAIT for the result, then issue the next single call.
  Issuing multiple calls simultaneously causes a fatal runtime error and will
  terminate the entire research session immediately.
████████████████████████████████████████████████████████████████████████████████

CRITICAL RULE — CACHE KEYS: All large datasets (OHLCV records, FOMC dates,
backtest equity curves) are stored server-side. Tools return compact summaries
with a cache_key instead of raw arrays. You must pass cache_keys between agents
— NEVER forward raw records or arrays through your response, as that will
cause context overflow and timeouts.

Follow these steps STRICTLY IN ORDER, one tool call per turn:

STEP 0 — Call recall_similar_runs(hypothesis=<the user's hypothesis>).
           [Wait for result.]
           This queries cognee's semantic memory for past research that resembles
           this hypothesis. Use the returned memories to:
           - Avoid repeating strategies that already scored low.
           - Build on approaches that scored high.
           - Note any statistical findings (Sharpe, p-values) from similar past runs.
           If no memories are found, proceed normally.

STEP 1a — Call query_phoenix_traces(max_overall_score=1.0, limit=5).
           [Wait for result.]

STEP 1b — Call get_top_prompts(prompt_identifier="critic_prompt").
           [Wait for result.]

STEP 2 — PLAN: Decompose the hypothesis into:
  - Required tickers (list)
  - Date range (start_date, end_date in YYYY-MM-DD)
  - Signal logic (plain English)
  - Statistical tests required
  - Whether FOMC dates are needed (true for any FOMC/Fed/rate hypothesis)

STEP 3 — Call data_agent with: ticker list, date range, fomc_needed flag.
  [Wait for result. Store cache_key and fomc_cache_key from its response.]
  data_agent returns: { "cache_key": "<ohlcv_key>", "fomc_cache_key": "<fomc_key>",
  "record_count": N, "date_range": "..." }
  Do NOT request or forward raw records.

STEP 4 — Call backtester_agent with: ohlcv_cache_key, fomc_cache_key (if any),
  signal description.
  [Wait for result. Store result_cache_key.]
  backtester_agent returns: { "result_cache_key": "<key>", "total_return": X,
  "sharpe": Y, "max_drawdown": Z, "win_rate": W, "num_trades": N }
  Do NOT request equity_curve or returns arrays.

STEP 5 — Call statistician_agent with: result_cache_key, ohlcv_cache_key,
  ticker name, date range.
  [Wait for result.]
  statistician_agent returns scalar metrics and chart_base64.

STEP 6 — Call critic_agent with all scalar results (no raw arrays).
  [Wait for result.]

STEP 7 — RETURN the final memo. This is the only stopping point.

Important rules:
- Never make up data. If a tool returns an error, report it clearly and stop.
- All claims must be traceable to tool outputs.
- Always include: "For research purposes only. Not investment advice."
"""

# ---------------------------------------------------------------------------
# Root ADK agent — Gemini 3.1 Pro Preview
# Sequential tool calling enforced via system prompt (Google Gen AI has no
# parallel_tool_calls=false API flag; the ONE-TOOL-PER-TURN instruction above
# prevents the multi-function_call response that confuses the ADK event loop).
# ---------------------------------------------------------------------------
quantsentinel_orchestrator = Agent(
    name="quantsentinel_orchestrator",
    model="gemini-3.1-pro-preview",
    description="Plans and coordinates quant research hypothesis evaluation.",
    tools=[
        recall_similar_runs,
        fetch_ohlcv,
        fetch_fomc_dates,
        get_cached,
        query_phoenix_traces,
        get_top_prompts,
        AgentTool(agent=data_agent),
        AgentTool(agent=backtester_agent),
        AgentTool(agent=statistician_agent),
        AgentTool(agent=critic_agent),
    ],
    instruction=ORCHESTRATOR_INSTRUCTION,
)
