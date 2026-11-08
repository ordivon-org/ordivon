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
committed `projection_ingests` identity, current input SHA-256, Episode
count **and every matching row in the five existing PG projection tables**.
It fails if the file is unavailable, altered, uncommitted, or if any stored
projection row is missing, unexpected, or differs from the frozen source.
The native implementation uses parameterized, bounded 256-key batches
inside one PG reader snapshot; no new schema or per-Episode N+1 query loop. Independent Artifact
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
  commits; the other checks the now-committed receipt **and its matching
  projection rows** and returns a replay result with zero new projections.
  The producer verifies the five native projection tables before writing
  a new successful ingest receipt, so an already-occupied projection identity
  with incompatible content aborts the entire attempt. No ad hoc process lock.
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
  identity tamper, missing/extra/modified projections in all five PG tables,
  stable read snapshots, bounded 513-row batch verification, uncommitted
  invisibility, interrupted transactions and competing same-ingest writers. Do not infer physical file GC safety from
  PostgreSQL MVCC alone.

This is one instance-level PG+byte contract and still requires upstream
Artifact/retention authority for durable file leases and actual old-version
reclamation. It does not automatically implement Iceberg/Delta semantics or
the abstract Lean `DataMultiVersion` state machine.

## Recovering an exact Episode source from a native AIP (read-only consumer)

The input byte-to-PG chain alone does not establish long-term availability.
An Archivematica AIP has **provider-owned** identity and location, which
must not be inferred from Episode's content-addressed `ingestId`. The
source-side composition uses exactly these independently grounded inputs:

1. An AIP **retrieved from Archivematica Storage Service** using its native
   `GET /api/v2/file/<UUID>/download/` endpoint, with its complete package
   SHA-256 established separately by a trusted provider receipt.
2. The exact internal original-file entry path in the AIP, not a glob, name
   search, or any claim that the latest archive is the right version.
3. The already committed Episode `ingestId` and an existing PG DSN.
   The Episode consumer checks that the source SHA-256, receipt identity,
   Episode count and **all five native projection tables** agree.

Use the installed upstream **7-Zip** binary, Episode's existing single-FD
`_frozen_source` and `read_committed_ingest_source` directly, rather than
reimplementing BagIt, METS, 7z, an AIP server or a preservation lease:

```sh
uv run python -m ordivon_experimental_episode_store.aip_readback   --archive /explicitly-downloaded/provider-aip.7z   --aip-uuid 00000000-0000-4000-8000-000000000001   --package-sha256 sha256:EXACT_PACKAGE_SHA256_FROM_PROVIDER_RECEIPT   --entry 'transfer-name-00000000-0000-4000-8000-000000000001/data/objects/data/episode-source.jsonl'   --ingest-id ingest:sha256:EXACT_EPISODE_INGEST_ID   --dsn 'EXPLICIT_EPISODE_POSTGRES_DSN'
```

These are **placeholders**, not current accepted AIP identity. The command
fails closed on missing/ambiguous/unsafe paths, symlinked or changed
package files, mismatched package SHA, excessive original-file size,
upstream 7z failures, missing PG receipt or mismatched stored projections.
The archive is temporarily frozen under an open file descriptor and 7z
consumes that very descriptor through `/proc/self/fd`, so a subsequent
pathname replacement cannot redirect extraction. The extracted original
is in a private temporary directory removed after readback. Source entries
are bounded to 64 MiB and complete packages to 512 MiB.

A PASS here asserts **the explicitly supplied archive bytes** and the
committed Episode DB state agree. The returned
`providerStorageStanding=UNKNOWN_NOT_OBSERVED` is deliberate: this CLI
does not authenticate Storage Service, confirm the AIP is still uploaded,
prove its METS/PREMIS completeness, or establish retention/replica/fixity
status. `retentionOrGcAuthorized=false` always. Check provider-native
Fixity/restore operations independently before allowing any data retirement.

### 2026-11-08 qualification and open provider boundary

- A **genuine provider-downloaded R6 Creative AIP**
  (`1593a748-703b-46b6-8114-314040f44bd8`) independently matched
  historical archive SHA-256
  `e08f0197821c05684cfc50b3dc6119801de6f9137dfeef1df5a43cc8a42ffbda`.
  The native frozen-descriptor 7z reader restored an exact 56-byte original
  `.gitignore` entry (SHA-256
  `4afb118f793fdfeeadab4520876d4c089b75c2f379d38993e2ea0b6d769f87fa`).
  This proves **native provider AIP recovery compatibility only**; that
  Creative AIP is **not** an Episode ingest.
- A separate **three-Episode synthetic acceptance source** was fully
  ingested/read back from a temporary PostgreSQL 18.6 database. Its source
  SHA-256 is
  `sha256:0153dfc684ac32b9c49b1dd7208e228fe1b092423eb4860b50876cbf891c84e7`;
  deterministic ingest identity is
  `ingest:sha256:449c42a9e51eaa7cb9fc972b07ce9330cb2afd111c6afb1ad392aa055d6db98a`.
  Original file size is 1,998 bytes. The exact source and **test-only**
  PostgreSQL readback receipt were put under the existing provider transfer
  source `/home/ordivon-episode-preservation-qualification-20261108-r1`.
  Its native installed `bagit.py` emitted a **valid BagIt 0.97** bag, not
  RFC 8493 BagIt 1.0; no format-version claim was silently upgraded.
  Submission through the Dashboard authenticated API was not admitted by
  the current execution environment. **No Episode AIP UUID, stored AIP
  receipt or provider-level Episode fixity exists from this attempt**.
  The test PostgreSQL database was disposable, not permanent owner truth.
- Synthetic 7z fixtures exercise native extraction, actual PostgreSQL
  re-ingest/consumer readback, same-path archive replacement, checksum
  mismatch, missing originals and stored projection tampering. They do not
  substitute for the missing native Episode AIP deposit/restore receipt.

This precise gap is **an archived synthetic Episode source with an
authoritative provider AIP identity and restored bytes**; it is not a reason
to create a new Ordivon archive index, shared lease registry or GC service.

## Historical R5C projection adapter

The existing native Study distribution owns the deterministic R5C-to-Episode projection and backfill CLI as ordivon-episode-r5c-backfill. Its read-only PostgreSQL source query is sql/runtime_r5c_export.sql; this does not assign Runtime database authority to the Study. The CLI and tests import existing Composition-owned schema/digest contracts rather than keeping an executable Next adapter or path alias.
