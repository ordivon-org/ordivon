# Module

Infrastructure Scheduler

## Layer

Infrastructure

## Type

Core infrastructure

## Role

Add a low-risk scheduler that decides when to invoke capability/orchestrator entrypoints without owning business meaning.

## Current Value

- Monitoring and orchestrator runtime already exist.
- There was scheduler documentation but no minimal scheduler service contract in `infra/`.

## Remaining Gap

- No low-risk scheduled trigger object existed.
- Trigger registration and dispatch were not formalized as infrastructure-owned behavior.

## Immediate Action

- Add `infra/scheduler/`
- Define `ScheduledTrigger`
- Add `SchedulerService`
- Keep the first trigger low-risk and capability-facing

## Wrong Placement To Avoid

- Do not put scheduler logic into `orchestrator/workflows/analyze.py`
- Do not let scheduler own business semantics
- Do not let scheduler mutate truth directly

## Required Test Pack

- `python -m compileall infra/scheduler`
- `pytest -q tests/unit/test_scheduler.py tests/unit/test_monitoring.py`

## Done Criteria

- `infra/scheduler/` exists
- `ScheduledTrigger` exists
- `SchedulerService` registers and dispatches triggers
- Dispatch stays capability/orchestrator-facing and low-risk

## Next Unlock

Infrastructure Monitoring History / Runbook Discipline

## Not Doing

- No cron UI
- No scheduler-driven business mutation
- No wake/resume ownership inside scheduler
