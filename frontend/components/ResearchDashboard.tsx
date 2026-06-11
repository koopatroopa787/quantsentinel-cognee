"use client";

import React, { useState } from "react";
import { Q, MetricCard, ScoreRow, EquityChart, PValueBar, CIBar } from "./DesignTokens";
import type { SeriesPoint } from "./DesignTokens";

export type RunMetrics = {
  ticker: string;
  start_date: string;
  end_date: string;
  total_return: number;
  benchmark_total_return: number;
  alpha: number;
  sharpe: number;
  max_drawdown: number;
  win_rate: number;
  num_trades: number;
  t_statistic: number;
  p_value: number;
  significant_at_5pct: boolean;
  bootstrap_lower: number;
  bootstrap_upper: number;
  bootstrap_mean: number;
  series: SeriesPoint[];
};

export type Scores = {
  faithfulness: number;
  stats_correctness: number;
  hallucination: number;
  risk_caveats: number;
  overall: number;
};

export type Suggestion = {
  title: string;
  rationale: string;
  new_hypothesis: string;
  priority: 'high' | 'medium' | 'low';
};

// ── Memo renderer ─────────────────────────────────────────────────────────────
function MemoText({ memo }: { memo: string }) {
  const SEC: Record<string, string> = {
    '1. HYPOTHESIS':           Q.accentBright,
    '2. DATA SOURCES':         Q.green,
    '3. METHODOLOGY':          Q.cyan,
    '4. RESULTS':              Q.amber,
    '5. STATISTICAL ANALYSIS': Q.accentBright,
    '6. RISK CAVEATS':         Q.red,
    '7. CONCLUSION':           Q.blue,
    '8. DISCLAIMER':           Q.muted,
  };
  return (
    <div>
      {memo.split('\n').map((line, i) => {
        const t = line.trim();
        const hdr = Object.keys(SEC).find(h => t.startsWith(h));
        if (hdr) return (
          <div key={i} style={{ marginTop: 16 }}>
            <span style={{
              fontSize: 10, fontWeight: 700, letterSpacing: '0.07em', textTransform: 'uppercase',
              color: SEC[hdr], background: `${SEC[hdr]}14`,
              border: `1px solid ${SEC[hdr]}30`,
              padding: '3px 9px', borderRadius: 5, fontFamily: Q.sans,
            }}>{t}</span>
          </div>
        );
        if (t.startsWith('- ')) return (
          <div key={i} style={{ display: 'flex', gap: 8, padding: '2px 0' }}>
            <span style={{ color: Q.accentBright, fontSize: 12, marginTop: 3, flexShrink: 0 }}>•</span>
            <span style={{ fontSize: 12, color: Q.sub, lineHeight: 1.7, fontFamily: Q.sans }}>{t.slice(2)}</span>
          </div>
        );
        if (t === '') return <div key={i} style={{ height: 5 }}/>;
        const kv = t.match(/^([a-zA-Z_\s]+):\s*(.+)$/);
        if (kv) return (
          <div key={i} style={{ display: 'flex', gap: 12, padding: '3px 0', alignItems: 'baseline' }}>
            <span style={{ fontSize: 11, color: Q.muted, minWidth: 140, fontFamily: Q.sans }}>{kv[1]}</span>
            <span style={{ fontSize: 12, color: Q.cyan, fontFamily: Q.mono, fontWeight: 600 }}>{kv[2]}</span>
          </div>
        );
        return <p key={i} style={{ fontSize: 12, color: Q.sub, lineHeight: 1.75, margin: '2px 0', fontFamily: Q.sans }}>{t}</p>;
      })}
    </div>
  );
}

// ── Research Dashboard ────────────────────────────────────────────────────────
export default function ResearchDashboard({
  metrics, scores, memo, suggestion, traceUrl, onRunSuggestion,
}: {
  metrics: RunMetrics;
  scores: Scores;
  memo: string;
  suggestion: Suggestion | null;
  traceUrl: string | null;
  onRunSuggestion?: (h: string) => void;
}) {
  const [chartMode, setChartMode] = useState('equity');
  const [memoOpen, setMemoOpen] = useState(false);

  const pct = (v: number) => `${(v * 100).toFixed(2)}%`;
  const fmt = (v: number, d = 4) => v.toFixed(d);
  const cv = (v: number, lo = 0, mid = 0.5, flip = false) => {
    if (flip) v = 1 - v;
    return v >= mid ? Q.green : v >= lo ? Q.amber : Q.red;
  };

  const retColor  = cv(metrics.total_return, 0, 0.1);
  const sharpeCol = metrics.sharpe >= 1 ? Q.green : metrics.sharpe >= 0.5 ? Q.amber : Q.red;
  const ddColor   = cv(Math.abs(metrics.max_drawdown), 0.3, 0.15, true);
  const wrColor   = cv(metrics.win_rate, 0.4, 0.55);
  const alphaCol  = (metrics.alpha ?? 0) >= 0 ? Q.green : Q.red;
  const sharpeRating = metrics.sharpe >= 1.5 ? 'Excellent' : metrics.sharpe >= 1 ? 'Good' : metrics.sharpe >= 0.5 ? 'Moderate' : 'Weak';

  const card = (children: React.ReactNode, extra: React.CSSProperties = {}) => (
    <div style={{
      background: Q.card, borderRadius: Q.r, boxShadow: Q.shadow, border: `1px solid ${Q.border}`,
      position: 'relative', overflow: 'hidden', backdropFilter: 'blur(18px)', ...extra,
    }}>
      {children}
    </div>
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14, fontFamily: Q.sans }}>

      {/* Report header */}
      {card(
        <>
          <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 2, background: `linear-gradient(90deg, ${Q.accent}, ${Q.cyan}, ${Q.accentBright})` }}/>
          <div style={{ padding: '14px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{ width: 40, height: 40, borderRadius: 12, background: Q.accentLt, border: `1px solid ${Q.border}`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                  <path d="M3 14 L7 9 L11 12 L15 6 L18 9" stroke={Q.accentBright} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
                  <circle cx="18" cy="9" r="1.5" fill={Q.accentBright}/>
                </svg>
              </div>
              <div>
                <div style={{ fontSize: 15, fontWeight: 700, color: Q.ink, letterSpacing: '-0.01em' }}>Research Report</div>
                <div style={{ fontSize: 11, color: Q.muted, fontFamily: Q.mono }}>Completed multi-agent analysis</div>
              </div>
              <span style={{ fontSize: 11, fontWeight: 700, color: Q.accentBright, background: Q.accentLt, border: `1px solid ${Q.border}`, borderRadius: Q.rpill, padding: '4px 12px', fontFamily: Q.mono }}>
                {metrics.ticker} · {metrics.start_date.slice(0,4)}–{metrics.end_date.slice(0,4)}
              </span>
            </div>
            {traceUrl && (
              <a href={traceUrl} target="_blank" rel="noopener noreferrer" style={{
                fontSize: 12, color: Q.cyan, background: Q.cyanLt,
                border: `1px solid rgba(96,108,56,0.4)`, borderRadius: Q.rpill,
                padding: '6px 14px', textDecoration: 'none', fontWeight: 600,
              }}>Phoenix Trace ↗</a>
            )}
          </div>
        </>
      )}

      {/* 6 Metric cards */}
      <div style={{ display: 'flex', gap: 10 }}>
        <MetricCard label="Strategy Return"  value={pct(metrics.total_return)}               sub={`${metrics.num_trades} trades`}          color={retColor}/>
        <MetricCard label="Benchmark B&H"    value={pct(metrics.benchmark_total_return ?? 0)} sub={`${metrics.ticker} buy & hold`}          color={Q.sub}/>
        <MetricCard label="Alpha vs B&H"     value={pct(metrics.alpha ?? 0)}                  sub={(metrics.alpha??0)>=0?'✓ Beat':'✗ Lagged'} color={alphaCol}/>
        <MetricCard label="Sharpe Ratio"     value={fmt(metrics.sharpe)}                      sub={sharpeRating}                            color={sharpeCol}/>
        <MetricCard label="Max Drawdown"     value={pct(metrics.max_drawdown)}                sub="% from peak"                             color={ddColor}/>
        <MetricCard label="Win Rate"         value={pct(metrics.win_rate)}                    sub="of held days"                            color={wrColor}/>
      </div>

      {/* Equity chart */}
      {card(
        <div style={{ padding: '18px 22px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
            <div>
              <div style={{ fontSize: 14, fontWeight: 700, color: Q.ink }}>
                {chartMode === 'equity' ? 'Equity Curve vs Benchmark' : 'Drawdown from Peak'}
              </div>
              <div style={{ fontSize: 11, color: Q.muted, marginTop: 2, fontFamily: Q.mono }}>
                {chartMode === 'equity' ? 'Strategy (amber glow) vs Buy & Hold (gray dashed)' : 'Percentage decline from rolling peak'}
              </div>
            </div>
            <div style={{ display: 'flex', gap: 6 }}>
              {['equity','drawdown'].map(tab => (
                <button key={tab} onClick={() => setChartMode(tab)} style={{
                  fontSize: 11, fontWeight: 600, padding: '6px 14px', borderRadius: Q.rpill,
                  cursor: 'pointer', textTransform: 'capitalize', border: 'none',
                  background: chartMode === tab ? Q.accentLt : Q.faint,
                  color: chartMode === tab ? Q.accentBright : Q.muted,
                  outline: chartMode === tab ? `1px solid ${Q.border}` : 'none',
                  boxShadow: chartMode === tab ? `0 0 14px ${Q.accentGlow}40` : 'none',
                  fontFamily: Q.sans, transition: 'all 0.2s',
                }}>{tab}</button>
              ))}
            </div>
          </div>
          <EquityChart series={metrics.series} mode={chartMode}/>
          <div style={{ display: 'flex', gap: 16, marginTop: 10, justifyContent: 'flex-end' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: Q.sub }}>
              <span style={{ width: 18, height: 2, background: Q.accentBright, display: 'inline-block', borderRadius: 1, boxShadow: `0 0 6px ${Q.accentBright}` }}/>
              Strategy
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: Q.muted }}>
              <span style={{ width: 18, height: 1.5, background: Q.sub, display: 'inline-block', borderRadius: 1, opacity: 0.4 }}/>
              Benchmark
            </span>
          </div>
        </div>
      )}

      {/* Stats + Memo Quality */}
      <div style={{ display: 'flex', gap: 14 }}>
        {card(
          <div style={{ padding: '18px 22px', display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div style={{ fontSize: 14, fontWeight: 700, color: Q.ink }}>Statistical Analysis</div>
            <PValueBar p={metrics.p_value} significant={metrics.significant_at_5pct}/>
            <CIBar lower={metrics.bootstrap_lower} upper={metrics.bootstrap_upper} mean={metrics.bootstrap_mean}/>
            <div style={{ display: 'flex', gap: 10 }}>
              {([
                ['t-stat',  metrics.t_statistic.toFixed(4), Q.cyan],
                ['Sharpe',  metrics.sharpe.toFixed(4),      sharpeCol],
                ['Trades',  metrics.num_trades.toString(),  Q.sub],
              ] as [string, string, string][]).map(([lbl, val, col]) => (
                <div key={lbl} style={{ flex: 1, background: Q.cardInner, border: `1px solid ${Q.borderFaint}`, borderRadius: 10, padding: '10px 12px' }}>
                  <div style={{ fontSize: 9, color: Q.muted, marginBottom: 5, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em' }}>{lbl}</div>
                  <div style={{ fontSize: 16, fontWeight: 700, fontFamily: Q.mono, color: col }}>{val}</div>
                </div>
              ))}
            </div>
          </div>,
          { flex: '1.4' }
        )}
        {card(
          <div style={{ padding: '18px 22px' }}>
            <div style={{ fontSize: 14, fontWeight: 700, color: Q.ink, marginBottom: 14 }}>Memo Quality</div>
            <ScoreRow label="Faithfulness"     value={scores.faithfulness}/>
            <ScoreRow label="Stats Correctness" value={scores.stats_correctness}/>
            <ScoreRow label="No Hallucination" value={scores.hallucination}/>
            <ScoreRow label="Risk Coverage"    value={scores.risk_caveats}/>
            <div style={{
              marginTop: 12, padding: '8px 12px', borderRadius: 8, textAlign: 'center',
              fontSize: 11, fontWeight: 600,
              background: scores.overall >= 0.7 ? Q.greenBg : Q.amberBg,
              border: `1px solid ${scores.overall >= 0.7 ? Q.greenBd : Q.amberBd}`,
              color: scores.overall >= 0.7 ? Q.green : Q.amber,
            }}>Overall {scores.overall.toFixed(2)} {scores.overall >= 0.7 ? '✓' : '⚠'}</div>
          </div>,
          { flex: '1' }
        )}
      </div>

      {/* AI Suggestion */}
      {suggestion && card(
        <div style={{ padding: '18px 22px', display: 'flex', alignItems: 'flex-start', gap: 18 }}>
          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
              <span style={{
                fontSize: 10, fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase',
                color:      suggestion.priority === 'high' ? Q.red : suggestion.priority === 'medium' ? Q.amber : Q.blue,
                background: suggestion.priority === 'high' ? Q.redBg : suggestion.priority === 'medium' ? Q.amberBg : 'rgba(96,165,250,0.10)',
                border:     `1px solid ${suggestion.priority === 'high' ? Q.redBd : suggestion.priority === 'medium' ? Q.amberBd : 'rgba(96,165,250,0.25)'}`,
                borderRadius: Q.rpill, padding: '3px 10px',
              }}>{suggestion.priority} priority</span>
              <span style={{ fontSize: 11, color: Q.muted, fontStyle: 'italic' }}>tested strategies auto-skipped</span>
            </div>
            <div style={{ fontSize: 15, fontWeight: 700, color: Q.ink, marginBottom: 8 }}>{suggestion.title}</div>
            <p style={{ fontSize: 12, color: Q.sub, lineHeight: 1.65, margin: '0 0 12px' }}>{suggestion.rationale}</p>
            <div style={{
              background: Q.cardInner, border: `1px solid ${Q.border}`,
              borderLeft: `3px solid ${Q.accent}`,
              borderRadius: '0 10px 10px 0',
              padding: '10px 14px', fontSize: 12, color: Q.sub, fontStyle: 'italic', lineHeight: 1.55,
              boxShadow: `inset 0 0 20px ${Q.accentGlow}08`,
            }}>
              💡 &ldquo;{suggestion.new_hypothesis}&rdquo;
            </div>
          </div>
          {onRunSuggestion && (
            <button onClick={() => onRunSuggestion(suggestion.new_hypothesis)} style={{
              flexShrink: 0, padding: '11px 20px', borderRadius: Q.rpill, border: 'none', cursor: 'pointer',
              background: `linear-gradient(135deg, ${Q.accent}, #bc6c25)`,
              color: '#1a2310', fontSize: 12, fontWeight: 700, fontFamily: Q.sans,
              boxShadow: `0 4px 20px ${Q.accentGlow}`, whiteSpace: 'nowrap', transition: 'all 0.2s',
            }}
              onMouseEnter={e => (e.currentTarget as HTMLElement).style.boxShadow = `0 6px 28px ${Q.accentGlow}`}
              onMouseLeave={e => (e.currentTarget as HTMLElement).style.boxShadow = `0 4px 20px ${Q.accentGlow}`}
            >⚡ Run This Instead →</button>
          )}
        </div>
      )}

      {/* Research Memo */}
      {card(
        <div>
          <button onClick={() => setMemoOpen(v => !v)} style={{
            width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            padding: '16px 22px', background: 'none', border: 'none', cursor: 'pointer', fontFamily: Q.sans,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: memoOpen ? Q.cyan : Q.muted, display: 'inline-block', boxShadow: memoOpen ? `0 0 8px ${Q.cyan}` : 'none' }}/>
              <span style={{ fontSize: 14, fontWeight: 700, color: Q.ink }}>Full Research Memo</span>
            </div>
            <span style={{ fontSize: 11, color: Q.muted, background: Q.faint, border: `1px solid ${Q.borderFaint}`, borderRadius: Q.rpill, padding: '4px 12px' }}>
              {memoOpen ? '▲ collapse' : '▼ expand'}
            </span>
          </button>
          {memoOpen && memo && (
            <div style={{ padding: '0 22px 22px', maxHeight: 480, overflowY: 'auto' }}>
              <div style={{ height: 1, background: Q.border, marginBottom: 16 }}/>
              <MemoText memo={memo}/>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
