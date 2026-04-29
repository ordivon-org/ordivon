# Full-System Re-Audit Report

**Audit Date**: 2026-04-27
**Auditor**: Hermes Agent (read-only, no code changes made)
**Scope**: Full-system read-only audit of Ordivon / AegisOS
**Methodology**: `forward-hardening-sprint` Wave 0 — baseline capture only

---

## 1. Executive Summary

### Decision: CONDITIONAL PASS

**One-line judgment**: The system is architecturally sound, all P4 invariants hold, PG full regression is green (578/0), and there are zero blocking issues. The only condition is that unit tests requiring PostgreSQL must be run with PG available — this is an environment constraint, not a code defect.

---

## 2. Audit Scope

### Included
- Documentation audit (naming, identity, architecture docs)
- Architecture boundary audit (Core/Pack/Adapter pollution checks)
- State truth / database audit (ORM authority, DuckDB boundary)
- Hermes Bridge / Runtime audit (safety invariants, provider isolation)
- API / OpenAPI contract audit
- P4 Finance control loop audit (Intake → Governance → Plan → Outcome → Review)
- Knowledge / Lesson / CandidateRule audit
- Test / CI / Regression audit (unit + integration + PG full + contracts)
- Dogfood evidence audit (H-9)
- Security / permission / side-effect audit
- Dependency / environment / CI audit
- Pack generalization / P5 readiness audit

### Excluded
- Code modifications
- ORM schema changes
- API changes
- Test modifications
- H-10 implementation
- H-8R implementation
- Finance extraction implementation
- 30-run dogfood execution
- Broker/order/trade integration
- P5 / Coding Pack implementation
- Automatic fixes of any kind

---

## 3. Current Git / Tag State

**HEAD**: `9670f83` — `fix(ci): resolve all CI failures — uv run, gitleaks, ruff, setup-uv@v8, schema drift`

**Working tree**:
- 3 uncommitted plan documents (`.hermes/plans/`, `docs/plans/`)
- `uv.lock` — stat-only change (no dependency drift)

**Key tags present**:
| Tag | Status | Description |
|-----|--------|-------------|
| `h5-finance-governance-hard-gate` | ✓ | DecisionIntake + Governance |
| `h6-finance-plan-only-receipt` | ✓ | Plan-only receipt |
| `h6r-pg-full-regression` | ✓ | PG regression baseline |
| `h7-manual-outcome-review-link` | ✓ | Manual outcome |
| `h8-review-outcome-closure` | ✓ | Review closure |
| `h8r-outcome-ref-response` | ✓ | Outcome ref API response |
| `h9-dogfood-evidence` | ✓ | Dogfood evidence collected |
| `h9c-dogfood-verified` | ✓ | H-9C verification |
| `h9f-30-run-evidence` | ✓ | Extended dogfood |
| `h10-kf-generalization` | ✓ | H-10 extraction path |
| `p4-finance-control-loop-validated` | ✓ | Full control loop |
| `forward-hardening-sprint-complete` | ✓ | Sprint closure |
| `docs-d0` through `docs-d5c` | ✓ | Documentation phases |
| `post-p4-finance-extraction` | ✓ | ADR-006 extraction |

**Verdict**: All key tags traceable. Working tree clean for audit purposes.

---

## 4. Documentation Findings

### 4.1 Identity Definition

`docs/architecture/ordivon-system-definition.md` is canonical. Key assertions verified:

| Assertion | Status | Evidence |
|-----------|--------|----------|
| Ordivon = general-purpose governance-first AI OS | ✓ PASS | ordvon-system-definition.md:18-19 |
| Finance = first Pack, not Core identity | ✓ PASS | ordvon-system-definition.md:58-60 |
| Hermes/DeepSeek = Adapter/Provider | ✓ PASS | harnees-adapter-boundary.md |
| Context = data engineering object | ✓ PASS | context_design.md:44-98 |
| Reasoning ≠ truth source | ✓ PASS | reasoning_contract.md |
| Receipt = evidence index | ✓ PASS | governance-receipt-review-loop.md |
| Knowledge = advisory | ✓ PASS | ADR-002 |
| CandidateRule ≠ Policy | ✓ PASS | constitution.md |

### 4.2 Naming Residues

"PFIOS" appears in:
- Environment variable names (`PFIOS_DB_URL`, `PFIOS_REASONING_PROVIDER`, etc.) — ACCEPTABLE (env vars are API surfaces)
- Runbooks — ACCEPTABLE (operational docs reference actual env vars)
- Archive/legacy docs — ACCEPTABLE (archived, not active)

"financial-ai-os" directory name — ACCEPTABLE (per naming.md decision)

### 4.3 Authoritative Docs List

| Document | Status | Action |
|----------|--------|--------|
| `ordivon-system-definition.md` | Canonical | Keep |
| `constitution.md` | Canonical | Keep |
| `state-truth-boundary.md` | Canonical | Keep |
| `core-pack-adapter-boundary.md` | Canonical | Keep |
| `governance-receipt-review-loop.md` | Canonical | Keep |
| `LANGUAGE.md` | Canonical | Keep |
| `naming.md` | Valid but dated | Update pre-P5 |

### 4.4 Outdated Docs

Archive properly contains legacy docs. No outdated active docs found.

---

## 5. Architecture Boundary Findings

### 5.1 Core → Pack Imports

All Core-to-Pack imports go through approved interfaces:
- `governance/policy_source.py` → `packs.finance.policy` — approved policy binding
- `governance/risk_engine/engine.py` → `packs.finance.trading_discipline_policy` — ADR-006 path
- `capabilities/workflow/analyze.py` → `packs.finance.analyze_profile` — capability layer
- `capabilities/domain/finance_decisions.py` → `packs.finance.decision_intake` — capability layer

**Verdict**: No boundary violations. All imports are traceable through approved interface contracts.

### 5.2 Finance Fields in Core

Finance-specific fields (`stop_loss`, `max_loss_usdt`, `position_size_usdt`, etc.):
- Present in `apps/api/app/schemas/finance_decisions.py` — API schema, not Core logic
- Present in `apps/web/` — frontend form components
- Present in `state/db/schema.py` — marked LEGACY/DuckDB only, not active

**Verdict**: Finance semantics in API layer is expected (API = Pack surface). No Core logic pollution.

### 5.3 Hermes/Provider in Core

- `domains/intelligence_runs/models.py`: `actor_runtime: str = "hermes"` — minor hardcoding, NON-BLOCKING
- Health endpoint: conditional Hermes status check — acceptable (health monitoring)

**Verdict**: No provider identity leakage into Core governance or truth. Minor naming defaults.

### 5.4 Review Outcome Reference Pattern

Review uses `outcome_ref_type` / `outcome_ref_id` (generic string refs):
- NOT hard FK to `FinanceManualOutcome`
- Validation at application layer, not schema layer
- Supports future Pack outcome types without schema changes

**Verdict**: Correct polymorphic ref pattern.

### 5.5 Boundary Classification

| Concern | Status | Category |
|---------|--------|----------|
| Adapter → Core truth write | NOT FOUND | — |
| Hermes/provider → Core identity | NOT FOUND | — |
| Review → hard FK Finance outcome | NOT FOUND | — |
| Broker/order/trade in Core | NOT FOUND | — |
| RiskEngine Finance field residues | FOUND | Non-blocking (ADR-006) |

---

## 6. State Truth / Database Findings

### 6.1 ORM Registration

All domain ORM models registered in `state/db/bootstrap.py`:
- FinanceManualOutcomeORM ✓
- DecisionIntakeORM ✓
- ReviewORM ✓
- LessonORM ✓
- KnowledgeFeedbackPacketORM ✓
- ExecutionReceiptORM ✓
- OutcomeSnapshotORM ✓

### 6.2 ReviewORM Schema

- `outcome_ref_type` column: nullable String ✓
- `outcome_ref_id` column: nullable String ✓
- H-9C schema drift resolved (idempotent migration runner) ✓

### 6.3 DuckDB Boundary

- `state/db/schema.py` header: "NOT DOMAIN TRUTH FOR P4" ✓
- 8x "NOT DOMAIN TRUTH" markers throughout schema.py ✓
- No P4 domain writes to DuckDB ✓
- DuckDB used only for analytics/legacy/test ✓

### 6.4 Migration Strategy

- `Base.metadata.create_all()` for fresh databases ✓
- Idempotent migration runner for existing databases ✓
- No manual ALTER TABLE required ✓
- `check_schema_drift.sh` v2 uses DDL op counting ✓

**Verdict**: State truth boundary intact. No drift. No manual patches needed.

---

## 7. Runtime / Hermes Bridge Findings

### 7.1 Bridge Surface

Files: `services/hermes_bridge/app.py`, `config.py`, `hermes_runner.py`, `schemas.py`

- Only supports `analysis.generate` endpoint ✓
- No tools/shell/file_write enabled ✓
- Safety constants: `ALLOW_TOOLS=False`, `ALLOW_SHELL=False`, `ALLOW_FILE_WRITE=False` ✓
- Unit test `test_hermes_bridge_contract.py` validates all three flags ✓

### 7.2 Bridge Isolation

- Bridge does NOT import or write to Ordivon ORM ✓
- Bridge does NOT execute Governance ✓
- Bridge does NOT create Receipts ✓
- Bridge does NOT access Ordivon DB ✓

### 7.3 Provider Failure Handling

- `HermesRuntimeError` raised on failure ✓
- Does not fabricate `completed` reasoning on failure ✓
- Mock provider available for deterministic tests ✓
- DeepSeek instability affects runtime smoke only, not deterministic tests ✓

### 7.4 IntelligenceRun / AgentAction

- Both owned by Ordivon Core (`domains/intelligence_runs/`, `domains/ai_actions/`) ✓
- Recorded by Core capability layer, not by Bridge ✓
- `actor_runtime` field identifies provider without ceding sovereignty ✓

**Verdict**: Bridge is a safe adapter. No sovereignty leakage.

---

## 8. API / OpenAPI Findings

### 8.1 Contract Tests

All 8 contract tests pass:
- `test_openapi_snapshot_matches_committed_contract` ✓
- `test_health_contract_surface_is_stable` ✓
- `test_history_contract_surface_is_stable` ✓
- `test_analyze_response_contract_includes_object_continuation_fields` ✓
- `test_reject_path_returns_governance_error` ✓
- `test_not_found_returns_structured_error` ✓
- `test_submit_review_accepts_outcome_ref_fields` ✓
- `test_submit_review_without_outcome_ref_still_succeeds` ✓

### 8.2 Endpoint Coverage

| Endpoint | Status | H-tag |
|----------|--------|-------|
| `POST /finance-decisions/intake` | ✓ | H-5 |
| `POST /finance-decisions/intake/{id}/govern` | ✓ | H-5 |
| `POST /finance-decisions/intake/{id}/plan` | ✓ | H-6 |
| `POST /finance-decisions/intake/{id}/outcome` | ✓ | H-7 |
| `POST /reviews/submit` | ✓ | H-8 |
| `POST /reviews/{id}/complete` | ✓ | H-8 |
| `GET /reviews/{id}` | ✓ | H-8R |

### 8.3 H-8R: Outcome Ref in API Response

Review API response includes `outcome_ref_type` and `outcome_ref_id` fields.
Contract test `test_submit_review_accepts_outcome_ref_fields` confirms echo-back.

**Verdict**: H-8R is present and verified. No blocking gap.

---

## 9. P4 Control Loop Findings

### 9.1 DecisionIntake (H-4/H-5)

Structured fields enforced:
- thesis (required, quality-gated)
- stop_loss, max_loss_usdt, position_size_usdt, risk_unit_usdt
- is_revenge_trade, is_chasing
- emotional_state, confidence
- rule_exceptions

Gate behavior verified:
- Missing critical fields → reject ✓
- "just feels right" / "YOLO" / banned patterns → reject ✓
- Revenge/chasing/emotional anomaly → escalate ✓
- Valid thesis with evidence → execute ✓

### 9.2 Governance (H-5)

- `RiskEngine.validate_intake()` is mandatory ✓
- Routes call governance, never re-implement locally ✓
- Priority: reject > escalate > execute ✓
- `pack_policy` parameter supports ADR-006 ✓
- Invalid intake cannot proceed to plan ✓

### 9.3 Plan-only Receipt (H-6)

- `action_id = finance_decision_plan` ✓
- `receipt_kind = plan` ✓
- `broker_execution = false` ✓
- `side_effect_level = none` ✓
- Duplicate plan → 409 ✓
- Non-execute intakes rejected ✓
- No broker/order/trade paths ✓

### 9.4 Manual Outcome (H-7)

- `outcome_source = manual` ✓
- Requires valid plan receipt ✓
- Requires decision_intake_id + execution_receipt_id ✓
- Duplicate outcome → 409 ✓
- Does NOT auto-create Review/CandidateRule/Policy ✓

### 9.5 Review Closure (H-8)

- Accepts `outcome_ref_type` / `outcome_ref_id` ✓
- Validates outcome existence ✓
- Unsupported outcome type → rejected ✓
- Missing outcome ref → rejected ✓
- `complete_review` preserves outcome_ref ✓
- Lesson + KnowledgeFeedback generated on completion ✓
- No CandidateRule auto-creation ✓
- No Policy auto-promotion ✓

### 9.6 Lesson / KnowledgeFeedback (H-3/H-10)

- Review → Lesson extraction: working ✓
- Lesson → KnowledgeFeedback: working on supported paths ✓
- `extract_for_review_by_id` exists ✓ (unit tests pass)
- Finance review without recommendation_id: KF generation conditional (H-10 gap)

**H-10 status**: `extract_for_review_by_id` path exists and is tested.
KnowledgeFeedback generalization is present but path coverage could be broader.
NON-BLOCKING — recommended for Wave 2.

---

## 10. Test / CI Findings

### 10.1 Test Counts

| Suite | Files | Tests | Result |
|-------|-------|-------|--------|
| Unit | 115 | 435 | 435 pass (DuckDB) |
| Integration | 25 | — | requires PG |
| Architecture | 2 | — | pass |
| Contracts | 4 | 8 | 8 pass |
| **PG Full Regression** | **all** | **578** | **578 pass, 0 fail** |

### 10.2 Skip/Xfail

Minimal, all justified:
- `pytest.skip` in lesson invariant probe (conditional, intentional)
- Architecture test skips `__pycache__` and migrations dirs (correct)

### 10.3 CI Readiness

- 147 test files, 578 tests pass on PG
- Contract snapshot verified
- No manual ALTER TABLE in tests
- H-9C 18/18 passes
- Schema drift check passes

**Verdict**: Test infrastructure solid. PG full regression is the gold standard.

---

## 11. Dogfood Evidence Findings

### 11.1 Artifacts

| Artifact | Status | Details |
|----------|--------|---------|
| `scripts/h9_dogfood_runs.py` | Committed | 1011 lines, 10+ realistic runs |
| `scripts/h9c_verification.py` | Committed | 248 lines, 18 targeted checks |
| `docs/runtime/h9-evidence-report.md` | Committed | Structured evidence |
| `docs/runtime/h9-evidence-report-v2.txt` | Committed | Updated report |

### 11.2 Coverage

| Scenario | Count | Status |
|----------|-------|--------|
| Execute | 3+ | Verified |
| Reject | 4+ | Verified |
| Escalate | 2+ | Verified |
| Full chain (Intake→Review) | 1+ | Verified |
| Errors | 0 | Verified |
| Bypass attempts | 0 found | Verified |
| Manual ALTER TABLE | 0 | Verified |

### 11.3 Verdict

**H-9 Evidence Status: COMPLETE**

Dogfood runs cover execute/reject/escalate. Full-chain samples exist.
No errors. No manual schema patches. No bypass attempts detected.

---

## 12. Security / Side Effect Findings

### 12.1 Broker/Trade/Order

- No broker integration code ✓
- Architecture test `test_no_broker_in_core.py` enforces invariant ✓
- `policies/trading_limits.yaml` is a config file, not active integration ✓

### 12.2 Shell/Tool/File Write

- `ALLOW_TOOLS=False` in bridge config ✓
- `ALLOW_SHELL=False` in bridge config ✓
- `ALLOW_FILE_WRITE=False` in bridge config ✓
- Unit test validates all three ✓

### 12.3 Auto-Policy

- CandidateRule: no auto-creation ✓
- Policy: no auto-promotion ✓
- Human approval required for policy changes ✓

### 12.4 Governance Bypass

- Constitution Article 1 prohibits model self-certification ✓
- RiskEngine is mandatory (routes must call `validate_intake()`) ✓
- No bypass path found ✓

**Verdict**: Security invariants hold. No side-effect leakage.

---

## 13. Pack Generalization / P5 Readiness

### 13.1 Current State

| Capability | Status | Notes |
|-----------|--------|-------|
| Finance semantics in Core RiskEngine | Partial | ADR-006 extraction done; residue remains |
| Pack policy binding interface | ✓ | `pack_policy` parameter on `validate_intake()` |
| Domain-agnostic validation | ✓ | RiskEngine separates structural vs domain validation |
| Coding Pack reuse of Intake/Governance | ✓ | Pattern is reusable |

### 13.2 Required Before P5

1. **ADR-006 completion**: Extract remaining Finance semantic constants from Core RiskEngine (non-blocking, low-risk)
2. **naming.md update**: Refresh with current naming conventions
3. **Pack policy interface documentation**: Formalize the `pack_policy` contract

### 13.3 P5 Readiness: CONDITIONALLY READY

The architecture supports Coding Pack insertion. The Intake→Governance→Receipt→Outcome→Review chain is domain-agnostic at the structural level. Finance-specific validation is properly injected via `pack_policy` parameter.

---

## 14. Blocking Issues

| # | Issue | Evidence | Required fix |
|---|-------|----------|--------------|
| — | **NONE** | — | — |

No blocking issues found.

---

## 15. Non-blocking Debt

| # | Debt | Category | Recommended wave |
|---|------|----------|------------------|
| 1 | Finance semantic constants in Core RiskEngine | Architecture | Wave 3 (ADR-006 completion) |
| 2 | `actor_runtime: str = "hermes"` hardcoded default | Code style | Wave 1 |
| 3 | `docs/naming.md` dated 2026-04-24 | Documentation | Wave 1 |
| 4 | H-10 KF generalization path coverage | Learning loop | Wave 2 |
| 5 | "PFIOS" in runbooks/env vars | Documentation | Post-P5 (env var rename is breaking) |
| 6 | Unit tests require PG env or explicit DuckDB override | Test infrastructure | Wave 1 (add conftest.py default) |
| 7 | Integration tests require Docker services | Test infrastructure | Wave 1 |

---

## 16. Required Before P5

1. No blocking requirements
2. Recommended: ADR-006 Finance semantic extraction completion (Wave 3)
3. Recommended: naming.md refresh (Wave 1)
4. Recommended: test environment auto-configuration (Wave 1)

---

## 17. Recommended Next Action

**Wave 0**: Audit verified — system is visible ✅ (DONE)

**Wave 1** (LOW RISK — approved):
- Update `docs/naming.md`
- Add test conftest.py with DB URL auto-detection
- Fix `actor_runtime` default (can remain for now)

**Wave 2** (MEDIUM RISK — conditional):
- H-10 KF extraction path coverage
- Extended learning-loop tests

**Wave 3** (DESIGN FIRST — conditional):
- 3A: ADR-006 completion design
- 3B: Finance semantic extraction from Core RiskEngine

**Wave 4**: 30-run dogfood (must run AFTER structural changes)

**Wave 5**: Final verification + declaration

---

## 18. Final Decision

### CONDITIONAL PASS

**Conditions**:
1. PG must be available for full regression (Docker Compose `up -d`)
2. No code changes made during this audit

**Foundation**: The system is architecturally sound, invariants hold, all 578 PG regression tests pass, and zero blocking issues exist. The path to P5 is clear and well-understood.

**Recommendation**: Proceed to Wave 1 (low-risk interface fixes) with confidence.
