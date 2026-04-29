"use client";
/** Ordivon Governance UI Components — Phase 6C Runtime Baseline.
 *  Pure CSS + React. No external dependencies.
 *  All components are preview/prototype — not production. */

import React from "react";

/* ═══════════════════════════════════════════════════════════════════
   EvidenceFreshnessBadge
   ═══════════════════════════════════════════════════════════════════ */

type Freshness = "current" | "stale" | "regenerated" | "missing" | "partial";

const FRESHNESS_STYLE: Record<Freshness, { bg: string; fg: string; label: string }> = {
  current:      { bg: "var(--ordivon-evidence-current-bg)", fg: "var(--ordivon-evidence-current)", label: "CURRENT" },
  stale:        { bg: "var(--ordivon-evidence-stale-bg)",   fg: "var(--ordivon-evidence-stale)",   label: "STALE" },
  regenerated:  { bg: "var(--ordivon-evidence-regenerated-bg)", fg: "var(--ordivon-evidence-regenerated)", label: "REGENERATED" },
  missing:      { bg: "var(--ordivon-evidence-missing-bg)", fg: "var(--ordivon-evidence-missing)", label: "MISSING" },
  partial:      { bg: "var(--ordivon-evidence-stale-bg)",   fg: "var(--ordivon-evidence-stale)",   label: "PARTIAL" },
};

export function EvidenceFreshnessBadge({ freshness }: { freshness: Freshness }) {
  const s = FRESHNESS_STYLE[freshness] ?? FRESHNESS_STYLE.missing;
  return (
    <span className="ordivon-badge" style={{ background: s.bg, color: s.fg, borderColor: s.fg }}>
      <span className="ordivon-badge__dot" style={{ background: s.fg }} />
      {s.label}
    </span>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   ActorIdentityBadge
   ═══════════════════════════════════════════════════════════════════ */

type Actor = "human" | "dependabot" | "ai_agent" | "workflow" | "unknown";

const ACTOR_COLOR: Record<Actor, string> = {
  human:      "var(--ordivon-actor-human)",
  dependabot: "var(--ordivon-actor-dependabot)",
  ai_agent:   "var(--ordivon-actor-ai-agent)",
  workflow:   "var(--ordivon-actor-workflow)",
  unknown:    "var(--ordivon-actor-unknown)",
};

const ACTOR_LABEL: Record<Actor, string> = {
  human: "Human", dependabot: "Dependabot", ai_agent: "AI Agent", workflow: "Workflow", unknown: "Unknown",
};

export function ActorIdentityBadge({ actor }: { actor: Actor }) {
  return (
    <span className="ordivon-badge" style={{ color: ACTOR_COLOR[actor], borderColor: ACTOR_COLOR[actor] }}>
      {ACTOR_LABEL[actor]}
    </span>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   PolicyStateBadge
   ═══════════════════════════════════════════════════════════════════ */

type PolicyStateLabel = "draft" | "proposed" | "approved" | "active_shadow" | "active_enforced" | "deprecated" | "rolled_back" | "rejected";

const POLICY_STATE: Record<PolicyStateLabel, { fg: string; label: string; note?: string }> = {
  draft:           { fg: "var(--ordivon-policy-draft)",      label: "DRAFT" },
  proposed:        { fg: "var(--ordivon-policy-proposed)",  label: "PROPOSED" },
  approved:        { fg: "var(--ordivon-policy-approved)",  label: "APPROVED" },
  active_shadow:   { fg: "var(--ordivon-policy-shadow)",    label: "ACTIVE SHADOW", note: "ADVISORY ONLY — Runtime Deferred" },
  active_enforced: { fg: "var(--ordivon-policy-enforced)",  label: "ACTIVE ENFORCED", note: "NOT AVAILABLE (Phase 5 NO-GO)" },
  deprecated:      { fg: "var(--ordivon-policy-deprecated)", label: "DEPRECATED" },
  rolled_back:     { fg: "var(--ordivon-policy-rolled-back)", label: "ROLLED BACK" },
  rejected:        { fg: "var(--ordivon-policy-rejected)",  label: "REJECTED" },
};

export function PolicyStateBadge({ state }: { state: PolicyStateLabel }) {
  const s = POLICY_STATE[state] ?? POLICY_STATE.draft;
  return (
    <span className="ordivon-badge" style={{ color: s.fg, borderColor: s.fg }}>
      {s.label}
      {s.note && <span className="ordivon-badge__note"> — {s.note}</span>}
    </span>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   ShadowVerdictBadge
   ═══════════════════════════════════════════════════════════════════ */

type ShadowV = "would_execute" | "would_escalate" | "would_reject" | "would_hold" | "would_recommend_merge" | "no_match";

const SHADOW_COLOR: Record<ShadowV, string> = {
  would_execute:         "var(--ordivon-shadow-execute)",
  would_escalate:        "var(--ordivon-shadow-escalate)",
  would_reject:          "var(--ordivon-shadow-reject)",
  would_hold:            "var(--ordivon-shadow-hold)",
  would_recommend_merge: "var(--ordivon-shadow-recommend)",
  no_match:              "var(--ordivon-shadow-no-match)",
};

const SHADOW_LABEL: Record<ShadowV, string> = {
  would_execute: "WOULD EXECUTE", would_escalate: "WOULD ESCALATE", would_reject: "WOULD REJECT",
  would_hold: "WOULD HOLD", would_recommend_merge: "WOULD RECOMMEND MERGE", no_match: "NO MATCH",
};

export function ShadowVerdictBadge({ verdict }: { verdict: ShadowV }) {
  return (
    <span className="ordivon-badge" style={{ color: SHADOW_COLOR[verdict], borderColor: SHADOW_COLOR[verdict] }}>
      {SHADOW_LABEL[verdict]}
      <span className="ordivon-badge__note"> — ADVISORY ONLY</span>
    </span>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   ApprovalOutcomeBadge
   ═══════════════════════════════════════════════════════════════════ */

type ApprovalO = "approved_for_shadow" | "rejected" | "needs_more_evidence" | "needs_more_shadow" | "deferred";

const APPROVAL_STYLE: Record<ApprovalO, { fg: string; bg: string; label: string; note?: string }> = {
  approved_for_shadow: { fg: "var(--ordivon-approval-shadow)", bg: "var(--ordivon-approval-shadow-bg)", label: "APPROVED FOR SHADOW", note: "Shadow mode only — not active enforcement" },
  rejected:            { fg: "var(--ordivon-approval-rejected)", bg: "transparent", label: "REJECTED" },
  needs_more_evidence: { fg: "var(--ordivon-approval-needs)",    bg: "transparent", label: "NEEDS MORE EVIDENCE" },
  needs_more_shadow:   { fg: "var(--ordivon-approval-needs)",    bg: "transparent", label: "NEEDS MORE SHADOW" },
  deferred:            { fg: "var(--ordivon-approval-deferred)", bg: "transparent", label: "DEFERRED" },
};

export function ApprovalOutcomeBadge({ outcome }: { outcome: ApprovalO }) {
  const s = APPROVAL_STYLE[outcome] ?? APPROVAL_STYLE.deferred;
  return (
    <span className="ordivon-badge" style={{ color: s.fg, borderColor: s.fg, background: s.bg }}>
      {s.label}
      {s.note && <span className="ordivon-badge__note"> — {s.note}</span>}
    </span>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   AdvisoryBoundaryBanner
   ═══════════════════════════════════════════════════════════════════ */

export function AdvisoryBoundaryBanner({ children }: { children?: React.ReactNode }) {
  return (
    <div className="ordivon-banner" style={{ background: "var(--ordivon-banner-advisory-bg)", borderColor: "var(--ordivon-banner-advisory-border)" }}>
      <strong>⚠ ADVISORY ONLY — NOT A GOVERNANCE DECISION</strong>
      <p>This surface shows advisory/shadow evaluation results. These are classifications, not enforced policies. No active policy is created by viewing this surface.</p>
      {children}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   PreviewDataBanner
   ═══════════════════════════════════════════════════════════════════ */

export function PreviewDataBanner() {
  return (
    <div className="ordivon-banner" style={{ background: "var(--ordivon-banner-preview-bg)", borderColor: "var(--ordivon-banner-preview-border)" }}>
      <strong>⚠ PREVIEW — NOT PRODUCTION</strong>
      <p>Data shown is sample/mock data for design validation. No real trades, policies, or user data are displayed.</p>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   DisabledHighRiskAction
   ═══════════════════════════════════════════════════════════════════ */

export function DisabledHighRiskAction({ action, reason }: { action: string; reason: string }) {
  return (
    <div className="ordivon-disabled-action" style={{ background: "var(--ordivon-action-disabled-bg)", color: "var(--ordivon-action-disabled-text)" }}>
      <button disabled className="ordivon-btn ordivon-btn--disabled">{action}</button>
      <span className="ordivon-disabled-action__reason">{reason}</span>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   EvidenceReferenceList
   ═══════════════════════════════════════════════════════════════════ */

type EvidenceRef = { ref_type: string; ref_id: string; freshness: Freshness };

export function EvidenceReferenceList({ refs }: { refs: EvidenceRef[] }) {
  if (!refs.length) return <p className="ordivon-empty">No evidence provided.</p>;
  return (
    <div className="ordivon-evidence-list">
      <h4 className="console-card__title">EVIDENCE REFERENCES ({refs.length})</h4>
      <table className="ordivon-table">
        <thead><tr><th>Type</th><th>ID</th><th>Freshness</th></tr></thead>
        <tbody>
          {refs.map((r, i) => (
            <tr key={i}>
              <td className="ordivon-mono">{r.ref_type}</td>
              <td className="ordivon-mono">{r.ref_id}</td>
              <td><EvidenceFreshnessBadge freshness={r.freshness} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   PolicyReviewCard
   ═══════════════════════════════════════════════════════════════════ */

type PolicyReview = {
  policy_id: string;
  title: string;
  state: PolicyStateLabel;
  evidence_count: number;
  shadow_summary: string;
  approval_outcome: ApprovalO;
  owner: string;
};

export function PolicyReviewCard({ policy }: { policy: PolicyReview }) {
  return (
    <div className="console-card console-card--soft ordivon-policy-card">
      <div className="ordivon-policy-card__header">
        <span className="ordivon-mono">{policy.policy_id}</span>
        <PolicyStateBadge state={policy.state} />
      </div>
      <p className="ordivon-policy-card__title">{policy.title}</p>
      <div className="ordivon-policy-card__meta">
        <span>Evidence: {policy.evidence_count} refs</span>
        <span>Owner: {policy.owner}</span>
      </div>
      <p className="console-card__copy">{policy.shadow_summary}</p>
      <div className="ordivon-policy-card__footer">
        <ApprovalOutcomeBadge outcome={policy.approval_outcome} />
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   CandidateRuleStatusLabel — for Knowledge / CandidateRule surfaces
   ═══════════════════════════════════════════════════════════════════ */

type CRStatus = "draft" | "under_review" | "accepted_candidate" | "rejected";

const CR_STATUS_MAP: Record<CRStatus, { fg: string; label: string }> = {
  draft:              { fg: "var(--ordivon-policy-draft)",  label: "DRAFT" },
  under_review:       { fg: "var(--ordivon-policy-proposed)", label: "UNDER REVIEW" },
  accepted_candidate: { fg: "var(--ordivon-policy-shadow)",  label: "ACCEPTED CANDIDATE" },
  rejected:           { fg: "var(--ordivon-policy-rejected)", label: "REJECTED" },
};

export function CandidateRuleStatusLabel({ status, sourceCount = 0 }: { status: CRStatus; sourceCount?: number }) {
  const s = CR_STATUS_MAP[status] ?? CR_STATUS_MAP.draft;
  return (
    <span className="ordivon-badge" style={{ color: s.fg, borderColor: s.fg }}>
      {s.label}
      {sourceCount > 0 && <span className="ordivon-badge__note"> — {sourceCount} source ref{sourceCount !== 1 ? "s" : ""}</span>}
    </span>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   ReviewGovernanceBanner — governance context for review surfaces
   ═══════════════════════════════════════════════════════════════════ */

export function CandidateRuleIsNotPolicyBanner() {
  return (
    <div className="ordivon-banner" style={{ background: "var(--ordivon-banner-advisory-bg)", borderColor: "var(--ordivon-banner-advisory-border)", fontSize: "0.78rem" }}>
      <strong>⚠ CandidateRule ≠ Policy</strong>
      <p>A CandidateRule is a learned pattern, not an active constraint. It must pass through human review, PolicyProposal, shadow evaluation, and approval before it can become a Policy. No active policy is created from this surface.</p>
    </div>
  );
}

export function ReviewAdvisoryBanner() {
  return (
    <div className="ordivon-banner" style={{ background: "var(--ordivon-banner-advisory-bg)", borderColor: "var(--ordivon-banner-advisory-border)", fontSize: "0.78rem" }}>
      <strong>⚠ REVIEW GUIDANCE — ADVISORY ONLY</strong>
      <p>AI-generated review suggestions, lesson extractions, and candidate rule drafts are advisory. They inform human judgment but do not replace it. All governance decisions require explicit human review.</p>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   FinanceLivePrepBanner — no-live-trading warning
   ═══════════════════════════════════════════════════════════════════ */

export function FinanceLivePrepBanner() {
  return (
    <div className="ordivon-banner" style={{ background: "var(--ordivon-banner-preview-bg)", borderColor: "var(--ordivon-banner-preview-border)" }}>
      <strong>⚠ PREVIEW — NOT PRODUCTION</strong>
      <p>No live trading is enabled. No broker API is connected. This is a governance prep surface for future manual trading workflows. All data is sample/mock data only.</p>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   FinanceConstitutionSummary — manual-only trading constraints
   ═══════════════════════════════════════════════════════════════════ */

type ConstitutionRule = { rule: string; value: string };

export function FinanceConstitutionSummary({ rules }: { rules: ConstitutionRule[] }) {
  return (
    <div className="ordivon-evidence-list">
      <h3 className="console-card__title">FINANCE CONSTITUTION</h3>
      <table className="ordivon-table">
        <thead><tr><th>Constraint</th><th>Value</th></tr></thead>
        <tbody>
          {rules.map((r, i) => (
            <tr key={i}><td>{r.rule}</td><td className="ordivon-mono">{r.value}</td></tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   RiskBudgetPanel — sample risk budget card
   ═══════════════════════════════════════════════════════════════════ */

type RiskBudget = {
  totalCapital: string;
  maxTotalLoss: string;
  maxPerTradeRisk: string;
  dailyStopPct: string;
  streakStopLosses: string;
};

export function RiskBudgetPanel({ budget }: { budget: RiskBudget }) {
  return (
    <div className="console-card console-card--soft">
      <h3 className="console-card__title">RISK BUDGET (SAMPLE)</h3>
      <div className="ordivon-workbench__row" style={{ gap: "1.5rem", fontSize: "0.82rem" }}>
        <div><span style={{ color: "var(--text-muted)" }}>Total Capital</span><br /><strong>{budget.totalCapital}</strong></div>
        <div><span style={{ color: "var(--text-muted)" }}>Max Total Loss</span><br /><strong style={{ color: "var(--ordivon-shadow-reject)" }}>{budget.maxTotalLoss}</strong></div>
        <div><span style={{ color: "var(--text-muted)" }}>Per-Trade Risk</span><br /><strong style={{ color: "var(--ordivon-shadow-escalate)" }}>{budget.maxPerTradeRisk}</strong></div>
        <div><span style={{ color: "var(--text-muted)" }}>Daily Stop</span><br /><strong>{budget.dailyStopPct}</strong></div>
        <div><span style={{ color: "var(--text-muted)" }}>Streak Stop</span><br /><strong>{budget.streakStopLosses}</strong></div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   DecisionIntakePreview — sample intake form
   ═══════════════════════════════════════════════════════════════════ */

type IntakeRow = { label: string; value: string };

export function DecisionIntakePreview({ rows }: { rows: IntakeRow[] }) {
  return (
    <div className="console-card console-card--soft">
      <h3 className="console-card__title">DECISION INTAKE (SAMPLE)</h3>
      <table className="ordivon-table">
        <thead><tr><th>Field</th><th>Value</th></tr></thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i}><td style={{ width: "33%" }}>{r.label}</td><td className="ordivon-mono">{r.value}</td></tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   PlanReceiptPreview — sample plan receipt
   ═══════════════════════════════════════════════════════════════════ */

type ReceiptRow = { label: string; value: string; allowed?: boolean };

export function PlanReceiptPreview({ rows }: { rows: ReceiptRow[] }) {
  return (
    <div className="console-card console-card--soft">
      <h3 className="console-card__title">PLAN RECEIPT (SAMPLE)</h3>
      <table className="ordivon-table">
        <thead><tr><th>Field</th><th>Value</th></tr></thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i}>
              <td style={{ width: "33%" }}>{r.label}</td>
              <td className="ordivon-mono">
                {r.value}
                {r.allowed === false && <span style={{ color: "var(--ordivon-shadow-reject)", marginLeft: "0.6rem" }}>FORBIDDEN</span>}
                {r.allowed === true && <span style={{ color: "var(--ordivon-shadow-execute)", marginLeft: "0.6rem" }}>ALLOWED</span>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   OutcomeCapturePreview — sample outcome capture
   ═══════════════════════════════════════════════════════════════════ */

export function OutcomeCapturePreview({ rows }: { rows: IntakeRow[] }) {
  return (
    <div className="console-card console-card--soft">
      <h3 className="console-card__title">MANUAL OUTCOME CAPTURE (SAMPLE)</h3>
      <table className="ordivon-table">
        <thead><tr><th>Field</th><th>Value</th></tr></thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i}><td style={{ width: "33%" }}>{r.label}</td><td className="ordivon-mono">{r.value}</td></tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   PostTradeReviewQueuePreview — sample review queue
   ═══════════════════════════════════════════════════════════════════ */

type ReviewEntry = { status: string; trade: string; candidateLesson: string; crStatus?: CRStatus };

export function PostTradeReviewQueuePreview({ entries }: { entries: ReviewEntry[] }) {
  return (
    <div className="console-card console-card--soft">
      <h3 className="console-card__title">POST-TRADE REVIEW QUEUE (SAMPLE)</h3>
      <table className="ordivon-table">
        <thead><tr><th>Status</th><th>Trade</th><th>Candidate Lesson</th><th>CR Status</th></tr></thead>
        <tbody>
          {entries.map((e, i) => (
            <tr key={i}>
              <td><span className="ordivon-badge" style={{ color: e.status === "PENDING" ? "var(--ordivon-evidence-stale)" : "var(--ordivon-evidence-current)", borderColor: e.status === "PENDING" ? "var(--ordivon-evidence-stale)" : "var(--ordivon-evidence-current)" }}>{e.status}</span></td>
              <td className="ordivon-mono">{e.trade}</td>
              <td className="ordivon-mono" style={{ fontSize: "0.7rem" }}>{e.candidateLesson}</td>
              <td>{e.crStatus ? <CandidateRuleStatusLabel status={e.crStatus} /> : <span style={{ color: "var(--text-muted)", fontStyle: "italic" }}>—</span>}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   Shared badge styles (append to globals.css via inline)
   ═══════════════════════════════════════════════════════════════════ */

export function GovernanceStyles() {
  return (
    <style>{`
      .ordivon-badge {
        display: inline-flex; align-items: center; gap: 0.35rem;
        padding: 0.25rem 0.6rem; border-radius: var(--radius-chip);
        border: 1px solid; font-size: 0.7rem; font-weight: 600;
        letter-spacing: 0.04em; line-height: 1.2;
      }
      .ordivon-badge__dot { width: 6px; height: 6px; border-radius: 50%; }
      .ordivon-badge__note { font-weight: 400; opacity: 0.75; font-size: 0.65rem; margin-left: 0.2rem; }
      .ordivon-banner {
        padding: 0.9rem 1.2rem; border-radius: var(--radius-card);
        border: 1px solid; font-size: 0.82rem; line-height: 1.55;
      }
      .ordivon-banner p { margin: 0.35rem 0 0; opacity: 0.85; }
      .ordivon-banner strong { font-size: 0.85rem; }
      .ordivon-disabled-action {
        display: inline-flex; align-items: center; gap: 0.75rem;
        padding: 0.5rem 0.9rem; border-radius: var(--radius-card);
        font-size: 0.78rem;
      }
      .ordivon-disabled-action__reason { opacity: 0.8; }
      .ordivon-btn--disabled {
        padding: 0.4rem 0.9rem; border-radius: var(--radius-chip);
        border: 1px solid var(--ordivon-action-disabled-text);
        background: transparent; color: var(--ordivon-action-disabled-text);
        cursor: not-allowed; font-size: 0.78rem;
      }
      .ordivon-btn { cursor: pointer; font-weight: 600; }
      .ordivon-mono { font-family: var(--font-mono); font-size: 0.72rem; }
      .ordivon-empty { color: var(--text-muted); font-style: italic; padding: 0.5rem 0; }
      .ordivon-table { width: 100%; border-collapse: collapse; font-size: 0.78rem; }
      .ordivon-table th { text-align: left; padding: 0.4rem 0.6rem; color: var(--text-muted); font-weight: 600; border-bottom: 1px solid var(--border-color); }
      .ordivon-table td { padding: 0.5rem 0.6rem; border-bottom: 1px solid rgba(137,176,255,0.06); }
      .ordivon-evidence-list { display: flex; flex-direction: column; gap: 0.5rem; }
      .ordivon-policy-card { display: flex; flex-direction: column; gap: 0.6rem; }
      .ordivon-policy-card__header { display: flex; justify-content: space-between; align-items: center; }
      .ordivon-policy-card__title { font-size: 0.92rem; font-weight: 600; line-height: 1.4; }
      .ordivon-policy-card__meta { display: flex; gap: 1.5rem; font-size: 0.74rem; color: var(--text-muted); }
      .ordivon-policy-card__footer { display: flex; gap: 0.5rem; }
      .ordivon-workbench { display: flex; flex-direction: column; gap: 1.25rem; }
      .ordivon-workbench h2 { font-size: 1.1rem; font-weight: 600; margin: 0; }
      .ordivon-workbench h3 { font-size: 0.85rem; color: var(--text-muted); margin: 0 0 0.3rem; text-transform: uppercase; letter-spacing: 0.08em; }
      .ordivon-workbench__row { display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center; }
    `}</style>
  );
}
