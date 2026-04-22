# Runtime Unhealthy

Use when Hermes runtime health is degraded or unavailable.

- Check `/api/v1/health` for `hermes_status` and monitoring summary.
- Check `/api/v1/health/history` for blocked-run or scheduler side effects during degraded runtime windows.
- Expect degraded or fallback analyze behavior, not silent success.
- Do not treat runtime fallback as trusted model output.
