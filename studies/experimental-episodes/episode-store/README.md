# Experimental Episode PostgreSQL Store R1

Canonical source owner: `studies/experimental-episodes/episode-store/`. This is a Study analytical projection consumer, not a Next-stage service. The relocation changes no Python distribution name, Alembic schema, source semantics, or PostgreSQL authority. Earlier source coordinates are historical evidence rather than supported imports or installed paths.

Status: **task-local analytical consumer / not deployed owner truth**

This consumer exists only because Experimental Episode R1 survived two materially different pressure tests: historical Runtime R5C and Harness RSI evidence.

## Owner boundary

PostgreSQL stores a rebuildable analytical projection. It does not replace Runtime, Harness, Host, Git, Artifact, domain, or evaluation truth.

Workstation continues to own PostgreSQL deployment/backup substrate. This directory owns only the consumer schema, migrations, ingest semantics, and analytical-store acceptance.

There is no long-lived service in R1.

## Projection-version law

The primary identity is `(episode_id, projection_digest)`.

A later enrichment of the same Episode creates another projection version. It never silently overwrites an earlier projection and does not assert which projection is owner-current.

## R1 tables

- `episode_projections`
- `episode_owner_refs`
- `episode_evidence_bindings`
- `episode_dimensions`
- `episode_measures`
- `projection_ingests`

No raw owner payload, prompt, workspace snapshot, execution plan, event payload, artifact bytes, credential, or secret column exists.

## Migration law

Alembic is the sole schema authority. The ingest program never creates or migrates schema.

## Ingest law

An ingest is bound to exact corpus ID, profile ID, source file SHA-256, projection-set digest, Episode schema digest, and adapter digest.

The deterministic ingest ID makes replay idempotent. Replaying an accepted ingest returns the retained receipt instead of writing a second ingest or mutating owner truth.

## Human: committed source files and reproducible read-back

Use the existing producer-owned JSONL stream and the Episode-owned Alembic
schema. The original ingest used two pathname opens (parse first, re-open
for SHA-256), which could bind different file versions. Current ingest freezes
the input into one private anonymous temporary-file snapshot while computing
its SHA-256; **both parsing and committed ingest identity use those exact
bytes**. No permanent file store or second object registry is created.

For an already migrated Episode PostgreSQL database, with an explicit DSN
and genuine corpus/projection/schema/adapter digests:

```sh
uv run ordivon-episode-store ingest /absolute/path/source.jsonl   --corpus-id YOUR_CORPUS --profile-id YOUR_PROFILE   --projection-set-digest sha256:... --schema-digest sha256:...   --adapter-digest sha256:...
uv run ordivon-episode-store readback /absolute/path/source.jsonl   --ingest-id ingest:sha256:...
```

These digests and paths are **input placeholders**, not ready-to-run evidence.
Retain the exact returned ingest ID. Readback is read-only: it checks the
committed `projection_ingests` identity, current input SHA-256 and Episode
count. It fails if the file is unavailable, altered, uncommitted or the
database receipt is contradictory. Independent Artifact
`artifact_core.input_snapshot.stage_verified_input` can freeze that same
SHA-bound file for a downstream native verifier. The DB receipt is not a
filesystem lease, a provider-rights grant, a Parquet validation or proof
of cross-store atomic commit.

## Agent: atomic source/PG admission and negative acceptance

The natural producer here is Experimental Episode, PostgreSQL owns receipt
durability, Artifact owns verified byte snapshots, Data owns discovery
semantics. Do not import another Owner's implementation modules into this
ingest package; compose their independently callable contracts.

- Create the schema only with Alembic. PG ingest runs inside one transaction;
  it never auto-migrates.
- Identical concurrent ingestion is resolved through PostgreSQL's unique
  `ingest_id` index and `ON CONFLICT ... DO NOTHING RETURNING`. One writer
  commits; the other checks the now-committed receipt and returns a replay
  result with zero new projections. No ad hoc process lock.
- Readback uses an explicitly supplied ingest ID and input path, a
  `REPEATABLE READ READ ONLY` PostgreSQL transaction and a fresh exact
  file-byte observation. Do not infer absent paths, input-rights, true source
  publication times, or owner-current version from successful readback.
- For native real PG verification, create a disposable PostgreSQL instance,
  database named `ordivon_episode_test`, apply
  `uv run alembic upgrade head`, then set
  `ORDIVON_EPISODE_PG_TEST_DSN` to that isolated instance and run
  `mise run verify`. Absence of the test DSN is SKIP, not a real DB PASS.
  These tests intentionally terminate their **own test writer backend** and
  tamper with their own test ingest rows. Never point this environment
  variable at production.
- Retain negative witnesses for swapped files, source/receipt digest conflict,
  identity tamper, uncommitted invisibility, interrupted transactions and
  competing same-ingest writers. Do not infer physical file GC safety from
  PostgreSQL MVCC alone.

This is one instance-level PG+byte contract and still requires upstream
Artifact/retention authority for durable file leases and actual old-version
reclamation. It does not automatically implement Iceberg/Delta semantics or
the abstract Lean `DataMultiVersion` state machine.

## Historical R5C projection adapter

The existing native Study distribution owns the deterministic R5C-to-Episode projection and backfill CLI as ordivon-episode-r5c-backfill. Its read-only PostgreSQL source query is sql/runtime_r5c_export.sql; this does not assign Runtime database authority to the Study. The CLI and tests import existing Composition-owned schema/digest contracts rather than keeping an executable Next adapter or path alias.
