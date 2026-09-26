# Learning Data Ownership Census R1

Date: 2026-09-23  
Status: **L01 COMPLETE — REUSE EXPERIMENTAL EPISODE CORE**

The repository already contains the right analytical waist: `experimental-episode-binding-r1`. It binds exact owner-native identities and evidence digests into deterministic derived episodes while explicitly refusing to become Runtime/Harness/domain truth.

Three data classes must remain separate: authoritative owner evidence, derived analytical episodes/features, and observability telemetry. Telemetry may correlate but never becomes a task label or effect truth.

## L02 disposition

`L02_NEW_STORE = CLOSED_REUSE_EXISTING`: `studies/experimental-episode/postgres-projection-r1` already provides the qualified PostgreSQL analytical consumer, so no second/new store is admitted. `L02_DEPLOYMENT = DEFER_ACTIVATION` until a named live consumer demonstrates a query/availability requirement that file/Parquet/DuckDB projections cannot satisfy. PostgreSQL remains an on-demand Workstation-realized read model, not an architecture objective by itself.

That test is now materialized by `INTEGRATED_C08_CAPITAL_READONLY_DOGFOOD_R1.md`, and `LEARNING_QUERY_PRESSURE_R1.md` measures the first live pressure. The existing Store R1 accepts the C08 Episode unchanged and remains available on demand, but the current live queries are already satisfied by the file projection. The next step is to accumulate additional real owner-native Episodes and re-evaluate activation only when a named consumer requirement is unmet.
