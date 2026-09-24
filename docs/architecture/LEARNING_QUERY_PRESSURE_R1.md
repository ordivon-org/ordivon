# Learning Query Pressure R1

Date: 2026-09-23
Status: **PASS — reuse existing Episode Store R1; no new PostgreSQL store; permanent realization remains demand-gated**

## Question

After the first real C08 Experimental Episode, should Ordivon build or permanently deploy a new PostgreSQL learning store?

## Existing capability

The repository already owns `meta/next/experimental/episode-store-r1`, a task-local PostgreSQL analytical consumer with Alembic-owned schema and no long-lived service. Historical RW3/RW4 evidence qualified it on 10,007 Episode projections (10,000 Runtime + 7 Harness) and found real descriptive analytical value, while leaving permanent deployment only `ELIGIBLE_BUT_NOT_YET_REALIZED`.

## Current C08 dogfood

The canonical C08 Episode `integrated-c08-capital-readonly-r1` was accepted by the existing Store R1 load contract without any schema or source change. An isolated PostgreSQL 18.6 cluster under `/tmp` was migrated with Alembic 0001, ingested the Episode once, replayed the exact same ingest idempotently with zero new projections, answered owner/native-verdict/recovery/evidence/job/profile queries, then was stopped and physically removed. No live Ordivon PostgreSQL instance was reused.

The same six questions are already answerable directly from the 4,433-byte Episode file. Across 2,000 identical direct-file query bundles: mean 13.712 µs, median 12.985 µs, p95 17.824 µs. The temporary PostgreSQL queries were all sub-2 ms, but this is not a database benchmark: the decisive observation is that the current live consumer has **no unmet query or availability requirement**.

## Decision

```text
new PostgreSQL Store code       -> REJECT / REUSE episode-store-r1
permanent PostgreSQL deployment -> DEFER until named live pressure exists
default small/local analysis    -> file projection; Parquet/DuckDB when tabular scale helps
on-demand PostgreSQL            -> existing Store R1 + Workstation-owned realization
```

Therefore L02 is no longer an open "build a PostgreSQL store" item. The software consumer already exists and is qualified. What remains conditional is only **activation/realization** of that existing consumer.

Machine evidence: `docs/architecture/learning-query-pressure-r1.json` (`sha256:bd8c1daf5a06e78d220b23d35be642f3c1084b3cdbb2d620c24cdd684a166150`).
