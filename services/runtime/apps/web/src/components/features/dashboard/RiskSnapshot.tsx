'use client';

export default function RiskSnapshot() {
  const stats = {
    todayAllow: 12,
    todayWarn: 3,
    todayBlock: 1,
    topRule: 'Vol_Surge_Limit',
    lastBlockReason: 'Confidence below 0.6 on critical exposure'
  };

  return (
    <div className="risk-snapshot glass" style={{
      padding: '1.25rem',
      borderRadius: '12px',
      height: '100%',
      borderLeft: '4px solid var(--warn)'
    }}>
      <h3 style={{ marginBottom: '1rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>🛡️ Risk & Governance</h3>
      
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: 'var(--success)' }}>{stats.todayAllow}</div>
          <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>ALLOW</div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: 'var(--warn)' }}>{stats.todayWarn}</div>
          <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>WARN</div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: 'var(--error)' }}>{stats.todayBlock}</div>
          <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>BLOCK</div>
        </div>
      </div>

      <div style={{ fontSize: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        <div>
          <span style={{ color: 'var(--text-muted)' }}>Top Rule:</span>
          <code style={{ marginLeft: '0.5rem', color: 'var(--primary-hover)', background: 'rgba(255,255,255,0.05)', padding: '2px 4px', borderRadius: '4px' }}>
            {stats.topRule}
          </code>
        </div>
        <div>
          <span style={{ color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Last Block Reason:</span>
          <div style={{ 
            color: 'var(--error)', 
            padding: '8px', 
            background: 'rgba(248, 81, 73, 0.05)',
            border: '1px solid rgba(248, 81, 73, 0.1)',
            borderRadius: '6px',
            fontSize: '0.7rem',
            lineHeight: '1.4'
          }}>
            {stats.lastBlockReason}
          </div>
        </div>
      </div>
    </div>
  );
}
