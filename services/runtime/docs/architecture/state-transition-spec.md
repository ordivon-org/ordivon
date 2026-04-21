# State Transition Spec

## Status

This document records the explicit transition rules currently enforced in PFIOS as of `2026-04-19`.

## Covered Objects

### Recommendation

Recommendation transitions are enforced through `RecommendationStateMachine`.

Key live path:

- `generated -> adopted`
- `adopted -> tracking`
- `tracking -> satisfied|failed|expired|superseded`
- `satisfied|failed|expired -> review_pending`
- `review_pending -> reviewed`
- `reviewed|superseded -> archived`

### Review

Review transitions are now enforced through `ReviewStateMachine`.

Current rules:

- `pending -> generated|in_progress|completed|cancelled`
- `generated -> in_progress|completed|cancelled`
- `in_progress -> completed|cancelled`
- `completed` and `cancelled` are terminal

### Intelligence Run

Intelligence run transitions are now enforced through `IntelligenceRunStateMachine`.

Current rules:

- `pending -> completed|failed`
- `completed` and `failed` are terminal

## Live Main-Chain Coverage

- analyze workflow:
  - intelligence run: `pending -> completed` or `pending -> failed`
- review workflow/service:
  - review: `pending -> completed`
- recommendation lifecycle:
  - explicit transitions continue to flow through `RecommendationService.transition`

## Remaining Gaps

- `WorkflowRun` is not yet a first-class state object, so workflow-level state transitions are still missing.
- `OutcomeSnapshot` is not yet connected to a broader recommendation outcome state machine.
- execution request / receipt lifecycle is still minimal and not yet part of this spec.
