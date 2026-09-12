# Temporal blue retirement

Date: 2026-09-12

## Standing

**BLUE DEV TEMPORAL RETIRED; PRODUCTION POSTGRESQL TEMPORAL IS THE ONLY LIVE TEMPORAL CLUSTER.**

The historical Agent Automation dev cluster on `127.0.0.1:7233` has completed its drain and retirement. It has no listener and its old systemd service is absent. New and continuing admitted Agent Automation work uses the Operations-managed PostgreSQL-backed Temporal cluster on `127.0.0.1:17233`.

The retirement did not fabricate or import Event History into the production cluster. The old SQLite state was archived in place under `/var/lib/ordivon-temporal-agent/archive/`.

Retirement receipt evidence records:

- running Agent Automation Workflows at shutdown: `0`;
- source database integrity: `ok`;
- exact archive: read-only;
- SQLite backup: integrity `ok`, read-only;
- source database bytes: `11,522,048`;
- source SHA-256: `sha256:ebc3553d713b8cc016e20b1b5781a9d02ac56ed3b2c1eac3b5437d06827ca2c9`.

The current-state manifest must therefore describe blue as **archived/retired**, not draining. Earlier green-acceptance documents remain historical records of the gates that existed before cutover.
