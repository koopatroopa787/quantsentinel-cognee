"use strict";

// ─── Top Bar ───────────────────────────────────────────────────────────────────
function TopBar({ running }) {
  return (
    <header style={{
      height: 60,
      background: 'rgba(6,9,26,0.92)',
      backdropFilter: 'blur(16px)',
      borderBottom: `1px solid ${Q.border}`,
      display: 'flex', alignItems: 'center', padding: '0 28px', gap: 18,
      flexShrink: 0, zIndex: 10, position: 'relative', fontFamily: Q.sans,
      boxShadow: '0 1px 0 rgba(96,108,56,0.14), 0 4px 24px rgba(0,0,0,0.4)',
    }}>
      {/* Hamburger */}
      <button style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 6, display: 'flex', flexDirection: 'column', gap: 4 }}>
        {[0,1,2].map(i => <span key={i} style={{ width: 18, height: 1.5, background: Q.muted, display: 'block', borderRadius: 1 }}/>)}
      </button>

      {/* Logo */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{
          width: 36, height: 36, borderRadius: 10, flexShrink: 0,
          background: `linear-gradient(135deg, ${Q.accent} 0%, #bc6c25 100%)`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: `0 4px 18px ${Q.accentGlow}, inset 0 1px 0 rgba(255,255,255,0.15)`,
          border: `1px solid ${Q.accentBright}30`,
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

      {/* Nav */}
      <div style={{ display: 'flex', gap: 2, marginLeft: 4 }}>
        {['Overview', 'Research', 'Analytics', 'Logs'].map((item, i) => (
          <button key={item} style={{
            background: i === 1 ? Q.accentLt : 'none',
            border: i === 1 ? `1px solid ${Q.border}` : '1px solid transparent',
            color: i === 1 ? Q.accentBright : Q.muted,
            borderRadius: 8, padding: '5px 13px',
            fontSize: 12, fontWeight: 500, cursor: 'pointer', fontFamily: Q.sans,
            transition: 'all 0.15s',
          }}>{item}</button>
        ))}
      </div>

      <div style={{ flex: 1 }}/>

      {/* Running pill */}
      {running && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: 7, padding: '6px 14px',
          background: Q.accentLt, borderRadius: Q.rpill, border: `1px solid ${Q.border}`,
        }}>
          <span style={{ width: 6, height: 6, borderRadius: '50%', background: Q.accent, display: 'inline-block', animation: 'q2Pulse 1.2s infinite', boxShadow: `0 0 8px ${Q.accent}` }}/>
          <span style={{ fontSize: 11, fontWeight: 600, color: Q.accentBright }}>Research running</span>
        </div>
      )}

      {/* Search */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8, padding: '7px 14px',
        background: Q.faint, borderRadius: Q.rpill, border: `1px solid ${Q.border}`,
      }}>
        <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
          <circle cx="5.5" cy="5.5" r="4.5" stroke={Q.muted} strokeWidth="1.3"/>
          <path d="M9 9L12 12" stroke={Q.muted} strokeWidth="1.3" strokeLinecap="round"/>
        </svg>
        <span style={{ fontSize: 12, color: Q.muted, minWidth: 110 }}>Search runs…</span>
        <span style={{ fontSize: 10, color: Q.muted, background: 'rgba(255,255,255,0.05)', border: `1px solid ${Q.borderFaint}`, borderRadius: 5, padding: '1px 6px', fontFamily: Q.mono }}>⌘K</span>
      </div>

      {/* Disclaimer */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 5, padding: '5px 10px', background: Q.amberBg, border: `1px solid ${Q.amberBd}`, borderRadius: Q.rpill }}>
        <span style={{ fontSize: 10, color: Q.amber }}>⚠</span>
        <span style={{ fontSize: 10, color: Q.amber, fontWeight: 500 }}>Research only · Not financial advice</span>
      </div>

      {/* User */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{
          width: 34, height: 34, borderRadius: '50%',
          background: `linear-gradient(135deg, ${Q.accent}, #bc6c25)`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 13, fontWeight: 700, color: '#1a2310',
          boxShadow: `0 2px 12px ${Q.accentGlow}`,
          border: `1.5px solid ${Q.accentBright}30`,
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

// ─── Left Column ───────────────────────────────────────────────────────────────
function LeftCol({ hypothesis, setHypothesis, onRun, running, tokens, history, canRun }) {
  const [showEx, setShowEx] = React.useState(false);
  const taRef = React.useRef(null);

  const EXAMPLES = [
    "Does a 14-day RSI below 30 on SPY generate significant mean-reversion returns over 5 trading days from 2015 to 2024?",
    "Do FOMC announcement days show elevated VIX spikes on QQQ from 2010 to 2023?",
    "Does a 50/200-day SMA golden cross on AAPL outperform buy-and-hold from 2012 to 2024?",
  ];

  const card = (children, extra = {}) => (
    <div style={{
      background: Q.card, borderRadius: Q.r, boxShadow: Q.shadow,
      border: `1px solid ${Q.border}`, overflow: 'hidden', position: 'relative',
      ...extra,
    }}>{children}</div>
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14, fontFamily: Q.sans }}>

      {/* Hypothesis card */}
      {card(
        <>
          <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 2, background: `linear-gradient(90deg, ${Q.accent}, ${Q.cyan})` }}/>
          <div style={{ padding: '20px 20px 0' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ width: 7, height: 7, borderRadius: '50%', background: Q.accent, boxShadow: `0 0 8px ${Q.accent}`, display: 'inline-block' }}/>
                <span style={{ fontSize: 13, fontWeight: 700, color: Q.ink }}>Research Hypothesis</span>
              </div>
              <button onClick={() => setShowEx(v => !v)} style={{
                fontSize: 11, color: Q.accentBright, background: Q.accentLt,
                border: `1px solid ${Q.border}`, borderRadius: Q.rpill, padding: '4px 12px',
                cursor: 'pointer', fontWeight: 600, fontFamily: Q.sans,
              }}>Examples {showEx ? '↑' : '↓'}</button>
            </div>

            {showEx && (
              <div style={{ marginBottom: 12, display: 'flex', flexDirection: 'column', gap: 6 }}>
                {EXAMPLES.map((ex, i) => (
                  <button key={i} onClick={() => { setHypothesis(ex); setShowEx(false); taRef.current?.focus(); }}
                    style={{
                      fontSize: 11, color: Q.sub, background: Q.cardInner,
                      border: `1px solid ${Q.borderFaint}`, borderRadius: 10,
                      padding: '9px 12px', textAlign: 'left', cursor: 'pointer',
                      lineHeight: 1.55, fontFamily: Q.sans, transition: 'all 0.15s',
                    }}
                    onMouseEnter={e => { e.currentTarget.style.borderColor = `${Q.accent}50`; e.currentTarget.style.color = Q.ink; }}
                    onMouseLeave={e => { e.currentTarget.style.borderColor = Q.borderFaint; e.currentTarget.style.color = Q.sub; }}
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
              onFocus={e => e.target.style.borderColor = `${Q.accent}60`}
              onBlur={e => e.target.style.borderColor = Q.borderFaint}
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
              background: canRun ? `linear-gradient(135deg, ${Q.accent} 0%, #bc6c25 100%)` : 'rgba(255,255,255,0.05)',
              color: canRun ? '#1a2310' : Q.muted,
              fontSize: 14, fontWeight: 700, cursor: canRun ? 'pointer' : 'not-allowed',
              fontFamily: Q.sans, letterSpacing: '0.01em',
              boxShadow: canRun ? `0 4px 24px ${Q.accentGlow}` : 'none',
              transition: 'all 0.2s', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
            }}
              onMouseEnter={e => { if (canRun) e.currentTarget.style.boxShadow = `0 6px 32px ${Q.accentGlow}`; }}
              onMouseLeave={e => { if (canRun) e.currentTarget.style.boxShadow = `0 4px 24px ${Q.accentGlow}`; }}
            >
              <span>{running ? '⟳' : '⚡'}</span>
              {running ? 'Researching…' : 'Run Research'}
              {!running && canRun && <span style={{ opacity: 0.65 }}>→</span>}
            </button>
          </div>
        </>
      )}

      {/* Token Usage */}
      {card(
        <div style={{ padding: '16px 20px' }}>
          <div style={{ fontSize: 10, fontWeight: 700, color: Q.muted, letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 12 }}>Token Usage</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
            {[['Input', tokens.input, Q.cyan], ['Output', tokens.output, Q.accentBright]].map(([lbl, val, col]) => (
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

      {/* Recent Runs */}
      {card(
        <div style={{ padding: '16px 20px' }}>
          <div style={{ fontSize: 10, fontWeight: 700, color: Q.muted, letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 12 }}>Recent Runs</div>
          {history.length === 0 ? (
            <p style={{ fontSize: 12, color: Q.muted, fontStyle: 'italic' }}>No runs yet.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
              {history.slice(0, 5).map((item, i) => (
                <div key={i} style={{
                  background: Q.cardInner, border: `1px solid ${Q.borderFaint}`,
                  borderRadius: 12, padding: '10px 12px', cursor: 'pointer', transition: 'all 0.15s',
                }}
                  onMouseEnter={e => { e.currentTarget.style.borderColor = `${Q.accent}40`; e.currentTarget.style.background = `${Q.accent}08`; }}
                  onMouseLeave={e => { e.currentTarget.style.borderColor = Q.borderFaint; e.currentTarget.style.background = Q.cardInner; }}
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

// ─── Score Tile ────────────────────────────────────────────────────────────────
function ScoreTile({ label, desc, value }) {
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

// ─── Right Column ──────────────────────────────────────────────────────────────
function RightCol({ scores, improvement }) {
  const demoData = Array.from({ length: 14 }, (_, i) => ({
    timestamp: new Date(Date.now() - (13 - i) * 86400000).toISOString(),
    overall: +(0.50 + i * 0.031 + Math.sin(i * 0.9) * 0.02).toFixed(3),
  }));
  const pts = improvement.length >= 1 ? improvement : demoData;
  const isDemo = improvement.length < 1;
  const scoreVals = pts.map(p => p.overall);

  const card = (children, extra = {}) => (
    <div style={{
      background: Q.card, borderRadius: Q.r, boxShadow: Q.shadow,
      border: `1px solid ${Q.border}`, overflow: 'hidden', position: 'relative',
      padding: 20, ...extra,
    }}>{children}</div>
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14, fontFamily: Q.sans }}>

      {/* Eval Scores */}
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

      {/* Self-Improvement */}
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
          <ImprovementLine2 data={scoreVals}/>
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

Object.assign(window, { TopBar, LeftCol, RightCol });
