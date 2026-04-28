"use client";
/** Shadow Policy Workbench — C14 from Console Inventory.
 *  Phase 6D MVP. Preview/advisory only.
 *  No active policy. No runtime enforcement. Sample data only. */

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

/* ── Sample data — all SAMPLE, no real policies ─────────────── */

const SAMPLE_EVIDENCE = [
  { ref_type: "candidate_rule", ref_id: "CR-DEP-001", freshness: "current" as const },
  { ref_type: "lesson",          ref_id: "L-042",      freshness: "current" as const },
  { ref_type: "review",          ref_id: "R-017",      freshness: "current" as const },
  { ref_type: "eval_result",     ref_id: "eval-df-005", freshness: "current" as const },
  { ref_type: "ci_artifact",     ref_id: "build-99",   freshness: "stale" as const },
];

const SAMPLE_POLICIES = [
  {
    policy_id: "POL-DOGFOOD-001",
    title: "Trusted Dependabot dependency-only PRs with fresh CI and evidence may be recommended for human merge.",
    state: "active_shadow" as const,
    evidence_count: 5,
    shadow_summary: "3× WOULD RECOMMEND MERGE (sentry-sdk, uvicorn, @types/node). 1× WOULD HOLD (React CI failure). 1× WOULD ESCALATE (stale evidence). Confidence: 0.85.",
    approval_outcome: "approved_for_shadow" as const,
    owner: "alice",
  },
  {
    policy_id: "POL-PENDING-002",
    title: "CodeQL medium-severity findings require human triage before merge.",
    state: "draft" as const,
    evidence_count: 1,
    shadow_summary: "Single ci_artifact evidence — insufficient for activation. Shadow verdict: WOULD_ESCALATE.",
    approval_outcome: "needs_more_evidence" as const,
    owner: "bob",
  },
];

const SHADOW_VERDICTS = [
  { case_id: "DF-005", description: "PR #5 sentry-sdk: dependency-only, fresh CI", verdict: "would_recommend_merge" as const, confidence: 0.85 },
  { case_id: "DF-006", description: "PR #6 uvicorn: dependency-only, fresh CI", verdict: "would_recommend_merge" as const, confidence: 0.85 },
  { case_id: "DF-008", description: "PR #8 @types/node: type-def, fresh CI", verdict: "would_recommend_merge" as const, confidence: 0.85 },
  { case_id: "DF-007", description: "PR #7 React: CI failure on frontend", verdict: "would_hold" as const, confidence: 0.90 },
  { case_id: "DF-STALE", description: "Stale governance evidence", verdict: "would_escalate" as const, confidence: 0.80 },
];

const ROLLBACK_CONTRACT = {
  trigger: "false_positive_rate > 5%",
  authorized_by: "alice",
  method: "state_transition",
  blast_radius: "CI gate repo-governance-pr",
  target_recovery_time: "seconds",
  post_rollback_reviewer: "bob",
};

export default function ShadowPolicyWorkbenchPage() {
  return (
    <div className="console-page ordivon-workbench" data-testid="shadow-policy-workbench">
      <GovernanceStyles />

      <PreviewDataBanner />
      <AdvisoryBoundaryBanner />

      {/* ── Header ─────────────────────────────────────────── */}
      <section>
        <h1 style={{ fontSize: "1.5rem", fontWeight: 700, margin: 0 }}>Shadow Policy Workbench</h1>
        <p style={{ color: "var(--text-muted)", marginTop: "0.3rem" }}>
          Preview and review shadow policy evaluations before any activation decision.
          All policies are advisory-only. No active enforcement.
        </p>
      </section>

      {/* ── Policy Review Cards ────────────────────────────── */}
      <section>
        <h2>Policy Drafts</h2>
        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
          {SAMPLE_POLICIES.map((p) => (
            <PolicyReviewCard key={p.policy_id} policy={p} />
          ))}
        </div>
      </section>

      {/* ── Evidence ───────────────────────────────────────── */}
      <section>
        <h2>Evidence</h2>
        <EvidenceReferenceList refs={SAMPLE_EVIDENCE} />
      </section>

      {/* ── Shadow Evaluation Results ──────────────────────── */}
      <section>
        <h2>Shadow Evaluation Results</h2>
        <table className="ordivon-table">
          <thead>
            <tr>
              <th>Case</th><th>Description</th><th>Verdict</th><th>Confidence</th>
            </tr>
          </thead>
          <tbody>
            {SHADOW_VERDICTS.map((sv) => (
              <tr key={sv.case_id}>
                <td className="ordivon-mono">{sv.case_id}</td>
                <td>{sv.description}</td>
                <td><ShadowVerdictBadge verdict={sv.verdict} /></td>
                <td>{(sv.confidence * 100).toFixed(0)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {/* ── Rollback Contract ──────────────────────────────── */}
      <section>
        <h2>Rollback Contract</h2>
        <div className="console-card console-card--soft" data-testid="rollback-contract">
          <table className="ordivon-table">
            <tbody>
              {Object.entries(ROLLBACK_CONTRACT).map(([k, v]) => (
                <tr key={k}>
                  <td style={{ color: "var(--text-muted)", fontWeight: 600, width: "200px" }}>{k.replace(/_/g, " ")}</td>
                  <td className="ordivon-mono">{String(v)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* ── Disabled Actions ───────────────────────────────── */}
      <section>
        <h2>Actions</h2>
        <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
          <DisabledHighRiskAction
            action="Activate Policy (active_enforced)"
            reason="active_enforced is DEFERRED (Phase 5 NO-GO). Shadow evaluation must run for ≥3 months with real data before activation review."
          />
          <DisabledHighRiskAction
            action="Enable Auto-Merge"
            reason="Auto-merge is NOT ALLOWED. Requires ≥3 months clean Dependabot history + explicit human approval gate."
          />
        </div>
      </section>

      <PreviewDataBanner />
    </div>
  );
}
