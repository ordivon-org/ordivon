# Next Action Recommendation

**Audit**: Full-System Re-Audit
**Date**: 2026-04-27
**Decision**: CONDITIONAL PASS
**Foundation**: 578/578 PG regression tests pass, zero blocking issues, all P4 invariants hold

---

## Summary of Findings

The system is in a **strong, clean state**. The Forward Hardening Sprint has delivered:
- H-1 through H-9 complete and verified
- All P4 control loop invariants validated
- PG full regression: 578 passed, 0 failed
- Contract tests: 8/8
- Architecture boundaries intact
- Dogfood evidence complete
- No blocking technical debt

The path to P5 is clear and well-understood. No emergency work needed.

---

## Recommended Execution Order

### Wave 0: System Visibility ✅ COMPLETE

This audit is Wave 0. The system is now fully visible.

**Key metrics**:
- 147 test files, 578 PG regression tests
- 0 blocking issues
- 7 non-blocking debts classified
- All architecture invariants verified

---

### Wave 1: Low-Risk Interface Fixes — APPROVED

**Risk**: Minimal. Surface-area changes only.

**Tasks**:
1. Add test conftest.py with DB URL auto-detection
   - Default to `duckdb:///:memory:` when `PFIOS_DB_URL` is unset
   - Eliminates the 13 spurious unit test failures
   - Risk: zero (disambiguates default, doesn't change behavior)

2. Update `docs/naming.md`
   - Mark as "Last verified: 2026-04-27 (Full-System Re-Audit)"
   - No content changes needed — naming decision still stands
   - Risk: zero

3. (Optional) `actor_runtime` default
   - Change "hermes" → "adapter" or keep as-is
   - Risk: minimal (renaming a default value)
   - Can defer indefinitely

**Acceptance criteria**:
- `uv run pytest tests/unit -q` should pass clean without env vars
- naming.md updated

**Do NOT**:
- Change any business logic
- Modify API schemas
- Touch governance
- Run dogfood (not needed for Wave 1)

---

### Wave 2: Medium-Risk Learning Loop — CONDITIONAL

**Risk**: Moderate. New code paths, but bounded surface area.

**Prerequisites**: Wave 1 complete. PG full regression green.

**Tasks**:
1. H-10 KF extraction path coverage expansion
   - Add integration test: review without recommendation_id → KF still generated
   - Add integration test: review without outcome_ref → KF handling
   - Add edge-case test: empty lessons → empty KF
   - Risk: LOW (adding tests, not changing logic)

2. KnowledgeFeedback completeness audit
   - Verify all `complete_review` paths generate KF
   - Verify KF generated for escalate-then-review paths
   - Risk: LOW (read-only verification)

**Acceptance criteria**:
- H-10 test coverage increased
- PG full regression still green
- No regressions

**Do NOT**:
- Change KF generation logic (unless bug found)
- Auto-create CandidateRule
- Auto-promote Policy
- Change Review workflow

---

### Wave 3: Architecture Extraction — CONDITIONAL (Design First)

**Risk**: Highest. Structural changes. Must verify behavioral equivalence.

**Phase 3A: Design (READ-ONLY)**:
1. Complete ADR-006 design document
   - Identify all remaining Finance semantic constants in Core RiskEngine
   - Design extraction target: what moves, what stays
   - Define behavioral equivalence tests
   - Risk: zero (design only, no code changes)

2. Pack interface documentation
   - Formalize `pack_policy` contract
   - Document what a new Pack must implement
   - Define Coding Pack template

**Phase 3B: Implementation (only if 3A accepted and Wave 1/2 stable)**:
1. Extract Finance semantic constants from Core RiskEngine
   - Move remaining constants to `packs/finance/trading_discipline_policy.py`
   - Core RiskEngine keeps only structural validation
   - Risk: MODERATE (must verify all existing tests still pass)

2. Verify behavioral equivalence
   - Run full H-5/H-9C test suite
   - Run PG full regression
   - Compare governance decisions before/after
   - Risk: MODERATE

**Acceptance criteria**:
- `rg "stop_loss|max_loss_usdt|position_size_usdt" governance/` → 0 results
- All existing tests pass
- Behavioral equivalence confirmed

**Do NOT**:
- Change governance flow
- Add new Pack types before extraction verified
- Skip design phase

---

### Wave 4: Extended Pressure Test — CONDITIONAL

**Risk**: Low (read-only verification). Must run AFTER structural changes.

**Prerequisites**: Wave 3 complete.

**Tasks**:
1. Run 30+ dogfood runs covering:
   - Execute: 10 runs (various valid scenarios)
   - Reject: 10 runs (thesis quality, risk limits, forbidden patterns)
   - Escalate: 10 runs (emotional, confidence, exceptions)

2. Full-chain samples:
   - At least 5 complete Intake→Governance→Plan→Outcome→Review chains
   - Verify Receipt immutability
   - Verify KnowledgeFeedback generation

**Acceptance criteria**:
- 30/30 runs complete with expected outcomes
- 0 errors
- 0 manual interventions
- 0 governance bypasses

---

### Wave 5: Final Verification — CONDITIONAL

**Prerequisites**: Wave 4 complete.

**Tasks**:
1. PG full regression: 578+ tests, 0 failures
2. Contract snapshot verification
3. All tags in sequence
4. Declaration document

---

## What Should NOT Happen Next

These tasks should NOT be started now:
- ❌ Broker/order/trade integration (not in scope)
- ❌ Coding Pack implementation (requires Wave 3 first)
- ❌ Large-scale refactoring (not needed)
- ❌ "P5 development" without audit findings addressed
- ❌ Running 30 dogfood runs before structural changes (tests old system, not new)
- ❌ Skipping Wave 1 and jumping to Wave 3 (low-risk cleanups should come first)

---

## Immediate Next Action

**Start Wave 1 immediately**:
1. Add test conftest.py (10-minute task)
2. Update naming.md (2-minute task)
3. Commit with tag `wave1-interface-fixes`

This is zero-risk work that improves developer experience and doesn't touch any business logic.

---

## Risk Map

```
Wave 1: ████░░░░░░  LOW — surface changes only
Wave 2: ██████░░░░  LOW-MED — test additions
Wave 3A: ██░░░░░░░░  ZERO — design only
Wave 3B: ████████░░  MEDIUM — structural extraction
Wave 4: ███░░░░░░░  LOW — verification only
Wave 5: ████░░░░░░  LOW — final checks
```
