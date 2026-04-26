# ADR-006: Pack Policy Binding — Finance Semantic Extraction from Core

> **Date**: 2026-04-26
> **Status**: PROPOSED
> **Replaces**: Known debt from P4 closure re-audit (A3 — Architecture Boundary)

## Context

`RiskEngine.validate_intake()` currently hardcodes finance-domain field names: `stop_loss`, `max_loss_usdt`, `position_size_usdt`, `risk_unit_usdt`, `is_revenge_trade`, `is_chasing`. This violates the Core/Pack boundary: Core governance should not know finance-domain semantics.

This was acceptable tactical debt during H-5/H-9C to validate the control loop quickly. Now that the loop is verified (Wave 0-2 complete), extraction is the next logical step.

## Decision

### Architecture

```
Before:
  RiskEngine.validate_intake(intake)
    → Gate 0: status check (generic)
    → Gate 1: thesis, stop_loss, emotional_state (mixed)
    → Gate 2: max_loss_usdt, position_size_usdt, risk_unit_usdt (finance)
    → Gate 3: risk limit ratios (finance)
    → Gate 4: is_revenge_trade, is_chasing, emotions, confidence (finance)
    → Decision: reject > escalate > execute

After:
  RiskEngine.validate_intake(intake, pack_policy=None)
    → Gate 0: status check (generic — stays)
    → Delegates to pack_policy.validate_fields/numeric/limits/behavioral
    → Decision: reject > escalate > execute (generic — stays)

  packs/finance/trading_discipline_policy.py:
    TradingDisciplinePolicy implements all current Gate 1-4 logic
```

### Interface Contract

```python
class RejectReason:
    message: str

class EscalateReason:
    message: str

class PackIntakePolicy(Protocol):
    def validate_fields(self, payload: dict) -> list[RejectReason | EscalateReason]: ...
    def validate_numeric(self, payload: dict) -> list[RejectReason]: ...
    def validate_limits(self, payload: dict) -> list[RejectReason]: ...
    def validate_behavioral(self, payload: dict) -> list[EscalateReason]: ...
```

### Call Site Change

```python
# capabilities/domain/finance_decisions.py:66
# Before:
decision = RiskEngine().validate_intake(intake)

# After:
from packs.finance.trading_discipline_policy import TradingDisciplinePolicy
decision = RiskEngine().validate_intake(intake, pack_policy=TradingDisciplinePolicy())
```

### Backward Compatibility

If `pack_policy=None`, all gates pass → `execute`. This is safe: the call site must explicitly opt into governance by providing a pack policy. No silent behavior change.

## Consequences

### Positive
- Core RiskEngine becomes domain-agnostic — no finance field names
- Adding a second domain Pack requires zero Core changes
- Finance Pack owns its own governance rules end-to-end
- Tests are already Partitioned: H-5/H-9C tests test governance behavior, not implementation

### Negative
- All 48 test calls must be updated to pass `pack_policy=TradingDisciplinePolicy()`
- `thesis_quality` module moves from `governance/risk_engine/` to `packs/finance/`
- Private helpers (`_as_str`, `_as_positive_float`, `_contains_emotional_risk`) are duplicated in Pack

### Risk Mitigation
- Each commit is a single file change with test verification
- Existing test expectations preserved — same input → same decision
- Final grep verification: `rg "stop_loss|is_chasing|risk_unit_usdt" governance/risk_engine/engine.py` → 0 results
