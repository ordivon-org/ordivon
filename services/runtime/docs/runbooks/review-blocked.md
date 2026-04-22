# Review Blocked

Use when `review_complete` is blocked by approval or workflow handoff.

- Check `/api/v1/health/history` for blocked-run refs and approval-blocked refs.
- Inspect review detail and trace refs.
- Confirm `blocked_reason` or `handoff_artifact_ref` on the related workflow run.
- Do not mark the review completed without a valid approval path.
