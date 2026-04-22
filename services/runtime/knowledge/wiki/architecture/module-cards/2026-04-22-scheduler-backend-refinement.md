# Module

Scheduler Backend Refinement

## Layer

Infrastructure

## Type

Core infrastructure

## Role

Move scheduler persistence from file-only dev storage to DB-backed persistence while keeping scheduler ownership narrow.

## Current Value

- Scheduler could already register, dispatch, and persist triggers to file.
- Trigger state was still process/file-scoped rather than system-backed.

## Remaining Gap

- No DB persistence for low-risk trigger state
- No repository/ORM layer for scheduler-owned trigger rows

## Immediate Action

- Add scheduler ORM and repository
- Add `save_to_repository()` and `load_from_repository()`
- Keep file persistence as dev fallback

## Wrong Placement To Avoid

- Do not put scheduler persistence into orchestration
- Do not let scheduler own business semantics
- Do not add scheduler API/UI in this module

## Required Test Pack

- `python -m compileall infra/scheduler state/db/bootstrap.py`
- `pytest -q tests/unit/test_scheduler.py tests/integration/test_scheduler_persistence.py`

## Done Criteria

- Scheduler triggers can persist and reload from DB
- Low-risk triggers remain capability-facing only
- File persistence still works as fallback

## Next Unlock

Scheduler backend refinement beyond low-risk persisted triggers

## Not Doing

- No cron UI
- No job queue
- No scheduler-owned truth mutation
