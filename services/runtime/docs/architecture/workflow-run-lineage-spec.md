# Workflow Run Lineage Spec

## Status

This document records the first workflow-level run lineage implementation in PFIOS as of `2026-04-19`.

## Current Scope

The current live workflow run object is:

- `WorkflowRun`

It is now attached to the `analyze` workflow and persists:

- `workflow_run_id`
- `workflow_name`
- `status`
- `request_summary`
- `step_statuses`
- `failed_step`
- `failure_reason`
- lineage refs for query / symbol / timeframe
- linked object ids when available

## Current Analyze Coverage

The analyze workflow now:

1. creates a pending workflow run before step execution
2. records each step as `completed` or `failed`
3. persists a completed run on success
4. rolls back partial business writes on failure
5. persists a failed workflow run with `failed_step` and `failure_reason`

## Exposed Lineage

`workflow_run_id` is now visible through:

- analyze API response metadata
- analysis metadata
- `analysis_completed` audit payload
- `recommendation_generated` audit payload
- `analysis_report_written` audit payload
- markdown report content

## Failure Discipline

If a workflow step fails:

- previous uncommitted business writes are rolled back
- the workflow run is persisted separately as `failed`
- the failed step and reason remain queryable

## Next Gaps

- step timing is stored, but not yet surfaced through API
- review workflow and other workflows do not yet use `WorkflowRun`
- workflow run state is not yet connected to a broader trace graph
