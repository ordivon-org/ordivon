# Rust Harness PG v1 reader

Experimental read-only consumer of the existing Python Harness PostgreSQL
schema v1. It owns no write transaction, lease acquisition, migration or new
database. It observes Contract/CAS/Journal in one REPEATABLE READ, READ ONLY
transaction and reconstructs Run revision/status/terminal boundary, preserves
UNKNOWN event kinds, causation and CAS references.

Verified Provider reference Port (B consumer proposal, pending A Owner acceptance):
the existing run_object_refs query already decodes and SHA256-checks EVERY
referenced CAS document in one read-only PG transaction. The same method now
returns only the Provider record kind's CanonicalDocument through private
VerifiedProviderReference accessors, plus digest/kind metadata for all verified
reference edges. Other CAS contents (Run State, Request, Result, Failure)
remain hidden from the B Consumer. No additional SQL query/Store/transaction,
lease, mutation, dispatch authority, or extra parser is introduced. B must
independently check the Provider Event→record digest, run/model/status and the
exact attachment-edge set before interpreting a recorded Provider head.
A valid readback is a historical snapshot, never current execution standing.

Production entrypoints and PG writers are NOT switched over.

Verification:
1. mise run rust:verify compiles and tests the Rust sources without a running
   database. PG integration fixture explicitly skips when no isolated PG test
   environment was bound.
2. On an isolated Linux PG18 test host, execute:
   bash services/harness/crates/harness-pg/tests/run_isolated_pg18.sh
   This boots a private Unix-socket-only cluster, creates 4 Runs using
   the Python PostgresHarnessStore, tests Rust readback and three independent
   corruptions, checks Rust DB role SELECT-only, and stops/removes the
   private cluster via a trap.

Known remaining gates: independent C verification, full legacy Run/Privacy/
Effect compatibility, multi-writer/lease, long-Run resume, B Loop integration,
release/deployment, TLS/native transport parity (current test uses NoTls).
This reader is not the full Python Store replacement.

Old objects exceeding this reader's frozen nesting/integer-digit limits
return UnsupportedLegacyRepresentation, not a false CAS corruption claim.
Consumers must qualify or version those legacy Runs before Rust takeover.
