"use client";

import React from "react";
import { Q, AGENTS, ImprovementLine, ScoreTile } from "./DesignTokens";

// ── Types ─────────────────────────────────────────────────────────────────────
export type AgentStep = {
  agent: string;
  status: "running" | "done" | "error" | "warning" | "planning";
  message: string;
  startedAt?: number;
  heartbeat?: string;
  output?: string;
};

export type Scores = {
  faithfulness: number;
  stats_correctness: number;
  hallucination: number;
  risk_caveats: number;
  overall: number;
};

export type HistoryItem = { hypothesis: string; score: number; timestamp: string };
export type ImprovementPoint = { timestamp: string; overall: number };
export type RunMetricsSnapshot = {
  total_return: number;
  benchmark_total_return: number;
  alpha: number;
  sharpe: number;
  max_drawdown: number;
  win_rate: number;
  p_value: number;
  significant_at_5pct: boolean;
};

const DEMO_POINTS: ImprovementPoint[] = [
  { timestamp: "2024-01-01T00:00:00Z", overall: 0.52 },
  { timestamp: "2024-01-08T00:00:00Z", overall: 0.55 },
  { timestamp: "2024-01-15T00:00:00Z", overall: 0.57 },
  { timestamp: "2024-01-22T00:00:00Z", overall: 0.60 },
  { timestamp: "2024-01-29T00:00:00Z", overall: 0.62 },
  { timestamp: "2024-02-05T00:00:00Z", overall: 0.64 },
  { timestamp: "2024-02-12T00:00:00Z", overall: 0.66 },
  { timestamp: "2024-02-19T00:00:00Z", overall: 0.68 },
  { timestamp: "2024-02-26T00:00:00Z", overall: 0.67 },
  { timestamp: "2024-03-04T00:00:00Z", overall: 0.69 },
  { timestamp: "2024-03-11T00:00:00Z", overall: 0.71 },
  { timestamp: "2024-03-18T00:00:00Z", overall: 0.70 },
  { timestamp: "2024-03-25T00:00:00Z", overall: 0.72 },
  { timestamp: "2024-04-01T00:00:00Z", overall: 0.73 },
];

// ── Top Bar ───────────────────────────────────────────────────────────────────
export function TopBar({ running }: { running: boolean }) {
  return (
    <header style={{
      height: 64, background: Q.card, backdropFilter: 'blur(18px)',
      borderBottom: `1px solid ${Q.border}`, display: 'flex', alignItems: 'center',
      padding: '0 26px', gap: 18, flexShrink: 0, zIndex: 10, position: 'relative',
      fontFamily: Q.sans, boxShadow: Q.shadow,
    }}>
      <button
        title="Coming soon"
        aria-label="Menu (coming soon)"
        style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 6, display: 'flex', flexDirection: 'column', gap: 4 }}
      >
        {[0,1,2].map(i => <span key={i} style={{ width: 18, height: 1.5, background: Q.muted, display: 'block', borderRadius: 1 }}/>)}
      </button>

      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{
          width: 36, height: 36, borderRadius: 12, flexShrink: 0,
          background: `linear-gradient(135deg, ${Q.accent} 0%, ${Q.cyan} 100%)`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: `0 6px 22px ${Q.accentGlow}, inset 0 1px 0 rgba(255,255,255,0.2)`,
          border: `1px solid ${Q.borderFaint}`,
        }}>
          <svg width="17" height="17" viewBox="0 0 18 18" fill="none">
            <polygon points="9,2 16,6 16,12 9,16 2,12 2,6" stroke="white" strokeWidth="1.3" fill="none" strokeLinejoin="round"/>
            <circle cx="9" cy="9" r="2.5" fill="white"/>
          </svg>
        </div>
        <div>
          <div style={{ fontSize: 15, fontWeight: 700, color: Q.ink, letterSpacing: '-0.02em', lineHeight: 1.1 }}>QuantSentinel</div>
          <div style={{ fontSize: 10, color: Q.muted, letterSpacing: '0.04em', fontFamily: Q.mono }}>Research Terminal</div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 4, marginLeft: 4 }}>
        {['Workspace', 'Research', 'Strategies', 'Insights'].map((item, i) => (
          <button
            key={item}
            title={`${item} · Coming soon`}
            aria-label={`${item} (coming soon)`}
            style={{
            background: i === 1 ? Q.accentLt : 'transparent',
            border: i === 1 ? `1px solid ${Q.border}` : `1px solid ${Q.borderFaint}`,
            color: i === 1 ? Q.accentBright : Q.muted,
            borderRadius: Q.rpill, padding: '6px 14px', fontSize: 12, fontWeight: 600, cursor: 'pointer', fontFamily: Q.sans, transition: 'all 0.15s',
          }}>{item}</button>
        ))}
      </div>

      <div style={{ flex: 1 }}/>

      {running && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 7, padding: '6px 14px', background: Q.accentLt, borderRadius: Q.rpill, border: `1px solid ${Q.border}` }}>
          <span style={{ width: 6, height: 6, borderRadius: '50%', background: Q.accent, display: 'inline-block', animation: 'q2Pulse 1.2s infinite', boxShadow: `0 0 8px ${Q.accent}` }}/>
          <span style={{ fontSize: 11, fontWeight: 600, color: Q.accentBright }}>Research live</span>
        </div>
      )}

      <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '7px 14px', background: Q.cardInner, borderRadius: Q.rpill, border: `1px solid ${Q.border}` }}>
        <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
          <circle cx="5.5" cy="5.5" r="4.5" stroke={Q.muted} strokeWidth="1.3"/>
          <path d="M9 9L12 12" stroke={Q.muted} strokeWidth="1.3" strokeLinecap="round"/>
        </svg>
        <span style={{ fontSize: 12, color: Q.muted, minWidth: 120 }}>Search runs, traces…</span>
        <span style={{ fontSize: 10, color: Q.muted, background: Q.faint, border: `1px solid ${Q.borderFaint}`, borderRadius: 5, padding: '1px 6px', fontFamily: Q.mono }}>⌘K</span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '5px 10px', background: Q.amberBg, border: `1px solid ${Q.amberBd}`, borderRadius: Q.rpill }}>
        <span style={{ fontSize: 10, color: Q.amber }}>⚠</span>
        <span style={{ fontSize: 10, color: Q.amber, fontWeight: 600 }}>Research only · Not financial advice</span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{
          width: 34, height: 34, borderRadius: '50%',
          background: `linear-gradient(135deg, ${Q.accent}, ${Q.cyan})`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 13, fontWeight: 700, color: '#0b1120',
          boxShadow: `0 2px 12px ${Q.accentGlow}`, border: `1.5px solid ${Q.borderFaint}`,
        }}>A</div>
        <div>
          <div style={{ fontSize: 12, fontWeight: 600, color: Q.ink, lineHeight: 1.2 }}>Admin User</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <span style={{ width: 5, height: 5, borderRadius: '50%', background: Q.green, display: 'inline-block', boxShadow: `0 0 6px ${Q.green}` }}/>
            <span style={{ fontSize: 10, color: Q.muted }}>Active</span>
          </div>
        </div>
      </div>
    </header>
  );
}

// ── Left Column ───────────────────────────────────────────────────────────────
export function LeftCol({
  hypothesis, setHypothesis, onRun, running, tokens, history, canRun,
}: {
  hypothesis: string; setHypothesis: (v: string) => void; onRun: () => void;
  running: boolean; tokens: { input: number; output: number };
  history: HistoryItem[]; canRun: boolean;
}) {
  const [showEx, setShowEx] = React.useState(false);
  const taRef = React.useRef<HTMLTextAreaElement>(null);
  const [builder, setBuilder] = React.useState({
    asset: "SPY",
    signal: "rsi",
    startYear: 2015,
    endYear: 2024,
    rsiPeriod: 14,
    rsiThreshold: 30,
    holdDays: 5,
    fast: 50,
    slow: 200,
    momentum: 252,
  });

  const EXAMPLES = [
    "Does a 14-day RSI below 30 on SPY generate significant mean-reversion returns over 5 trading days from 2015 to 2024?",
    "Do FOMC announcement days show elevated VIX spikes on QQQ from 2010 to 2023?",
    "Does a 50/200-day SMA golden cross on AAPL outperform buy-and-hold from 2012 to 2024?",
  ];

  const card = (children: React.ReactNode, extra: React.CSSProperties = {}) => (
    <div style={{
      background: Q.card, borderRadius: Q.r, boxShadow: Q.shadow, border: `1px solid ${Q.border}`,
      overflow: 'hidden', position: 'relative', backdropFilter: 'blur(18px)', ...extra,
    }}>
      {children}
    </div>
  );
  const fieldStyle: React.CSSProperties = {
    display: 'flex', flexDirection: 'column', gap: 6,
    fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: Q.muted,
  };
  const inputStyle: React.CSSProperties = {
    marginTop: 2, background: Q.cardInner, border: `1px solid ${Q.borderFaint}`,
    borderRadius: 10, padding: '8px 10px', fontSize: 12, color: Q.ink, outline: 'none',
  };
  const buildHypothesis = () => {
    const start = Math.min(builder.startYear, builder.endYear);
    const end = Math.max(builder.startYear, builder.endYear);
    if (builder.signal === "rsi") {
      return `Does a ${builder.rsiPeriod}-day RSI below ${builder.rsiThreshold} on ${builder.asset} generate mean-reversion returns over ${builder.holdDays} trading days from ${start} to ${end}?`;
    }
    if (builder.signal === "sma") {
      return `Does a ${builder.fast}/${builder.slow}-day SMA crossover on ${builder.asset} outperform buy-and-hold from ${start} to ${end}?`;
    }
    if (builder.signal === "momentum") {
      return `Does a ${builder.momentum}-day momentum filter on ${builder.asset} improve risk-adjusted returns from ${start} to ${end}?`;
    }
    if (builder.signal === "fomc") {
      return `Do FOMC announcement days drive abnormal ${builder.asset} returns within ${builder.holdDays} trading days from ${start} to ${end}?`;
    }
    return `Evaluate ${builder.asset} strategy performance from ${start} to ${end}.`;
  };
  const applyBuilder = () => {
    setHypothesis(buildHypothesis());
    setShowEx(false);
    taRef.current?.focus();
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14, fontFamily: Q.sans }}>
      {card(
        <div style={{ padding: '18px 20px', display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <div style={{ fontSize: 13, fontWeight: 700, color: Q.ink }}>No-code Strategy Builder</div>
              <div style={{ fontSize: 11, color: Q.muted, marginTop: 4 }}>Inspired by CoinQuant-style builders</div>
            </div>
            <span style={{ fontSize: 10, color: Q.accentBright, background: Q.accentLt, border: `1px solid ${Q.border}`, borderRadius: Q.rpill, padding: '3px 9px', fontWeight: 700 }}>
              beta
            </span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            <label style={fieldStyle}>
              Asset
              <select
                value={builder.asset}
                onChange={e => setBuilder(b => ({ ...b, asset: e.target.value }))}
                style={inputStyle}
              >
                {["SPY", "QQQ", "AAPL", "NVDA", "BTC", "ETH"].map(t => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </label>
            <label style={fieldStyle}>
              Signal
              <select
                value={builder.signal}
                onChange={e => setBuilder(b => ({ ...b, signal: e.target.value }))}
                style={inputStyle}
              >
                <option value="rsi">RSI mean reversion</option>
                <option value="sma">SMA crossover</option>
                <option value="momentum">Momentum filter</option>
                <option value="fomc">FOMC event study</option>
              </select>
            </label>
            <label style={fieldStyle}>
              Start year
              <input
                type="number"
                value={builder.startYear}
                onChange={e => setBuilder(b => ({ ...b, startYear: Number(e.target.value || 0) }))}
                style={inputStyle}
              />
            </label>
            <label style={fieldStyle}>
              End year
              <input
                type="number"
                value={builder.endYear}
                onChange={e => setBuilder(b => ({ ...b, endYear: Number(e.target.value || 0) }))}
                style={inputStyle}
              />
            </label>
          </div>
          {builder.signal === "rsi" && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10 }}>
              <label style={fieldStyle}>
                RSI period
                <input
                  type="number"
                  value={builder.rsiPeriod}
                  onChange={e => setBuilder(b => ({ ...b, rsiPeriod: Number(e.target.value || 0) }))}
                  style={inputStyle}
                />
              </label>
              <label style={fieldStyle}>
                Threshold
                <input
                  type="number"
                  value={builder.rsiThreshold}
                  onChange={e => setBuilder(b => ({ ...b, rsiThreshold: Number(e.target.value || 0) }))}
                  style={inputStyle}
                />
              </label>
              <label style={fieldStyle}>
                Hold days
                <input
                  type="number"
                  value={builder.holdDays}
                  onChange={e => setBuilder(b => ({ ...b, holdDays: Number(e.target.value || 0) }))}
                  style={inputStyle}
                />
              </label>
            </div>
          )}
          {builder.signal === "sma" && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
              <label style={fieldStyle}>
                Fast SMA
                <input
                  type="number"
                  value={builder.fast}
                  onChange={e => setBuilder(b => ({ ...b, fast: Number(e.target.value || 0) }))}
                  style={inputStyle}
                />
              </label>
              <label style={fieldStyle}>
                Slow SMA
                <input
                  type="number"
                  value={builder.slow}
                  onChange={e => setBuilder(b => ({ ...b, slow: Number(e.target.value || 0) }))}
                  style={inputStyle}
                />
              </label>
            </div>
          )}
          {builder.signal === "momentum" && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 10 }}>
              <label style={fieldStyle}>
                Momentum lookback
                <input
                  type="number"
                  value={builder.momentum}
                  onChange={e => setBuilder(b => ({ ...b, momentum: Number(e.target.value || 0) }))}
                  style={inputStyle}
                />
              </label>
            </div>
          )}
          {builder.signal === "fomc" && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 10 }}>
              <label style={fieldStyle}>
                Hold days
                <input
                  type="number"
                  value={builder.holdDays}
                  onChange={e => setBuilder(b => ({ ...b, holdDays: Number(e.target.value || 0) }))}
                  style={inputStyle}
                />
              </label>
            </div>
          )}
          <button
            onClick={applyBuilder}
            style={{
              width: '100%', padding: '11px 14px', borderRadius: Q.rpill, border: `1px solid ${Q.border}`,
              background: `linear-gradient(135deg, ${Q.accent} 0%, ${Q.cyan} 100%)`,
              color: '#0b1120', fontSize: 12, fontWeight: 700, cursor: 'pointer', letterSpacing: '0.02em',
              boxShadow: `0 8px 22px ${Q.accentGlow}`,
            }}
          >
            Build hypothesis
          </button>
        </div>
      )}
      {card(
        <>
          <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 2, background: `linear-gradient(90deg, ${Q.accent}, ${Q.cyan})` }}/>
          <div style={{ padding: '20px 20px 0' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ width: 7, height: 7, borderRadius: '50%', background: Q.accent, boxShadow: `0 0 8px ${Q.accent}`, display: 'inline-block' }}/>
                <span style={{ fontSize: 13, fontWeight: 700, color: Q.ink }}>Hypothesis Editor</span>
              </div>
              <button onClick={() => setShowEx(v => !v)} style={{
                fontSize: 11, color: Q.accentBright, background: Q.accentLt,
                border: `1px solid ${Q.border}`, borderRadius: Q.rpill, padding: '4px 12px',
                cursor: 'pointer', fontWeight: 600, fontFamily: Q.sans,
              }}>Strategy library {showEx ? '↑' : '↓'}</button>
            </div>

            {showEx && (
              <div style={{ marginBottom: 12, display: 'flex', flexDirection: 'column', gap: 6 }}>
                {EXAMPLES.map((ex, i) => (
                  <button key={i} onClick={() => { setHypothesis(ex); setShowEx(false); taRef.current?.focus(); }}
                    style={{
                      fontSize: 11, color: Q.sub, background: Q.cardInner,
                      border: `1px solid ${Q.borderFaint}`, borderRadius: 12,
                      padding: '9px 12px', textAlign: 'left', cursor: 'pointer',
                      lineHeight: 1.55, fontFamily: Q.sans, transition: 'all 0.15s',
                    }}
                    onMouseEnter={e => { (e.currentTarget as HTMLElement).style.borderColor = `${Q.accent}70`; (e.currentTarget as HTMLElement).style.color = Q.ink; }}
                    onMouseLeave={e => { (e.currentTarget as HTMLElement).style.borderColor = Q.borderFaint; (e.currentTarget as HTMLElement).style.color = Q.sub; }}
                  >{ex}</button>
                ))}
              </div>
            )}

            <textarea
              ref={taRef} value={hypothesis}
              onChange={e => setHypothesis(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) onRun(); }}
              placeholder="Describe your trading hypothesis…"
              rows={5}
              style={{
                width: '100%', boxSizing: 'border-box',
                background: Q.cardInner, border: `1.5px solid ${Q.borderFaint}`,
                borderRadius: 12, padding: '11px 14px', fontSize: 13, color: Q.ink,
                lineHeight: 1.65, resize: 'none', fontFamily: Q.sans,
                transition: 'border-color 0.15s', outline: 'none',
              }}
              onFocus={e => (e.target.style.borderColor = `${Q.accent}60`)}
              onBlur={e => (e.target.style.borderColor = Q.borderFaint)}
            />

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', margin: '8px 0 14px' }}>
              <span style={{ fontSize: 11, color: Q.muted, fontFamily: Q.mono }}>{hypothesis.length} chars · ⌘↵ to run</span>
              {running && (
                <span style={{ fontSize: 11, color: Q.accentBright, display: 'flex', alignItems: 'center', gap: 5 }}>
                  <span style={{ width: 5, height: 5, borderRadius: '50%', background: Q.accent, display: 'inline-block', animation: 'q2Pulse 1.2s infinite', boxShadow: `0 0 6px ${Q.accent}` }}/>
                  Researching…
                </span>
              )}
            </div>
          </div>

          <div style={{ padding: '0 20px 20px' }}>
            <button onClick={onRun} disabled={!canRun} style={{
              width: '100%', padding: '12px 20px', borderRadius: Q.rpill, border: 'none',
              background: canRun ? `linear-gradient(135deg, ${Q.accent} 0%, ${Q.cyan} 100%)` : Q.cardInner,
              color: canRun ? '#0b1120' : Q.muted,
              fontSize: 14, fontWeight: 700, cursor: canRun ? 'pointer' : 'not-allowed',
              fontFamily: Q.sans, letterSpacing: '0.01em',
              boxShadow: canRun ? `0 8px 24px ${Q.accentGlow}` : 'none',
              transition: 'all 0.2s', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
            }}
              onMouseEnter={e => { if (canRun) (e.currentTarget as HTMLElement).style.boxShadow = `0 6px 32px ${Q.accentGlow}`; }}
              onMouseLeave={e => { if (canRun) (e.currentTarget as HTMLElement).style.boxShadow = `0 4px 24px ${Q.accentGlow}`; }}
            >
              <span>{running ? '⟳' : '⚡'}</span>
              {running ? 'Researching…' : 'Run Research'}
              {!running && canRun && <span style={{ opacity: 0.65 }}>→</span>}
            </button>
          </div>
        </>
      )}

      {card(
        <div style={{ padding: '16px 20px' }}>
          <div style={{ fontSize: 10, fontWeight: 700, color: Q.muted, letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 12 }}>Token Usage</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
            {([['Input', tokens.input, Q.cyan], ['Output', tokens.output, Q.accentBright]] as [string, number, string][]).map(([lbl, val, col]) => (
              <div key={lbl} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', background: Q.cardInner, borderRadius: 10, border: `1px solid ${Q.borderFaint}` }}>
                <span style={{ fontSize: 11, color: Q.sub }}>{lbl} tokens</span>
                <span style={{ fontSize: 15, fontFamily: Q.mono, fontWeight: 700, color: val > 0 ? col : Q.muted, textShadow: val > 0 ? `0 0 16px ${col}50` : 'none' }}>
                  {val > 0 ? val.toLocaleString() : '—'}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {card(
        <div style={{ padding: '16px 20px' }}>
          <div style={{ fontSize: 10, fontWeight: 700, color: Q.muted, letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 12 }}>Recent Runs</div>
          {history.length === 0 ? (
            <p style={{ fontSize: 12, color: Q.muted, fontStyle: 'italic' }}>No runs yet.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
              {history.slice(0, 5).map((item, i) => (
                <div key={i} style={{ background: Q.cardInner, border: `1px solid ${Q.borderFaint}`, borderRadius: 12, padding: '10px 12px', cursor: 'pointer', transition: 'all 0.15s' }}
                  onMouseEnter={e => { (e.currentTarget as HTMLElement).style.borderColor = `${Q.accent}40`; (e.currentTarget as HTMLElement).style.background = `${Q.accent}08`; }}
                  onMouseLeave={e => { (e.currentTarget as HTMLElement).style.borderColor = Q.borderFaint; (e.currentTarget as HTMLElement).style.background = Q.cardInner; }}
                >
                  <p style={{ fontSize: 11, color: Q.sub, lineHeight: 1.45, margin: '0 0 7px', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                    {item.hypothesis}
                  </p>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{
                      fontSize: 11, fontWeight: 700, fontFamily: Q.mono,
                      color: item.score >= 0.7 ? Q.green : Q.amber,
                      background: item.score >= 0.7 ? Q.greenBg : Q.amberBg,
                      border: `1px solid ${item.score >= 0.7 ? Q.greenBd : Q.amberBd}`,
                      borderRadius: Q.rpill, padding: '2px 8px',
                    }}>{item.score.toFixed(2)}</span>
                    <span style={{ fontSize: 10, color: Q.muted, fontFamily: Q.mono }}>{new Date(item.timestamp).toLocaleDateString()}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Right Column ──────────────────────────────────────────────────────────────
export function RightCol({ scores, improvement, metrics }: { scores: Scores; improvement: ImprovementPoint[]; metrics: RunMetricsSnapshot | null }) {
  const pts = improvement.length >= 1 ? improvement : DEMO_POINTS;
  const isDemo = improvement.length < 1;
  const scoreVals = pts.map(p => p.overall);
  const drawdownAbs = metrics ? Math.abs(metrics.max_drawdown) : 0;
  const confidence = !metrics
    ? { label: "Waiting", color: Q.muted, bg: Q.faint, border: Q.borderFaint }
    : metrics.sharpe >= 1 && metrics.significant_at_5pct
      ? { label: "Strong edge", color: Q.green, bg: Q.greenBg, border: Q.greenBd }
      : metrics.sharpe >= 0.5
        ? { label: "Developing", color: Q.amber, bg: Q.amberBg, border: Q.amberBd }
        : { label: "Weak edge", color: Q.red, bg: Q.redBg, border: Q.redBd };
  const risk = !metrics
    ? { label: "—", color: Q.muted, bg: Q.faint, border: Q.borderFaint }
    : drawdownAbs >= 0.25
      ? { label: "High risk", color: Q.red, bg: Q.redBg, border: Q.redBd }
      : drawdownAbs >= 0.15
        ? { label: "Elevated", color: Q.amber, bg: Q.amberBg, border: Q.amberBd }
        : { label: "Contained", color: Q.green, bg: Q.greenBg, border: Q.greenBd };
  const edge = !metrics
    ? { label: "—", color: Q.muted, bg: Q.faint, border: Q.borderFaint }
    : metrics.alpha >= 0
      ? { label: "Positive alpha", color: Q.green, bg: Q.greenBg, border: Q.greenBd }
      : { label: "Negative alpha", color: Q.red, bg: Q.redBg, border: Q.redBd };
  const alerts: Array<{ title: string; detail: string; tone: "high" | "medium" | "low" }> = [];
  if (metrics) {
    if (!metrics.significant_at_5pct) {
      alerts.push({ title: "Edge not significant", detail: `p-value ${metrics.p_value.toFixed(3)}`, tone: "high" });
    }
    if (metrics.alpha < 0) {
      alerts.push({ title: "Alpha below benchmark", detail: `${(metrics.alpha * 100).toFixed(2)}%`, tone: "medium" });
    }
    if (drawdownAbs >= 0.2) {
      alerts.push({ title: "Drawdown above 20%", detail: `${(drawdownAbs * 100).toFixed(1)}% peak-to-trough`, tone: "medium" });
    }
    if (metrics.win_rate < 0.45) {
      alerts.push({ title: "Low win rate", detail: `${(metrics.win_rate * 100).toFixed(1)}% of held days`, tone: "low" });
    }
  }
  if (scores.overall > 0 && scores.overall < 0.7) {
    alerts.push({ title: "Memo quality below bar", detail: `overall ${scores.overall.toFixed(2)}`, tone: "low" });
  }

  const card = (children: React.ReactNode, extra: React.CSSProperties = {}) => (
    <div style={{
      background: Q.card, borderRadius: Q.r, boxShadow: Q.shadow, border: `1px solid ${Q.border}`,
      overflow: 'hidden', position: 'relative', padding: 20, backdropFilter: 'blur(18px)', ...extra,
    }}>
      {children}
    </div>
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14, fontFamily: Q.sans }}>
      {card(
        <>
          <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 2, background: `linear-gradient(90deg, ${Q.accent}, ${Q.cyan})` }}/>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
            <div>
              <div style={{ fontSize: 14, fontWeight: 700, color: Q.ink, letterSpacing: '-0.01em' }}>Market Pulse</div>
              <div style={{ fontSize: 11, color: Q.muted, marginTop: 3 }}>Signal health · risk · alpha</div>
            </div>
            {!metrics && (
              <span style={{ fontSize: 10, color: Q.muted, background: Q.faint, border: `1px solid ${Q.borderFaint}`, borderRadius: Q.rpill, padding: '3px 9px' }}>
                waiting for run
              </span>
            )}
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 8 }}>
            {[
              { label: "Confidence", meta: confidence },
              { label: "Risk", meta: risk },
              { label: "Edge", meta: edge },
            ].map(item => (
              <div key={item.label} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 12px', borderRadius: 12, background: Q.cardInner, border: `1px solid ${Q.borderFaint}` }}>
                <span style={{ fontSize: 12, color: Q.sub }}>{item.label}</span>
                <span style={{ fontSize: 11, fontWeight: 700, color: item.meta.color, background: item.meta.bg, border: `1px solid ${item.meta.border}`, borderRadius: Q.rpill, padding: '2px 10px' }}>
                  {item.meta.label}
                </span>
              </div>
            ))}
          </div>
          {metrics && (
            <div style={{ marginTop: 12, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              {[
                { label: "Sharpe", value: metrics.sharpe.toFixed(2) },
                { label: "Alpha", value: `${(metrics.alpha * 100).toFixed(2)}%` },
                { label: "Drawdown", value: `${(drawdownAbs * 100).toFixed(1)}%` },
                { label: "Win rate", value: `${(metrics.win_rate * 100).toFixed(1)}%` },
              ].map(item => (
                <div key={item.label} style={{ background: Q.cardInner, border: `1px solid ${Q.borderFaint}`, borderRadius: 12, padding: '10px 12px' }}>
                  <div style={{ fontSize: 9, color: Q.muted, letterSpacing: '0.08em', textTransform: 'uppercase', fontWeight: 700 }}>{item.label}</div>
                  <div style={{ fontSize: 13, color: Q.ink, fontFamily: Q.mono, fontWeight: 700, marginTop: 4 }}>{item.value}</div>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {card(
        <>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
            <div>
              <div style={{ fontSize: 14, fontWeight: 700, color: Q.ink, letterSpacing: '-0.01em' }}>Alert Feed</div>
              <div style={{ fontSize: 11, color: Q.muted, marginTop: 3 }}>CoinQuant-style signals</div>
            </div>
            <span style={{ fontSize: 10, color: Q.cyan, background: Q.cyanLt, border: `1px solid ${Q.border}`, borderRadius: Q.rpill, padding: '3px 9px' }}>
              realtime
            </span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {(alerts.length ? alerts : [{ title: "No active alerts", detail: "Run a strategy to populate signals.", tone: "low" as const }]).map((alert, idx) => {
              const tone = alert.tone === "high" ? { c: Q.red, bg: Q.redBg, b: Q.redBd }
                : alert.tone === "medium" ? { c: Q.amber, bg: Q.amberBg, b: Q.amberBd }
                  : { c: Q.blue, bg: `${Q.blue}20`, b: `${Q.blue}40` };
              return (
                <div key={`${alert.title}-${idx}`} style={{ background: Q.cardInner, border: `1px solid ${Q.borderFaint}`, borderRadius: 12, padding: '10px 12px', display: 'flex', justifyContent: 'space-between', gap: 10 }}>
                  <div>
                    <div style={{ fontSize: 12, color: Q.ink, fontWeight: 600 }}>{alert.title}</div>
                    <div style={{ fontSize: 10, color: Q.muted, marginTop: 4 }}>{alert.detail}</div>
                  </div>
                  <span style={{ fontSize: 10, fontWeight: 700, color: tone.c, background: tone.bg, border: `1px solid ${tone.b}`, borderRadius: Q.rpill, padding: '2px 8px', height: 18 }}>
                    {alert.tone}
                  </span>
                </div>
              );
            })}
          </div>
        </>
      )}
      {card(
        <>
          <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 2, background: `linear-gradient(90deg, ${Q.cyan}, ${Q.accent})` }}/>
          <div style={{ fontSize: 14, fontWeight: 700, color: Q.ink, marginBottom: 14, letterSpacing: '-0.01em', marginTop: 4 }}>Eval Scores</div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 14 }}>
            <ScoreTile label="Faithfulness"  desc="Claims match data"    value={scores.faithfulness      || 0}/>
            <ScoreTile label="Stats"         desc="p-value & CI correct" value={scores.stats_correctness || 0}/>
            <ScoreTile label="Grounded"      desc="No hallucination"     value={scores.hallucination     || 0}/>
            <ScoreTile label="Risk Caveats"  desc="≥3 risk factors"      value={scores.risk_caveats      || 0}/>
          </div>

          <div style={{ borderTop: `1px solid ${Q.border}`, paddingTop: 14 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <span style={{ fontSize: 12, fontWeight: 700, color: Q.ink }}>Overall</span>
              <span style={{
                fontSize: 26, fontFamily: Q.mono, fontWeight: 800,
                color: scores.overall >= 0.7 ? Q.green : scores.overall >= 0.4 ? Q.amber : Q.muted,
                textShadow: scores.overall >= 0.7 ? `0 0 24px ${Q.green}60` : scores.overall >= 0.4 ? `0 0 24px ${Q.amber}60` : 'none',
              }}>{scores.overall === 0 ? '—' : scores.overall.toFixed(2)}</span>
            </div>
            <div style={{ height: 5, background: 'rgba(255,255,255,0.05)', borderRadius: 99 }}>
              <div style={{
                height: 5, borderRadius: 99, width: `${(scores.overall || 0) * 100}%`,
                background: scores.overall >= 0.7
                  ? `linear-gradient(90deg, ${Q.green}70, ${Q.green})`
                  : scores.overall >= 0.4
                    ? `linear-gradient(90deg, ${Q.amber}70, ${Q.amber})`
                    : Q.muted,
                transition: 'width 0.8s ease',
                boxShadow: scores.overall > 0 ? `0 0 10px ${scores.overall >= 0.7 ? Q.green : Q.amber}50` : 'none',
              }}/>
            </div>
            {scores.overall > 0 && (
              <div style={{
                marginTop: 10, padding: '6px 12px', borderRadius: 8, textAlign: 'center', fontSize: 11, fontWeight: 600,
                background: scores.overall >= 0.7 ? Q.greenBg : Q.amberBg,
                border: `1px solid ${scores.overall >= 0.7 ? Q.greenBd : Q.amberBd}`,
                color: scores.overall >= 0.7 ? Q.green : Q.amber,
              }}>
                {scores.overall >= 0.7 ? '✓ Meets quality threshold (≥ 0.70)' : '⚠ Below threshold — revision may trigger'}
              </div>
            )}
          </div>
        </>
      )}

      {card(
        <>
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 12 }}>
            <div>
              <div style={{ fontSize: 14, fontWeight: 700, color: Q.ink, letterSpacing: '-0.01em' }}>Self-Improvement</div>
              <div style={{ fontSize: 11, color: Q.muted, marginTop: 3 }}>Eval score · nightly DSPy optimisation</div>
            </div>
            {isDemo && (
              <span style={{ fontSize: 10, color: Q.muted, background: Q.faint, border: `1px solid ${Q.borderFaint}`, borderRadius: Q.rpill, padding: '3px 9px', marginTop: 2 }}>demo</span>
            )}
          </div>
          <ImprovementLine data={scoreVals}/>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 8, fontSize: 10, fontFamily: Q.mono, color: Q.muted }}>
            <span>run 1</span>
            <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <span style={{ width: 12, height: 2, background: Q.accentBright, display: 'inline-block', borderRadius: 1 }}/>overall
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <span style={{ width: 10, height: 1, background: Q.green, display: 'inline-block', borderRadius: 1, opacity: 0.6 }}/>0.70
              </span>
            </div>
            <span>run {pts.length}</span>
          </div>
        </>
      )}
    </div>
  );
}
