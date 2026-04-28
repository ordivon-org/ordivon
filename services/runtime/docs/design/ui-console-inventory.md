# Ordivon UI Console Inventory

Status: **PROPOSED** (Phase 6A)
Date: 2026-04-29
Phase: 6A
Tags: `design`, `console`, `inventory`, `ui`, `surface`, `priority`

## 1. Purpose

This document catalogs every console in the Ordivon application,
mapping each to its governance layer, primary user, maturity,
implementation priority, risks, and required evidence labels.

It serves as the implementation roadmap for Phase 6 UI work.
Consoles are ordered by priority, not by layer number.

## 2. Console Inventory

### C01 — Home / Live Command Center

| Property | Value |
|----------|-------|
| Layer | L0 — Application Shell |
| Primary User | All users |
| Governed Objects | Dashboard summary, recent decisions, active policy count |
| Maturity | **real** (working frontend exists) |
| Priority | **P0** — foundation for all other surfaces |
| Risks | Low. Primarily read-only aggregation. |
| Evidence Labels | "Live Data" / "Mock Data" for any preview sections |

**Current state**: Dashboard component exists with inline styles.
Needs Design System integration.

### C02 — Analyze / Execution Workspace

| Property | Value |
|----------|-------|
| Layer | L1-L2 — Governance Core + Domain State |
| Primary User | Analyst, Operator |
| Governed Objects | DecisionIntake, AnalysisRequest, AnalysisResult |
| Maturity | **real** (working frontend) |
| Priority | **P0** — primary intake surface |
| Risks | Medium. Intake surface must validate before submission. |
| Evidence Labels | "Intake Payload" / "Governance Result" |

### C03 — Reviews / Supervision Workbench

| Property | Value |
|----------|-------|
| Layer | L3 — Pack Layer |
| Primary User | Reviewer, Governance Officer |
| Governed Objects | Review, ReviewDecision, Lesson, CandidateRule |
| Maturity | **real** (working frontend) |
| Priority | **P0** — core supervision surface |
| Risks | Medium. Review actions must be auditable. |
| Evidence Labels | "Review Verdict" / "Reviewer Identity" |

### C04 — Capabilities Map

| Property | Value |
|----------|-------|
| Layer | L4 — Capability / API Bridge |
| Primary User | Developer, Operator |
| Governed Objects | Capability registry, API surface |
| Maturity | **real** (working frontend) |
| Priority | **P1** — useful but not blocking |
| Risks | Low. Read-only capability catalog. |
| Evidence Labels | "API Contract" |

### C05 — State / Trace & Outcome Graph

| Property | Value |
|----------|-------|
| Layer | L5 — Execution / Receipt |
| Primary User | Auditor, Operator |
| Governed Objects | ExecutionReceipt, ExecutionRequest, AuditEvent, Outcome |
| Maturity | **real** (working frontend) |
| Priority | **P0** — essential for audit traceability |
| Risks | Medium. Trace completeness must be verifiable. |
| Evidence Labels | "Receipt ID" / "Execution Timestamp" / "Side Effects: false" |

### C06 — Knowledge / Feedback + Candidate Rule Console

| Property | Value |
|----------|-------|
| Layer | L6 — Intelligence / Runtime |
| Primary User | Reviewer, Governance Officer |
| Governed Objects | KnowledgeFeedback, Lesson, CandidateRule, PolicyProposal |
| Maturity | **real** (working frontend) |
| Priority | **P0** — learning loop is a core differentiator |
| Risks | Medium. CandidateRule promotion is a governance action. |
| Evidence Labels | "Lesson Source" / "CandidateRule Status" |

### C07 — Execution / Request & Receipt Console

| Property | Value |
|----------|-------|
| Layer | L7 — Verification / CI |
| Primary User | Developer, Operator |
| Governed Objects | ExecutionRequest, ExecutionReceipt |
| Maturity | **real** (working frontend) |
| Priority | **P1** — useful for debugging |
| Risks | Low. Read-only execution history. |
| Evidence Labels | "Receipt Status" / "Plan vs Actual" |

### C08 — Intelligence / Runtime & Context Console

| Property | Value |
|----------|-------|
| Layer | L8 — Learning Platform |
| Primary User | Developer, ML Operator |
| Governed Objects | Model runtime, task history, context snapshots |
| Maturity | **preview** (partial frontend) |
| Priority | **P2** — defer until active model pipeline exists |
| Risks | Medium. Runtime details may expose model internals. |
| Evidence Labels | "Model Version" / "Context Window" / "Preview — Not Production" |

### C09 — Governance / Decision & Approval Console

| Property | Value |
|----------|-------|
| Layer | L9 — Policy Platform |
| Primary User | Governance Officer, Reviewer |
| Governed Objects | GovernanceDecision, PolicyRecord, ApprovalDecision |
| Maturity | **preview** (conceptual, no working frontend) |
| Priority | **P0** — essential for Policy Platform dogfood |
| Risks | High. Must not imply active/enforced policy. Shadow only. |
| Evidence Labels | "Shadow Decision — Advisory Only" / "APPROVED_FOR_SHADOW" / "active_enforced: NOT AVAILABLE" |

### C10 — Orchestration / Workflow Run Console

| Property | Value |
|----------|-------|
| Layer | L10 — Product / Frontend |
| Primary User | Operator, Developer |
| Governed Objects | WorkflowRun, orchestration state |
| Maturity | **future** (not implemented) |
| Priority | **P2** — defer until workflows are active |
| Risks | Medium. Workflow state must be auditable. |
| Evidence Labels | "Workflow Status" / "Step History" |

### C11 — Infrastructure / Scheduler / Monitoring / Runbook Center

| Property | Value |
|----------|-------|
| Layer | — (cross-cutting) |
| Primary User | Operator, SRE |
| Governed Objects | Scheduler state, health checks, runbooks |
| Maturity | **future** (not implemented) |
| Priority | **P2** — defer until production deployment |
| Risks | High. Monitoring access may expose system internals. |
| Evidence Labels | "Health Status" / "Uptime" / "Runbook Reference" |

### C12 — Pack / Finance Pack Ownership Console

| Property | Value |
|----------|-------|
| Layer | — (Pack-specific) |
| Primary User | Finance Operator, Risk Manager |
| Governed Objects | FinanceDecisionIntake, FinanceOutcome, RiskMetrics |
| Maturity | **preview** (partial frontend) |
| Priority | **P1** — important but blocked on Phase 7 live readiness |
| Risks | Critical. Must not imply live trading capability. |
| Evidence Labels | "PREVIEW — NOT PRODUCTION" / "No Live Trading" / "Risk Simulation Only" |

### C13 — Adapter / External Systems Adapter Console

| Property | Value |
|----------|-------|
| Layer | — (Adapter-specific) |
| Primary User | Developer, Integrator |
| Governed Objects | Adapter configurations, external system status |
| Maturity | **future** (not implemented) |
| Priority | **P2** — defer until multi-adapter deployment |
| Risks | Medium. Adapter config may contain credentials. |
| Evidence Labels | "Adapter Status" / "Connection Health" |

### C14 — Future Policy / Shadow Policy Workbench

| Property | Value |
|----------|-------|
| Layer | L9 — Policy Platform |
| Primary User | Governance Officer, Policy Designer |
| Governed Objects | PolicyRecord(draft), ShadowResult, ApprovalDecision |
| Maturity | **future** (design only in Phase 5 domain model) |
| Priority | **P0** — Phase 6 priority surface |
| Risks | High. Shadow evaluation is advisory only. Must not imply enforcement. |
| Evidence Labels | "Shadow Policy — Advisory Only" / "Not Active" / "active_enforced: DEFERRED" |

## 3. Implementation Priority Summary

### P0 — Phase 6 Must-Have

| Console | Reason |
|---------|--------|
| C01 Home / Command Center | Foundation surface |
| C02 Analyze / Execution Workspace | Primary intake |
| C03 Reviews / Supervision Workbench | Core supervision |
| C05 State / Trace & Outcome Graph | Audit traceability |
| C06 Knowledge / Candidate Rule Console | Learning loop visibility |
| C09 Governance / Decision Console | Policy Platform visibility |
| C14 Shadow Policy Workbench | Phase 6 priority new surface |

### P1 — Phase 6 Should-Have

| Console | Reason |
|---------|--------|
| C04 Capabilities Map | Useful reference |
| C07 Execution / Request Console | Debugging support |
| C12 Finance Pack Console | Important but blocked on P7 |

### P2 — Phase 6 Could-Have / Defer

| Console | Reason |
|---------|--------|
| C08 Intelligence Console | Blocked on active model pipeline |
| C10 Orchestration Console | Blocked on workflows |
| C11 Infrastructure Console | Blocked on production deployment |
| C13 Adapter Console | Blocked on multi-adapter deployment |

## 4. Maturity Summary

| Maturity | Count | Consoles |
|----------|-------|----------|
| **real** | 7 | C01, C02, C03, C04, C05, C06, C07 |
| **preview** | 3 | C08, C09, C12 |
| **future** | 4 | C10, C11, C13, C14 |

## 5. Risk Summary

| Risk Level | Count | Consoles |
|-----------|-------|----------|
| Critical | 1 | C12 (Finance — must not imply live trading) |
| High | 2 | C09, C14 (Policy — must not imply enforcement) |
| Medium | 5 | C02, C03, C05, C06, C08 |
| Low | 6 | C01, C04, C07, C10, C11, C13 |

## 6. Evidence Label Requirements

All consoles with `maturity: preview` or `maturity: future` must display:

- A persistent `PreviewBanner` component: "PREVIEW — NOT PRODUCTION"
- On surfaces with mock data: `MockDataLabel` component: "SAMPLE DATA"
- On Policy surfaces: "Shadow Decision — Advisory Only" or "active_enforced: DEFERRED"
- On Finance surfaces: "No Live Trading" or "Risk Simulation Only"

These labels are **design contracts**. They must not be removed or hidden
by implementation without explicit governance review.

## 7. Non-Goals

- This inventory does not specify pixel-level layouts.
- This inventory does not define component API contracts.
- Maturity labels are aspirational — implementation may reveal blockers.
- Priority assignments are guidance, not enforcement.
