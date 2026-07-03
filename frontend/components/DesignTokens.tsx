"use client";

import React, { useState } from "react";

// Design tokens — v3 QuantSentinel palette
export const Q = {
  bg:           '#050505',
  card:         'rgba(12,12,12,0.9)',
  cardInner:    'rgba(8,8,8,0.95)',
  border:       'rgba(255,255,255,0.10)',
  borderFaint:  'rgba(255,255,255,0.06)',
  shadow:       '0 12px 36px rgba(0,0,0,0.55)',
  shadowHi:     '0 22px 60px rgba(0,0,0,0.7)',
  accent:       '#f2f2f2',
  accentLt:     'rgba(255,255,255,0.08)',
  accentBright: '#ffffff',
  accentGlow:   'rgba(255,255,255,0.35)',
  cyan:         '#d4d4d4',
  cyanLt:       'rgba(255,255,255,0.08)',
  cyanGlow:     'rgba(255,255,255,0.2)',
  ink:          '#f5f5f5',
  sub:          'rgba(245,245,245,0.7)',
  muted:        'rgba(245,245,245,0.45)',
  faint:        'rgba(245,245,245,0.08)',
  green:        '#f5f5f5',
  greenBg:      'rgba(255,255,255,0.08)',
  greenBd:      'rgba(255,255,255,0.22)',
  amber:        '#cfcfcf',
  amberBg:      'rgba(255,255,255,0.06)',
  amberBd:      'rgba(255,255,255,0.18)',
  red:          '#bdbdbd',
  redBg:        'rgba(255,255,255,0.06)',
  redBd:        'rgba(255,255,255,0.18)',
  blue:         '#e0e0e0',
  r:            '16px',
  rsm:          '10px',
  rpill:        '999px',
  sans:         "'Inter', system-ui, sans-serif",
  mono:         "'JetBrains Mono', 'IBM Plex Mono', monospace",
} as const;

export const AGENTS: Record<string, { label: string; color: string; icon: string }> = {
  orchestrator:               { label: 'Orchestrator', color: '#ffffff', icon: '⬡' },
  quantsentinel_orchestrator: { label: 'Orchestrator', color: '#ffffff', icon: '⬡' },
  data_agent:                 { label: 'Data Agent',   color: '#d9d9d9', icon: '◈' },
  backtester_agent:           { label: 'Backtester',   color: '#bfbfbf', icon: '◉' },
  statistician_agent:         { label: 'Statistician', color: '#a6a6a6', icon: '◆' },
  critic_agent:               { label: 'Critic',       color: '#cfcfcf', icon: '✦' },
  system:                     { label: 'System',       color: 'rgba(245,245,245,0.4)', icon: '▸' },
  cognee_memory:              { label: 'Cognee Memory', color: '#a5b4fc',              icon: '◎' },
};

// ── Arc math ──────────────────────────────────────────────────────────────────
function polar(cx: number, cy: number, r: number, deg: number): [number, number] {
  const rad = (deg * Math.PI) / 180;
  return [cx + r * Math.cos(rad), cy + r * Math.sin(rad)];
}
function arcD(cx: number, cy: number, r: number, startDeg: number, sweepDeg: number): string {
  if (sweepDeg >= 360) sweepDeg = 359.99;
  const [sx, sy] = polar(cx, cy, r, startDeg);
  const [ex, ey] = polar(cx, cy, r, startDeg + sweepDeg);
  return `M ${sx.toFixed(2)} ${sy.toFixed(2)} A ${r} ${r} 0 ${sweepDeg > 180 ? 1 : 0} 1 ${ex.toFixed(2)} ${ey.toFixed(2)}`;
}

// ── Arc Gauge ─────────────────────────────────────────────────────────────────
export function ArcGauge({ value = 0, size = 74 }: { value?: number; size?: number }) {
  const cx = size / 2, cy = size / 2, r = size / 2 - 9;
  const START = 150, SWEEP = 240;
  const fill = Math.max(0.008, value * SWEEP);
  const color = value >= 0.7 ? Q.green : value >= 0.4 ? Q.amber : value > 0 ? Q.red : Q.muted;
  const uid = `ag${size}`;
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ overflow: 'visible' }}>
      <defs>
        <filter id={uid}>
          <feGaussianBlur stdDeviation="2.5" result="blur"/>
          <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
        </filter>
      </defs>
      <path d={arcD(cx, cy, r, START, SWEEP)} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={6} strokeLinecap="round"/>
      <path d={arcD(cx, cy, r, START, fill)} fill="none" stroke={color} strokeWidth={6} strokeLinecap="round"
        filter={value > 0 ? `url(#${uid})` : undefined}
        style={{ transition: 'all 0.7s ease' }}/>
      <text x={cx} y={cy + 2} textAnchor="middle" dominantBaseline="middle"
        fill={value > 0 ? color : Q.muted} fontSize={size * 0.2} fontWeight="700" fontFamily={Q.mono}>
        {value === 0 ? '—' : value.toFixed(2)}
      </text>
    </svg>
  );
}

// ── Metric card ───────────────────────────────────────────────────────────────
export function MetricCard({ label, value, sub, color, detail }: {
  label: string; value: string; sub?: string; color?: string; detail?: string;
}) {
  return (
    <div style={{
      flex: 1, minWidth: 0,
      background: Q.card, borderRadius: 14,
      padding: '14px 16px',
      border: `1px solid ${Q.border}`,
      boxShadow: Q.shadow,
      position: 'relative', overflow: 'hidden',
    }}>
      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 2, background: `linear-gradient(90deg, transparent, ${color || Q.accent}80, transparent)` }}/>
      <div style={{ fontSize: 9, fontWeight: 600, color: Q.muted, letterSpacing: '0.09em', textTransform: 'uppercase', marginBottom: 8, fontFamily: Q.sans }}>{label}</div>
      <div style={{ fontSize: 22, fontWeight: 700, fontFamily: Q.mono, color: color || Q.ink, lineHeight: 1, marginBottom: 4 }}>{value}</div>
      {sub && <div style={{ fontSize: 11, color: Q.sub, fontFamily: Q.sans }}>{sub}</div>}
      {detail && <div style={{ fontSize: 10, color: Q.muted, marginTop: 2, fontFamily: Q.sans }}>{detail}</div>}
    </div>
  );
}

// ── Score row ─────────────────────────────────────────────────────────────────
export function ScoreRow({ label, value }: { label: string; value: number }) {
  const color = value >= 0.7 ? Q.green : value >= 0.4 ? Q.amber : value > 0 ? Q.red : Q.muted;
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
        <span style={{ fontSize: 12, color: Q.sub, fontWeight: 500, fontFamily: Q.sans }}>{label}</span>
        <span style={{ fontSize: 12, fontFamily: Q.mono, color, fontWeight: 700 }}>{value === 0 ? '—' : value.toFixed(2)}</span>
      </div>
      <div style={{ height: 4, background: 'rgba(255,255,255,0.05)', borderRadius: 99 }}>
        <div style={{
          height: 4, width: `${value * 100}%`,
          background: `linear-gradient(90deg, ${color}80, ${color})`,
          borderRadius: 99, transition: 'width 0.7s ease',
          boxShadow: value > 0 ? `0 0 8px ${color}60` : 'none',
        }}/>
      </div>
    </div>
  );
}

// ── Agent badge ───────────────────────────────────────────────────────────────
export function AgentBadge({ agent }: { agent: string }) {
  const m = AGENTS[agent] || { label: agent, color: Q.sub, icon: '·' };
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 6,
      fontSize: 10, fontWeight: 700, letterSpacing: '0.02em',
      color: m.color, background: `${m.color}18`,
      border: `1px solid ${m.color}30`,
      borderRadius: Q.rpill, padding: '4px 11px', fontFamily: Q.sans,
    }}>
      <span style={{ width: 6, height: 6, borderRadius: '50%', background: m.color, boxShadow: `0 0 6px ${m.color}`, flexShrink: 0, display: 'inline-block' }}/>
      {m.label}
    </span>
  );
}

// ── Equity chart ──────────────────────────────────────────────────────────────
export type SeriesPoint = { date: string; equity: number; benchmark: number; drawdown: number };

export function EquityChart({ series = [], mode = 'equity' }: { series?: SeriesPoint[]; mode?: string }) {
  if (!series.length) return null;
  const W = 400, H = 160;
  const [hover, setHover] = useState<number | null>(null);
  const count = series.length;
  const denom = Math.max(count - 1, 1);
  const xAt = (i: number) => (i / denom) * W;
  const scaleY = (v: number, mn: number, mx: number) => {
    const rng = mx - mn || 1;
    return H - 4 - ((v - mn) / rng) * (H - 16);
  };
  const handleMove = (event: React.MouseEvent<SVGSVGElement>) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const idx = Math.round((x / rect.width) * denom);
    const clamped = Math.max(0, Math.min(count - 1, idx));
    setHover(clamped);
  };
  const handleLeave = () => setHover(null);
  const hoverPoint = hover === null ? null : series[hover];
  const hoverX = hover === null ? 0 : xAt(hover);
  const fmt = (v: number, d = 2) => v.toFixed(d);
  const gridYs = [0.2, 0.4, 0.6, 0.8].map(t => (4 + (1 - t) * (H - 16)).toFixed(1));

  if (mode === 'equity') {
    const eqData = series.map(s => s.equity), bnData = series.map(s => s.benchmark);
    const all = [...eqData, ...bnData], mn = Math.min(...all), mx = Math.max(...all);
    const eqPts = eqData.map((v, i) => ({ x: xAt(i), y: scaleY(v, mn, mx) }));
    const bnPts = bnData.map((v, i) => ({ x: xAt(i), y: scaleY(v, mn, mx) }));
    const eqLine = eqPts.map(p => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ');
    const bnLine = bnPts.map(p => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ');
    const area = `0,${H} ${eqLine} ${W},${H} Z`;
    const hoverEq = hover === null ? null : eqPts[hover];
    const hoverBn = hover === null ? null : bnPts[hover];
    return (
      <div style={{ position: 'relative' }}>
        <svg
          viewBox={`0 0 ${W} ${H}`}
          preserveAspectRatio="none"
          style={{ width: '100%', height: 200, cursor: 'crosshair' }}
          onMouseMove={handleMove}
          onMouseLeave={handleLeave}
        >
          <defs>
            <linearGradient id="gEq3" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={Q.accent} stopOpacity="0.3"/>
              <stop offset="75%" stopColor={Q.accent} stopOpacity="0.04"/>
              <stop offset="100%" stopColor={Q.accent} stopOpacity="0"/>
            </linearGradient>
            <filter id="eqGlow3">
              <feGaussianBlur stdDeviation="3" result="blur"/>
              <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
            </filter>
          </defs>
          {gridYs.map((y, i) => <line key={i} x1="0" y1={y} x2={W} y2={y} stroke="rgba(255,255,255,0.04)" strokeWidth="1"/>)}
          <polygon points={area} fill="url(#gEq3)"/>
          <polyline points={bnLine} fill="none" stroke="rgba(148,163,184,0.25)" strokeWidth="1.2" strokeDasharray="5 3"/>
          <polyline points={eqLine} fill="none" stroke={Q.accentBright} strokeWidth="4" opacity="0.18"/>
          <polyline points={eqLine} fill="none" stroke={Q.accentBright} strokeWidth="2" filter="url(#eqGlow3)"/>
          {hover !== null && hoverEq && hoverBn && (
            <>
              <line x1={hoverX.toFixed(1)} y1="0" x2={hoverX.toFixed(1)} y2={H} stroke={Q.borderFaint} strokeWidth="1"/>
              <circle cx={hoverEq.x.toFixed(1)} cy={hoverEq.y.toFixed(1)} r="4" fill={Q.accentBright} stroke={Q.accent} strokeWidth="1.2"/>
              <circle cx={hoverBn.x.toFixed(1)} cy={hoverBn.y.toFixed(1)} r="3" fill="rgba(148,163,184,0.9)" stroke="rgba(148,163,184,0.6)" strokeWidth="1"/>
            </>
          )}
        </svg>
        {hoverPoint && (
          <div style={{
            position: 'absolute', top: 10, right: 12, background: Q.cardInner,
            border: `1px solid ${Q.borderFaint}`, borderRadius: 10, padding: '8px 10px',
            fontSize: 10, color: Q.sub, fontFamily: Q.mono, boxShadow: Q.shadow,
          }}>
            <div style={{ fontSize: 11, color: Q.ink, fontWeight: 700 }}>{hoverPoint.date}</div>
            <div style={{ marginTop: 4 }}>Equity: {fmt(hoverPoint.equity)}</div>
            <div>Bench: {fmt(hoverPoint.benchmark)}</div>
            <div>Drawdown: {(hoverPoint.drawdown * 100).toFixed(1)}%</div>
          </div>
        )}
      </div>
    );
  } else {
    const ddData = series.map(s => s.drawdown);
    const mn = Math.min(...ddData), mx = Math.max(...ddData);
    const ddPts = ddData.map((v, i) => ({ x: xAt(i), y: scaleY(v, mn, mx) }));
    const ddLine = ddPts.map(p => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ');
    const ddArea = `0,${H} ${ddLine} ${W},${H} Z`;
    const hoverDd = hover === null ? null : ddPts[hover];
    return (
      <div style={{ position: 'relative' }}>
        <svg
          viewBox={`0 0 ${W} ${H}`}
          preserveAspectRatio="none"
          style={{ width: '100%', height: 200, cursor: 'crosshair' }}
          onMouseMove={handleMove}
          onMouseLeave={handleLeave}
        >
          <defs>
            <linearGradient id="gDd3" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={Q.red} stopOpacity="0.22"/>
              <stop offset="100%" stopColor={Q.red} stopOpacity="0"/>
            </linearGradient>
            <filter id="ddGlow3">
              <feGaussianBlur stdDeviation="2.5" result="blur"/>
              <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
            </filter>
          </defs>
          {gridYs.map((y, i) => <line key={i} x1="0" y1={y} x2={W} y2={y} stroke="rgba(255,255,255,0.04)" strokeWidth="1"/>)}
          <polygon points={ddArea} fill="url(#gDd3)"/>
          <polyline points={ddLine} fill="none" stroke={Q.red} strokeWidth="2" filter="url(#ddGlow3)"/>
          {hover !== null && hoverDd && (
            <>
              <line x1={hoverX.toFixed(1)} y1="0" x2={hoverX.toFixed(1)} y2={H} stroke={Q.borderFaint} strokeWidth="1"/>
              <circle cx={hoverDd.x.toFixed(1)} cy={hoverDd.y.toFixed(1)} r="4" fill={Q.red} stroke={Q.redBd} strokeWidth="1.2"/>
            </>
          )}
        </svg>
        {hoverPoint && (
          <div style={{
            position: 'absolute', top: 10, right: 12, background: Q.cardInner,
            border: `1px solid ${Q.borderFaint}`, borderRadius: 10, padding: '8px 10px',
            fontSize: 10, color: Q.sub, fontFamily: Q.mono, boxShadow: Q.shadow,
          }}>
            <div style={{ fontSize: 11, color: Q.ink, fontWeight: 700 }}>{hoverPoint.date}</div>
            <div style={{ marginTop: 4 }}>Drawdown: {(hoverPoint.drawdown * 100).toFixed(1)}%</div>
          </div>
        )}
      </div>
    );
  }
}

// ── Improvement sparkline ─────────────────────────────────────────────────────
export function ImprovementLine({ data = [] }: { data?: number[] }) {
  if (data.length < 2) return null;
  const [hover, setHover] = useState<number | null>(null);
  const W = 100, H = 56;
  const mn = Math.min(...data), mx = Math.max(...data), rng = mx - mn || 0.1;
  const denom = Math.max(data.length - 1, 1);
  const pts = data.map((v, i) => {
    const x = (i / denom) * W;
    const y = H - 4 - ((v - mn) / rng) * (H - 10);
    return { x, y, v };
  });
  const line = pts.map(p => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ');
  const area = `0,${H} ${line} ${W},${H} Z`;
  const thY = H - 4 - ((0.7 - mn) / rng) * (H - 10);
  const handleMove = (event: React.MouseEvent<SVGSVGElement>) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const idx = Math.round((x / rect.width) * denom);
    const clamped = Math.max(0, Math.min(data.length - 1, idx));
    setHover(clamped);
  };
  const handleLeave = () => setHover(null);
  const hoverPoint = hover === null ? null : pts[hover];
  return (
    <div style={{ position: 'relative' }}>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        preserveAspectRatio="none"
        style={{ width: '100%', height: 72, cursor: 'crosshair' }}
        onMouseMove={handleMove}
        onMouseLeave={handleLeave}
      >
        <defs>
          <linearGradient id="gImp3" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={Q.accent} stopOpacity="0.32"/>
            <stop offset="100%" stopColor={Q.accent} stopOpacity="0"/>
          </linearGradient>
          <filter id="sparkGlow3">
            <feGaussianBlur stdDeviation="1.5" result="blur"/>
            <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
          </filter>
        </defs>
        {thY > 2 && thY < H && (
          <line x1="0" y1={thY.toFixed(1)} x2={W} y2={thY.toFixed(1)} stroke={Q.green} strokeDasharray="3 2" strokeWidth="0.8" opacity="0.5"/>
        )}
        <polygon points={area} fill="url(#gImp3)"/>
        <polyline points={line} fill="none" stroke={Q.accentBright} strokeWidth="2" strokeLinejoin="round" filter="url(#sparkGlow3)"/>
        {pts.map((p, i) => <circle key={i} cx={p.x.toFixed(1)} cy={p.y.toFixed(1)} r="2" fill={Q.accentBright}/>)}
        {hoverPoint && (
          <>
            <line x1={hoverPoint.x.toFixed(1)} y1="0" x2={hoverPoint.x.toFixed(1)} y2={H} stroke={Q.borderFaint} strokeWidth="1"/>
            <circle cx={hoverPoint.x.toFixed(1)} cy={hoverPoint.y.toFixed(1)} r="3.2" fill={Q.accentBright} stroke={Q.accent} strokeWidth="1"/>
          </>
        )}
      </svg>
      {hoverPoint && (
        <div style={{
          position: 'absolute', top: 6, right: 6, background: Q.cardInner,
          border: `1px solid ${Q.borderFaint}`, borderRadius: 8, padding: '4px 6px',
          fontSize: 9, color: Q.sub, fontFamily: Q.mono,
        }}>
          {hoverPoint.v.toFixed(3)}
        </div>
      )}
    </div>
  );
}

// ── P-value bar ───────────────────────────────────────────────────────────────
export function PValueBar({ p, significant }: { p: number; significant: boolean }) {
  const color = significant ? Q.green : Q.amber;
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
        <span style={{ fontSize: 11, color: Q.sub, fontFamily: Q.sans }}>p-value significance</span>
        <span style={{ fontSize: 11, color, fontWeight: 600, fontFamily: Q.sans }}>{significant ? '✓ p < 0.05' : '✗ p ≥ 0.05'}</span>
      </div>
      <div style={{ position: 'relative', height: 6, background: 'rgba(255,255,255,0.05)', borderRadius: 99 }}>
        <div style={{ height: 6, width: `${Math.min(p * 100, 100)}%`, background: `linear-gradient(90deg, ${color}70, ${color})`, borderRadius: 99, transition: 'width 0.7s', boxShadow: `0 0 8px ${color}50` }}/>
        <div style={{ position: 'absolute', top: -2, left: '5%', width: 1.5, height: 10, background: Q.red, borderRadius: 1, opacity: 0.7 }}/>
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4, fontSize: 9, fontFamily: Q.mono, color: Q.muted }}>
        <span>0</span><span style={{ color: Q.red }}>0.05</span>
        <span>p = {p.toFixed(4)}</span><span>1.0</span>
      </div>
    </div>
  );
}

// ── CI bar ────────────────────────────────────────────────────────────────────
export function CIBar({ lower, upper, mean }: { lower: number; upper: number; mean: number }) {
  const mn = Math.min(lower, 0) - Math.abs(upper - lower) * 0.1;
  const mx = Math.max(upper, 0) + Math.abs(upper - lower) * 0.1;
  const rng = mx - mn || 1;
  const lP = ((lower - mn) / rng) * 100, uP = ((upper - mn) / rng) * 100;
  const mP = ((mean - mn) / rng) * 100, zP = ((0 - mn) / rng) * 100;
  const spans = lower < 0 && upper > 0;
  const color = spans ? Q.amber : Q.green;
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
        <span style={{ fontSize: 11, color: Q.sub, fontFamily: Q.sans }}>95% Bootstrap CI</span>
        <span style={{ fontSize: 11, color, fontFamily: Q.sans }}>{spans ? 'spans zero' : 'positive edge'}</span>
      </div>
      <div style={{ position: 'relative', height: 9, background: 'rgba(255,255,255,0.05)', borderRadius: 99 }}>
        <div style={{ position: 'absolute', left: `${lP}%`, width: `${uP - lP}%`, height: 9, background: `${color}25`, borderRadius: 99 }}/>
        <div style={{ position: 'absolute', left: `${mP}%`, top: 0.5, width: 8, height: 8, background: color, borderRadius: '50%', transform: 'translateX(-50%)', boxShadow: `0 0 8px ${color}` }}/>
        <div style={{ position: 'absolute', left: `${zP}%`, top: -2, width: 1.5, height: 13, background: Q.muted, borderRadius: 1 }}/>
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4, fontSize: 9, fontFamily: Q.mono, color: Q.muted }}>
        <span>{lower.toFixed(5)}</span><span>μ = {mean.toFixed(5)}</span><span>{upper.toFixed(5)}</span>
      </div>
    </div>
  );
}

// ── Score Tile ────────────────────────────────────────────────────────────────
export function ScoreTile({ label, desc, value }: { label: string; desc: string; value: number }) {
  const color = value >= 0.7 ? Q.green : value >= 0.4 ? Q.amber : value > 0 ? Q.red : Q.muted;
  const bg    = value >= 0.7 ? Q.greenBg : value >= 0.4 ? Q.amberBg : value > 0 ? Q.redBg : Q.faint;
  const bd    = value >= 0.7 ? Q.greenBd : value >= 0.4 ? Q.amberBd : value > 0 ? Q.redBd : Q.borderFaint;
  const icon  = value >= 0.7 ? '✓' : value >= 0.4 ? '◑' : value > 0 ? '⚠' : '—';
  return (
    <div style={{ background: bg, border: `1px solid ${bd}`, borderRadius: 12, padding: '12px 13px', position: 'relative', overflow: 'hidden' }}>
      <div style={{ position: 'absolute', top: 0, right: 0, width: 36, height: 36, borderRadius: '0 12px 0 36px', background: `${color}10` }}/>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 5 }}>
        <span style={{ fontSize: 9, fontWeight: 700, color, letterSpacing: '0.06em', textTransform: 'uppercase', fontFamily: Q.sans }}>{label}</span>
        <span style={{ fontSize: 13, color, lineHeight: 1 }}>{icon}</span>
      </div>
      <div style={{ fontSize: 26, fontWeight: 800, fontFamily: Q.mono, color, lineHeight: 1, marginBottom: 4, textShadow: value > 0 ? `0 0 20px ${color}50` : 'none' }}>
        {value === 0 ? '—' : value.toFixed(2)}
      </div>
      <div style={{ fontSize: 10, color: Q.muted, marginBottom: 8, fontFamily: Q.sans }}>{desc}</div>
      <div style={{ height: 3, background: 'rgba(255,255,255,0.05)', borderRadius: 99 }}>
        <div style={{ height: 3, width: `${Math.max(0, value) * 100}%`, background: color, borderRadius: 99, transition: 'width 0.8s ease', boxShadow: value > 0 ? `0 0 6px ${color}` : 'none' }}/>
      </div>
    </div>
  );
}
