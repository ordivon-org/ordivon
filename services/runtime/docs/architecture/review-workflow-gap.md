# Review Workflow Gap — Orchestrator Bypass

> **Date**: 2026-04-25
> **Linked Audit**: [Phase 4 Readiness Audit](../audits/phase-4-readiness/phase-4-readiness-audit-report.md)
> **Finding**: [F-002](../audits/phase-4-readiness/findings-register.md#finding-f-002-only-one-workflow-exists-analyze-review-and-outcome-are-api-triggered-not-orchestrator-driven)
> **Remediation**: [P4 Batch 1 Item 1.1](../audits/phase-4-readiness/remediation-plan.md#item-11-migrate-review-to-orchestrator-workflow)

## Current State

The review lifecycle (submit → complete → lesson → outcome → knowledge_feedback) follows this path:

```
API Route (apps/api/app/api/v1/reviews.py)
    → ReviewCapability (capabilities/workflow/reviews.py)
        → ReviewExecutionAdapter (execution/adapters/reviews.py)
            → ReviewService (domains/journal/service.py)
                → LessonService
                → OutcomeService  (backfill)
                → KnowledgeFeedbackService (build packet)
    → db.commit() or db.rollback() in route handler
```

The orchestrator's `analyze` workflow follows a different path:

```
API Route (apps/api/app/api/v1/analyze.py)
    → PFIOSOrchestrator.run(analyze_workflow)
        → BuildContextStep
        → ReasonStep (with retry + fallback)
        → PersistAnalysisStep
        → GovernanceGateStep (risk engine validation)
        → GenerateRecommendationStep (if allowed)
        → RecordUsageStep
        → AuditTrailStep
        → RenderReportStep + WriteWikiStep
```

## What the Orchestrator Provides That Reviews Lack

| Capability | Orchestrator (analyze) | Reviews (current) |
|---|---|---|
| Step-level atomicity | Each step is a discrete unit | Single method call with inline mutations |
| Retry + fallback | `RecoveryPolicy` with max_retries and `FallbackDecision` | None |
| Handoff artifacts | `HandoffArtifact` with `WakeReason`/`ResumeReason` | None |
| Governance gating | `GovernanceGateStep` before state mutations | None (governance is manual via approval_id) |
| Audit trail consistency | `AuditTrailStep` after all mutations | Partial — embedded in `ReviewService.complete_review()` |
| Workflow run tracking | `WorkflowRunORM` with status, lineage, metadata | None |
| Execution request/receipt | Through execution adapters | Through execution adapters (same) |
| Rollback boundaries | Orchestrator manages compensation detail | Route handler manages commit/rollback (thin) |

## Risk Acceptance for Phase 4

During Phase 4, reviews will continue to operate outside the orchestrator. This is accepted with the following mitigations:

1. **Error handling hardening** (P4 Batch 0, Item 0.2): `complete_review` will gracefully handle `_build_knowledge_feedback` failures without leaving partial state.
2. **Documentation**: This document provides a clear migration target.
3. **No feature regression**: The review flow is functional and tested. The gap is in recoverability and governance consistency, not in basic correctness.

## Target State (P4 Batch 1)

```
API Route → PFIOSOrchestrator.run(review_workflow)
    → BuildContextStep (from review request)
    → GovernanceGateStep (optional, based on approval requirement)
    → ExecuteSubmitStep (through ReviewExecutionAdapter)
    → ExecuteCompleteStep (through ReviewExecutionAdapter)
    → BackfillOutcomeStep
    → BuildKnowledgeFeedbackStep
    → AuditTrailStep
```

This brings reviews under the same recoverability, traceability, and governance guarantees as analysis.

## Related Files

- `orchestrator/workflows/analyze.py` — reference workflow implementation
- `orchestrator/runtime/engine.py` — PFIOSOrchestrator
- `apps/api/app/api/v1/reviews.py` — current review API routes
- `capabilities/workflow/reviews.py` — current review capability facade
- `domains/journal/service.py` — ReviewService (to be decomposed into workflow steps)
- `execution/adapters/reviews.py` — ReviewExecutionAdapter
