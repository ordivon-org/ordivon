# Phase 4 Readiness — Remediation Plan

> **Linked to**: [phase-4-readiness-audit-report.md](./phase-4-readiness-audit-report.md)
> **Findings**: [findings-register.md](./findings-register.md)
> **Plan Date**: 2026-04-25

---

## P4 Batch 0 — Pre-Phase-4 Entry (Must Complete Before Feature Work)

**Estimated effort**: 1-2 days
**Purpose**: Resolve all RED findings and clear blocking conditions.

### Item 0.1: Fix Test Infrastructure — Per-Worker DB Isolation

| Field | Detail |
|---|---|
| **Fixes** | F-008 |
| **Action** | Add a `conftest.py` fixture or `pytest.ini` setting that sets `PFIOS_DB_URL=duckdb:///:memory:` or `duckdb:///./data/test_{worker_id}.duckdb` for all parallel test runs. Update `package.json` test scripts to match. |
| **Files** | `tests/conftest.py`, `pyproject.toml`, `package.json` |
| **Validation** | `PFIOS_DB_URL=duckdb:///:memory: python -m pytest tests/unit/ tests/integration/ -n 4 -q` passes with ≤ 2 failures (non-DB-lock failures only). |
| **Owner** | tests/ |
| **Severity** | RED → expected GREEN after fix |

### Item 0.2: Harden complete_review Error Handling

| Field | Detail |
|---|---|
| **Fixes** | F-003 |
| **Action** | Wrap `_build_knowledge_feedback()` call in `ReviewService.complete_review()` with try/except. On failure: log error, emit `knowledge_feedback_failed` audit event, return the completed review with `knowledge_feedback = None` rather than crashing. Also add a comment block documenting the known non-atomicity and the planned P4 Batch 1 resolution. |
| **Files** | `domains/journal/service.py` (lines 145-146) |
| **Validation** | Unit test injecting a `ValueError` during `_build_knowledge_feedback` verifies review status is COMPLETED, lessons are persisted, audit event `knowledge_feedback_failed` is emitted, and the method returns successfully. |
| **Owner** | domains/journal |
| **Severity** | RED → YELLOW after fix |

### Item 0.3: Document Review/Orchestrator Gap

| Field | Detail |
|---|---|
| **Fixes** | F-002 |
| **Action** | Create `docs/architecture/review-workflow-gap.md` documenting: (a) current review flow path (API → Capability → Adapter → Service), (b) what the orchestrator provides that this path lacks (recoverability, governance gating, audit consistency, handoff artifacts), (c) target state for P4 Batch 1 (orchestrator workflow `review.py`), (d) risk acceptance for Phase 4. Add `# WARNING: operates outside orchestrator — see docs/architecture/review-workflow-gap.md` comment to `apps/api/app/api/v1/reviews.py` and `capabilities/workflow/reviews.py`. |
| **Files** | New: `docs/architecture/review-workflow-gap.md`; Edit: `apps/api/app/api/v1/reviews.py`, `capabilities/workflow/reviews.py` |
| **Validation** | Document exists and both code files reference it. |
| **Owner** | docs/ + apps/api |
| **Severity** | RED → YELLOW after documentation |

### Item 0.4: Regenerate OpenAPI Snapshot

| Field | Detail |
|---|---|
| **Fixes** | F-012 |
| **Action** | Run `pnpm generate:openapi` and commit the updated snapshot. Verify `test_openapi_snapshot_matches_committed_contract` passes. |
| **Files** | (auto-generated OpenAPI snapshot file) |
| **Validation** | `python -m pytest tests/contracts/test_api_contracts.py::test_openapi_snapshot_matches_committed_contract -q` passes. |
| **Owner** | tests/contracts |
| **Severity** | YELLOW → GREEN after fix |

### Item 0.5: Add LEGACY/ACTIVE Tags to All DuckDB Schema Tables

| Field | Detail |
|---|---|
| **Fixes** | F-001 |
| **Action** | Audit `state/db/schema.py` for any DuckDB DDL block that lacks a `# LEGACY — no active read/write code` or `# ACTIVE — ...` comment. Add missing tags. Add a startup log line in `ensure_pipeline_schema` that counts and reports legacy tables created. |
| **Files** | `state/db/schema.py` |
| **Validation** | `grep -c "LEGACY\|ACTIVE" state/db/schema.py` ≥ number of `conn.execute()` calls. |
| **Owner** | state/db |
| **Severity** | YELLOW → GREEN after fix |

### Item 0.6: Tag Placeholder Directories with Phase/Deferral

| Field | Detail |
|---|---|
| **Fixes** | F-010 |
| **Action** | Add `# PHASE 5 DEFERRED — not implemented` to the first line of each STUB README in: `domains/portfolio/`, `domains/market/`, `domains/risk/`, `domains/trading/`, `domains/userprefs/`, `domains/reporting/`, `state/repositories/`, `state/schemas/`, `state/services/`, `state/snapshots/`, `state/trace/`, `knowledge/memory/`, `knowledge/indexes/`, `knowledge/retrieval/` (directory), `intelligence/evaluators/`, `orchestrator/dispatch/`. |
| **Files** | 16 STUB README.md files |
| **Validation** | `grep -rl "PHASE 5 DEFERRED" domains/ state/ knowledge/ intelligence/ orchestrator/` returns ≥ 16 files. |
| **Owner** | docs/ |
| **Severity** | YELLOW → GREEN after fix |

---

## P4 Batch 1 — During Phase 4 (Complete Before Phase 4 Ship)

**Estimated effort**: 3-5 days
**Purpose**: Resolve YELLOW findings that require code changes but do not block Phase 4 entry.

### Item 1.1: Migrate Review to Orchestrator Workflow

| Field | Detail |
|---|---|
| **Fixes** | F-002, F-003, F-011 |
| **Action** | Create `orchestrator/workflows/review.py` with steps: `BuildContext → GovernanceGate(optional) → ExecuteSubmit → ExecuteComplete → AuditTrail → BuildKnowledgeFeedback`. Move `ReviewService.complete_review()` logic into workflow steps with proper boundaries. Update API routes to delegate to `PFIOSOrchestrator.run(review_workflow)`. Extract `ReviewServiceFactory` dependency. |
| **Files** | New: `orchestrator/workflows/review.py`; Edit: `apps/api/app/api/v1/reviews.py`, `capabilities/workflow/reviews.py`, `domains/journal/service.py` |
| **Validation** | Integration test verifying review submit+complete through orchestrator with mock failures mid-way and confirming rollback or resume. |
| **Owner** | orchestrator + domains/journal |
| **Severity** | RED → GREEN after completion |

### Item 1.2: Add Hint-Weighting to RiskEngine

| Field | Detail |
|---|---|
| **Fixes** | F-004 |
| **Action** | Modify `RiskEngine.validate_analysis()` to: count `lesson_caution` hints for the current symbol; if count ≥ threshold (configurable, default 2), force `decision="escalate"` with reason "Prior lesson cautions exist for this symbol." Add hint-to-decision trace to `GovernanceDecision.reasons`. Surface this in `GovernanceDetailInspector.tsx`. |
| **Files** | `governance/risk_engine/engine.py`, `governance/decision.py`, `apps/web/src/components/features/analyze/GovernanceDetailInspector.tsx` |
| **Validation** | Unit test: 3 `lesson_caution` hints for symbol "PEPE" → `validate_analysis()` returns `decision="escalate"`. |
| **Owner** | governance/risk_engine |
| **Severity** | YELLOW → GREEN after completion |

### Item 1.3: Enforce Execution Request/Receipt in Orchestrator

| Field | Detail |
|---|---|
| **Fixes** | F-005 |
| **Action** | Add `ExecutionGate` step (or pre-step hook) in `PFIOSOrchestrator` that: before any step with `side_effect_level="state_mutation"`, checks that an `ExecutionRequestORM` row exists with matching `action_id` and `idempotency_key`; after the step, verifies a corresponding `ExecutionReceiptORM` row was written. Non-adapter steps that don't go through the adapter registry must explicitly create request/receipt rows. |
| **Files** | `orchestrator/runtime/engine.py`, `execution/gate.py` (new) |
| **Validation** | Test that a workflow step without a pre-created `ExecutionRequest` raises an error. |
| **Owner** | execution + orchestrator |
| **Severity** | YELLOW → GREEN after completion |

### Item 1.4: Make Policy Resolution Pack-Aware

| Field | Detail |
|---|---|
| **Fixes** | F-009 |
| **Action** | Refactor `RiskEngine.validate_intake()` to use `pack_id` from `DecisionIntake` to resolve the appropriate policy class rather than hardcoding `TradingDisciplinePolicy`. Use the `get_finance_policy_overlays()` pattern already present in `GovernancePolicySource`. Extend `HintAwareContextBuilder.enrich()` to accept optional `pack_id` and dispatch accordingly. |
| **Files** | `governance/risk_engine/engine.py`, `governance/policy_source.py`, `intelligence/context_builder.py` |
| **Validation** | Adding a mock `packs/health/` with a health policy class does not require modifying `governance/policy_source.py` — only registering the new pack. |
| **Owner** | governance |
| **Severity** | YELLOW → GREEN after completion |

---

## Phase 5 Deferred — Out of Phase 4 Scope

**Purpose**: Items that are architecturally acknowledged but not required for Phase 4 Personal Control Loop delivery.

### Deferred-5.1: Remove Legacy DuckDB Tables After Migration

| Field | Detail |
|---|---|
| **Fixes** | F-001 (complete resolution) |
| **Action** | Write migration to copy any valuable historical data from legacy DuckDB tables to ORM-backed paths. Delete legacy DDL blocks from `schema.py`. Remove `ensure_pipeline_schema` dependency on legacy tables. |
| **Owner** | state/db |
| **Note** | Requires data archaeology to determine if any historical OHLCV/feature/signal data is worth preserving. |

### Deferred-5.2: Dynamic Workflow Dispatch

| Field | Detail |
|---|---|
| **Fixes** | F-002 (complete resolution) |
| **Action** | Implement `orchestrator/dispatch/` with dynamic routing: scheduler triggers → dispatch resolves workflow → orchestrator executes. Enable cron-driven review scheduling. |
| **Owner** | orchestrator/dispatch |

### Deferred-5.3: Vector Semantic Search for Knowledge Retrieval

| Field | Detail |
|---|---|
| **Fixes** | knowledge retrieval gap |
| **Action** | Replace exact-match SQL retrieval in `knowledge/retrieval.py` with vector similarity search for cross-referencing past mistakes by semantics rather than exact symbol/ID match. |
| **Owner** | knowledge/ |
| **Note** | Already documented in `current-state-report-2026-04-24.md:75-76` as P3/Phase 5. |

### Deferred-5.4: Implement STUB Directories

| Field | Detail |
|---|---|
| **Fixes** | F-010 (complete resolution) |
| **Action** | Implement `domains/portfolio/`, `domains/market/`, `domains/risk/`, `knowledge/memory/`, `intelligence/evaluators/`, `orchestrator/dispatch/`, `state/trace/` based on Phase 5 requirements. |
| **Owner** | Per directory |

### Deferred-5.5: Frontend Trust Tier Lint Enforcement

| Field | Detail |
|---|---|
| **Fixes** | F-007 (hardening) |
| **Action** | Add ESLint rule that prevents rendering `KnowledgeHint` data outside of a `<TrustBadge>` wrapper component. Automates the trust-tier discipline. |
| **Owner** | apps/web |

---

## Batched Summary

| Batch | Items | Effort | Blocks Phase 4? |
|---|---|---|---|
| **P4 Batch 0** | 0.1 – 0.6 | 1-2 days | **YES** — must complete before feature work |
| **P4 Batch 1** | 1.1 – 1.4 | 3-5 days | No — complete during Phase 4 |
| **Phase 5 Deferred** | D-5.1 – D-5.5 | TBD | No |

---

## Completion Gates

- [ ] P4 Batch 0 complete → Phase 4 feature work begins
- [ ] P4 Batch 1 complete → Phase 4 ships
- [ ] All RED findings resolved → YELLOW/GREEN
- [ ] All YELLOW findings either resolved → GREEN or deferred to Phase 5 with explicit acceptance
- [ ] Test baseline at > 95% pass rate with per-worker DB isolation
- [ ] Frontend test and TypeScript baseline confirmed in development environment
