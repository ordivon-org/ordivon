# Rust Harness PostgreSQL v1 readback and experimental native lease

Experimental port of the existing Python Harness PostgreSQL schema v1.
The read_run_readonly API remains SELECT-only and observes Contract/CAS/Journal
in one REPEATABLE READ, READ ONLY transaction. It reconstructs Run
revision/status/terminal boundaries and preserves UNKNOWN events,
causation and CAS references.

The separate lease module contributes only two native PG v1 operations:
acquire_run_lease and release_run_lease. They use the same
runs -> run_leases row lock order, existing tables, expected Run revision,
lease generation, exact expiry and full-tuple release as the Python Store.
They introduce neither an ORM/registry nor any new schema, event writer
or dispatch authority. A caller must supply a provisioned PG writer role;
the test-only SELECT user is denied by PostgreSQL SQLSTATE 42501.
This is a contribution candidate to the single A-owned PG Store,
not a competing published Harness Writer/Run executor.

Production entrypoints and PG writers are NOT switched over.

Verification:
1. mise run rust:verify compiles and tests the Rust sources without a running
   database. PG integration fixture explicitly skips when no isolated PG test
   environment was bound.
2. On an isolated Linux PG18 test host, execute:
   bash services/harness/crates/harness-pg/tests/run_isolated_pg18.sh
   This boots a private Unix-socket-only cluster with real Python
   PostgresHarnessStore-created Runs, checks Rust readback, CAS/edge/revision
   corruption, a legitimate legacy parser-UNKNOWN case and SELECT-only
   DB role, then stops/removes the private cluster via a trap.
3. To test the native lease contribution in the same disposable DB:
   HARNESS_PG_NATIVE_LEASE=1 bash services/harness/crates/harness-pg/tests/run_isolated_pg18.sh
   Test flow: Python Store creates six live Run fixtures and a source
   lease, Python Journal moves one Run to revision 2 -> Rust acquires,
   idempotently re-observes, replaces an expired lease, refuses a foreign
   owner, rejects stale revision and terminal Runs, and races two actual
   PostgreSQL connections under FOR UPDATE. SELECT-only acquire and
   release both fail with SQLSTATE 42501. Rust then writes a live lease;
   Python consumes that exact lease with its real atomic append_events
   transaction; Rust finally replays the new Journal revision 2 and
   checks the prior lease is gone. No Tool/Provider effect is sent.

Known remaining gates: A-owned native transactional append_events
writer and durable Tool/Provider Intent and Fence, independent C-seat
qualification, full legacy Run/Privacy/Effect compatibility, long-Run
resume, B Loop integration, production release/deployment, TLS/native
transport parity (tests use local Unix socket + NoTls). Existing leases
alone are NOT permission to dispatch or evidence of physical completion.
A read-only RunSnapshot is NOT a live lease. Rust does not yet replace
the full Python Harness Store.

Old objects exceeding this reader's frozen nesting/integer-digit limits
return UnsupportedLegacyRepresentation, not a false CAS corruption claim.
Consumers must qualify or version those legacy Runs before Rust takeover.
