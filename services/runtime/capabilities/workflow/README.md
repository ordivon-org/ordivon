# Workflow Capabilities

`capabilities/workflow/` exposes user-visible actions that coordinate multiple layers but still return product-facing contracts.

## Current Modules

- `analyze.py`
- `reviews.py`

## Read These First

- `analyze.py`
  - wraps the analyze workflow/orchestrator path
  - normalizes governance payload, workflow refs, execution refs, and intelligence feedback signals into a capability result
- `reviews.py`
  - wraps review submit/complete flows
  - exposes pending review list and review detail view contracts
  - bridges to review execution adapter paths

## Role In The Stack

Workflow capabilities sit between:

- Experience/API entrypoints
- deeper orchestration/domain/execution work

They are where user-visible workflow semantics become stable payloads.

## What They Own

- product-facing workflow contracts
- action-context enforcement at capability entry
- shaping rich metadata into stable user-visible fields

## What They Do Not Own

- persistence truth
- raw state transitions
- execution request/receipt storage
- policy source definitions

## Current Main Paths

### Analyze

`API -> AnalyzeCapability -> PFIOSOrchestrator -> analyze workflow -> result contract`

### Reviews

`API -> ReviewCapability -> ReviewExecutionAdapter / ReviewService -> result contract`

## Rules

- workflow capabilities may call orchestrators and services
- they should return stable capability contracts
- they do not own persistence truth directly
- they should preserve honest missing/unavailable semantics from deeper layers
