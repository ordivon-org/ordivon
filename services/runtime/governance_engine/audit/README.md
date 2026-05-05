# Governance Audit

`governance/audit/` owns traceability and audit persistence.

This package is for:

- audit event records
- audit repository and retrieval
- JSONL and database-backed audit writing

This package is not for:

- business review content
- recommendation meaning
- product capability formatting

Default rule:

If the object exists so the system can explain or prove what it decided and persisted, it belongs here.
