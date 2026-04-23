# Monitoring Signals

## Purpose

This runbook documents the operational signals exposed through `/api/v1/health`
and `/api/v1/health/history`. These signals are operational summaries, not
business truth.

## Current Signal Groups

- runtime status and active runtime metadata
- workflow failure counts by failed step
- execution failure counts by action family
- blocked run counts and blocked reason counts
- recovery action counts gathered from workflow step statuses
- approval-blocked run counts
- scheduler trigger counts and dispatch activity

## Operational Reading Rules

- Treat blocked or stale run counts as operational attention signals, not as
  business outcomes.
- Treat recovery-action counts as workflow-recovery visibility, not proof that a
  recommendation or review succeeded.
- Use blocked reason counts to route incident response and runbook selection.
- Use scheduler trigger counts to validate trigger registration and dispatch
  health, not to infer product completion.
