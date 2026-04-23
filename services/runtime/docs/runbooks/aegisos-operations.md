# AegisOS Operations

Current operational checks:

- Confirm `/api/v1/health` returns monitoring snapshot and history summary.
- Confirm `/api/v1/health/history` returns blocked-run and scheduler summaries.
- Confirm workflow failure counts and blocked counts remain honest.
- Treat monitoring history as operational signal, not business truth.
- If `PFIOS_SENTRY_DSN` is configured, confirm new runtime exceptions appear in Sentry before declaring an incident resolved.
- If `PFIOS_OTEL_EXPORTER_OTLP_ENDPOINT` is configured, confirm HTTP request, analyze workflow, scheduler dispatch, and health snapshot spans are arriving in the external backend.
- Use the external observability sink for alerting, and the built-in `/health` and `/health/history` surfaces for operator confirmation.
