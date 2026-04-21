# Execution Adapters

`execution/adapters/` contains family-level execution facades.

## Current Families

- recommendation
- review
- validation

## Read These Files First

- `recommendations.py`
  - `generate(...)`
  - `update_status(...)`
- `reviews.py`
  - `submit(...)`
  - `complete(...)`
- `validation.py`
  - `report_issue(...)`

## What These Adapters Own

- request/receipt lifecycle orchestration
- family-level success/failure semantics
- audit ref attachment
- family-level single-owner success audit discipline where implemented

## What These Adapters Do Not Own

- domain truth rules
- governance policy
- API transport schemas

## Why This Directory Matters

This is where PFIOS stops treating consequential actions as plain service calls and starts treating them as execution families with:

- `ExecutionRequest`
- `ExecutionReceipt`
- failure paths
- stable audit refs

## Current Pattern

For a family-backed action:

1. validate/require action context
2. create execution request
3. call domain truth operation
4. create success or failed receipt
5. attach refs to audit payload and return payload

That pattern is now real for recommendation, review, and validation families.
