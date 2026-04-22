# AegisOS Operations

Current operational checks:

- Confirm `/api/v1/health` returns monitoring snapshot and history summary.
- Confirm `/api/v1/health/history` returns blocked-run and scheduler summaries.
- Confirm workflow failure counts and blocked counts remain honest.
- Treat monitoring history as operational signal, not business truth.
