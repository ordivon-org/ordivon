# Module

Monitoring Ops History Endpoint

## Layer

Infrastructure

## Type

Core infrastructure

## Role

Expose richer monitoring history through a dedicated operational endpoint and align runbooks to the real runtime/blocked/scheduler state.

## Current Value

- `/api/v1/health` already exposed compact monitoring summary.
- Monitoring history existed, but not as a dedicated operational read surface.

## Remaining Gap

- No history endpoint for blocked runs, approval blocks, and scheduler summary
- Runbooks did not yet point to the richer history surface

## Immediate Action

- Add `GET /api/v1/health/history`
- Expand monitoring history models
- Add scheduler stalled runbook
- Update existing runbooks to reference the history endpoint

## Wrong Placement To Avoid

- Do not turn monitoring into business truth
- Do not add an ops dashboard in this module
- Do not let scheduler history redefine orchestration state

## Required Test Pack

- `python -m compileall infra/monitoring apps/api/app/api/v1/health.py`
- `pytest -q tests/unit/test_monitoring.py tests/unit/test_health.py tests/integration/test_health_monitoring_api.py`

## Done Criteria

- Health history endpoint exposes blocked/failure/scheduler summaries
- Runbooks point to real operational entrypoints
- Compact `/api/v1/health` remains compact

## Next Unlock

Richer ops discipline beyond health-history summaries

## Not Doing

- No new ops UI
- No business-semantic reporting
- No alerting platform
