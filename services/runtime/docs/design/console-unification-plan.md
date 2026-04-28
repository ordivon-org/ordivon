# Console Unification Plan

Status: **DOCUMENTED** (Phase 6B)
Date: 2026-04-29
Phase: 6B
Tags: `console`, `unification`, `ui`, `p0`, `implementation`

## 1. Purpose

Define the plan for unifying the existing 7 real consoles under the
Design System baseline and adding the new Shadow Policy Workbench.
P1/P2 consoles receive preview treatment only.

## 2. P0 Console Specifications

### C01 — Command Center

| Property | Value |
|----------|-------|
| Layout | Console Shell + Metric Card Grid |
| Unique Panels | Live Status Overview, Recent Governance Decisions, Active Policy Summary, Quick Actions |
| Governed Objects | Dashboard summary, GovernanceDecision, PolicyRecord count |
| Labels | "Live Data" on production sections, "SAMPLE DATA" on mock sections |
| High-Risk Actions | None (read-only aggregation) |
| Readiness | **Ready** — existing dashboard component, needs token migration |

### C02 — Analyze Workspace

| Property | Value |
|----------|-------|
| Layout | Console Shell + Primary Workbench + Right Inspection Drawer |
| Unique Panels | New Analysis Intake form, Analysis History table, Analysis Detail panel |
| Governed Objects | DecisionIntake, AnalysisResult |
| Labels | "Intake Payload" on submission, "Governance Result" on output |
| High-Risk Actions | Submit analysis (requires intake validation) |
| Readiness | **Ready** — existing component, needs token migration + validation UI |

### C03 — Reviews Workbench

| Property | Value |
|----------|-------|
| Layout | Console Shell + Split Review Layout + Action Rail + Evidence Drawer |
| Unique Panels | Review Queue, Review Detail, Lesson Extraction form, CandidateRule Draft |
| Governed Objects | Review, ReviewDecision, Lesson, CandidateRule |
| Labels | "Review Verdict" + SeverityBadge, "Reviewer: @name" |
| High-Risk Actions | Accept review, Reject review, Extract lesson, Create CandidateRule |
| Readiness | **Ready** — existing component, needs split layout + evidence drawer |

### C05 — State / Trace & Outcome

| Property | Value |
|----------|-------|
| Layout | Console Shell + Timeline Rail + Detail Panel |
| Unique Panels | Decision Trace timeline, Execution Trace, Outcome Timeline |
| Governed Objects | ExecutionReceipt, AuditEvent, FinanceManualOutcome |
| Labels | "Receipt ID: ER-xxx", "Timestamp: ...", "Side Effects: false" |
| High-Risk Actions | None (read-only trace) |
| Readiness | **Ready** — existing component, needs timeline component |

### C06 — Knowledge / Candidate Rule Console

| Property | Value |
|----------|-------|
| Layout | Console Shell + Primary Workbench + Right Inspection Drawer |
| Unique Panels | CandidateRule list + detail, PolicyProposal list, Lessons Library, Evidence Explorer |
| Governed Objects | CandidateRule, PolicyProposal, Lesson, KnowledgeFeedback |
| Labels | "CandidateRule Status: draft/under_review/accepted_candidate", "Source: lesson:L001" |
| High-Risk Actions | Submit for review, Accept candidate, Create PolicyProposal |
| Readiness | **Ready** — existing component, needs CandidateRuleCard + PolicyReviewCard |

### C09 — Governance Decision Console

| Property | Value |
|----------|-------|
| Layout | Console Shell + Timeline Rail + Right Inspection Drawer |
| Unique Panels | Decision History timeline, Approval Queue, Policy Registry viewer |
| Governed Objects | GovernanceDecision, PolicyRecord, ApprovalDecision |
| Labels | **"ADVISORY ONLY"** on shadow decisions, "active_enforced: NOT AVAILABLE" on Policy state |
| High-Risk Actions | **None enabled** — all activation actions disabled (Phase 5 NO-GO) |
| Readiness | **Needs upgrade** — currently preview maturity, needs decision timeline + registry viewer |

### C14 — Shadow Policy Workbench (NEW)

| Property | Value |
|----------|-------|
| Layout | Console Shell + Primary Workbench + Evidence Drawer + Action Rail |
| Unique Panels | Policy Draft Editor, Shadow Evaluation Results, Evidence Gate Output, Approval Workflow |
| Governed Objects | PolicyRecord, ShadowResult, EvidenceGateResult, ApprovalDecision |
| Labels | **"ADVISORY ONLY — No active policy is created"** banner, "READY_FOR_HUMAN_ACTIVATION_REVIEW" on gate output |
| High-Risk Actions | **All disabled** — "active_enforced: DEFERRED (Phase 5 NO-GO)" |
| Readiness | **New build** — no existing UI, highest Phase 6 priority |

## 3. P1 Console Preview Treatment

P1 consoles (Capabilities, Execution, Finance Pack) receive preview treatment only:

- Use Console Shell layout
- Display PreviewBanner: "PREVIEW — NOT PRODUCTION"
- P1 components are placeholder/stub — no production data binding
- High-risk actions disabled

## 4. P2 Console Preview Treatment

P2 consoles (Intelligence, Orchestration, Infrastructure, Adapter) receive:

- Listed in navigation but grayed out with "Future" badge
- No implementation in Phase 6
- No data binding
- Landing page with description + maturity badge only

## 5. Unification Checklist

For each real P0 console:

- [ ] Migrate to Console Shell layout
- [ ] Replace inline styles with Design Tokens
- [ ] Add Top Status Bar (actor, freshness, notifications)
- [ ] Add Left Navigation (layer-grouped)
- [ ] Replace custom badges with Design System badges
- [ ] Add PreviewBanner if maturity=preview
- [ ] Add MockDataLabel if sample data present
- [ ] Disable high-risk actions with reason text
- [ ] Add evidence freshness badges where evidence is shown
- [ ] Add actor identity badges where governed objects are shown
- [ ] Verify Policy safety labels on all Policy surfaces

## 6. Implementation Order

1. **Console Shell + Design Tokens** — foundation for all surfaces
2. **Shadow Policy Workbench (C14)** — highest-value new surface
3. **Governance Console Upgrade (C09)** — preview → real
4. **Reviews Workbench Unification (C03)** — split layout + evidence drawer
5. **Knowledge Console Unification (C06)** — CandidateRuleCard + PolicyReviewCard
6. **State Console Unification (C05)** — timeline component
7. **Command Center Unification (C01)** — token migration
8. **Analyze Workspace Unification (C02)** — intake validation UI

## 7. Phase 6C Readiness

Before any UI implementation:

- [ ] Design System Architecture stable (design-system-architecture.md)
- [ ] Token taxonomy complete (design-token-spec.md)
- [ ] Governance component taxonomy complete (governance-component-spec.md)
- [ ] Primitive strategy selected (component-primitive-strategy.md) — Radix UI primary
- [ ] Console Shell layout defined with Design Tokens
- [ ] Left Navigation with layer grouping implemented
- [ ] Top Status Bar with actor + freshness + notifications
- [ ] All 8 P0 badge components implemented
- [ ] AdvisoryBoundaryBanner implemented and mandatory on Policy surfaces
- [ ] PreviewDataBanner implemented and mandatory on preview surfaces
- [ ] HighRiskActionButton with confirmation dialog implemented
- [ ] Shadow Policy Workbench skeleton with safety labels
- [ ] active_enforced disabled everywhere with reason text
- [ ] Component workbench (Storybook) available for governance state documentation
