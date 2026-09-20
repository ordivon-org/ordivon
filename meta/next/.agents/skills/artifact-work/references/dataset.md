# Dataset reference

## Bounded proven profile

`dataset-parquet-flat-r1`

- Apache Parquet / `application/vnd.apache.parquet`
- flat bounded scalar columns
- object-specific contract defines ordered columns, logical types, nullability, primary key, and optional row bounds
- row order is not authoritative in R1
- Standing: `SHADOW_PROFILE_LIVE_PROVEN`

## Prior proven providers

- DuckDB 1.5.5 — native Parquet schema/repetition plus logical row observation
- PyArrow 25.0.1 — independent reader/schema evidence

## Boundary

The embedded Parquet schema and the object-specific Dataset Contract are separate authority layers and must agree. Generic SQL projection metadata is not automatically native Parquet repetition/nullability authority.

## Source evidence

`/root/projects/ordivon-artifact-v2/docs/ARTIFACT_FAMILY_DATASET_R1.md`
