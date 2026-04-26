# H-2 to H-5: Closure Summary

> **Date**: 2026-04-26
> **Status**: All CLOSED
> **Scope**: H-2 through H-5 runtime baseline stages

This document provides a concise record of H-2 through H-5 completion,
matching the pattern established by [H-1](../runtime/h1-real-model-under-control.md).

---

## H-2: State Truth Boundary

**Tag**: `h2` | **Evidence**: `docs/architecture/state-truth-boundary.md` | **Date**: 2026-04-26

### Goal

Establish a hard boundary between SQLAlchemy ORM (domain truth) and DuckDB (analytics).
Every write that affects governance, workflow state, audit history, or business decisions
MUST go through a SQLAlchemy repository.

### Evidence

- `docs/architecture/state-truth-boundary.md` (192 lines) — authoritative boundary spec
- `state/db/bootstrap.py` — canonical schema initialization via `Base.metadata.create_all`
- All domain ORM models registered in bootstrap: AnalysisORM, RecommendationORM,
  DecisionIntakeORM, ReviewORM, LessonORM, KnowledgeFeedbackPacketORM,
  ExecutionRequestORM, ExecutionReceiptORM, WorkflowRunORM, etc.
- Repository pattern enforced: `domains/*/repository.py` for all truth writes

### Tests

- `tests/unit/test_boundary_import_hygiene.py` — verifies boundary imports don't leak
- `tests/unit/test_db_bootstrap.py` — verifies all ORM models register correctly
- Integration tests verify repository write paths

### Non-goals

- Does not delete DuckDB — DuckDB remains for analytics/legacy pipeline
- Does not rewrite existing DuckDB queries
- Does not add a migration framework beyond existing Alembic

---

## H-2A: Architecture Language Baseline

**Tag**: `h2a` | **Evidence**: `docs/architecture/LANGUAGE.md` | **Date**: 2026-04-22

### Goal

Establish a shared, enforceable vocabulary for all Ordivon/PFIOS architecture discussions.
Generic words are banned from architecture output to prevent vagueness.

### Evidence

- `docs/architecture/LANGUAGE.md` (76 lines) — defines Module, Interface, Implementation,
  Seam (Internal/External), Adapter, Depth, Leverage, Locality, Caller, Call Site,
  Test Surface, Variation, Pass-through, Deletion Test
- Referenced as canonical vocabulary in architecture-baseline.md
- All architecture docs that post-date LANGUAGE.md use these terms

### Tests

- No programmatic tests (language enforcement is human-level)
- Doc cross-reference check: architecture-baseline.md defers to LANGUAGE.md for terminology

### Non-goals

- Does not enforce language in code comments or commit messages
- Does not define domain-specific terms (finance, governance — those live in their own specs)

---

## H-3: Review → Lesson → KnowledgeFeedback Closure

**Tag**: `h3` | **Evidence**: `domains/journal/`, `domains/knowledge_feedback/`, `governance/feedback.py`

### Goal

Close the learning loop: after a recommendation plays out, a Review is conducted,
Lessons are extracted, and KnowledgeFeedback packets feed back into future decisions.

### Evidence

- `domains/journal/models.py` — Review dataclass with verdict, variance_summary, cause_tags,
  lessons, followup_actions
- `domains/journal/lesson_models.py` — Lesson model with source recommendation/analysis refs
- `domains/journal/lesson_service.py` — Lesson extraction and persistence
- `domains/knowledge_feedback/models.py` — KnowledgeFeedbackPacketRecord linking
  recommendation → review → knowledge entries
- `domains/knowledge_feedback/service.py` / `repository.py` — feedback persistence
- `governance/feedback.py` — GovernanceFeedbackHintConsumer: consumes evidence-backed
  governance hints under advisory-only semantics
- `knowledge/feedback.py` — KnowledgeFeedbackService
- `knowledge/extraction.py` — LessonExtractionService
- `intelligence/feedback.py` — IntelligenceFeedbackHintConsumer

### Tests

- `tests/unit/test_review_service.py`
- `tests/unit/test_lesson_extraction.py`
- `tests/unit/governance/test_governance_feedback.py`
- `tests/unit/test_intelligence_feedback.py`
- `tests/unit/test_knowledge_feedback.py`
- `tests/unit/test_knowledge_feedback_packet_repository.py`
- `tests/unit/test_knowledge_retrieval.py`
- `tests/unit/test_knowledge_activation_invariants.py`
- `tests/unit/test_domain_review_imports.py`
- `tests/unit/test_domain_lesson_imports.py`
- `tests/integration/test_knowledge_lesson_adapter.py`
- `tests/integration/test_api_v1_reviews.py`

### Non-goals

- Does not automate lesson extraction from unstructured text (human-in-loop for now)
- Does not enforce lesson application — lessons are advisory hints, not hard constraints
- Does not close the loop on CandidateRule promotion (H-6+ territory)

---

## H-4: DecisionIntake Discipline Validation

**Tag**: `h4` | **Evidence**: `domains/decision_intake/`, `packs/finance/decision_intake.py`

### Goal

Validate every DecisionIntake payload before it reaches governance. Enforce discipline
fields (thesis, stop_loss, max_loss, risk_unit, emotional_state, revenge/chase detection)
as required inputs. Invalid intakes are blocked before governance runs.

### Evidence

- `domains/decision_intake/models.py` — DecisionIntake dataclass with status
  (draft/validated/invalid), governance_status (not_started/execute/escalate/reject),
  payload dict, validation_errors list
- `domains/decision_intake/service.py` — Domain service for intake lifecycle
- `domains/decision_intake/repository.py` — SQLAlchemy persistence
- `domains/decision_intake/orm.py` — DecisionIntakeORM registered in bootstrap
- `packs/finance/decision_intake.py` — FinanceDecisionValidationResult,
  `validate_finance_decision_intake()` with full field validation:
  - Required fields: symbol, timeframe, direction, thesis, entry_condition,
    invalidation_condition, stop_loss, target, position_size_usdt, max_loss_usdt,
    risk_unit_usdt, is_revenge_trade, is_chasing, emotional_state, confidence
  - Direction must be in {long, short, hold, observe}
  - Confidence must be 0.0–1.0
  - Discipline flags (is_revenge_trade, is_chasing) validated
- `apps/api/app/api/v1/finance_decisions.py` — POST endpoint for intake submission
- `apps/api/app/schemas/finance_decisions.py` — Pydantic schemas
- `capabilities/domain/finance_decisions.py` — Capability contract

### Tests

- `tests/unit/test_finance_decision_intake_validation.py` — field-level validation
- `tests/unit/test_decision_intake_domain.py` — domain model invariants
- `tests/unit/test_finance_decision_intake.py` — intake lifecycle
- `tests/integration/test_finance_decision_intake_api.py` — API roundtrip

### Non-goals

- Does not enforce position limits or portfolio constraints (P4 territory)
- Does not wire intake to automated execution (H-6 is plan-only, H-7+ is execution)
- Does not validate against historical performance (CandidateRule territory)

---

## H-5: Finance Governance Hard Gate

**Tag**: `h5` | **Evidence**: `governance/risk_engine/engine.py`, `tests/unit/governance/test_h5_finance_governance_hard_gate.py`

### Goal

Enforce 12 hard-gate rules on every validated DecisionIntake before any execution path
is opened. Decision priority: **reject > escalate > execute**.

### Evidence

- `governance/risk_engine/engine.py` (200 lines) — RiskEngine with explicit H-5 header
- `tests/unit/governance/test_h5_finance_governance_hard_gate.py` (300 lines) —
  comprehensive test suite with 12+ test cases

#### Hard Gate Rules

**REJECT** (highest priority — any single reject reason blocks execution):

| # | Rule | Severity |
|---|------|----------|
| 1 | Intake status is `"invalid"` | REJECT |
| 2 | Missing thesis | REJECT |
| 3 | Missing stop_loss | REJECT |
| 4 | Missing emotional_state | REJECT |
| 5 | Missing max_loss_usdt | REJECT |
| 6 | Missing position_size_usdt | REJECT |
| 7 | Missing risk_unit_usdt | REJECT |
| 8 | max_loss_usdt > 2× risk_unit_usdt | REJECT |
| 9 | position_size_usdt > 10× risk_unit_usdt | REJECT |
| 10 | thesis is empty or whitespace-only | REJECT |

**ESCALATE** (medium priority — needs human review):

| # | Rule | Severity |
|---|------|----------|
| 11 | is_revenge_trade = true | ESCALATE |
| 12 | is_chasing = true | ESCALATE |

**EXECUTE** (lowest priority — all checks passed):
- All fields valid, no reject reasons, no escalate reasons

#### Decision Priority Algorithm

```python
if any_reject_reason:
    return GovernanceDecision(decision="reject", reasons=reject_reasons)
elif any_escalate_reason:
    return GovernanceDecision(decision="escalate", reasons=escalate_reasons)
else:
    return GovernanceDecision(decision="execute", reasons=[])
```

### Tests

- `tests/unit/governance/test_h5_finance_governance_hard_gate.py`:
  - `test_h5_invalid_intake_rejected`
  - `test_h5_missing_thesis_rejected`
  - `test_h5_missing_stop_loss_rejected`
  - `test_h5_missing_emotional_state_rejected`
  - `test_h5_missing_max_loss_rejected`
  - `test_h5_missing_position_size_rejected`
  - `test_h5_missing_risk_unit_rejected`
  - `test_h5_max_loss_exceeds_risk_unit_ratio_rejected`
  - `test_h5_position_size_exceeds_risk_unit_ratio_rejected`
  - `test_h5_empty_thesis_rejected`
  - `test_h5_revenge_trade_escalated`
  - `test_h5_chasing_escalated`
  - `test_h5_valid_intake_executed`
  - `test_h5_priority_reject_over_escalate`
  - `test_h5_side_effect_free_validation`

### Non-goals

- Does not implement dynamic risk limits (static limits from trading_limits.yaml)
- Does not implement portfolio-level risk checks (P4 territory)
- Does not implement market-condition-based gates (P4 territory)
- Governance hints are advisory only — they do not override hard gates

---

## Cross-H-Stage Invariants

These invariants hold across H-1 through H-5 and must be preserved in H-6+:

1. **SQLAlchemy is the single source of truth** for all domain writes (H-2)
2. **Governance runs before any execution path** (H-5)
3. **All intakes are validated before reaching governance** (H-4)
4. **Reviews produce lessons that feed back as advisory hints** (H-3)
5. **Real model calls go through the Ordivon bridge, not direct API** (H-1)
6. **Architecture vocabulary is enforced in all new docs** (H-2A)
