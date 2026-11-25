# Runtime relational evidence ownership R1 — qualified proposal

Status: native PostgreSQL 18 proof and test candidate; **not installed or authorized for production**.
This refines the existing cross-core evidence and retirement Spec. It introduces
no new service, registry, cache, authority, or execution path.

## Contract

A Job owns Attempts, and an Attempt-scoped Artifact or Event must reference
that same Job. An Event with NULL attempt_id remains a Job-level Event.
Existing separate foreign keys prove existence, not pair consistency.
The proposed native representation is a unique B-tree on
attempts(job_id, attempt_id) and two MATCH SIMPLE composite foreign keys,
retaining existing constraints until a separate dependency and workload audit.

Input: exact qualified Runtime schema, source, physical epoch, schema shape,
operator maintenance standing, and existing relational rows.
Output: native enforced and validated owner-pair constraints, or a precise
inconclusive/conflicting state; not a claim of Artifact content integrity.
Invariant: valid writes remain possible; no cross-owner pair can be newly
committed; a NULL Event Attempt remains legal; no historical row is silently
rewritten, deleted, relabeled, or reparented.
Effect: additive native constraints and a derived index only.
Cost: native unique-index build and FK validation, with an additional write
check and index maintenance; actual production lock/WAL/latency unmeasured.
Provenance: PostgreSQL catalog, exact source and physical epoch, native
SQLSTATE 23503 and constraint identity, native positive/negative tests.
Residual: corruption outside constraints, file/manifest identity, historical
restores, old-client behavior, FK-trigger disablement, and concurrency remain
separate proof obligations.

## Target capability and expansion sequence

1. Recover the installed Runtime source/schema/epoch from the actual normal
   entry point. Establish the existing operator-owned maintenance fence across
   concurrent DDL/cutover; require rollback/recovery standing. Check catalog
   identity and existing invalid objects. Use bounded operator timeouts.
2. Take a read-only repeatable-read census of both relations and all parent
   identities. Unknown is not zero. Existing wrong associations are evidence
   for review, not automatic repair.
3. Use the following native DDL shape as the proposed expansion, **not a
   standalone runbook**. Integrate into the existing qualified operator path,
   with exact catalog pre/postflight and resumable stages, before installation.

    CREATE UNIQUE INDEX CONCURRENTLY idx_attempts_owner_pair
      ON attempts(job_id, attempt_id);
    ALTER TABLE artifacts ADD CONSTRAINT artifact_owner_pair_fk
      FOREIGN KEY(job_id, attempt_id) REFERENCES attempts(job_id, attempt_id)
      MATCH SIMPLE NOT VALID;
    ALTER TABLE job_events ADD CONSTRAINT event_owner_pair_fk
      FOREIGN KEY(job_id, attempt_id) REFERENCES attempts(job_id, attempt_id)
      MATCH SIMPLE NOT VALID;
    ALTER TABLE artifacts VALIDATE CONSTRAINT artifact_owner_pair_fk;
    ALTER TABLE job_events VALIDATE CONSTRAINT event_owner_pair_fk;

4. Check native index identity, validity/readiness/liveness, uniqueness,
   column order, operator classes, and no extra predicate/expression. Check
   constraint ownership, both column mappings, MATCH SIMPLE, NO ACTION,
   enforcement, validation, and dependencies. A matching name alone is not
   acceptance. A NOT VALID constraint is a distinct state: new writes are
   checked, but historical data is not certified.
5. For incompatible history, failed validation, cancellation, lock timeout
   or lost response, report native standing. Do not auto-drop, rewrite or
   claim rollback. A retry requires exact catalog readback and qualification.
   Independently verify valid ordinary admission, terminal, cancel, Artifact
   and Event writes, nullable Job-level Event, wrong pair rejection, and
   readback / wire contract on both Linux and Windows consumers.
6. Measure native write amplification, parent update/delete costs, index
   space and concurrent workload tail before removing redundant individual
   FKs or any readback integrity check. Do not remove the existing Job FK
   on nullable Events (MATCH SIMPLE skips the composite check for NULL).
   Keep all historical and immutable-content readback safeguards.
7. Rollback requires explicit operator approval, correct identities,
   dependency checks, and appropriate recovery qualification. Drop only
   the exact new constraints before the exact derived index, if qualified.
   No archival or data deletion is implied.

## Verification

The private PG test pg18_native_owner_pair_expand_validate_contract
uses the existing Scratch native fixture. It demonstrates old-schema
acceptance of a false pair, new-write rejection under NOT VALID, failure of
historical validation, preservation of bad fixture rows, successful
validation after removing only intentionally injected private rows, legal
NULL Attempt Event, UPDATE and parent-rebind rejection, and existing
admission under the new contract. Exact SQLSTATE and named constraint are
checked, not generic failure. It does not install new production DDL or
qualify a full migration/restore.

Separate scale experiment: 54,581 synthetic Attempts, 271,842 Artifacts,
408,314 Events. Native unique index 2,236,416 bytes; one observed build
42.279 ms, validations 54.309/77.154 ms. No production latency or throughput
claim; identifiers and workload are synthetic. See Host R16 evidence.

References:
- https://www.postgresql.org/docs/18/ddl-constraints.html
- https://www.postgresql.org/docs/18/sql-altertable.html
- https://www.postgresql.org/docs/18/sql-createindex.html
- https://www.postgresql.org/docs/18/transaction-iso.html
