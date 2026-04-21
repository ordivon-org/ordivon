# Execution Request / Receipt Spec

## Status

This document records the first live execution request / receipt path in PFIOS as of `2026-04-19`.

It complements:

- [Execution Action Catalog](./execution-action-catalog.md)
- [Architecture Baseline](./architecture-baseline.md)

## Current Scope

The first implemented request / receipt family is:

- `analysis_report_write`

This family covers the consequential report write performed in `WriteWikiStep` during the analyze workflow.

## Request Model

Execution requests now capture:

- `action_id`
- `family`
- `side_effect_level`
- `status`
- `actor`
- `context`
- `reason`
- `idempotency_key`
- `entity_type`
- `entity_id`
- `analysis_id`
- `recommendation_id`
- `payload`

## Receipt Model

Execution receipts now capture:

- `request_id`
- `action_id`
- `status`
- `result_ref`
- `external_reference`
- `detail`
- `error`

## Live Analyze Path

The current analyze workflow now does the following for `analysis_report_write`:

1. Build an `ExecutionRequest` before writing the markdown report.
2. Write the markdown document.
3. Persist analysis metadata and audit lineage.
4. Persist an `ExecutionReceipt`.
5. Expose `execution_request_id` and `execution_receipt_id` through:
   - analysis metadata
   - `analysis_report_written` audit payload
   - analyze API response metadata

## Failure Behavior

If report writing or post-write metadata persistence fails:

- the markdown file is compensated by deletion when appropriate
- the execution request is marked `failed`
- the execution receipt is marked `failed`
- the error is retained in the receipt record

## Next Families

The next best families for request / receipt rollout remain:

1. `analysis_metadata_update`
2. `recommendation_generate`
3. `recommendation_status_update`
4. `review_submit`
5. `review_complete`
6. `validation_issue_report`
7. `intelligence_run_write`
8. `agent_action_write`
