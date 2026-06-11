## QuantSentinel

### Commands

**Backend**
- `cd backend`
- `pip install -r requirements.txt`
- `uvicorn main:app --reload`
- Single connectivity check: `python ..\test_vertex_gemini.py`

**Frontend**
- `cd frontend`
- `npm install`
- `npm run dev`
- `npm run build`
- `npm run lint`

### Architecture

QuantSentinel is a two-part app: a Next.js 14 frontend streams research runs from a FastAPI backend over SSE.

- `frontend/app/api/run/route.ts` proxies `/run`, `/history`, and `/improvement` to the backend and keeps the browser-facing stream alive.
- `backend/main.py` is the API entrypoint. It prefers the Google ADK orchestrator path, then falls back to a direct Python tool pipeline if ADK times out or fails.
- The backend pipeline is organized around `agents/` (orchestrator, data, backtester, statistician, critic), `tools/` (market data, backtests, stats, charts, Phoenix queries, run store), `evals/`, and `optimizer/`.
- `backend/tracing.py` must run before instrumented imports so Phoenix/OpenTelemetry wiring is active when available.
- `backend/tools/run_store.py` persists completed runs to `run_store.jsonl`; Phoenix history/improvement endpoints are only used as fallback sources.

### Conventions

- Keep SSE event names stable: `plan`, `step`, `agent_output`, `heartbeat`, `chart`, `metrics`, `memo`, `scores`, `suggestion`, `tokens`, `done`, `error`.
- Pass cache keys and compact summaries between agents/tools; do not expand large arrays into prompts or events.
- Preserve the orchestrator rule in `backend/agents/orchestrator.py`: one tool call per turn.
- Frontend UI is built with client components, inline styles, and `components/DesignTokens.tsx`; avoid introducing CSS modules or Tailwind-first rewrites.
- Bootstrap data through `/api/run?mode=bootstrap`; keep the route resilient when backend or Phoenix is unavailable.
- Use `backend/.env` from `.env.example` for secrets and runtime settings; `frontend/.env.local` only for the frontend backend URL.
- Avoid editing generated/vendor trees such as `frontend/.next/`, `frontend/node_modules/`, `backend/.venv/`, and `__pycache__/`.
