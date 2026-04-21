# Strategy Domain

`domains/strategy/` owns recommendation and outcome business semantics.

## This Package Is For

- recommendation lifecycle objects
- recommendation state transitions
- outcome snapshots that are meaningful in relation to a recommendation

## Core Files

- `models.py` / `orm.py`
  - recommendation truth
- `repository.py`
  - recommendation persistence and read helpers
- `service.py`
  - recommendation creation and lifecycle transitions
- `state_machine.py`
  - recommendation state rules
- `outcome_models.py` / `outcome_orm.py`
  - outcome snapshot truth
- `outcome_repository.py` / `outcome_service.py`
  - outcome snapshot persistence and lookup

## Most Important Runtime Role

This domain is where recommendation truth and recommendation aftermath truth live.

The critical paths are:

- `analyze -> recommendation_generate -> recommendation row`
- `recommendation_status_update -> recommendation transition`
- `review_complete -> outcome snapshot backfill`

## This Package Is Not For

- operator usage counters
- audit trail enforcement
- low-level execution transport

## Boundary Decision

Outcome snapshots remain domain-owned for now because they describe whether a recommendation thesis was satisfied, failed, expired, or unchanged. If they later become pure operational telemetry, part of that behavior can move into `state/`.
