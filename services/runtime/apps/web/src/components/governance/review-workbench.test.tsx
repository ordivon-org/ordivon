import { render, screen } from "@testing-library/react";
import { describe, expect, test } from "vitest";

import {
  CandidateRuleStatusLabel,
  CandidateRuleIsNotPolicyBanner,
  ReviewAdvisoryBanner,
  DisabledHighRiskAction,
  GovernanceStyles,
} from "@/components/governance";

/* ═══════════════════════════════════════════════════════════════════
   CandidateRuleStatusLabel
   ═══════════════════════════════════════════════════════════════════ */

describe("CandidateRuleStatusLabel", () => {
  test("renders DRAFT status", () => {
    render(<CandidateRuleStatusLabel status="draft" />);
    expect(screen.getByText("DRAFT")).toBeDefined();
  });

  test("renders UNDER REVIEW status", () => {
    render(<CandidateRuleStatusLabel status="under_review" />);
    expect(screen.getByText("UNDER REVIEW")).toBeDefined();
  });

  test("renders ACCEPTED CANDIDATE status", () => {
    render(<CandidateRuleStatusLabel status="accepted_candidate" />);
    expect(screen.getByText("ACCEPTED CANDIDATE")).toBeDefined();
  });

  test("renders REJECTED status", () => {
    render(<CandidateRuleStatusLabel status="rejected" />);
    expect(screen.getByText("REJECTED")).toBeDefined();
  });

  test("shows source count when provided", () => {
    render(<CandidateRuleStatusLabel status="accepted_candidate" sourceCount={3} />);
    expect(screen.getByText(/3 source refs/)).toBeDefined();
  });

  test("shows singular source ref label", () => {
    render(<CandidateRuleStatusLabel status="draft" sourceCount={1} />);
    expect(screen.getByText(/1 source ref\b/)).toBeDefined();
  });
});

/* ═══════════════════════════════════════════════════════════════════
   CandidateRuleIsNotPolicyBanner
   ═══════════════════════════════════════════════════════════════════ */

describe("CandidateRuleIsNotPolicyBanner", () => {
  test("renders CandidateRule ≠ Policy warning", () => {
    render(<CandidateRuleIsNotPolicyBanner />);
    expect(screen.getByText(/CandidateRule ≠ Policy/i)).toBeDefined();
    expect(screen.getByText(/not an active constraint/i)).toBeDefined();
    expect(screen.getByText(/No active policy is created/i)).toBeDefined();
  });
});

/* ═══════════════════════════════════════════════════════════════════
   ReviewAdvisoryBanner
   ═══════════════════════════════════════════════════════════════════ */

describe("ReviewAdvisoryBanner", () => {
  test("renders advisory-only label", () => {
    render(<ReviewAdvisoryBanner />);
    expect(screen.getByText(/REVIEW GUIDANCE/i)).toBeDefined();
    expect(screen.getByText(/ADVISORY ONLY/i)).toBeDefined();
    expect(screen.getByText(/AI-generated review suggestions/i)).toBeDefined();
  });
});

/* ═══════════════════════════════════════════════════════════════════
   DisabledHighRiskAction — verify no activate/promote enabled
   ═══════════════════════════════════════════════════════════════════ */

describe("DisabledHighRiskAction (reviews context)", () => {
  test("promote action is disabled with reason", () => {
    render(
      <DisabledHighRiskAction
        action="Promote to Policy"
        reason="CandidateRule promotion requires ≥3 real interceptions + 2-week observation period. See doctrine §3.6."
      />
    );
    const btn = screen.getByRole("button", { name: "Promote to Policy" });
    expect(btn).toBeDefined();
    expect((btn as HTMLButtonElement).disabled).toBe(true);
    expect(screen.getByText(/≥3 real interceptions/)).toBeDefined();
  });
});

/* ═══════════════════════════════════════════════════════════════════
   GovernanceStyles
   ═══════════════════════════════════════════════════════════════════ */

describe("GovernanceStyles on reviews", () => {
  test("renders style tag", () => {
    const { container } = render(<GovernanceStyles />);
    expect(container.querySelector("style")).toBeDefined();
  });
});
