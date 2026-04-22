# Module

Monitoring History Depth / Ops Refinement

## Layer

Infrastructure

## Type

Core infrastructure

## Role

Deepen monitoring history with top-failure summaries and blocked-run references while keeping it operational rather than business truth.

## Current Value

- Monitoring history summary already existed.
- Runbooks already existed for key operational paths.

## Remaining Gap

- Health API did not summarize top failure categories.
- Blocked run refs were not exposed.

## Immediate Action

- Add top workflow/execution failure summaries
- Add blocked run id summary
- Keep runbook discipline grounded in current real modules

## Wrong Placement To Avoid

- Do not turn health into an ops product
- Do not turn monitoring history into state truth
- Do not add speculative runbook content

## Required Test Pack

- `python -m compileall infra/monitoring apps/api/app/api/v1/health.py`
- `pytest -q tests/unit/test_monitoring.py tests/unit/test_health.py tests/integration/test_health_monitoring_api.py`

## Done Criteria

- Health returns deeper history summary fields
- History still remains compact and honest
- Runbook discipline remains aligned with current components

## Next Unlock

Richer operational observability

## Not Doing

- No new ops UI
- No log aggregation
- No speculative failure taxonomy
