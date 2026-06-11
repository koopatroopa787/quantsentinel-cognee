"use strict";

function StatusDot2({ status }) {
  const map = { done: Q.green, error: Q.red, warning: Q.amber, running: Q.accent, planning: Q.blue };
  const col = map[status] || Q.muted;
  const pulse = status === 'running' || status === 'planning';
  return (
    <span style={{
      width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
      background: col, display: 'inline-block', marginTop: 2,
      boxShadow: pulse ? `0 0 10px ${col}, 0 0 20px ${col}50` : `0 0 6px ${col}60`,
      ...(pulse ? { animation: 'q2Pulse 1.2s ease-in-out infinite' } : {}),
    }}/>
  );
}

function ProgressBar2({ color }) {
  return (
    <div style={{ height: 2, borderRadius: 99, background: `${color}12`, overflow: 'hidden', marginTop: 8 }}>
      <div style={{
        height: '100%', width: '40%', borderRadius: 99,
        background: `linear-gradient(90deg, transparent, ${color}, transparent)`,
        animation: 'q2Shimmer 1.8s ease-in-out infinite',
        boxShadow: `0 0 8px ${color}`,
      }}/>
    </div>
  );
}

function ElapsedTimer2({ startedAt }) {
  const [now, setNow] = React.useState(Date.now());
  React.useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);
  const s = Math.floor((now - startedAt) / 1000);
  const str = s < 60 ? `${s}s` : `${Math.floor(s/60)}m ${String(s%60).padStart(2,'0')}s`;
  return <span style={{ fontSize: 10, color: Q.muted, fontFamily: Q.mono }}>⏱ {str}</span>;
}

function AgentTimeline2({ steps, running }) {
  const bottomRef = React.useRef(null);
  const [expanded, setExpanded] = React.useState(new Set());
  const toggle = i => setExpanded(prev => { const n = new Set(prev); n.has(i) ? n.delete(i) : n.add(i); return n; });

  React.useEffect(() => {
    if (bottomRef.current) {
      const p = bottomRef.current.parentElement;
      p.scrollTop = p.scrollHeight;
    }
  }, [steps]);

  const isEmpty = steps.length === 0 && !running;

  return (
    <div style={{
      background: Q.card, borderRadius: Q.r, boxShadow: Q.shadow,
      border: `1px solid ${Q.border}`, overflow: 'hidden',
      fontFamily: Q.sans, display: 'flex', flexDirection: 'column',
      position: 'relative',
    }}>
      {/* Top accent strip */}
      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 2, background: `linear-gradient(90deg, ${Q.accent}, ${Q.cyan}, ${Q.accentBright})` }}/>

      {/* Header */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '18px 22px', paddingTop: 20, borderBottom: `1px solid ${Q.border}`,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 32, height: 32, borderRadius: 9,
            background: Q.accentLt, border: `1px solid ${Q.border}`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <svg width="15" height="15" viewBox="0 0 16 16" fill="none">
              <path d="M2 8 L5 4 L9 9 L12 5 L14 8" stroke={Q.accentBright} strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <div>
            <div style={{ fontSize: 14, fontWeight: 700, color: Q.ink, lineHeight: 1.1 }}>Agent Pipeline</div>
            <div style={{ fontSize: 11, color: Q.muted, fontFamily: Q.mono }}>{steps.length} events</div>
          </div>
        </div>
        {running ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: 7, padding: '5px 13px', background: Q.accentLt, borderRadius: Q.rpill, border: `1px solid ${Q.border}` }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: Q.accent, display: 'inline-block', animation: 'q2Pulse 1s infinite', boxShadow: `0 0 10px ${Q.accent}` }}/>
            <span style={{ fontSize: 11, fontWeight: 600, color: Q.accentBright }}>Live</span>
          </div>
        ) : steps.length > 0 ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: 7, padding: '5px 13px', background: Q.greenBg, borderRadius: Q.rpill, border: `1px solid ${Q.greenBd}` }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: Q.green, display: 'inline-block', boxShadow: `0 0 8px ${Q.green}` }}/>
            <span style={{ fontSize: 11, fontWeight: 600, color: Q.green }}>Complete</span>
          </div>
        ) : null}
      </div>

      {/* Feed */}
      <div style={{ padding: '16px 20px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 0, minHeight: 200, maxHeight: 420 }}>
        {isEmpty ? (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 14, paddingTop: 40, paddingBottom: 40 }}>
            <div style={{
              width: 64, height: 64, borderRadius: '50%',
              background: Q.cardInner, border: `1.5px dashed ${Q.border}`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              boxShadow: `0 0 32px ${Q.accentGlow}20`,
            }}>
              <svg width="26" height="26" viewBox="0 0 26 26" fill="none">
                <polygon points="13,3 22,8 22,18 13,23 4,18 4,8" stroke={Q.accentBright} strokeWidth="1.5" fill="none" opacity="0.45"/>
                <circle cx="13" cy="13" r="3" stroke={Q.accentBright} strokeWidth="1.5" fill="none" opacity="0.45"/>
              </svg>
            </div>
            <div style={{ textAlign: 'center' }}>
              <p style={{ fontSize: 14, color: Q.sub, margin: '0 0 6px', fontWeight: 600 }}>Waiting for research query</p>
              <p style={{ fontSize: 12, color: Q.muted, maxWidth: 260, lineHeight: 1.65, margin: 0 }}>
                Submit a hypothesis on the left to start the multi-agent research pipeline.
              </p>
            </div>
          </div>
        ) : (
          <>
            {steps.map((step, i) => {
              const meta = AGENTS2[step.agent] || { label: step.agent, color: Q.sub, icon: '·' };
              const isRunning = step.status === 'running';
              const isDone = step.status === 'done';
              const isError = step.status === 'error';
              const isWarn = step.status === 'warning';

              return (
                <div key={`${step.agent}-${i}`} style={{
                  background: '#1c1c1c',
                  border: `1px solid ${isRunning ? meta.color + '60' : 'rgba(96,108,56,0.38)'}`, 
                  borderLeft: `3px solid ${meta.color}`,
                  borderRadius: 12, padding: '12px 14px', marginBottom: 8,
                  boxShadow: isRunning ? `0 0 20px ${meta.color}20` : '0 1px 8px rgba(0,0,0,0.3)',
                  transition: 'border-color 0.3s',
                }}>
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
                    {/* Agent icon */}
                    <div style={{
                      width: 36, height: 36, borderRadius: 10, flexShrink: 0,
                      background: `${meta.color}14`, border: `1px solid ${meta.color}28`,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: 15, color: meta.color, fontWeight: 700,
                      boxShadow: isRunning ? `0 0 14px ${meta.color}35` : 'none',
                    }}>{meta.icon}</div>

                    {/* Content */}
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 5, flexWrap: 'wrap' }}>
                        <span style={{ fontSize: 12, fontWeight: 700, color: Q.ink }}>{meta.label}</span>
                        {isDone && (
                          <span style={{ fontSize: 10, color: Q.green, background: Q.greenBg, border: `1px solid ${Q.greenBd}`, borderRadius: Q.rpill, padding: '2px 7px', fontWeight: 700 }}>✓ done</span>
                        )}
                        {isError && (
                          <span style={{ fontSize: 10, color: Q.red, background: Q.redBg, border: `1px solid ${Q.redBd}`, borderRadius: Q.rpill, padding: '2px 7px', fontWeight: 700 }}>✗ error</span>
                        )}
                        {isWarn && (
                          <span style={{ fontSize: 10, color: Q.amber, background: Q.amberBg, border: `1px solid ${Q.amberBd}`, borderRadius: Q.rpill, padding: '2px 7px', fontWeight: 700 }}>⚠ timeout</span>
                        )}
                        {isRunning && step.startedAt && <ElapsedTimer2 startedAt={step.startedAt}/>}
                      </div>

                      <p style={{ fontSize: 11, color: isRunning ? Q.sub : Q.muted, lineHeight: 1.6, margin: 0 }}>
                        {step.heartbeat ?? step.message}
                      </p>
                      {isRunning && <ProgressBar2 color={meta.color}/>}

                      {step.output && (
                        <div style={{ marginTop: 8 }}>
                          <button onClick={() => toggle(i)} style={{
                            display: 'inline-flex', alignItems: 'center', gap: 5,
                            fontSize: 10, color: expanded.has(i) ? meta.color : Q.muted,
                            background: `${meta.color}08`, border: `1px solid ${expanded.has(i) ? meta.color + '40' : Q.borderFaint}`,
                            borderRadius: 8, padding: '4px 10px', cursor: 'pointer', fontFamily: Q.mono,
                            transition: 'all 0.15s',
                          }}>
                            <span style={{ fontSize: 8 }}>{expanded.has(i) ? '▼' : '▶'}</span>
                            {expanded.has(i) ? 'Hide' : 'Show'} output
                            <span style={{ color: Q.muted }}>({step.output.length.toLocaleString()} chars)</span>
                          </button>
                          {expanded.has(i) && (
                            <pre style={{
                              marginTop: 6, padding: '10px 14px',
                              background: Q.cardInner, border: `1px solid ${Q.borderFaint}`,
                              borderRadius: 10, fontSize: 11, fontFamily: Q.mono,
                              color: Q.sub, lineHeight: 1.65, whiteSpace: 'pre-wrap',
                              maxHeight: 300, overflowY: 'auto',
                            }}>{step.output}</pre>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}

            {running && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, paddingLeft: 4, marginTop: 4 }}>
                <span style={{ display: 'flex', gap: 4 }}>
                  {[0,1,2].map(n => (
                    <span key={n} style={{
                      width: 5, height: 5, borderRadius: '50%', background: Q.accent,
                      boxShadow: `0 0 8px ${Q.accent}`,
                      animation: `q2Bounce 1.2s ease-in-out ${n * 0.2}s infinite`,
                      display: 'inline-block',
                    }}/>
                  ))}
                </span>
                <span style={{ fontSize: 12, color: Q.muted }}>Agents working…</span>
              </div>
            )}
          </>
        )}
        <div ref={bottomRef}/>
      </div>
    </div>
  );
}

Object.assign(window, { AgentTimeline2 });
