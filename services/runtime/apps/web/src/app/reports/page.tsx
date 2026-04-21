import LatestReportsList from '@/components/features/reports/LatestReportsList';

export default function ReportsPage() {
  return (
    <div className="reports-page glass" style={{ padding: '2rem', borderRadius: '12px' }}>
      <header style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 'bold' }}>Research Archive</h1>
        <p style={{ color: 'var(--text-muted)' }}>Historical knowledge and persistent research objects.</p>
      </header>
      <LatestReportsList />
    </div>
  );
}
