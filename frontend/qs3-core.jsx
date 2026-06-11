"use strict";
// ─── Design tokens ─────────────────────────────────────────────────────────────
const Q = {
  bg:           '#0c0c0c',
  card:         '#161616',
  cardInner:    '#101010',
  border:       'rgba(96,108,56,0.32)',
  borderFaint:  'rgba(96,108,56,0.14)',
  shadow:       '0 0 0 1px rgba(96,108,56,0.18), 0 4px 32px rgba(0,0,0,0.55)',
  shadowHi:     '0 0 0 1px rgba(96,108,56,0.32), 0 8px 48px rgba(0,0,0,0.65)',
  accent:       '#dda15e',
  accentLt:     'rgba(221,161,94,0.13)',
  accentBright: '#e8bc82',
  accentGlow:   'rgba(221,161,94,0.38)',
  cyan:         '#606c38',
  cyanLt:       'rgba(96,108,56,0.14)',
  cyanGlow:     'rgba(96,108,56,0.28)',
  ink:          '#fefae0',
  sub:          'rgba(254,250,224,0.65)',
  muted:        'rgba(254,250,224,0.36)',
  faint:        'rgba(254,250,224,0.05)',
  green:        '#6b7a38',
  greenBg:      'rgba(107,122,56,0.16)',
  greenBd:      'rgba(107,122,56,0.35)',
  amber:        '#dda15e',
  amberBg:      'rgba(221,161,94,0.13)',
  amberBd:      'rgba(221,161,94,0.30)',
  red:          '#bc6c25',
  redBg:        'rgba(188,108,37,0.14)',
  redBd:        'rgba(188,108,37,0.30)',
  blue:         '#e8bc82',
  r:            '16px',
  rsm:          '10px',
  rpill:        '100px',
  sans:         "'Space Grotesk', system-ui, sans-serif",
  mono:         "'JetBrains Mono', 'IBM Plex Mono', monospace",
};

// ─── Arc math ──────────────────────────────────────────────────────────────────
function polar2(cx, cy, r, deg) {
  const rad = deg * Math.PI / 180;
  return [cx + r * Math.cos(rad), cy + r * Math.sin(rad)];
}
function arcD2(cx, cy, r, startDeg, sweepDeg) {
  if (sweepDeg >= 360) sweepDeg = 359.99;
  const [sx, sy] = polar2(cx, cy, r, startDeg);
  const [ex, ey] = polar2(cx, cy, r, startDeg + sweepDeg);
  return `M ${sx.toFixed(2)} ${sy.toFixed(2)} A ${r} ${r} 0 ${sweepDeg > 180 ? 1 : 0} 1 ${ex.toFixed(2)} ${ey.toFixed(2)}`;
}

// ─── Arc Gauge ─────────────────────────────────────────────────────────────────
function ArcGauge2({ value = 0, size = 74 }) {
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
      <path d={arcD2(cx, cy, r, START, SWEEP)} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={6} strokeLinecap="round"/>
      <path d={arcD2(cx, cy, r, START, fill)} fill="none" stroke={color} strokeWidth={6} strokeLinecap="round"
        filter={value > 0 ? `url(#${uid})` : undefined}
        style={{ transition: 'all 0.7s ease' }}/>
      <text x={cx} y={cy + 2} textAnchor="middle" dominantBaseline="middle"
        fill={value > 0 ? color : Q.muted} fontSize={size * 0.2} fontWeight="700" fontFamily={Q.mono}>
        {value === 0 ? '—' : value.toFixed(2)}
      </text>
    </svg>
  );
}

// ─── Metric card ───────────────────────────────────────────────────────────────
function MetricCard2({ label, value, sub, color, detail }) {
  return (
    <div style={{
      flex: 1, minWidth: 0,
      background: Q.card, borderRadius: 14,
      padding: '14px 16px',
      border: `1px solid ${Q.border}`,
      boxShadow: Q.shadow,
      position: 'relative', overflow: 'hidden',
    }}>
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: 2,
        background: `linear-gradient(90deg, transparent, ${color || Q.accent}80, transparent)`,
      }}/>
      <div style={{ fontSize: 9, fontWeight: 600, color: Q.muted, letterSpacing: '0.09em', textTransform: 'uppercase', marginBottom: 8, fontFamily: Q.sans }}>{label}</div>
      <div style={{ fontSize: 22, fontWeight: 700, fontFamily: Q.mono, color: color || Q.ink, lineHeight: 1, marginBottom: 4 }}>{value}</div>
      {sub && <div style={{ fontSize: 11, color: Q.sub, fontFamily: Q.sans }}>{sub}</div>}
      {detail && <div style={{ fontSize: 10, color: Q.muted, marginTop: 2, fontFamily: Q.sans }}>{detail}</div>}
    </div>
  );
}

// ─── Score row ─────────────────────────────────────────────────────────────────
function ScoreRow2({ label, value }) {
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

// ─── Agent badge ───────────────────────────────────────────────────────────────
const AGENTS2 = {
  orchestrator:               { label: 'Orchestrator', color: '#dda15e', icon: '⬡' },
  quantsentinel_orchestrator: { label: 'Orchestrator', color: '#dda15e', icon: '⬡' },
  data_agent:                 { label: 'Data Agent',   color: '#8fa855', icon: '◈' },
  backtester_agent:           { label: 'Backtester',   color: '#e8bc82', icon: '◉' },
  statistician_agent:         { label: 'Statistician', color: '#bc6c25', icon: '◆' },
  critic_agent:               { label: 'Critic',       color: '#606c38', icon: '✦' },
  system:                     { label: 'System',       color: 'rgba(254,250,224,0.4)', icon: '▸' },
};

function AgentBadge2({ agent }) {
  const m = AGENTS2[agent] || { label: agent, color: Q.sub, icon: '·' };
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

// ─── Equity chart (dark neon) ──────────────────────────────────────────────────
function EquityChart2({ series = [], mode = 'equity' }) {
  if (!series.length) return null;
  const W = 400, H = 160;
  function toPoints(data, mn, mx) {
    const rng = mx - mn || 1;
    return data.map((v, i) => {
      const x = (i / (data.length - 1)) * W;
      const y = H - 4 - ((v - mn) / rng) * (H - 16);
      return [x.toFixed(1), y.toFixed(1)];
    });
  }
  function pStr(pts) { return pts.map(p => p.join(',')).join(' '); }
  function aStr(pts) { return `0,${H} ${pStr(pts)} ${W},${H} Z`; }
  const gridYs = [0.2, 0.4, 0.6, 0.8].map(t => (4 + (1 - t) * (H - 16)).toFixed(1));

  if (mode === 'equity') {
    const eqData = series.map(s => s.equity), bnData = series.map(s => s.benchmark);
    const all = [...eqData, ...bnData], mn = Math.min(...all), mx = Math.max(...all);
    const eqPts = toPoints(eqData, mn, mx), bnPts = toPoints(bnData, mn, mx);
    return (
      <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" style={{ width: '100%', height: 200 }}>
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
        {gridYs.map((y, i) => (
          <line key={i} x1="0" y1={y} x2={W} y2={y} stroke="rgba(255,255,255,0.04)" strokeWidth="1"/>
        ))}
        <polygon points={aStr(eqPts)} fill="url(#gEq3)"/>
        <polyline points={pStr(bnPts)} fill="none" stroke="rgba(148,163,184,0.25)" strokeWidth="1.2" strokeDasharray="5 3"/>
        <polyline points={pStr(eqPts)} fill="none" stroke={Q.accentBright} strokeWidth="4" opacity="0.18"/>
        <polyline points={pStr(eqPts)} fill="none" stroke={Q.accentBright} strokeWidth="2" filter="url(#eqGlow3)"/>
      </svg>
    );
  } else {
    const ddData = series.map(s => s.drawdown);
    const mn = Math.min(...ddData), mx = Math.max(...ddData);
    const ddPts = toPoints(ddData, mn, mx);
    return (
      <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" style={{ width: '100%', height: 200 }}>
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
        {gridYs.map((y, i) => (
          <line key={i} x1="0" y1={y} x2={W} y2={y} stroke="rgba(255,255,255,0.04)" strokeWidth="1"/>
        ))}
        <polygon points={aStr(ddPts)} fill="url(#gDd3)"/>
        <polyline points={pStr(ddPts)} fill="none" stroke={Q.red} strokeWidth="2" filter="url(#ddGlow3)"/>
      </svg>
    );
  }
}

// ─── Improvement sparkline ─────────────────────────────────────────────────────
function ImprovementLine2({ data = [] }) {
  if (data.length < 2) return null;
  const W = 100, H = 56;
  const mn = Math.min(...data), mx = Math.max(...data), rng = mx - mn || 0.1;
  const pts = data.map((v, i) => {
    const x = (i / (data.length - 1)) * W;
    const y = H - 4 - ((v - mn) / rng) * (H - 10);
    return [x.toFixed(1), y.toFixed(1)];
  });
  const line = pts.map(p => p.join(',')).join(' ');
  const area = `0,${H} ${line} ${W},${H} Z`;
  const thY = H - 4 - ((0.7 - mn) / rng) * (H - 10);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" style={{ width: '100%', height: 72 }}>
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
      {pts.map(([x, y], i) => <circle key={i} cx={x} cy={y} r="2" fill={Q.accentBright}/>)}
    </svg>
  );
}

// ─── P-value bar ───────────────────────────────────────────────────────────────
function PValueBar2({ p, significant }) {
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

// ─── CI bar ────────────────────────────────────────────────────────────────────
function CIBar2({ lower, upper, mean }) {
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

Object.assign(window, { Q, ArcGauge2, MetricCard2, ScoreRow2, AgentBadge2, AGENTS2, EquityChart2, ImprovementLine2, PValueBar2, CIBar2 });
