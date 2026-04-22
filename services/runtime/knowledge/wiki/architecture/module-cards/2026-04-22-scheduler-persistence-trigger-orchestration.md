# Module

Scheduler Persistence / Trigger Orchestration

## Layer

Infrastructure

## Type

Core infrastructure

## Role

Deepen scheduler behavior with persistence and multi-trigger dispatch while keeping infra ownership limited to `when`, not `what`.

## Current Value

- `infra/scheduler/` exists.
- It could register and dispatch triggers in memory.

## Remaining Gap

- No persistence existed.
- No batch dispatch behavior existed.

## Immediate Action

- Add file persistence for triggers
- Add enabled-trigger dispatch
- Preserve low-risk capability-facing semantics

## Wrong Placement To Avoid

- Do not put business logic into scheduler
- Do not let scheduler mutate truth directly
- Do not move wake/resume into infra

## Required Test Pack

- `python -m compileall infra/scheduler`
- `pytest -q tests/unit/test_scheduler.py`

## Done Criteria

- Trigger persistence exists
- Enabled-trigger batch dispatch exists
- Scheduler remains infra-owned and low-risk

## Next Unlock

Persistent backend or richer scheduling policies

## Not Doing

- No cron UI
- No database scheduler table
- No business policy logic
