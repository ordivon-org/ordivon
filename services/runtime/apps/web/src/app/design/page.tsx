"use client";
/** Ordivon Design Workbench — Preview route for governance components.
 *  All data is SAMPLE. No production data. No real policies. */

import React from "react";
import {
  GovernanceStyles,
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
} from "@/components/governance";

const SAMPLE_REFS = [
  { ref_type: "candidate_rule", ref_id: "CR-001", freshness: "current" as const },
  { ref_type: "lesson",          ref_id: "L-042",  freshness: "current" as const },
  { ref_type: "review",          ref_id: "R-017",  freshness: "current" as const },
  { ref_type: "ci_artifact",     ref_id: "build-99", freshness: "stale" as const },
];

const SAMPLE_POLICY: Parameters<typeof PolicyReviewCard>[0]["policy"] = {
  policy_id: "POL-DOGFOOD-001",
  title: "Trusted Dependabot dependency-only PRs with fresh CI and evidence may be recommended for human merge.",
  state: "active_shadow",
  evidence_count: 4,
  shadow_summary: "3× WOULD RECOMMEND MERGE, 1× WOULD HOLD (React CI failure), 1× WOULD ESCALATE (stale evidence). Confidence: 0.85.",
  approval_outcome: "approved_for_shadow",
  owner: "alice",
};

export default function DesignWorkbenchPage() {
  return (
    <div className="console-page ordivon-workbench">
      <GovernanceStyles />

      <PreviewDataBanner />
      <AdvisoryBoundaryBanner />

      {/* ── Evidence Freshness ────────────────────────────────── */}
      <section>
        <h2>EvidenceFreshnessBadge</h2>
        <div className="ordivon-workbench__row">
          <EvidenceFreshnessBadge freshness="current" />
          <EvidenceFreshnessBadge freshness="stale" />
          <EvidenceFreshnessBadge freshness="regenerated" />
          <EvidenceFreshnessBadge freshness="missing" />
          <EvidenceFreshnessBadge freshness="partial" />
        </div>
      </section>

      {/* ── Actor Identity ───────────────────────────────────── */}
      <section>
        <h2>ActorIdentityBadge</h2>
        <div className="ordivon-workbench__row">
          <ActorIdentityBadge actor="human" />
          <ActorIdentityBadge actor="dependabot" />
          <ActorIdentityBadge actor="ai_agent" />
          <ActorIdentityBadge actor="workflow" />
          <ActorIdentityBadge actor="unknown" />
        </div>
      </section>

      {/* ── Policy State ──────────────────────────────────────── */}
      <section>
        <h2>PolicyStateBadge</h2>
        <div className="ordivon-workbench__row">
          <PolicyStateBadge state="draft" />
          <PolicyStateBadge state="proposed" />
          <PolicyStateBadge state="approved" />
          <PolicyStateBadge state="active_shadow" />
          <PolicyStateBadge state="active_enforced" />
          <PolicyStateBadge state="deprecated" />
          <PolicyStateBadge state="rolled_back" />
          <PolicyStateBadge state="rejected" />
        </div>
      </section>

      {/* ── Shadow Verdict ────────────────────────────────────── */}
      <section>
        <h2>ShadowVerdictBadge</h2>
        <div className="ordivon-workbench__row">
          <ShadowVerdictBadge verdict="would_recommend_merge" />
          <ShadowVerdictBadge verdict="would_execute" />
          <ShadowVerdictBadge verdict="would_escalate" />
          <ShadowVerdictBadge verdict="would_hold" />
          <ShadowVerdictBadge verdict="would_reject" />
          <ShadowVerdictBadge verdict="no_match" />
        </div>
      </section>

      {/* ── Approval Outcome ──────────────────────────────────── */}
      <section>
        <h2>ApprovalOutcomeBadge</h2>
        <div className="ordivon-workbench__row">
          <ApprovalOutcomeBadge outcome="approved_for_shadow" />
          <ApprovalOutcomeBadge outcome="rejected" />
          <ApprovalOutcomeBadge outcome="needs_more_evidence" />
          <ApprovalOutcomeBadge outcome="needs_more_shadow" />
          <ApprovalOutcomeBadge outcome="deferred" />
        </div>
      </section>

      {/* ── Disabled High-Risk Actions ────────────────────────── */}
      <section>
        <h2>DisabledHighRiskAction</h2>
        <div className="ordivon-workbench__row">
          <DisabledHighRiskAction action="Activate Policy" reason="active_enforced is DEFERRED (Phase 5 NO-GO). See Phase 5Z red-team closure." />
          <DisabledHighRiskAction action="Enable Live Trading" reason="Finance live trading is DEFERRED (Phase 7 gate). Phase 6 does not enable trading." />
        </div>
      </section>

      {/* ── Evidence Reference List ───────────────────────────── */}
      <section>
        <h2>EvidenceReferenceList</h2>
        <EvidenceReferenceList refs={SAMPLE_REFS} />
      </section>

      {/* ── Policy Review Card ────────────────────────────────── */}
      <section>
        <h2>PolicyReviewCard</h2>
        <PolicyReviewCard policy={SAMPLE_POLICY} />
      </section>

      <PreviewDataBanner />
    </div>
  );
}
