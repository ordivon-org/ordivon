'use client';

import { useState } from 'react';

export default function AuditList() {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const audits = [
    { 
      id: 'evt_1', 
      symbol: 'BTC/USDT', 
      decision: 'allow', 
      workflow: 'analyze_and_suggest', 
      time: '12m ago',
      rules: [],
      summary: 'Trend breakout analysis confirmed by volume.'
    },
    { 
      id: 'evt_2', 
      symbol: 'ETH/USDT', 
      decision: 'warn', 
      workflow: 'analyze_and_suggest', 
      time: '1h ago',
      rules: ['Low_Confidence_Bias', 'Vwap_Distance_Warn'],
      summary: 'Analysis suggests overextension without macro support.'
    },
    { 
      id: 'evt_3', 
      symbol: 'SOL/USDT', 
      decision: 'block', 
      workflow: 'analyze_and_suggest', 
      time: '3h ago',
      rules: ['Critical_Exposure_Limit', 'Counter_Evidence_Missing'],
      summary: 'Action blocked due to missing contra-indicators and existing position size.'
    },
  ];

  return (
    <div className="audit-list">
      <div style={{ display: 'grid', gridTemplateColumns: '80px 1fr 120px 100px 80px', padding: '1rem', borderBottom: '2px solid var(--border-color)', fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 'bold' }}>
        <div>DECISION</div>
        <div>SUBJECT / REASON</div>
        <div>WORKFLOW</div>
        <div>TIME</div>
        <div>ACTION</div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column' }}>
        {audits.map(a => (
          <div key={a.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
            <div 
              onClick={() => setExpandedId(expandedId === a.id ? null : a.id)}
              style={{ 
                display: 'grid', 
                gridTemplateColumns: '80px 1fr 120px 100px 80px', 
                padding: '1.25rem 1rem', 
                alignItems: 'center',
                cursor: 'pointer',
                background: expandedId === a.id ? 'rgba(255,255,255,0.02)' : 'transparent'
              }}
            >
              <div className={`badge badge-${a.decision}`}>{a.decision}</div>
              <div style={{ fontSize: '0.9rem' }}>
                <strong>{a.symbol}</strong>
                <span style={{ marginLeft: '1rem', color: 'var(--text-muted)', fontSize: '0.8rem' }}>{a.summary.slice(0, 60)}...</span>
              </div>
              <div style={{ fontSize: '0.75rem', opacity: 0.7 }}>{a.workflow}</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{a.time}</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--primary-hover)' }}>{expandedId === a.id ? 'Hide ↑' : 'View ↓'}</div>
            </div>

            {expandedId === a.id && (
              <div style={{ padding: '1rem 2rem 2rem 6rem', background: 'rgba(0,0,0,0.2)', borderLeft: `4px solid var(--${a.decision === 'allow' ? 'success' : a.decision === 'warn' ? 'warn' : 'error'})` }}>
                <h4 style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>TRIGGERED RULES & CONTEXT</h4>
                {a.rules.length > 0 ? (
                  <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
                    {a.rules.map(r => (
                      <span key={r} style={{ padding: '4px 8px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-color)', borderRadius: '4px', fontSize: '0.7rem' }}>
                        🚫 {r}
                      </span>
                    ))}
                  </div>
                ) : (
                  <div style={{ color: 'var(--success)', fontSize: '0.75rem', marginBottom: '1rem' }}>✓ Passed all safety check invariant rules.</div>
                )}
                
                <p style={{ fontSize: '0.85rem', lineHeight: '1.5', color: 'var(--foreground)', marginBottom: '1rem' }}>
                  <strong>Context Summary:</strong> {a.summary}
                </p>

                <div style={{ display: 'flex', gap: '1rem' }}>
                  <button style={{ padding: '6px 12px', background: 'rgba(137, 87, 229, 0.1)', border: '1px solid var(--primary)', borderRadius: '4px', color: 'white', fontSize: '0.7rem', cursor: 'pointer' }}>
                    Open Audit Trace
                  </button>
                  <button style={{ padding: '6px 12px', background: 'transparent', border: '1px solid var(--border-color)', borderRadius: '4px', color: 'var(--text-muted)', fontSize: '0.7rem', cursor: 'pointer' }}>
                    View Raw Analysis
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
