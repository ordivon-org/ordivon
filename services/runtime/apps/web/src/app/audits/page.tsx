import AuditSummary from '@/components/features/audits/AuditSummary';
import AuditList from '@/components/features/audits/AuditList';

export default function AuditsPage() {
  return (
    <div className="audits-page">
      <header style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>Governance Audit Center</h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Comprehensive monitoring of policy enforcement and intelligence gating decisions.</p>
      </header>

      {/* Top: Aggregate Stats */}
      <AuditSummary />

      <div className="glass" style={{ borderRadius: '12px', overflow: 'hidden' }}>
        <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 style={{ fontSize: '1rem', fontWeight: '600' }}>Decision Events History</h2>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button style={{ padding: '6px 12px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-color)', borderRadius: '4px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>Filter by Status</button>
            <button style={{ padding: '6px 12px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-color)', borderRadius: '4px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>Export CSV</button>
          </div>
        </div>
        
        {/* Bottom: Detailed Event List */}
        <AuditList />
      </div>
    </div>
  );
}
