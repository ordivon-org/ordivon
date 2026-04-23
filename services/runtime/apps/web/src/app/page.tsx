import SystemStatusBar from '@/components/status/SystemStatusBar';
import QuickAnalyze from '@/components/features/dashboard/QuickAnalyze';
import LatestDecisionList from '@/components/features/dashboard/LatestDecisionList';
import RiskSnapshot from '@/components/features/dashboard/RiskSnapshot';
import LatestReportsList from '@/components/features/dashboard/LatestReportsList';
import EvalStatus from '@/components/features/dashboard/EvalStatus';
import RecentRecommendations from '@/components/features/dashboard/RecentRecommendations';
import PendingReviews from '@/components/features/dashboard/PendingReviews';
import ValidationHub from '@/components/features/validation/ValidationHub';
import { ConsoleSection } from '@/components/layout/ConsoleSection';
import { MainContentGrid } from '@/components/layout/MainContentGrid';
import { PageHeader } from '@/components/layout/PageHeader';
import { ConsolePageFrame } from '@/components/workspace/ConsolePageFrame';

export default function Dashboard() {
  return (
    <ConsolePageFrame>
      <div className="console-page dashboard-page">
      <PageHeader
        eyebrow="Experience / Command Center"
        title="Command Center"
        description="Live command center for current system status, recommendation previews, review queue previews, and product-level diagnostics."
      />

      <SystemStatusBar />

      <ConsoleSection
        title="Action Entry"
        description="Use the command center to seed a new workflow run. Deep execution still belongs in the analyze workspace."
      >
        <QuickAnalyze />
      </ConsoleSection>

      <ConsoleSection
        title="Audit / Decision / Report"
        description="Preview decision and risk surfaces without turning the command center into a deep work page."
      >
        <MainContentGrid columns="two-up">
          <LatestDecisionList />
          <RiskSnapshot />
        </MainContentGrid>
      </ConsoleSection>

      <ConsoleSection
        title="Reports / Diagnostics"
        description="Operational and reporting surfaces stay visible here so the command center retains system awareness."
      >
        <MainContentGrid columns="two-up">
          <LatestReportsList />
          <EvalStatus />
        </MainContentGrid>
      </ConsoleSection>

      <ConsoleSection
        title="Recommendation / Review"
        description="Keep these as previews and jump points. Recommendation follow-through and deep supervision still belong in the review workbench."
      >
        <MainContentGrid columns="two-up">
          <RecentRecommendations />
          <PendingReviews />
        </MainContentGrid>
      </ConsoleSection>

      <ConsoleSection
        title="Validation / Stability"
        description="Validation and stability stay visible at the command-center layer without replacing execution or supervision ownership."
      >
        <ValidationHub />
      </ConsoleSection>
      </div>
    </ConsolePageFrame>
  );
}
