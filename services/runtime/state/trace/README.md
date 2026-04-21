# State Trace

`state/trace/` owns main-chain query bundles and trace resolution rules.

## Current Focus

- workflow trace
- recommendation trace
- review trace
- honest `present / missing / unlinked` relation semantics

## Read These Files First

- `models.py`
  - `TraceReference`
  - `TraceBundle`
- `service.py`
  - trace root entrypoints
  - relation hardening logic
  - direct-ref vs audit/metadata fallback behavior

## Active Trace Roots

- `trace_workflow_run(workflow_run_id)`
- `trace_recommendation(recommendation_id)`
- `trace_review(review_id)`

## Current Design Rule

Trace prefers:

1. direct persisted refs
2. queryable object lookups
3. audit/metadata fallback

And only then returns:

- `present`
- `missing`
- `unlinked`

## Boundary

Trace resolves relations.
It does not create new business truth.
