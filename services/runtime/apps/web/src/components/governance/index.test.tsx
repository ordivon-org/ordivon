import { render, screen } from "@testing-library/react";
import { describe, expect, test } from "vitest";

import {
  EvidenceFreshnessBadge,
  ActorIdentityBadge,
  PolicyStateBadge,
  ShadowVerdictBadge,
  ApprovalOutcomeBadge,
  AdvisoryBoundaryBanner,
  PreviewDataBanner,
  DisabledHighRiskAction,
  EvidenceReferenceList,
  PolicyReviewCard,
  GovernanceStyles,
} from "@/components/governance";

/* ═══════════════════════════════════════════════════════════════════
   EvidenceFreshnessBadge
   ═══════════════════════════════════════════════════════════════════ */

describe("EvidenceFreshnessBadge", () => {
  test("renders CURRENT state", () => {
    render(<EvidenceFreshnessBadge freshness="current" />);
    expect(screen.getByText("CURRENT")).toBeDefined();
  });

  test("renders STALE state", () => {
    render(<EvidenceFreshnessBadge freshness="stale" />);
    expect(screen.getByText("STALE")).toBeDefined();
  });

  test("renders REGENERATED state", () => {
    render(<EvidenceFreshnessBadge freshness="regenerated" />);
    expect(screen.getByText("REGENERATED")).toBeDefined();
  });

  test("renders MISSING state", () => {
    render(<EvidenceFreshnessBadge freshness="missing" />);
    expect(screen.getByText("MISSING")).toBeDefined();
  });
});

/* ═══════════════════════════════════════════════════════════════════
   ActorIdentityBadge
   ═══════════════════════════════════════════════════════════════════ */

describe("ActorIdentityBadge", () => {
  test("renders dependabot actor", () => {
    render(<ActorIdentityBadge actor="dependabot" />);
    expect(screen.getByText("Dependabot")).toBeDefined();
  });

  test("renders human actor", () => {
    render(<ActorIdentityBadge actor="human" />);
    expect(screen.getByText("Human")).toBeDefined();
  });

  test("renders unknown actor", () => {
    render(<ActorIdentityBadge actor="unknown" />);
    expect(screen.getByText("Unknown")).toBeDefined();
  });
});

/* ═══════════════════════════════════════════════════════════════════
   PolicyStateBadge
   ═══════════════════════════════════════════════════════════════════ */

describe("PolicyStateBadge", () => {
  test("active_shadow shows ADVISORY ONLY label", () => {
    render(<PolicyStateBadge state="active_shadow" />);
    expect(screen.getByText(/ADVISORY ONLY/i)).toBeDefined();
  });

  test("active_enforced shows NO-GO label", () => {
    render(<PolicyStateBadge state="active_enforced" />);
    expect(screen.getByText(/NO-GO/i)).toBeDefined();
  });

  test("renders draft state", () => {
    render(<PolicyStateBadge state="draft" />);
    expect(screen.getByText("DRAFT")).toBeDefined();
  });
});

/* ═══════════════════════════════════════════════════════════════════
   ShadowVerdictBadge
   ═══════════════════════════════════════════════════════════════════ */

describe("ShadowVerdictBadge", () => {
  test("all verdicts show ADVISORY ONLY label", () => {
    const verdicts = ["would_execute", "would_escalate", "would_reject", "would_hold", "would_recommend_merge", "no_match"] as const;
    for (const v of verdicts) {
      const { container, unmount } = render(<ShadowVerdictBadge verdict={v} />);
      expect(container.textContent).toContain("ADVISORY ONLY");
      unmount();
    }
  });

  test("would_recommend_merge renders", () => {
    render(<ShadowVerdictBadge verdict="would_recommend_merge" />);
    expect(screen.getByText(/WOULD RECOMMEND MERGE/i)).toBeDefined();
  });
});

/* ═══════════════════════════════════════════════════════════════════
   ApprovalOutcomeBadge
   ═══════════════════════════════════════════════════════════════════ */

describe("ApprovalOutcomeBadge", () => {
  test("approved_for_shadow shows shadow mode note", () => {
    render(<ApprovalOutcomeBadge outcome="approved_for_shadow" />);
    expect(screen.getByText(/APPROVED FOR SHADOW/i)).toBeDefined();
    expect(screen.getByText(/Shadow mode only/i)).toBeDefined();
  });
});

/* ═══════════════════════════════════════════════════════════════════
   Banners
   ═══════════════════════════════════════════════════════════════════ */

describe("PreviewDataBanner", () => {
  test("renders PREVIEW label", () => {
    render(<PreviewDataBanner />);
    expect(screen.getByText(/PREVIEW — NOT PRODUCTION/i)).toBeDefined();
    expect(screen.getByText(/sample\/mock data/i)).toBeDefined();
  });
});

describe("AdvisoryBoundaryBanner", () => {
  test("renders ADVISORY ONLY label", () => {
    render(<AdvisoryBoundaryBanner />);
    const elements = screen.getAllByText(/ADVISORY ONLY/i);
    expect(elements.length).toBeGreaterThan(0);
    expect(screen.getByText(/NOT A GOVERNANCE DECISION/i)).toBeDefined();
  });
});

/* ═══════════════════════════════════════════════════════════════════
   DisabledHighRiskAction
   ═══════════════════════════════════════════════════════════════════ */

describe("DisabledHighRiskAction", () => {
  test("renders disabled button with reason", () => {
    render(<DisabledHighRiskAction action="Activate Policy" reason="NO-GO" />);
    const btn = screen.getByRole("button", { name: "Activate Policy" });
    expect(btn).toBeDefined();
    expect((btn as HTMLButtonElement).disabled).toBe(true);
    expect(screen.getByText("NO-GO")).toBeDefined();
  });
});

/* ═══════════════════════════════════════════════════════════════════
   EvidenceReferenceList
   ═══════════════════════════════════════════════════════════════════ */

describe("EvidenceReferenceList", () => {
  test("renders evidence refs with freshness", () => {
    const refs = [
      { ref_type: "candidate_rule", ref_id: "CR-001", freshness: "current" as const },
      { ref_type: "lesson", ref_id: "L-042", freshness: "stale" as const },
    ];
    render(<EvidenceReferenceList refs={refs} />);
    expect(screen.getByText("CR-001")).toBeDefined();
    expect(screen.getAllByText("CURRENT").length).toBeGreaterThan(0);
    expect(screen.getAllByText("STALE").length).toBeGreaterThan(0);
  });

  test("renders empty state", () => {
    render(<EvidenceReferenceList refs={[]} />);
    expect(screen.getByText("No evidence provided.")).toBeDefined();
  });
});

/* ═══════════════════════════════════════════════════════════════════
   PolicyReviewCard
   ═══════════════════════════════════════════════════════════════════ */

describe("PolicyReviewCard", () => {
  test("renders policy with evidence and owner", () => {
    render(<PolicyReviewCard policy={{
      policy_id: "POL-001",
      title: "Test policy title",
      state: "active_shadow",
      evidence_count: 3,
      shadow_summary: "Shadow results summary.",
      approval_outcome: "approved_for_shadow",
      owner: "alice",
    }} />);
    expect(screen.getByText("POL-001")).toBeDefined();
    expect(screen.getByText("Test policy title")).toBeDefined();
    expect(screen.getByText(/3 refs/)).toBeDefined();
    expect(screen.getByText(/alice/)).toBeDefined();
  });
});

/* ═══════════════════════════════════════════════════════════════════
   GovernanceStyles renders without error
   ═══════════════════════════════════════════════════════════════════ */

describe("GovernanceStyles", () => {
  test("renders style tag", () => {
    const { container } = render(<GovernanceStyles />);
    expect(container.querySelector("style")).toBeDefined();
  });
});
