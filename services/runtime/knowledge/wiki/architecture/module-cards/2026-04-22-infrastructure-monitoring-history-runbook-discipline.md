# Module

Infrastructure Monitoring History / Runbook Discipline

## Layer

Infrastructure

## Type

Core infrastructure

## Role

Extend current health monitoring into a minimal history summary and attach real runbooks to currently-supported failure paths.

## Current Value

- `/api/v1/health` already exposed current monitoring snapshot fields.
- Monitoring had no history summary and runbooks were still weak.

## Remaining Gap

- No history metrics for blocked or failed flows.
- No runbooks for current real operational failure modes.

## Immediate Action

- Add monitoring history summary models/helpers
- Extend `/api/v1/health` with minimal history counts
- Add runbooks for blocked review, runtime unhealthy, and trace inconsistency

## Wrong Placement To Avoid

- Do not replace the existing monitoring snapshot
- Do not create a new operations UI in this module
- Do not turn monitoring history into business truth

## Required Test Pack

- `python -m compileall infra/monitoring apps/api/app/api/v1/health.py`
- `pytest -q tests/unit/test_monitoring.py tests/unit/test_health.py tests/integration/test_health_monitoring_api.py`

## Done Criteria

- Monitoring history summary exists
- `/api/v1/health` returns minimal history fields
- Runbooks exist and refer only to current real components

## Next Unlock

Experience Global Trust-tier Rollout

## Not Doing

- No ops dashboard
- No speculative runbook content
- No new truth objects
