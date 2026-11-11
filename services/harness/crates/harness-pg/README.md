# Rust Harness PostgreSQL v1 readback, native lease and experimental Journal Writer

Experimental port of the existing Python Harness PostgreSQL schema v1.
The read_run_readonly API remains SELECT-only and observes Contract/CAS/Journal
in one REPEATABLE READ, READ ONLY transaction. It reconstructs Run
revision/status/terminal boundaries and preserves UNKNOWN events,
causation and CAS references.

The separate lease module contributes only two native PG v1 operations:
acquire_run_lease and release_run_lease. They use the same
runs -> run_leases row lock order, existing tables, expected Run revision,
lease generation, exact expiry and full-tuple release as the Python Store.
They introduce neither an ORM/registry nor any new schema or dispatch
authority. The separate journal_write module now supplies an experimental
native append_events operation; it is not a replacement for the entire
Python Store or an external-effect authorization. A caller must supply a provisioned PG writer role;
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

4. Full independent Writer+Lease+Contract+legacy-CAS corpus in the same
   disposable PG18 server:
   HARNESS_PG_NATIVE_WRITER=1 HARNESS_PG_NATIVE_LEASE=1 HARNESS_CONSUMER_FALSIFY_CONTRACT=1 bash services/harness/crates/harness-pg/tests/run_isolated_pg18.sh
   The Python Store creates eight source-valid v1 Runs, including a real
   referenced CAS object. Rust atomically validates and appends real
   Event/CAS/Run Revision batches then Python Store validates them and
   accepts exact replay even though the original lease was consumed.
   Source-controlled cases cover batch length 256 accepted/257 rejected;
   completed status, terminal-last, causedBy across Runs, missing CAS
   reference, expired lease, stale revision, duplicate Event ID with altered
   content, partial replay, 2 PostgreSQL clients racing one Run, SELECT-only
   role SQLSTATE 42501, and Python Store/Rust Reader cross-language readback.
   Events marked UNKNOWN are persisted as UNKNOWN, not reduced to false.

The new journal_write.append_events is a single native PostgreSQL transaction:
prepare immutable Canonical CAS, validate references, SELECT runs FOR UPDATE,
check exact old Event batch identities or fail partial replay, check the
RunRevision and the exact owner/generation/expiry of its lease under row lock,
enforce causation/time/terminal state and bounded event count, update Run,
append events and reference edges, and DELETE the exact consumed lease.
All SQL uses the existing Python Store schema v1. This is a candidate for
the sole A-owned Rust Store, not a second independent Store.

The read-only observe_exact_batch operation is specifically for reconnecting
after an uncertain Journal commit. It reuses read_run_readonly and its
REPEATABLE READ snapshot, including versioned Contract and CAS verification;
it compares exact Event ID, revision, payload digest, causation, time, and
referenced CAS digest/kind/length. The same readback projects the verified
referenced CAS content once for downstream B consumers; do not add another
reference parser or store. NotObserved means only that the Event batch was
not observed in the queried Journal snapshot; it says NOTHING about whether
a Provider/Runtime/Tool physical effect happened. A commit socket error is
UNKNOWN until reconciled; no automatic duplicate dispatch.

Known remaining gates: the *A Owner must review and accept this candidate*,
original C-seat independent source qualification, full Python create_run/
put_object/inspect and producer/consumer behavior not yet native, native
Tool/Provider Intent+Fence, Runtime/Provider physical delivery and
Receipt/UNKNOWN reconciliation, restart/recovery, eventual release/deploy,
and TLS/native transport parity (current PG tests use a private Unix socket
+ NoTls). No Tool/Provider physical effect is sent by these tests. A lease,
Journal admission or a read-only RunSnapshot is NOT a physical effect
permission or domain goal success. Rust does not yet replace the full
Python Harness Store.

Old objects exceeding this reader's frozen nesting/integer-digit limits
return UnsupportedLegacyRepresentation, not a false CAS corruption claim.
Consumers must qualify or version those legacy Runs before Rust takeover.
