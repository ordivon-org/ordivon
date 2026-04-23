import { MonitoringHistoryPanel } from '@/components/features/history/MonitoringHistoryPanel';
import { ConsoleSection } from '@/components/layout/ConsoleSection';
import { PageHeader } from '@/components/layout/PageHeader';
import { ConsolePageFrame } from '@/components/workspace/ConsolePageFrame';

export default function HistoryPage() {
  return (
    <ConsolePageFrame>
      <div className="console-page history-page">
        <PageHeader
          eyebrow="Internal / Monitoring Inspector"
          title="Operational History"
          description="Internal monitoring and recovery inspector backed by the current health history API. These signals support operations and incident response; they do not create business truth."
        />

        <ConsoleSection
          title="Monitoring / Recovery"
          description="Use this surface to inspect blocked reasons, recovery actions, and scheduler activity without turning monitoring into the business record."
        >
          <MonitoringHistoryPanel />
        </ConsoleSection>
      </div>
    </ConsolePageFrame>
  );
}
