# Runtime Unhealthy

Use when Hermes runtime health is degraded or unavailable.

- Check `/api/v1/health` for `hermes_status` and monitoring summary.
- Check `/api/v1/health/history` for blocked-run or scheduler side effects during degraded runtime windows.
- Expect degraded or fallback analyze behavior, not silent success.
- Do not treat runtime fallback as trusted model output.
- If `PFIOS_SENTRY_DSN` is configured, confirm new runtime failures are present in Sentry before closing the incident.
- If `PFIOS_OTEL_EXPORTER_OTLP_ENDPOINT` is configured, confirm `workflow.analyze_and_suggest` spans and `scheduler.dispatch` spans are still arriving during the incident window.
