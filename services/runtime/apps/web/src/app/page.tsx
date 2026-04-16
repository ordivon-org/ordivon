import SystemStatusBar from '@/components/status/SystemStatusBar';
import QuickAnalyze from '@/components/features/dashboard/QuickAnalyze';
import LatestDecisionList from '@/components/features/dashboard/LatestDecisionList';
import RiskSnapshot from '@/components/features/dashboard/RiskSnapshot';
import LatestReportsList from '@/components/features/dashboard/LatestReportsList';
import EvalStatus from '@/components/features/dashboard/EvalStatus';
import RecentRecommendations from '@/components/features/dashboard/RecentRecommendations';
import PendingReviews from '@/components/features/dashboard/PendingReviews';
import ValidationHub from '@/components/features/validation/ValidationHub';

export default function Dashboard() {
  return (
    <div className="dashboard-page">
      <header style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>Dashboard</h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Welcome back to PFIOS Command Surface. All systems operational.</p>
      </header>

      {/* 1. System Status Bar (Status & Verification) */}
      <SystemStatusBar />

      {/* 2. Quick Analyze Panel (Command Execution) */}
      <QuickAnalyze />

      {/* Grid Layout for Insights & Governance */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))', 
        gap: '1.5rem',
        marginBottom: '1.5rem'
      }}>
        {/* 3. Latest Decisions */}
        <LatestDecisionList />
        
        {/* 4. Risk & Governance Snapshot */}
        <RiskSnapshot />
      </div>

      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))', 
        gap: '1.5rem'
      }}>
        {/* 5. Latest Reports Archive */}
        <LatestReportsList />

        {/* 6. Evaluation Scorecard (Step 8.4 Output) */}
        <EvalStatus />
      </div>

      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))', 
        gap: '1.5rem',
        marginTop: '1.5rem'
      }}>
        {/* 7. Business Lifecycle Closure - Step 10 */}
        <RecentRecommendations />
        <PendingReviews />
      </div>

      {/* 8. Stability & Real Usage Trace - Step 11 */}
      <ValidationHub />
    </div>
  );
}
