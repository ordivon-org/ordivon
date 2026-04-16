'use client';

interface GovernancePanelProps {
  data: any | null;
  isLoading: boolean;
}

export default function GovernancePanel({ data, isLoading }: GovernancePanelProps) {
  if (isLoading) {
    return (
      <div className="governance-panel glass" style={{ padding: '1.5rem', height: '100%', opacity: 0.5 }}>
        <h3 style={{ marginBottom: '1.5rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>🛡️ Gating Status</h3>
        <div style={{ padding: '1rem', border: '1px dashed var(--border-color)', borderRadius: '8px', textAlign: 'center' }}>
          Validating policy...
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="governance-panel glass" style={{ padding: '1.5rem', height: '100%', border: '1px dashed var(--border-color)', borderRadius: '12px' }}>
        <h3 style={{ marginBottom: '1.5rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>🛡️ Gating Status</h3>
        <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>No active governance trail for current state.</div>
      </div>
    );
  }

  const { status, decision, risk_flags, audit_event_id, report_path } = data;
  const isBlock = decision === 'block';
  const isWarn = decision === 'warn';

  return (
    <div className="governance-panel glass" style={{
      padding: '1.5rem',
      borderRadius: '12px',
      height: '100%',
      // borderLeft: '1px solid var(--border-color)',
      backgroundColor: isBlock ? 'rgba(248, 81, 73, 0.03)' : 'transparent'
    }}>
      <h3 style={{ marginBottom: '1.5rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>🛡️ Gating Result</h3>

      {/* Decision Status */}
      <div style={{ 
        textAlign: 'center', 
        padding: '1.5rem', 
        borderRadius: '8px', 
        background: isBlock ? 'rgba(248, 81, 73, 0.1)' : isWarn ? 'rgba(210, 153, 34, 0.1)' : 'rgba(35, 134, 54, 0.1)',
        border: `1px solid ${isBlock ? 'rgba(248, 81, 73, 0.2)' : isWarn ? 'rgba(210, 153, 34, 0.2)' : 'rgba(35, 134, 54, 0.2)'}`,
        marginBottom: '2rem'
      }}>
        <div style={{ 
          fontSize: '2rem', 
          fontWeight: '900', 
          letterSpacing: '2px',
          color: isBlock ? 'var(--error)' : isWarn ? 'var(--warn)' : 'var(--success)'
        }}>
          {decision?.toUpperCase()}
        </div>
        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '4px' }}>
          POLICY VALIDATION COMPLETE
        </div>
      </div>

      {/* Why / Triggered Rules */}
      <section style={{ marginBottom: '2rem' }}>
        <h4 style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>REASONING & RISK FLAGS</h4>
        {risk_flags && risk_flags.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {risk_flags.map((flag: string, i: number) => (
              <div key={i} style={{ 
                padding: '8px 12px', 
                background: 'rgba(248, 81, 73, 0.05)', 
                borderLeft: '3px solid var(--error)',
                borderRadius: '4px',
                fontSize: '0.75rem',
                color: 'var(--foreground)'
              }}>
                🚩 {flag}
              </div>
            ))}
          </div>
        ) : (
          <div style={{ color: 'var(--success)', fontSize: '0.8rem' }}>✓ No policy violations detected.</div>
        )}
      </section>

      {/* Traceability */}
      <section style={{ 
        marginTop: 'auto', 
        paddingTop: '1.5rem', 
        borderTop: '1px solid var(--border-color)',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.75rem',
        fontSize: '0.75rem'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ color: 'var(--text-muted)' }}>Audit UUID:</span>
          <code style={{ fontSize: '0.7rem', color: 'var(--primary-hover)' }}>{audit_event_id?.slice(0, 8)}...</code>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ color: 'var(--text-muted)' }}>Workflow:</span>
          <span>analyze_and_suggest</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ color: 'var(--text-muted)' }}>Archive:</span>
          <span style={{ color: 'var(--success)' }}>PERSISTED</span>
        </div>
        
        {report_path && (
          <button style={{
            marginTop: '1rem',
            padding: '10px',
            background: 'rgba(255,255,255,0.05)',
            border: '1px solid var(--border-color)',
            borderRadius: '6px',
            color: 'var(--foreground)',
            cursor: 'pointer',
            fontWeight: '600'
          }}>
            📖 View Full Report
          </button>
        )}
      </section>
    </div>
  );
}
