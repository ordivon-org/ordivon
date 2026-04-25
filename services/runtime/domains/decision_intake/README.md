# Decision Intake Domain

## Purpose

`domains/decision_intake` owns persisted intake truth only.

It stores a submitted intake payload, structured validation errors, the current intake status, and the governance handoff status stub for later phases.

## Owns

- persisted intake payload
- persisted `validated` / `invalid` state
- persisted structured `validation_errors`
- persisted `governance_status` stub for later handoff

## Does Not Own

This domain does not own:

- governance decisions
- execution requests or receipts
- outcomes
- review completion
- knowledge feedback
- candidate rules

Those remain deferred to later Phase 4 batches.
