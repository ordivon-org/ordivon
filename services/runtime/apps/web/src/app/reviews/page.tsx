import { Suspense } from "react";

import { ReviewConsole } from "@/components/features/reviews/ReviewConsole";
import { ConsolePageFrame } from "@/components/workspace/ConsolePageFrame";
import { ReviewAdvisoryBanner, CandidateRuleIsNotPolicyBanner, GovernanceStyles } from "@/components/governance";

export default function ReviewsPage() {
  return (
    <ConsolePageFrame>
      <GovernanceStyles />
      <ReviewAdvisoryBanner />
      <CandidateRuleIsNotPolicyBanner />
      <Suspense fallback={<div style={{ padding: "1rem", color: "var(--text-muted)" }}>Loading review workbench...</div>}>
        <ReviewConsole />
      </Suspense>
    </ConsolePageFrame>
  );
}
