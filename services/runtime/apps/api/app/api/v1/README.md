# API v1

`apps/api/app/api/v1/` is the active public HTTP surface for the current single-agent PFIOS baseline.

## What Lives Here

- request entrypoints
- route-to-capability wiring
- honest transport-level error handling
- HTTP exposure of trace, review, recommendation, dashboard, and health surfaces

## Key Files To Read First

- `router.py`
  - mounts the full v1 route tree
- `analyze.py`
  - main analyze-and-suggest entrypoint
- `reviews.py`
  - review submit, complete, pending list, and review detail
- `recommendations.py`
  - recommendation list and status mutation surface
- `traces.py`
  - workflow/recommendation/review trace exposure
- `health.py`
  - runtime health plus monitoring snapshot
- `dashboard.py`
  - homepage summary surface

## How The Main Path Usually Flows

For a typical user-facing write path:

1. HTTP request enters a route here
2. route validates transport shape with `apps/api/app/schemas/*`
3. route calls a capability or orchestrator-backed entrypoint
4. capability/domain/execution/orchestration layers do the real work
5. route returns a transport-safe response with honest missing/unavailable semantics

## Current Coverage

- `health`
- `analyze`
- `recommendations`
- `reviews`
- `traces`
- `audits`
- `reports`
- `validation`
- `dashboard`
- `agent_actions`

## Important Rules

- response shapes must reflect real objects and honest missing states
- routes should stay thin
- routes should not invent business semantics
- routes should not bypass capability/domain/orchestration boundaries without a documented reason
- routes must not overstate outcome, knowledge hint, or trace completeness
