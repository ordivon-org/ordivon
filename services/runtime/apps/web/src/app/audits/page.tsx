import AuditSummary from '@/components/features/audits/AuditSummary';
import AuditList from '@/components/features/audits/AuditList';

export default function AuditsPage() {
  return (
    <div className="audits-page">
      <header style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>Governance Audit Center</h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
          Live monitoring of recent governance and audit events from the v1 audit API.
        </p>
      </header>

      <AuditSummary />

      <div className="glass" style={{ borderRadius: '12px', overflow: 'hidden' }}>
        <div
          style={{
            padding: '1.5rem',
            borderBottom: '1px solid var(--border-color)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <h2 style={{ fontSize: '1rem', fontWeight: '600' }}>Recent Audit Events</h2>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Source: `/api/v1/audits/recent`
          </div>
        </div>

        <AuditList />
      </div>
    </div>
  );
}
