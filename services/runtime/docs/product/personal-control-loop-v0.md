# Personal Control Loop v0

## Product Reading

Personal Control Loop v0 is the first practical pressure test of the AegisOS control substrate against a real user problem:

- impulsive action
- missing discipline fields
- emotional override
- unstructured risk taking

The first pack used for this pressure test is finance, but the loop is intended to validate a general control pattern rather than a finance-only product identity.

## v0 Surface Map

### `/`

Homepage remains the command center.

It may link to a controlled-decision entry on `/analyze`, but it does not own the intake form.

### `/analyze`

`/analyze` remains the execution workspace and now also owns the first structured decision intake panel for controlled high-consequence actions.

Batch 1 stops after intake validation and persistence.

### `/reviews`

`/reviews` remains the supervision workbench.

In Batch 1 it stays unchanged and reserved for later outcome/review loops.

## v0 User Flow

The first v0 loop is:

`homepage -> /analyze?mode=controlled -> structured intake -> persisted valid/invalid result -> governance not started`

## v0 Safety Boundaries

v0 does not:

- execute broker actions
- create execution receipts
- run governance gate decisions
- capture outcomes
- close reviews
- generate knowledge feedback
- promote candidate rules into policy

## Batch 1 Validation Scope

Batch 1 validates the presence and shape of the first discipline fields:

- thesis
- stop_loss
- max_loss_usdt
- position_size_usdt
- risk_unit_usdt
- emotional_state
- explicit is_revenge_trade
- explicit is_chasing

It also validates:

- numeric finance fields are positive
- direction is one of `long`, `short`, `hold`, `observe`
- confidence, when present, stays within `0..1`

Stop-loss numeric semantics are deferred to Batch 2. Batch 1 only validates stop-loss presence.
