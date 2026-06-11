"use client";

import React, { useEffect, useRef, useState } from "react";
import AgentTimeline from "../components/AgentTimeline";
import ResearchDashboard from "../components/ResearchDashboard";
import { Q } from "../components/DesignTokens";
import { TopBar, LeftCol, RightCol } from "../components/Layout";
import type { AgentStep } from "../components/AgentTimeline";
import type { RunMetrics, Scores, Suggestion } from "../components/ResearchDashboard";
import type { HistoryItem, ImprovementPoint } from "../components/Layout";

const defaultScores: Scores = {
  faithfulness: 0, stats_correctness: 0, hallucination: 0, risk_caveats: 0, overall: 0,
};

export default function HomePage() {
  const [running, setRunning]         = useState(false);
  const [hypothesis, setHypothesis]   = useState("");
  const [steps, setSteps]             = useState<AgentStep[]>([]);
  const [memo, setMemo]               = useState("");
  const [scores, setScores]           = useState<Scores>(defaultScores);
  const [history, setHistory]         = useState<HistoryItem[]>([]);
  const [improvement, setImprovement] = useState<ImprovementPoint[]>([]);
  const [traceUrl, setTraceUrl]       = useState<string | null>(null);
  const [runMetrics, setRunMetrics]   = useState<RunMetrics | null>(null);
  const [suggestion, setSuggestion]   = useState<Suggestion | null>(null);
  const [tokens, setTokens]           = useState({ input: 0, output: 0 });

  // Bootstrap history and improvement data from backend
  useEffect(() => {
    void (async () => {
      try {
        const res = await fetch("/api/run?mode=bootstrap");
        if (!res.ok) return;
        const data = await res.json();
        setHistory(data.history ?? []);
        setImprovement(data.improvement ?? []);
      } catch {
        // Phoenix not connected — ignore
      }
    })();
  }, []);

  // ── SSE stream processor ─────────────────────────────────────────────────────
  async function processStream(response: Response, hyp: string) {
    if (!response.body) { setRunning(false); return; }
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const chunks = buffer.split("\n\n");
        buffer = chunks.pop() ?? "";
        for (const chunk of chunks) {
          const eventMatch = chunk.match(/^event:\s*(.+)$/m);
          const dataMatch  = chunk.match(/^data:\s*(.+)$/m);
          if (!eventMatch || !dataMatch) continue;
          const event = eventMatch[1].trim();
          let data: Record<string, unknown>;
          try { data = JSON.parse(dataMatch[1]); } catch { continue; }

          if (event === "plan") {
            setSteps(cur => [...cur, { agent: "orchestrator", status: "planning", message: "Decomposing hypothesis into research plan…", startedAt: Date.now() }]);
          } else if (event === "step") {
            setSteps(cur => {
              const msg = data.message as string;
              if (data.agent === "system" && msg?.includes("direct pipeline")) {
                return cur.map(s => (s.status === "running" || s.status === "planning") ? { ...s, status: "warning" as const, message: "Timed out — fallback pipeline starting…" } : s);
              }
              const idx = cur.findLastIndex(s => s.agent === data.agent);
              if (idx >= 0 && data.status === "done") {
                const next = [...cur]; next[idx] = { ...next[idx], status: "done", message: msg }; return next;
              }
              return [...cur, { ...(data as AgentStep), startedAt: Date.now() }];
            });
          } else if (event === "agent_output") {
            setSteps(cur => {
              const next = [...cur];
              const idx = next.findLastIndex(s => s.agent === data.agent);
              if (idx >= 0) { next[idx] = { ...next[idx], output: (next[idx].output || "") + (data.text as string) }; return next; }
              return [...next, { agent: data.agent as string, status: "running", message: "Working...", output: data.text as string, startedAt: Date.now() }];
            });
          } else if (event === "heartbeat") {
            setSteps(cur => {
              const next = [...cur];
              const idx = next.findLastIndex(s => s.agent === (data.agent as string) && s.status === "running");
              if (idx >= 0) next[idx] = { ...next[idx], heartbeat: data.message as string };
              return next;
            });
          } else if (event === "metrics") {
            setRunMetrics(data as unknown as RunMetrics);
          } else if (event === "suggestion") {
            setSuggestion(data as unknown as Suggestion);
          } else if (event === "memo") {
            setMemo((data.text as string) ?? "");
          } else if (event === "scores") {
            const incoming = data as Scores;
            setScores(incoming);
            setImprovement(cur => [...cur, { timestamp: new Date().toISOString(), overall: incoming.overall ?? 0 }]);
            setHistory(cur => [{ hypothesis: hyp, score: incoming.overall ?? 0, timestamp: new Date().toISOString() }, ...cur.slice(0, 4)]);
          } else if (event === "tokens") {
            setTokens(cur => ({ input: cur.input + ((data.input as number) || 0), output: cur.output + ((data.output as number) || 0) }));
          } else if (event === "done") {
            setTraceUrl((data.phoenix_trace_url as string) ?? null);
            setRunning(false);
          } else if (event === "error") {
            setSteps(cur => [...cur, { agent: "system", status: "error", message: (data.message as string) ?? "Unknown error" }]);
            setRunning(false);
          }
        }
      }
    } catch (streamErr) {
      setSteps(cur => [...cur, {
        agent: "system", status: "error",
        message: `Stream interrupted: ${streamErr instanceof Error ? streamErr.message : "connection lost"}. The backend may still be running — check the terminal.`,
      }]);
    } finally {
      setRunning(false);
    }
  }

  // ── Run handler ───────────────────────────────────────────────────────────────
  async function onRun(hyp?: string) {
    const h = hyp ?? hypothesis;
    if (!h.trim() || running) return;
    setRunning(true);
    setSteps([]);
    setMemo("");
    setScores(defaultScores);
    setTraceUrl(null);
    setRunMetrics(null);
    setSuggestion(null);
    if (hyp) setHypothesis(hyp);

    let response: Response;
    try {
      response = await fetch("/api/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ hypothesis: h, session_id: crypto.randomUUID() }),
      });
    } catch { setRunning(false); return; }

    await processStream(response, h);
  }

  const canRun = hypothesis.trim().length >= 5 && !running;
  const hasResults = !!runMetrics;
  const navItems = [
    { icon: "O", label: "Overview" },
    { icon: "R", label: "Runs" },
    { icon: "A", label: "Analytics" },
    { icon: "S", label: "Settings" },
  ];
  const activeNav = 0;

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      <aside style={{
        width: 72, background: "rgba(7,10,20,0.9)", borderRight: `1px solid ${Q.border}`,
        display: "flex", flexDirection: "column", alignItems: "center", padding: "18px 0", gap: 14,
      }}>
        <div style={{
          width: 38, height: 38, borderRadius: 12, background: Q.accentLt, border: `1px solid ${Q.border}`,
          display: "flex", alignItems: "center", justifyContent: "center", color: Q.accentBright, fontWeight: 800,
          boxShadow: Q.shadow,
        }}>
          QS
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: 8, flex: 1 }}>
          {navItems.map((item, idx) => (
            <button
              key={item.label}
              title={`${item.label} · Coming soon`}
              aria-label={`${item.label} (coming soon)`}
              style={{
                width: 40, height: 40, borderRadius: 12,
                background: idx === activeNav ? Q.accentLt : "transparent",
                border: `1px solid ${idx === activeNav ? Q.border : Q.borderFaint}`,
                color: idx === activeNav ? Q.accentBright : Q.muted,
                display: "flex", alignItems: "center", justifyContent: "center",
                boxShadow: idx === activeNav ? Q.shadow : "none",
                fontSize: 16,
              }}
            >
              {item.icon}
            </button>
          ))}
        </div>
        <div style={{
          width: 40, height: 40, borderRadius: 14, background: Q.cardInner, border: `1px solid ${Q.borderFaint}`,
          color: Q.ink, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 12, fontWeight: 700,
        }}>
          Y
        </div>
      </aside>

      <div style={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}>
        <TopBar running={running}/>

        <div style={{ flex: 1, overflowY: 'auto', padding: '24px 26px 32px', display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr 320px', gap: 16, alignItems: 'start' }}>

            {/* Left column */}
            <LeftCol
              hypothesis={hypothesis}
              setHypothesis={setHypothesis}
              onRun={() => onRun()}
              running={running}
              tokens={tokens}
              history={history}
              canRun={canRun}
            />

            {/* Centre column */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <AgentTimeline steps={steps} running={running}/>
              {hasResults && (
                <ResearchDashboard
                  metrics={runMetrics}
                  scores={scores}
                  memo={memo}
                  suggestion={suggestion}
                  traceUrl={traceUrl}
                  onRunSuggestion={h => onRun(h)}
                />
              )}
            </div>

            {/* Right column */}
            <RightCol scores={scores} improvement={improvement} metrics={runMetrics}/>
          </div>
          <div style={{ height: 8 }}/>
        </div>
      </div>
    </div>
  );
}
