# Phase 4 Readiness — Findings Register

> **Audit Date**: 2026-04-25
> **Auditor**: PFIOS Internal Audit (Phase 4 Readiness)
> **Scope**: Phase 4 Personal Control Loop readiness
> **Methodology**: Static code inspection + test baseline execution against 10 audit criteria

---

## Finding F-001: DuckDB Legacy Schema Contains 20+ Tables with Zero Active Read/Write Code

| Field | Detail |
|---|---|
| **Condition** | `state/db/schema.py` defines ~27 DuckDB tables via `ensure_pipeline_schema()`. Only `system_init` is ACTIVE. All others are marked LEGACY with no active read/write code in the Python domain layer. |
| **Criteria** | Audit Standard #1: State is truth. The schema file creates tables (`ohlcv`, `features`, `signals`, `ai_reviews`, `account_sync_runs`, `account_balances`, `account_positions`, `account_open_orders`, `position_states`, `position_lifecycles`, `position_events`, `approvals`, `executions`, `policies`, `risk_audits`, `recommendations`, `performance_reviews`, `usage_logs`, `issue_triage`, `validation_summaries`, plus `analysis_cache`, `analysis_summaries`) that are never read or written. |
| **Evidence** | `state/db/schema.py:38-409` — all LEGACY blocks. The SQLAlchemy bootstrap in `state/db/bootstrap.py` imports 18 ORM models — none map to these legacy DuckDB DDL tables. The active domain layer (`domains/*/orm.py`) exclusively uses SQLAlchemy ORM models registered in `Base`. |
| **Cause** | Inherited from pre-PFIOS monolithic trading system. DDL retained for backward compatibility so that `ensure_pipeline_schema` does not break on startup when existing `.duckdb` files are opened. |
| **Risk** | **Medium**. Dual schema confusion: newcomers may assume DuckDB DDL is authoritative. Table name collisions between legacy DDL (`recommendations`, `policies`, `approvals`) and SQLAlchemy ORM tables of the same name create ambiguity. Historical data in legacy tables is inaccessible through current query paths. |
| **Recommendation** | (1) Add LEGACY/ACTIVE tag comments to every table — **partially done**, some DDL blocks still lack clear tags. (2) Create a migration script that copies any valuable historical data from legacy tables to ORM-backed paths. (3) Remove or gate `ensure_pipeline_schema` behind a feature flag after migration. (4) Add a startup log line listing exactly which legacy tables were created. |
| **Severity** | YELLOW |
| **Owner** | state/db |
| **Validation** | Verify all DuckDB DDL tables except `system_init` have `# LEGACY — no active read/write code` comments; verify no ORM model has a table name that collides with a legacy DDL table. |

---

## Finding F-002: Only One Workflow Exists (analyze); Review and Outcome Are API-Triggered, Not Orchestrator-Driven

| Field | Detail |
|---|---|
| **Condition** | `orchestrator/workflows/` contains exactly one workflow: `analyze.py`. The `orchestrator/dispatch/` directory is a STUB (empty README). Review creation/completion, outcome detection, and knowledge feedback looping are all triggered by direct API calls (`/reviews/submit`, `/reviews/{id}/complete`) rather than through the orchestrator engine. |
| **Criteria** | Audit Standard #3: Execution requires request/receipt. Audit Standard #4: Governance before side effect. The review/outcome/knowledge loop should be orchestrator-driven so that governance gates, recoverability, and audit lineage are applied uniformly — not ad-hoc per API route. |
| **Evidence** | (1) `orchestrator/workflows/` contains only `analyze.py`. (2) Review submission and completion flow through `apps/api/app/api/v1/reviews.py` → `capabilities/workflow/reviews.py` → `ReviewExecutionAdapter` → `ReviewService.complete_review()` — none of this touches `PFIOSOrchestrator`. (3) `orchestrator/dispatch/README.md`: "Placeholder for future dispatch logic (dynamic workflow routing)." |
| **Cause** | The analyze workflow was built as the MVP path; review/knowledge loops were deferred. The API routes grew organically and accumulated orchestration responsibility. |
| **Risk** | **High**. The review lifecycle (submit → complete → lesson → outcome → knowledge_feedback) operates outside the orchestrator's recoverability, governance gating, and audit trail consistency guarantees. If a review completion fails mid-way through `_build_knowledge_feedback`, there is no formal rollback or resume mechanism — the `db.commit()` in the API route is the only safety net. |
| **Recommendation** | (1) P4 Batch 0: Document the review/orchestrator gap with explicit risk acknowledgment. (2) P4 Batch 1: Migrate review submission/completion into an orchestrator workflow (`orchestrator/workflows/review.py`) that uses the same `BuildContext → GovernanceGate → Execute → AuditTrail → RenderReport` step pattern. (3) Phase 5: Add dynamic workflow dispatch so the scheduler can trigger reviews automatically. |
| **Severity** | RED |
| **Owner** | orchestrator |
| **Validation** | Verify `orchestrator/workflows/` contains a `review.py` workflow; verify `/reviews/submit` and `/reviews/{id}/complete` API routes delegate to `PFIOSOrchestrator` rather than calling `ReviewService` directly. |

---

## Finding F-003: complete_review Drives Lesson, Outcome, and Knowledge Feedback — But in a Non-Atomic, Non-Resumable Manner

| Field | Detail |
|---|---|
| **Condition** | `ReviewService.complete_review()` (lines 66-147 of `domains/journal/service.py`) performs: (1) state transition to COMPLETED, (2) backfill outcome snapshot via `_backfill_outcome_snapshot`, (3) persist Lesson rows, (4) build KnowledgeFeedbackPacket. This is a multi-step mutation. If step 3 or 4 fails, step 1 and 2 may have already taken effect. |
| **Criteria** | Audit Standard #3: Execution requires request/receipt. Audit Standard #4: Governance before side effect. Multi-step mutations should be atomic or resumable. |
| **Evidence** | `domains/journal/service.py:66-147`. The method calls `self.review_repository.db.flush()` at line 90, then proceeds to `_backfill_outcome_snapshot()` (line 108), lesson creation loop (lines 116-143), and `_build_knowledge_feedback()` (line 145). If `KnowledgeFeedbackService.build_packet()` raises, the review status is already COMPLETED with lesson rows orphaned. |
| **Cause** | The method was built incrementally, adding backfill and feedback capabilities to an initially simple state transition. |
| **Risk** | **Medium-High**. Recovery from a partial `complete_review` failure requires manual inspection. The audit trail records `review_completed` and `lesson_persisted` events before the knowledge feedback packet is built — so if feedback fails, the audit log claims success. |
| **Recommendation** | (1) P4 Batch 0: Add explicit error handling around `_build_knowledge_feedback` that logs and does not prevent the review from completing (soft failure). (2) P4 Batch 1: Refactor into an orchestrator workflow with proper step boundaries and checkpointing. (3) Use `savepoint` or transactional scoping so that review completion + lesson + outcome backfill + feedback are all-or-nothing. |
| **Severity** | RED |
| **Owner** | domains/journal |
| **Validation** | Verify that a test injecting a failure during `_build_knowledge_feedback` correctly rolls back the review state and does not emit `review_completed` audit event until all steps succeed. |

---

## Finding F-004: GovernanceDecision Is Structured But RiskEngine Ignores Advisory Hints for Decision-Making

| Field | Detail |
|---|---|
| **Condition** | `GovernanceDecision` includes `advisory_hints: tuple[GovernanceAdvisoryHint, ...]`, and the workflow's `GovernanceGateStep` correctly passes them. However, `RiskEngine.validate_analysis()` passes hints into the decision output but never uses them to influence the decision itself — the decision logic is purely: check forbidden symbols → check suggested actions → execute/escalate/reject. |
| **Criteria** | Audit Standard #2: Knowledge is advisory. Audit Standard #4: Governance before side effect. Advisory hints should be visible and available for governance, but the current code does not let hints influence the decision even as an "escalate" weight factor. |
| **Evidence** | `governance/risk_engine/engine.py:10-52`. Hints are passed through to the `GovernanceDecision` constructor but never accessed by any conditional logic. The 2026-04-24 architecture report (Section 3.4) confirms: "advisory_hints are extracted from past lessons and passed to the GovernanceDecision, but the Governance engine completely ignores them when deciding to Execute/Escalate/Reject." |
| **Cause** | Hints were wired into the data flow but decision logic using them was deferred ("Phase 4 will expose these hints in the UI. Phase 5 will implement logic to force escalation based on past negative outcomes." — `current-state-report-2026-04-24.md:80`). |
| **Risk** | **Medium**. The system accumulates knowledge feedback but governance cannot act on it. A user who has repeatedly made the same mistake on the same symbol will receive advisory hints but will not see forced escalation. |
| **Recommendation** | P4 Batch 1: Add hint-weighting to `RiskEngine.validate_analysis()` — if any hint's `hint_type` is `"lesson_caution"` and the symbol matches, force `decision="escalate"`. Surface hint-to-decision linkage in the GovernanceDetailInspector frontend component. |
| **Severity** | YELLOW |
| **Owner** | governance/risk_engine |
| **Validation** | Verify test that a symbol with 3+ prior `lesson_caution` hints on the same symbol forces `escalate` in `validate_analysis()`. |

---

## Finding F-005: ExecutionRequest/Receipt Exist But Are Not Used by the Orchestrator

| Field | Detail |
|---|---|
| **Condition** | `ExecutionRequestORM` and `ExecutionReceiptORM` are defined in `domains/execution_records/orm.py` and registered in `state/db/bootstrap.py`. The execution catalog (`execution/catalog.py`) defines 15 `ExecutionActionSpec` entries with request/receipt semantics. However, the orchestrator's analyze workflow does not directly write ExecutionRequest/Receipt rows — the `RecommendationExecutionAdapter` and `ReviewExecutionAdapter` do this internally. |
| **Criteria** | Audit Standard #3: Execution requires request/receipt. |
| **Evidence** | (1) `execution/catalog.py` defines 15 action specs, 8 marked `primary_receipt_candidate=True`. (2) The workflow's `GenerateRecommendationStep` stores `execution_request_id` and `execution_receipt_id` in metadata (lines 418-422), but these are produced by the adapter, not the orchestrator. (3) The `AuditTrailStep` references these IDs in audit payload. (4) No orchestrator-level pre-check ensures an ExecutionRequest exists before executing a side effect. |
| **Cause** | The execution catalog was designed for formal action accountability but the orchestrator integration is partial — adapters handle their own request/receipt lifecycle. |
| **Risk** | **Medium**. The system has the request/receipt infrastructure but does not enforce it uniformly. A new workflow step that calls a domain service directly without going through an adapter would bypass request/receipt entirely. |
| **Recommendation** | P4 Batch 1: Have the orchestrator engine (or a new `ExecutionGate` step) require an `ExecutionRequest` row before any `side_effect_level="state_mutation"` step proceeds, and require an `ExecutionReceipt` to be written before the step is marked complete. |
| **Severity** | YELLOW |
| **Owner** | execution + orchestrator |
| **Validation** | Verify a test that a non-adapter side effect (e.g., writing directly to a repository) fails in the orchestrator because no ExecutionRequest was pre-created. |

---

## Finding F-006: CandidateRule Cannot Auto-Promote to Policy — Confirmed as Compliant

| Field | Detail |
|---|---|
| **Condition** | `domains/candidate_rules/models.py` defines `VALID_CANDIDATE_RULE_STATES = {"draft", "under_review", "rejected", "accepted_candidate"}`. The only creation path is `CandidateRuleService.create_from_recurring_issue()` which sets `status="draft"`. There is no `promoted` state and no code path that auto-promotes a CandidateRule into a Policy. |
| **Criteria** | Audit Standard #9: CandidateRule cannot auto-promote to Policy. |
| **Evidence** | `domains/candidate_rules/models.py:9`, `domains/candidate_rules/service.py:12-23`. The design doctrine (`aegisos-design-doctrine.md:459-461`) enforces: "Knowledge may influence future behavior, but may not redefine truth or auto-activate policy." |
| **Cause** | Deliberate design choice — promotion to policy requires explicit human action. |
| **Risk** | **Low — Compliance verified.** |
| **Recommendation** | Add a comment in `CandidateRuleService` explicitly noting "No auto-promotion to Policy by design — Doctrine 8, Knowledge Layer Invariant." For future safety, add a test that verifies no code path directly creates a CandidateRule in a state that maps to a Policy. |
| **Severity** | GREEN |
| **Owner** | domains/candidate_rules |
| **Validation** | Verify `VALID_CANDIDATE_RULE_STATES` does not include "promoted" or "policy_active"; verify no import of `CandidateRuleORM` or `CandidateRule` exists in `governance/`. |

---

## Finding F-007: Frontend Semantic Signal System Correctly Distinguishes Fact from Hint

| Field | Detail |
|---|---|
| **Condition** | `apps/web/src/lib/semanticSignals.ts` defines `SemanticSignalKind` with values: `trace_detail` (→ `fact`), `outcome_signal` (→ `outcome_signal`), `knowledge_hint` (→ `hint`), `report_artifact` (→ `artifact`). The `honestMissingCopy()` function returns "not linked yet", "unavailable", "Not prepared yet" for missing states. |
| **Criteria** | Audit Standard #10: Frontend expresses truth, does not invent truth. |
| **Evidence** | `apps/web/src/lib/semanticSignals.ts:2-61`. The frontend trust tier distinguishes 5 states (`fact`, `artifact`, `outcome_signal`, `hint`, `missing`) and provides honest copy for each. The `semanticNote()` function adds disclaimers: "This is the latest recorded outcome signal, not a fully closed loop", "These are derived signals, not state truth, policy updates, or system learning." |
| **Cause** | Intentional design aligned with Doctrine 2 ("Truth Must Exist Separately"). |
| **Risk** | **Low — Compliance verified.** |
| **Recommendation** | Maintain discipline: never let a new component display a `KnowledgeHint` as if it were a `Fact`. Consider adding a lint rule that prohibits rendering any `KnowledgeHint`-typed data outside of a `<TrustBadge tier="hint">` wrapper. |
| **Severity** | GREEN |
| **Owner** | apps/web |
| **Validation** | Verify all frontend components that render `outcome_signal` or `knowledge_hint` data wrap them in trust-tier-aware components. |

---

## Finding F-008: Test Infrastructure — DuckDB Lock Conflicts Make Parallel Testing Unreliable

| Field | Detail |
|---|---|
| **Condition** | Running `pytest -n 4` (parallel with xdist) causes DuckDB lock conflicts on `data/pfios.duckdb`. The test configuration defaults to this file (`settings.db_url = "duckdb:///./data/pfios.duckdb"`) and does not use per-worker or per-session DB paths. |
| **Criteria** | Baseline: unit, integration, contract tests must run reliably to assess readiness. |
| **Evidence** | Unit tests: 16 failed out of 186 (170 passed, 16 failed — all DB-related `OperationalError: Could not set lock on file`). Integration tests: 29 failed, 6 errors out of 87 (52 passed). Contract tests: 2 failed out of 4 (OpenAPI snapshot mismatch + response contract field issue). Frontend tests: blocked by network connectivity (npm registry unreachable). |
| **Cause** | DuckDB's file-level locking does not support concurrent write connections from multiple pytest-xdist workers accessing the same `.duckdb` file. The `package.json` scripts show the intended pattern (`PFIOS_DB_URL=duckdb:///./data/quality-unit.duckdb`, etc.) but these are not wired into pytest configuration. |
| **Risk** | **High for development velocity**. Flaky CI makes it hard to trust test results. |
| **Recommendation** | P4 Batch 0: Add `PFIOS_DB_URL` override to pytest conftest that uses `duckdb:///:memory:` or per-process temp files. Also: mark the OpenAPI snapshot test as needing a regeneration pass (benign mismatch from recent schema additions). |
| **Severity** | RED |
| **Owner** | tests/ (conftest.py, pyproject.toml) |
| **Validation** | Run `PFIOS_DB_URL=duckdb:///:memory: python -m pytest tests/unit/ tests/integration/ -n 4 -q` — expect near-zero DB-lock failures. |

---

## Finding F-009: Adaption / Pack / Core Boundary Is Respected but Finance-Hardcoded Defaults Leak into Orchestrator Context Builder

| Field | Detail |
|---|---|
| **Condition** | `orchestrator/context/context_builder.py` is listed in `layer-module-inventory.md` as "has finance-hardcoded defaults." The `BuildContextStep` in `orchestrator/workflows/analyze.py:70` calls `HintAwareContextBuilder(ctx.db).enrich(analysis_ctx, symbol=...)` using only `symbol` — a finance domain concept. |
| **Criteria** | Audit Standard #7: Finance is first pack, not system identity. Audit Standard #8: Hermes is adapter, not system identity. |
| **Evidence** | (1) `orchestrator/workflows/analyze.py:70-71` — `HintAwareContextBuilder` enriches by `symbol` without pack-aware dispatch. (2) `governance/policy_source.py:28-42` hardcodes `ForbiddenSymbolsPolicy` and `TradingDisciplinePolicy` — both finance-specific. (3) The `FinanceDecisionCapability` in `capabilities/domain/finance_decisions.py` correctly uses the pack facade pattern, but `RiskEngine.validate_intake()` at `governance/risk_engine/engine.py:67` hardcodes `TradingDisciplinePolicy` instead of delegating to a pack-aware policy resolver. |
| **Cause** | The pack extraction pattern was applied to `packs/finance/` for the frontend and analysis profile but was not completed for governance policy resolution. |
| **Risk** | **Low-Medium**. Currently acceptable because only one pack exists (finance). But adding a `packs/health` or `packs/research` pack would require touching `governance/policy_source.py` and `orchestrator/context/context_builder.py` — violating the Pack extraction goal. |
| **Recommendation** | P4 Batch 1: Move `TradingDisciplinePolicy` import in `RiskEngine.validate_intake()` behind a pack-aware resolver (similar to `get_finance_policy_overlays()` pattern already in `policy_source.py`). Have `HintAwareContextBuilder` accept a `pack_id` parameter for non-finance packs. |
| **Severity** | YELLOW |
| **Owner** | governance + orchestrator |
| **Validation** | Verify that adding a hypothetical `packs/health/` with its own policy class does not require modifying `governance/policy_source.py`. |

---

## Finding F-010: Placeholder Directories (18 STUBs) Remain Without Implementation Signals

| Field | Detail |
|---|---|
| **Condition** | `layer-module-inventory.md` (2026-04-24) catalogs 18 STUB/placeholder directories. As of 2026-04-25, these remain unchanged: `domains/portfolio/`, `domains/market/`, `domains/risk/`, `domains/trading/`, `domains/userprefs/`, `domains/reporting/`, `state/repositories/`, `state/schemas/`, `state/services/`, `state/snapshots/`, `state/trace/`, `knowledge/memory/`, `knowledge/indexes/`, `knowledge/retrieval/` (directory, not file), `intelligence/evaluators/`, `orchestrator/dispatch/`, and others. |
| **Criteria** | Phase 4 readiness demands that placeholder directories either have concrete implementation plans or are marked for deferral. |
| **Evidence** | All directories contain only a `README.md` with text like "Placeholder for future..." or "Stub — not yet implemented." |
| **Cause** | Created during Step 1 skeleton initialization to communicate intended architecture. |
| **Risk** | **Low-Medium**. The directories create false expectations of capability existence. A new team member browsing `domains/portfolio/` would assume portfolio management is implemented. |
| **Recommendation** | P4 Batch 0: Add a `// PHASE 5 DEFERRED` comment to each STUB README. P4 Batch 1: Create a `docs/placeholder-register.md` that maps each STUB to its target phase and owner. |
| **Severity** | YELLOW |
| **Owner** | docs/ |
| **Validation** | Verify the placeholder register exists and each entry has a phase target and owner. |

---

## Finding F-011: API Route `reviews.py` Is Too Thick — Orchestration Logic Lives in Route Handler

| Field | Detail |
|---|---|
| **Condition** | `apps/api/app/api/v1/reviews.py:121-176` (`complete_performance_review`) constructs `ReviewService` with 4 dependencies (`LessonService`, `RiskAuditor`, `OutcomeService`, `RecommendationService`), builds `action_context`, calls `review_capability.complete_review()`, and then either `db.commit()` or `db.rollback()` based on exception type. This is orchestration logic, not API surface logic. |
| **Criteria** | Audit Standard #4: Governance before side effect. API routes should be thin facades that delegate to capabilities, not construction sites for service graphs. |
| **Evidence** | `apps/api/app/api/v1/reviews.py:121-176`. The route handler instantiates 5 service objects, builds context, and implements commit/rollback branching. The same pattern repeats in `submit_performance_review` (lines 89-118) and `get_pending_reviews` (lines 55-69) and `get_review_detail` (lines 72-86). |
| **Cause** | Organic growth — as features were added to the review flow, service construction was copy-pasted into each route handler. |
| **Risk** | **Medium**. Duplicated service construction creates maintenance hazards: changing `ReviewService.__init__` signature requires updating 4 route handlers. Cross-cutting concerns (audit trail, execution request/receipt) are inconsistently applied. |
| **Recommendation** | P4 Batch 1: Extract a `ReviewServiceFactory` or FastAPI dependency that constructs the full service graph once, and have route handlers receive it via `Depends()`. P4 Batch 1: Move orchestration logic (action_context building, commit/rollback branching) into the `ReviewCapability` layer so the route handler is a thin delegate. |
| **Severity** | YELLOW |
| **Owner** | apps/api + capabilities |
| **Validation** | Verify route handlers are ≤ 15 lines and delegate all service construction and orchestration to injected dependencies. |

---

## Finding F-012: OpenAPI Snapshot Test Is Out of Sync with Current Schema

| Field | Detail |
|---|---|
| **Condition** | `tests/contracts/test_api_contracts.py::test_openapi_snapshot_matches_committed_contract` fails with differing items in the API schema, including `'/api/v1/agent-actions/latest'` paths. |
| **Criteria** | Contract tests must pass to guarantee API surface stability for Phase 4 frontend integration. |
| **Evidence** | Contract test failure: 2 failed out of 4. The diff shows changes in paths, components, and schemas between the committed snapshot and the live OpenAPI generation. |
| **Cause** | API routes were added/modified (`agent-actions`, `finance-decisions`) without regenerating the committed OpenAPI snapshot. |
| **Risk** | **Low**. The snapshot just needs regeneration. No behavioral breakage. |
| **Recommendation** | P4 Batch 0: Regenerate the OpenAPI snapshot by running the committed `generate:openapi` script and committing the result. |
| **Severity** | YELLOW |
| **Owner** | tests/contracts |
| **Validation** | Verify `test_openapi_snapshot_matches_committed_contract` passes after snapshot regeneration. |

---

## Summary of Findings by Severity

| Severity | Count | Findings |
|---|---|---|
| **RED** | 3 | F-002 (single workflow), F-003 (non-atomic review closure), F-008 (test infra flaky) |
| **YELLOW** | 7 | F-001 (legacy schema), F-004 (hints ignored), F-005 (request/receipt not enforced), F-009 (finance hardcoding), F-010 (placeholder dirs), F-011 (thick API routes), F-012 (OpenAPI snapshot) |
| **GREEN** | 2 | F-006 (CandidateRule compliance), F-007 (frontend semantic signals) |
| **TOTAL** | 12 | |
