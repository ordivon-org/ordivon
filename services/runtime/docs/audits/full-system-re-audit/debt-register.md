# Technical Debt Register

**Audit**: Full-System Re-Audit
**Date**: 2026-04-27
**Status**: Read-only classification — no debt cleared during audit

---

## Debt Classification Legend

| Severity | Meaning |
|----------|---------|
| **BLOCKING** | Must fix before any forward progress |
| **HIGH** | Should fix before P5 |
| **MEDIUM** | Should fix when touching related code |
| **LOW** | Cosmetic, documentation, or can wait indefinitely |

---

## Active Debt Register

### D-001: Finance Semantic Constants in Core RiskEngine
- **Severity**: MEDIUM
- **Category**: Architecture / ADR-006
- **Evidence**: `governance/risk_engine/engine.py` still contains `validate_intake()` logic. `packs/finance/trading_discipline_policy.py` exists but some constants remain in Core.
- **Risk if unfixed**: Mixing domain semantics with Core validation makes future Pack insertion harder. Risk is LOW — the `pack_policy` parameter isolates domain logic structurally.
- **Recommended wave**: Wave 3B
- **Blocking P5?**: No
- **ADR**: ADR-006

### D-002: `actor_runtime` Hardcoded Default "hermes"
- **Severity**: LOW
- **Category**: Code style
- **Evidence**: `domains/intelligence_runs/models.py:14` and `domains/ai_actions/models.py:15` default to `"hermes"`. Functional but semantically implies Hermes is the only runtime.
- **Risk if unfixed**: Misleading for future multi-provider setups. Zero functional impact.
- **Recommended wave**: Wave 1 (or defer indefinitely)
- **Blocking P5?**: No

### D-003: `docs/naming.md` Outdated
- **Severity**: LOW
- **Category**: Documentation
- **Evidence**: Dated 2026-04-24. Current naming conventions (Ordivon/AegisOS/PFIOS) haven't changed but the document doesn't reflect post-forward-hardening-sprint state.
- **Risk if unfixed**: Minor confusion for new contributors. No functional impact.
- **Recommended wave**: Wave 1
- **Blocking P5?**: No

### D-004: H-10 KnowledgeFeedback Path Coverage
- **Severity**: MEDIUM
- **Category**: Learning loop
- **Evidence**: `extract_for_review_by_id` exists and has unit tests (`tests/unit/knowledge/test_h10_extraction.py`). Path works. Coverage is not exhaustive — edge cases (no recommendation_id, no outcome_ref) could be more tested.
- **Risk if unfixed**: Learning loop may miss edge-case feedback. System still degrades gracefully (returns empty list, doesn't crash).
- **Recommended wave**: Wave 2
- **Blocking P5?**: No

### D-005: "PFIOS" in Runbooks and Environment Variables
- **Severity**: LOW
- **Category**: Naming / Documentation
- **Evidence**: Environment variables (`PFIOS_DB_URL`, `PFIOS_REASONING_PROVIDER`, etc.) use PFIOS prefix. Runbooks reference PFIOS. This is an API surface — renaming would break all existing configurations.
- **Risk if unfixed**: Naming inconsistency with Ordivon/AegisOS identity. Zero functional impact.
- **Recommended wave**: Post-P5 (breaking change, needs migration plan)
- **Blocking P5?**: No

### D-006: Unit Tests Require Explicit DuckDB or PG
- **Severity**: LOW
- **Category**: Test infrastructure
- **Evidence**: 13 unit tests fail with `PFIOS_DB_URL` defaulting to PostgreSQL when PG is unavailable. All pass when run with explicit `PFIOS_DB_URL=duckdb:///:memory:`. No root `conftest.py` to auto-detect environment.
- **Risk if unfixed**: New developers may see spurious failures. CI is configured correctly.
- **Recommended wave**: Wave 1
- **Blocking P5?**: No

### D-007: Integration Tests Require Docker Services
- **Severity**: LOW
- **Category**: Test infrastructure
- **Evidence**: Integration tests require PG + Redis running via Docker Compose. No auto-start in test runner.
- **Risk if unfixed**: Manual Docker startup needed before integration tests. CI handles this correctly.
- **Recommended wave**: Wave 1
- **Blocking P5?**: No

---

## Resolved Debt (Historical)

These debts were identified in prior audits and have been resolved:

| # | Debt | Resolution | Evidence |
|---|------|-----------|----------|
| H-9C1 | Schema drift (outcome_ref columns) | Idempotent migration runner | `state/db/migrations/runner.py` |
| H-9C2 | No escalate pathway | Emotional state + confidence escalation | `scripts/h9c_verification.py` |
| H-9C3 | Thesis quality bypass | Banned pattern detection | `governance/risk_engine/thesis_quality.py` |
| H-1 | Bridge tools/shell/file_write | ALLOW_* = False constants | `services/hermes_bridge/config.py` |
| H-2 | DuckDB as truth source | SQLAlchemy ORM boundary | `state/db/schema.py` markers |
| H-6R | PG full regression missing | PG test infrastructure | CI + Docker Compose |

---

## Debt by Wave (Recommended Execution Order)

### Wave 0: Audit (DONE)
- This audit — no debt cleared, only classified

### Wave 1: Low-Risk Interface Fixes
- D-006: Test auto-configuration
- D-007: Integration test Docker awareness
- D-003: naming.md update
- D-002: actor_runtime default (optional, can defer)

### Wave 2: Medium-Risk Learning Loop
- D-004: H-10 KF path coverage

### Wave 3: Architecture Extraction
- D-001: ADR-006 Finance semantic extraction

### Wave 4: Pressure Test
- 30-run dogfood (not debt — verification)

### Post-P5:
- D-005: PFIOS env var rename (breaking change)

---

## Total Debt Summary

| Severity | Count | Blocking |
|----------|-------|----------|
| BLOCKING | 0 | 0 |
| HIGH | 0 | 0 |
| MEDIUM | 2 | 0 |
| LOW | 5 | 0 |
| **Total** | **7** | **0** |
