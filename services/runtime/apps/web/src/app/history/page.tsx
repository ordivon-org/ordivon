export default function HistoryPage() {
  return (
    <div className="history-page glass" style={{ padding: '2rem', borderRadius: '12px' }}>
      <header style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 'bold' }}>Intelligence History</h1>
        <p style={{ color: 'var(--text-muted)' }}>Long-term memory objects and execution timeline.</p>
      </header>
      <div style={{ padding: '4rem', textAlign: 'center', border: '1px dashed var(--border-color)', borderRadius: '8px' }}>
        <p style={{ color: 'var(--text-muted)' }}>History synchronization in progress. Case details are viewable in the Audits section.</p>
      </div>
    </div>
  );
}
