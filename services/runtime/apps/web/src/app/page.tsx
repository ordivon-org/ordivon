import SystemStatusBar from '@/components/status/SystemStatusBar';
import QuickAnalyze from '@/components/features/dashboard/QuickAnalyze';
import LatestDecisionList from '@/components/features/dashboard/LatestDecisionList';
import RiskSnapshot from '@/components/features/dashboard/RiskSnapshot';
import LatestReportsList from '@/components/features/dashboard/LatestReportsList';
import EvalStatus from '@/components/features/dashboard/EvalStatus';
import RecentRecommendations from '@/components/features/dashboard/RecentRecommendations';
import PendingReviews from '@/components/features/dashboard/PendingReviews';
import ValidationHub from '@/components/features/validation/ValidationHub';
import { ConsolePageFrame } from '@/components/workspace/ConsolePageFrame';

export default function Dashboard() {
  return (
    <ConsolePageFrame>
    <div className="dashboard-page">
      <header style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>Dashboard</h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
          Live command center for current system status, recommendation flow, review queue previews, and product-level diagnostics.
        </p>
      </header>

      {/* 1. System Status Bar (Status & Verification) */}
      <SystemStatusBar />

      <section style={{ marginBottom: '1rem' }}>
        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.65rem' }}>
          Action Entry
        </div>
      </section>

      <QuickAnalyze />

      <section style={{ marginBottom: '0.75rem' }}>
        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.65rem' }}>
          Audit / Decision / Report
        </div>
      </section>

      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))', 
        gap: '1.5rem',
        marginBottom: '1.5rem'
      }}>
        <LatestDecisionList />
        <RiskSnapshot />
      </div>

      <section style={{ marginBottom: '0.75rem' }}>
        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.65rem' }}>
          Reports / Diagnostics
        </div>
      </section>

      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))', 
        gap: '1.5rem'
      }}>
        <LatestReportsList />
        <EvalStatus />
      </div>

      <section style={{ marginBottom: '0.75rem', marginTop: '1.5rem' }}>
        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.65rem' }}>
          Recommendation / Review
        </div>
      </section>

      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))', 
        gap: '1.5rem'
      }}>
        <RecentRecommendations />
        <PendingReviews />
      </div>

      <section style={{ marginBottom: '0.75rem', marginTop: '1.5rem' }}>
        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.65rem' }}>
          Validation / Stability
        </div>
      </section>

      <ValidationHub />
    </div>
    </ConsolePageFrame>
  );
}
