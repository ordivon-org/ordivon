'use client';

export default function AuditSummary() {
  const stats = {
    allow: 156,
    warn: 24,
    block: 8,
    passRate: 84,
    avgLatency: '1.2s'
  };

  return (
    <div className="audit-summary glass" style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(4, 1fr)',
      gap: '1.5rem',
      padding: '2rem',
      borderRadius: '12px',
      marginBottom: '2rem'
    }}>
      <div style={{ textAlign: 'center' }}>
        <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: 'var(--success)' }}>{stats.allow}</div>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', letterSpacing: '1px' }}>TOTAL ALLOWED</div>
      </div>
      <div style={{ textAlign: 'center' }}>
        <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: 'var(--warn)' }}>{stats.warn}</div>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', letterSpacing: '1px' }}>TOTAL WARNINGS</div>
      </div>
      <div style={{ textAlign: 'center' }}>
        <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: 'var(--error)' }}>{stats.block}</div>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', letterSpacing: '1px' }}>TOTAL BLOCKS</div>
      </div>
      <div style={{ textAlign: 'center', backgroundColor: 'rgba(137, 87, 229, 0.05)', borderRadius: '8px', padding: '10px' }}>
        <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: 'var(--primary-hover)' }}>{stats.passRate}%</div>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', letterSpacing: '1px' }}>PASS THROUGH RATE</div>
      </div>
    </div>
  );
}
