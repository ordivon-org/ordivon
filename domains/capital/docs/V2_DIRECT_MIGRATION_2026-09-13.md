# Market Capital v2 Direct Migration — 2026-09-13

The former `/root/projects/ordivon-market-capital-v2` clean-room foundation is no longer an architectural or runtime component. Its retained capabilities were migrated into the single canonical `/root/projects/ordivon-market-capital-next` repository.

## Migrated directly

| Former v2 surface | Canonical destination |
|---|---|
| semantic implementation | `src/market_capital/semantic.py` |
| semantic freeze contract | `contracts/semantic-core-v1.json` |
| production authorization | `contracts/production-authorization.json` |
| external boundary contract | `contracts/external-boundary-v1.json` |
| false-green corpus | `destroyer/false-green-corpus-v0.json` |
| semantic test suite | `tests/test_semantic_core.py` |
| R1 Arrow/Parquet/DuckDB example | `examples/r1_witness_parquet_duckdb.py` |
| optional Redpanda/QuestDB substrate | `infra/optional-witness-substrate.compose.yaml` |
| original R0/R1 acceptance evidence | `evidence/migration-source-v2-r0-r1-20260911.json` |

The original evidence is copied unchanged as migration provenance. Active contracts were promoted from the temporary `market-capital-v2` namespace to the canonical `ordivon.market-capital.*` namespace.

## Not retained as architecture

There is no cross-repository provider/binding layer, no provider revision lookup, no provider contract digest dependency, and no runtime import from `ordivon-market-capital-v2`.

Optional Redpanda/QuestDB remain commodity demonstration infrastructure only. They do not own observation order, truth, capital authority, settlement or production authorization.
