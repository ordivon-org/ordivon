# ADR-006 Completion Design — Wave 3A

**Date**: 2026-04-27
**Status**: DESIGN (read-only, no code changes)
**Audit**: Full-System Re-Audit → Wave 3A

---

## 1. Current State Audit

### 1.1 What's Done (90%)

| Component | Status | Location |
|-----------|--------|----------|
| Pack policy interface | ✅ | `packs/finance/trading_discipline_policy.py` |
| Gate 1-4 logic extracted | ✅ | `TradingDisciplinePolicy.validate_fields/numeric/limits/behavioral` |
| `pack_policy` parameter | ✅ | `RiskEngine.validate_intake(intake, pack_policy=...)` |
| Delegation in RiskEngine | ✅ | `if pack_policy is not None → delegate` |
| Call site passes policy | ✅ | `finance_decisions.py:65`: `pack_policy=TradingDisciplinePolicy()` |
| Finance constants | ✅ | All in Pack (BANNED, EMOTIONAL, INVALIDATION, CONFIRMATION) |
| Private helpers | ✅ | `_as_str`, `_as_positive_float`, `_contains_emotional_risk` in Pack |

### 1.2 What Remains (10%)

Three items only:

| # | Item | Location | Impact |
|---|------|----------|--------|
| 1 | `isinstance(reason, RejectReason)` couples Core to Pack types | `engine.py:88,90` | Core imports Pack classes |
| 2 | `from packs.finance... import RejectReason, EscalateReason` | `engine.py:7` | Boundary violation |
| 3 | Dead code: `thesis_quality.py` still in Core | `governance/risk_engine/thesis_quality.py` | 114 lines of duplicated constants, not imported anywhere |

### 1.3 Verification

```bash
# Confirmed: check_thesis_quality is NOT called anywhere
$ rg "check_thesis_quality|thesis_quality" governance capabilities domains tests -n
# → Only definition in thesis_quality.py, no callers

# Confirmed: thesis_quality is NOT referenced in tests
$ rg "thesis_quality" tests -n
# → 0 results

# Confirmed: Only RejectReason/EscalateReason import in Core
$ rg "RejectReason|EscalateReason" governance -n --glob '!thesis_quality.py'
# → engine.py:7,88,90 only
```

---

## 2. Design

### 2.1 Approach: Severity-Based Protocol

Replace `isinstance` checks with a `.severity` string attribute:

```python
# BEFORE (engine.py:7,88,90)
from packs.finance.trading_discipline_policy import RejectReason, EscalateReason

...
if isinstance(reason, RejectReason):
    reject_reasons.append(reason.message)
elif isinstance(reason, EscalateReason):
    escalate_reasons.append(reason.message)

# AFTER — duck-typing protocol
# No import from packs.finance
...
if reason.severity == "reject":
    reject_reasons.append(reason.message)
elif reason.severity == "escalate":
    escalate_reasons.append(reason.message)
```

**Rationale**: The `.severity` attribute is a Core-owned concept (reject/escalate is a governance primitive). The Pack provides objects that satisfy this simple protocol. No Core→Pack import needed.

### 2.2 Pack Change

Add `.severity` to reason classes:

```python
# packs/finance/trading_discipline_policy.py


class RejectReason:
    def __init__(self, message: str) -> None:
        self.message = message
        self.severity: str = "reject"  # ← ADD


class EscalateReason:
    def __init__(self, message: str) -> None:
        self.message = message
        self.severity: str = "escalate"  # ← ADD
```

### 2.3 Dead Code Removal

Delete `governance/risk_engine/thesis_quality.py` (114 lines):
- All constants already exist in `packs/finance/trading_discipline_policy.py`
- `check_thesis_quality()` not called by any code
- No test references
- The logic lives in `TradingDisciplinePolicy.validate_fields()` lines 88-108

### 2.4 Final Verification

```bash
# After all changes:
rg "RejectReason|EscalateReason" governance/risk_engine/engine.py → 0 results
rg "thesis_quality" governance/ → 0 results
rg "stop_loss|is_chasing|risk_unit_usdt" governance/risk_engine/engine.py → 0 results
```

---

## 3. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Existing tests break | LOW | Tests would catch immediately | Run full PG regression after each commit |
| Protocol mismatch (Pack returns wrong type) | ZERO | — | Pack already returns RejectReason/EscalateReason; we're just adding `.severity` |
| Behavioral change | ZERO | — | Same objects, same messages, same routing; just different classification mechanism |
| Dead code removal breaks something | ZERO | Dead code confirmed | `rg check_thesis_quality` → 0 callers |

---

## 4. Implementation Plan (Wave 3B — only if approved)

### Phase 3B-1: Add `.severity` to Pack classes (3 lines)
```
File: packs/finance/trading_discipline_policy.py
Change: Add `self.severity = "reject"` to RejectReason.__init__
Change: Add `self.severity = "escalate"` to EscalateReason.__init__
Verify: uv run pytest tests/unit/finance/ -q
Tag: adr006-step1-severity
```

### Phase 3B-2: Replace isinstance with severity check (4 lines)
```
File: governance/risk_engine/engine.py
Change: Remove `from packs.finance... import RejectReason, EscalateReason`
Change: Replace isinstance(reason, RejectReason) → reason.severity == "reject"
Change: Replace isinstance(reason, EscalateReason) → reason.severity == "escalate"
Verify: uv run pytest tests/unit/governance/ -q
Verify: PFIOS_DB_URL=... uv run pytest tests/ -q
Tag: adr006-step2-severity
```

### Phase 3B-3: Delete dead thesis_quality.py
```
File: governance/risk_engine/thesis_quality.py → DELETE
Verify: uv run pytest tests/ -q (full regression)
Tag: adr006-step3-cleanup
```

### Phase 3B-4: Final boundary verification
```
Verify: rg "RejectReason|EscalateReason" governance/risk_engine/engine.py → 0
Verify: rg "thesis_quality" governance/ → 0
Verify: rg "stop_loss|is_chasing|risk_unit_usdt" governance/risk_engine/engine.py → 0
Tag: adr006-complete
```

**Total estimated effort**: ~15 minutes
**Total risk**: ZERO (duck-typing change, dead code removal)
**Lines changed**: ~10 lines added, ~117 lines deleted

---

## 5. Decision

### ADR-006 Status: DESIGN COMPLETE → Ready for Wave 3B

The extraction is already 90% done. The remaining work is trivial:
1. Replace `isinstance` with `.severity` string check (decouples Core from Pack types)
2. Delete dead `thesis_quality.py` (no callers, no tests, constants duplicated)

No structural changes. No behavior changes. Full test verification at every step.

### Recommendation: PROCEED to Wave 3B

Risk is zero. All existing tests will pass without modification (the `.severity` attribute is additive, not a breaking change).
