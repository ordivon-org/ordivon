export default function ReportsPage() {
  return (
    <div className="reports-page glass" style={{ padding: '2rem', borderRadius: '12px' }}>
      <header style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 'bold' }}>Research Archive</h1>
        <p style={{ color: 'var(--text-muted)' }}>Historical knowledge and persistent research objects.</p>
      </header>
      <div style={{ padding: '4rem', textAlign: 'center', border: '1px dashed var(--border-color)', borderRadius: '8px' }}>
        <p style={{ color: 'var(--text-muted)' }}>Archive browser is initializing. Latest reports are available on the Dashboard.</p>
      </div>
    </div>
  );
}
