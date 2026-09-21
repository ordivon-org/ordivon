# Ordivon Capital External-Owner Census R1

## Purpose

This document records ownership, not a new Ordivon methodology. `config/capital_domain_taxonomy.json` separately freezes the current source-owner domain taxonomy. `config/external_owner_census.json` is the machine-readable authority. The rule is: standards define semantics, providers own authoritative external reality, and mature implementations are candidates for replaceable mechanics. A candidate becomes an owner only after contract-equivalent qualification against the smallest credible local baseline. Ordivon Capital retains bounded local mechanisms and composition/evidence/authority/reconciliation seams when they win that comparison.

## Current hierarchy

```text
Ordivon
└── Capital
    ├── accounting/   bounded accounting semantics + SQLite WAL/FULL substrate
    └── market/       currently instantiated Market domain
```

Treasury, Compute, Enterprise, Human, Distribution, and other conceptual domains are intentionally **not** local packages. They remain external-owner entries until a real use case exists.

## External owners currently bound or referenced

| Responsibility | External owner | Local standing |
| --- | --- | --- |
| asset-management lifecycle reference | ISO 55000 / ISO 55001 | reference only |
| enterprise risk reference | ISO 31000 | reference only |
| risk-data governance reference | BCBS 239 | reference only; no compliance claim |
| electronic trading semantics | FIX standards / venue contracts | bound/reference |
| financial messaging | ISO 20022 where applicable | reference |
| FMI/finality principles | CPMI-IOSCO PFMI | reference only; Ordivon is not an FMI |
| legal-entity identity | GLEIF / LEI | provider adapter |
| accounting mechanics | SQLite 3.53.1 via Python 3.14.7 stdlib | current bounded single-host implementation; TigerBeetle 0.17.9 is a distributed challenger |
| policy decisions | bounded local deterministic Python | current implementation; OPA 1.20.2 is a historical/future distributed-policy challenger |
| numerical/statistical mechanics | NumPy / SciPy / scikit-learn | bound implementation |
| bounded US-equity execution feasibility | local fee-aware sizer | current exact-contract owner after zero-mismatch LEAN differential |
| historical/general trading engine | QuantConnect LEAN / NautilusTrader | candidates only; LEAN latest is functionally qualified but supply-chain blocked |
| monitoring persistence | local bounded row validation + PyArrow/Parquet + DuckDB | current implementation; MLflow/Pandera are candidates only |
| lineage | OpenLineage | candidate only; no active lineage-event contract |
| Market observability | Prometheus 3.14.0 / node exporter / OpenTelemetry / Grafana | candidates only; current Market path has static text/rule artifacts but no active scrape/TSDB/rule-evaluation consumer |
| future compute economics | FinOps Framework / OpenCost | no local domain code |

## Current requalification standing

- OPA 1.20.2 lost the current bounded policy contract after 354 differential cases produced zero mismatches against a much smaller direct Python implementation and the deployed integration provided no independent authority boundary. Rego is preserved as historical challenger evidence.
- TigerBeetle 0.17.9 lost the current single-host accounting contract after a SQLite WAL/FULL baseline passed the same reserve/post/void/idempotency/restart mechanics and a 400-step randomized differential produced zero status or balance mismatches. TigerBeetle remains the challenger for a future distributed/replicated contract.
- QuantConnect LEAN master `985ef30` builds on .NET SDK 10.0.401 and passes historical M1/M2/M3/M4/M6 functional qualification. A fee-aware local sizer then matched 57/57 current exact-contract symbol comparisons. LEAN is not core-admitted because its latest build also reports known critical/high NuGet advisories; it remains isolated historical/general-engine evidence.
- OpenLineage, OpenTelemetry and Grafana are candidates rather than owners because no active current contract binds them. Prometheus 3.14.0 is also only a Market-domain candidate: the active Network v2 Prometheus has no Market target/rules/series, while the configured shared Prometheus and node exporter endpoints are inactive.
- Caller-supplied counterfactual projection remains bounded read-only local glue: it performs no ranking, allocation, autonomous sizing, or execution authority.
- Historical expected shortfall remains a thin NumPy descriptive statistic rather than adding a broad portfolio library solely to replace transparent quantile/mean operations.

## Remaining extraction / naming work

1. **Research/data extraction** — current mature mechanics are PyArrow/Parquet, DuckDB, jsonschema, NumPy/SciPy/scikit-learn and provider data. The one active monitoring schema is validated by bounded local code after a zero-mismatch Pandera differential. MLflow/Pandera/OpenLineage remain candidates only for future contracts that actually require experiment tracking, richer dataframe validation, or lineage events; Capital must not grow a duplicate data platform.
2. **Physical repository source coordinate** — the semantic package/project identity is Ordivon Capital, but `/root/projects/ordivon-market-capital-next` is retained because frozen Research/Paper1 provenance records use that exact absolute source coordinate for source re-entry and retention anchors. This is now a reproducibility compatibility contract, not an unresolved cosmetic rename. A future move requires an explicit Research provenance migration/alias authority; no permanent filesystem symlink is introduced.

## Non-goals

Ordivon Capital does not claim ISO, Basel, IFRS, PFMI, or other regulatory certification/compliance merely because those standards are referenced. It does not own venue mechanics, legal settlement truth, external-account ownership, investment suitability, or production-trading authorization.

## R2 subtraction note — 2026-09-20

The historical Wave-A prototype (`build_m1..m4`) and its test-only GLEIF/SEC/Cboe/equal-weight portfolio slice were removed after a caller census found no active runtime/script/CI consumer. Their dedicated configs and schemas were removed with them; historical evidence and Git history remain the record.

The surviving monitoring_persistence adapter now performs bounded local row validation, PyArrow/Parquet materialization, DuckDB independent readback and content-addressed manifest generation. MLflow, Pandera and pandas were removed from the current dependency graph after the active-contract census; historical MLflow evidence remains historical. The adapter does not claim experiment-tracking or OpenLineage/W3C-PROV authority.

## R2 retained compatibility identities

Historical-looking names remain only where they carry real evidence compatibility. The deployed `ordivon_market_capital_*` Prometheus metric family and the exact frozen `wave_a_target_portfolio.json` fixture remain compatibility identities. TigerBeetle-specific stable-ID seeds are retained only inside historical qualification artifacts; current SQLite accounting uses provider-neutral `ordivon-capital:accounting:*` identities.

The absolute repository path `/root/projects/ordivon-market-capital-next` is also retained as a frozen Research provenance source coordinate. A 2026-09-20 host census found it in Paper1/Research Git-universe, source-linkage, episode-screening and retention-anchor records, including source-recovery-required entries. Physical rename is therefore blocked by reproducibility semantics rather than by Capital package naming.
