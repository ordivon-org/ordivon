# Host v1 Historical Projection R3

Date: 2026-09-13

Standing: **ACCEPTED_BOUNDED**

## Purpose

Host v1 is retired. Its final SQLite backup remains the historical authority boundary. R3 replaces the operational need to keep a PostgreSQL archive schema available for ordinary historical querying with a small, open, rebuildable projection:

```text
retired Host v1 SQLite backup
        │
        ├── historical authority
        │
        ▼
Apache Parquet files
        │
        └── open derived columnar projection
        │
        ▼
DuckDB catalog/views
        │
        └── disposable local query plane
```

PostgreSQL remains a migration-comparison artifact only. It is not required to query the retained history after R3.

## Source authority

Exact source:

`/var/lib/ordivon/retired/host-v1/host-v1-48104ae46bc92c66.sqlite3`

SHA-256:

`70cc55a34f6fdf97609f0593e13227740fb3e887052a629e3b7d8712a9f54e8b`

Bytes: `45,838,336`

SQLite `PRAGMA quick_check`: **ok**.

The source contains the 15 historical Host v1 tables used by the prior PostgreSQL archival projector. PostgreSQL's `migration_receipts` table is deliberately excluded because it is projector metadata, not Host source history.

## Mature projection method

R3 uses the installed DuckDB SQLite scanner to attach the immutable SQLite backup directly. The exporter selects the exact source columns in the same canonical ordering already used by the PostgreSQL migration evidence and writes one Parquet file per source table with Zstandard compression.

The retained DuckDB file contains views over the retained Parquet paths rather than another duplicate copy of all history.

No Python `duckdb`, `pandas`, or `pyarrow` runtime was introduced. The projection uses the installed DuckDB CLI plus Python standard library and the already-installed PostgreSQL client library for comparison evidence.

## Live PostgreSQL comparison

R3 did not trust only the prior receipt. It re-read the live schema:

`ordivon_host_stage_r1.host_retired_final_20260912`

PostgreSQL version: `18.6`.

For every one of the 15 source tables, R3 recomputed the existing length-prefixed canonical row digest and required equality across:

1. immutable SQLite source;
2. live PostgreSQL final projection;
3. the prior PostgreSQL archival receipt;
4. retained Parquet/DuckDB projection.

All 15 tables matched exactly.

Representative retained counts:

- streams/tasks: **2,025**;
- Board messages: **15,640**;
- events: **14,417**;
- object refs: **44,414**;
- event object refs: **30,854**;
- task head validations: **2,025**;
- news editions/publications: **14 / 14**.

## Bidirectional row-equivalence check

Parquet/DuckDB validation is stronger than a row-count-only check. Every table is compared to the attached SQLite source in both directions using `EXCEPT ALL`:

```text
SQLite MINUS projection = 0
projection MINUS SQLite = 0
```

The retained projection is then exported back through DuckDB's JSON writer in canonical row order and hashed using the same row-digest algorithm used by the PostgreSQL archival projector.

Therefore an equal row count with substituted or duplicated rows does not pass R3.

## Invariants

All five historical invariants are zero in both live PostgreSQL and retained DuckDB/Parquet:

- dangling Board replies: `0`;
- event payload-edge violations: `0`;
- event/stream-head violations: `0`;
- news-head mismatches: `0`;
- task-projection/head violations: `0`.

## Destructive rebuild proof

The final implementation revision is:

`6c97508507f59167a2d288b09451b60ff6c5b578`

R3 performed:

1. initial complete materialization;
2. delete entire derived projection and rebuild #1;
3. delete entire derived projection and rebuild #2.

Total complete materializations: **3**.

All three produced the same logical fingerprint:

`d3a89e5abe5e4af4da07df5213a83add4f8abfb7e29d4dabacc8e86d5e88a5fc`

All three also produced the same physical Parquet fingerprint:

`2c68db342948f222851067ef8101e5f2b784268223745542217df0d5b47e71dc`

Manifest SHA-256 was identical across all three:

`094f9bf2f3569b44baef22a12519bfb41e4307084a0140aff475526948a31072`

This establishes that the derived projection can be destroyed and regenerated from the immutable SQLite authority.

## Final retained projection

Path:

`/var/lib/ordivon/retired/host-v1/projections/host-v1-final-r3`

Approximate retained size: **7.2 MiB**.

Contents:

```text
host-v1-final-r3/
├── manifest.json
├── host-history.duckdb
└── parquet/
    ├── board_messages.parquet
    ├── event_object_refs.parquet
    ├── events.parquet
    ├── host_metadata.parquet
    ├── leases.parquet
    ├── legacy_object_refs.parquet
    ├── news_editions.parquet
    ├── news_publications.parquet
    ├── object_refs.parquet
    ├── object_validation.parquet
    ├── schema_migrations.parquet
    ├── streams.parquet
    ├── task_extension_state.parquet
    ├── task_head_validation.parquet
    └── task_projection.parquet
```

DuckDB version:

`v1.5.5 (Variegata) d8cdaa33fd`

Final DuckDB catalog SHA-256:

`411f5b58e6b427b0016283d7e1eb699a1a68fbac3843ec30ecbe8056102d5b89`

## Post-publication consumer acceptance

A first consumer check found and prevented a real acceptance bug: the initial DuckDB catalog had retained staging-directory paths after the staging tree was renamed. Internal generation checks had passed because the staging paths still existed during validation.

R3 was not accepted in that state.

The generator was changed so that it:

1. validates staged Parquet before publication;
2. renames the validated projection into the retained destination;
3. recreates the DuckDB catalog using the final retained paths;
4. validates the final-path catalog again before emitting the receipt.

The corrected final consumer readback then passed.

Observed directly from the retained DuckDB catalog:

```text
cancelled   43
completed   1749
ready       233

board_messages        15640
latest_event_sequence 14417
```

`PRAGMA database_list` showed only the retained DuckDB database. A final path guard confirmed no `.cycle-*` staging path remained in the view definitions.

## Disposition

After R3:

| Object | Disposition |
|---|---|
| retired final SQLite backup | **retain — historical authority** |
| retirement receipt / durable-tree evidence | **retain — historical authority evidence** |
| Parquet projection | **retain — derived, open, rebuildable** |
| DuckDB catalog | **retain — derived query convenience** |
| PostgreSQL `host_retired_final_20260912` | **redundant migration evidence; no longer required for routine historical query** |
| Host v1 runtime/service | **remains retired** |

The PostgreSQL schema was intentionally not dropped in R3. It can be removed in a later cleanup without losing historical query capability, but its deletion is a separate destructive disposition action.

## Nonclaims

R3 does not recreate or establish:

- Host v1 writer semantics;
- lease/concurrency semantics;
- an active Host service;
- Temporal history continuity;
- PostgreSQL, Parquet, or DuckDB as Host authority;
- permission to delete the immutable SQLite source or retirement evidence.

Machine-readable receipt:

`evidence/host-v1-parquet-duckdb-r3-20260913.json`
