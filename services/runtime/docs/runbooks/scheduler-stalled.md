# Scheduler Stalled

Use this runbook when low-risk scheduled triggers stop dispatching or remain persisted without progress.

- Check `/api/v1/health`
- Check `/api/v1/health/history`
- Confirm scheduler trigger summary is present
- Confirm blocked workflow runs are not masking a scheduler-owned issue

Recover by:

1. verifying trigger registration at startup
2. inspecting persisted scheduler trigger rows
3. re-enabling or re-registering low-risk triggers if they were disabled

Do not treat scheduler state as business truth.
