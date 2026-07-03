# QuantSentinel

QuantSentinel is a self-improving quantitative research agent that transforms market hypotheses into auditable research memos. It uses a multi-agent orchestration pipeline powered by Google ADK, with **Cognee as the persistent semantic memory layer** — so the agent actually remembers what it has already tested, recalls similar past research before starting a new run, and avoids repeating failed strategies.

Built for the WeMakeDevs "The Hangover Part AI" hackathon.

## 🧠 Cognee Memory Integration

Cognee powers the full memory lifecycle for QuantSentinel:

| Cognee primitive | Where it's used |
|-----------------|-----------------|
| **remember** | After each completed run: `cognee.add()` + `cognee.cognify()` stores the hypothesis, scores, and backtest verdict in a persistent knowledge graph |
| **recall** | Before each new run: `cognee.search()` surfaces semantically similar past research so the agent starts informed |
| **improve** | Recalled context is injected into the orchestrator prompt and the suggestion engine — the agent builds on what worked and avoids what didn't |
| **forget** | Low-scoring runs (below threshold) are pruned via `cognee.delete()` to keep the memory graph clean |

The orchestrator calls `recall_similar_runs()` as its first tool call (STEP 0) before planning, and a `memory` SSE event is emitted to the UI showing what was recalled.

## 🏗️ Project Architecture

```text
User UI (Next.js) <---> SSE Proxy API
                           |
                           v
                    FastAPI Backend
                           |
      +--------------------+--------------------+--------------------+
      |                    |                    |                    |
 Orchestrator (ADK)   Tools & Services     Optimizer (DSPy)   Cognee Memory
      |                    |                    |                    |
      |-- [STEP 0]         |-- yfinance/FRED    |-- Trace Retrieval  |-- remember()
      |   recall_similar   |-- Backtest Sandbox |-- Prompt Promotion |-- recall()
      |-- Data Agent       |-- Stats/Charts     |-- Golden Dataset   |-- improve()
      |-- Backtester       |-- cognee_memory.py |                    |-- forget()
      |-- Statistician     |-- Run Store        |                    |
      |-- Critic           |                    |                    |
      v                    v                    v                    v
Phoenix Traces <----> Evaluator (Rubrics) <----> run_store.jsonl + Cognee Graph DB
```

## 📂 Directory Structure

### 📁 Root
- `.env.example` - Template for required environment variables.
- `test_vertex_gemini.py` - Utility to verify Google Cloud Vertex AI connectivity.
- `infra/` - Deployment scripts and YAML manifests for Google Cloud Run.

### 📁 Backend (`/backend`)
The core engine powered by Python 3.13 and FastAPI.
- `main.py` - Primary entry point defining the API surface and SSE streaming logic.
- `agents/` - Agent definitions using Google ADK.
  - `orchestrator.py` - The "brain" that decomposes hypotheses into tasks for sub-agents.
  - `prompts.py` - Centralized system instructions and few-shot examples for all agents.
- `tools/` - The functional layer providing quantitative capabilities.
  - `market_data.py` - Fetches OHLCV data via `yfinance` and macroeconomic dates via `FRED`.
  - `backtest_runner.py` - Executes dynamically generated signal code in a safe environment.
  - `signal_factory.py` - Heuristically generates Python signal code from text descriptions.
  - `stats_tools.py` - Computes Sharpe ratios, Welch's t-tests, and Bootstrap Confidence Intervals.
  - `chart_tools.py` - Generates Base64-encoded PNG equity curves using Matplotlib.
  - `suggestion_engine.py` - Recommends hypothesis iterations based on backtest failures.
  - `phoenix_query_tool.py` - Interfaces with Arize Phoenix to retrieve past traces and scores.
  - `run_store.py` - Manages local JSONL persistence for research metadata.
- `evals/` - The "Judge" layer.
  - `evaluator.py` - Implements LLM-as-a-judge rubrics to score research memos.
  - `golden_dataset.py` - A set of benchmark hypotheses used to evaluate agent performance.
- `optimizer/` - Self-improvement loop.
  - `nightly_optimizer.py` - Uses DSPy (BootstrapFewShot) to optimize agent prompts based on high-scoring traces.
- `tracing.py` - Configures OpenInference instrumentation for automatic Phoenix logging.

### 📁 Frontend (`/frontend`)
A modern React dashboard built with Next.js 14 and Tailwind CSS.
- `app/` - Next.js App Router structure.
  - `page.tsx` - The main interactive research terminal.
  - `api/run/route.ts` - Edge-compatible SSE proxy to handle long-running backend connections.
- `components/` - Atomic UI units.
  - `ResearchDashboard.tsx` - The primary state manager for the research workflow.
  - `AgentTimeline.tsx` - A real-time visualization of agent activity and "thought" streams.
  - `HypothesisForm.tsx` - Input component for market theories.
  - `EvalScoreCard.tsx` - Visual breakdown of rubric scores (Logic, Evidence, Risk).
  - `MemoPanel.tsx` - Markdown-rendered research report display.
  - `ImprovementChart.tsx` - Recharts-based visualization of evaluation score trends.

## 🔌 API Reference

### `GET /health`
Simple heartbeat check.
- **Response:** `{"status": "ok"}`

### `POST /run`
The main research execution endpoint.
- **Body:**
  ```json
  {
    "hypothesis": "Buying SPY when RSI < 30 and selling when RSI > 70",
    "session_id": "unique-user-session-id"
  }
  ```
- **Response:** `text/event-stream` (SSE)
- **Event Types:**
  - `plan`: The orchestrator's initial decomposition of the task.
  - `step`: Status updates for specific agents (`running`, `done`).
  - `agent_output`: Real-time streaming of agent "thoughts" and intermediate tool results.
  - `heartbeat`: Progress pings during long-running data or compute tasks.
  - `chart`: Base64 PNG data of the strategy's equity curve.
  - `metrics`: Structured backtest results (Sharpe, Returns, Alpha).
  - `memo`: The final structured research report.
  - `scores`: LLM-generated evaluation results.
  - `suggestion`: AI-suggested next steps for hypothesis refinement.
  - `done`: Final event containing the `run_id` and Phoenix trace URL.

### `GET /history`
Retrieves a list of recent research runs.
- **Response:** `{"items": [...]}`

### `GET /golden-dataset`
Exposes the benchmark hypotheses for regression testing.
- **Response:** `{"count": 10, "hypotheses": [...]}`

### `POST /optimize`
Manually triggers the DSPy prompt optimization pipeline.
- **Response:** `{"status": "success", "exit_code": 0}`

### `GET /improvement`
Returns a time-series of evaluation scores to visualize agent improvement over time.
- **Response:** `{"points": [{"timestamp": "...", "score": 85}, ...]}`

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| **Language** | Python 3.13, TypeScript |
| **Backend Framework** | FastAPI |
| **Agent Framework** | Google ADK (Agent Development Kit) |
| **LLM** | Google Gemini 1.5 Pro / Flash |
| **Memory Layer** | Cognee (graph-vector hybrid memory: remember, recall, improve, forget) |
| **Observability** | Arize Phoenix, OpenInference |
| **Optimization** | DSPy (Declarative Self-improving Language Programs) |
| **Frontend** | Next.js 14, React 18, Tailwind CSS, Recharts |
| **Quant Libraries** | Pandas, Numpy, Scipy, Matplotlib, yfinance |
| **Deployment** | Google Cloud Run, Cloud Run Jobs |

## 🚀 Getting Started

### Prerequisites
- Python 3.13+ & Node.js 18+
- Google Cloud Project with Vertex AI enabled.
- Arize Phoenix instance (Local or Cloud).

### Installation
1. **Clone the repo:**
   ```bash
   git clone https://github.com/koopatroopa787/quantsentinel-cognee.git
   cd quantsentinel
   ```
2. **Setup Backend:**
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   pip install -r requirements.txt
   cp ../.env.example .env
   uvicorn main:app --reload
   ```
3. **Setup Frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

### MCP setup for AI agents (VS Code)
- Workspace MCP configuration is committed at `.vscode/mcp.json`.
- Enabled servers:
  - `fetch` (HTTP/web content retrieval)
  - `filesystem` (workspace file access)
  - `git` (repository-aware diff/log/status tools)
- In VS Code, run `MCP: List Servers` and trust/start these servers for this workspace.

## ⚖️ License
Apache 2.0. See `LICENSE` for details.

## ⚠️ Disclaimer
This software is for educational and research purposes only. It does not constitute financial advice. Past performance is not indicative of future results.
