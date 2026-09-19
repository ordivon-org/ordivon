# Ordivon Capital External-Owner Census R1

## Purpose

This document records ownership, not a new Ordivon methodology. `config/external_owner_census.json` is the machine-readable authority. The rule is: standards own semantics, mature implementations own mechanics, providers own external reality, and Ordivon Capital owns only composition/evidence/authority/reconciliation seams that no single external owner can establish.

## Current hierarchy

```text
Ordivon
└── Capital
    ├── accounting/   TigerBeetle integration; TigerBeetle owns accounting mechanics
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
| accounting mechanics | TigerBeetle | bound implementation |
| policy decisions | Open Policy Agent | bound implementation |
| numerical/statistical mechanics | NumPy / SciPy / scikit-learn | bound implementation |
| market execution/research engine | NautilusTrader / LEAN where applicable | qualified/bound by use case |
| experiment/data validation | MLflow / Pandera / Parquet / DuckDB | bound implementation |
| lineage target | OpenLineage | migration target |
| observability | OpenTelemetry / Prometheus / Grafana | external owner |
| future compute economics | FinOps Framework / OpenCost | no local domain code |

## Substitutions completed in R1

- `src/market_capital` was retired. Current Python hierarchy is `ordivon_capital.market` plus the cross-domain `ordivon_capital.accounting` TigerBeetle integration.
- Current protocol kinds use `ordivon.capital.market.*`; historical evidence/fixture identities were not rewritten.
- Live-test account admission rules moved from a dedicated Python policy module into OPA; the local module was deleted.
- Portfolio risk-limit decisions moved from Python threshold logic into OPA.
- Pre-trade counterfactual evidence-gate decisions moved from Python into OPA.
- Caller-supplied counterfactual projection remains read-only local glue: it performs no ranking, allocation, or autonomous sizing.
- Historical expected shortfall remains a thin NumPy descriptive statistic rather than adding Riskfolio-Lib solely to replace transparent quantile/mean operations.
- Portfolio/counterfactual census was split after substitution audit: numerical/statistical mechanics are library-owned, OPA owns controls, and the remaining caller-supplied read-only projection is retained as irreducible glue rather than misusing an optimizer or execution risk engine.

## Remaining extraction / naming work

1. **Research/data extraction** — current mechanics are already externally owned by MLflow, Pandera, Parquet/Arrow, DuckDB, NumPy/SciPy/scikit-learn and provider data. The remaining work is cross-domain extraction of generic bindings into the shared Ordivon Research/Data substrate, with OpenLineage as the lineage standard target; Capital must not grow a duplicate data platform.
2. **Physical repository source coordinate** — the semantic package/project identity is Ordivon Capital, but `/root/projects/ordivon-market-capital-next` is retained because frozen Research/Paper1 provenance records use that exact absolute source coordinate for source re-entry and retention anchors. This is now a reproducibility compatibility contract, not an unresolved cosmetic rename. A future move requires an explicit Research provenance migration/alias authority; no permanent filesystem symlink is introduced.

## Non-goals

Ordivon Capital does not claim ISO, Basel, IFRS, PFMI, or other regulatory certification/compliance merely because those standards are referenced. It does not own venue mechanics, legal settlement truth, external-account ownership, investment suitability, or production-trading authorization.

## R2 subtraction note — 2026-09-20

The historical Wave-A prototype (`build_m1..m4`) and its test-only GLEIF/SEC/Cboe/equal-weight portfolio slice were removed after a caller census found no active runtime/script/CI consumer. Their dedicated configs and schemas were removed with them; historical evidence and Git history remain the record.

The surviving monitoring persistence adapter was renamed from `model_lineage` to `monitoring_persistence`. It no longer hardcodes a per-output SQLite MLflow backend: MLflow tracking configuration is supplied by the caller or `MLFLOW_TRACKING_URI`, consistent with MLflow's own configuration contract. The adapter does not claim OpenLineage/W3C-PROV-style lineage authority.

## R2 retained compatibility identities

Three historical-looking names remain intentionally: the deployed `ordivon_market_capital_*` Prometheus metric family, TigerBeetle/provider stable-ID seeds beginning with `market-capital:`, and the exact frozen `wave_a_target_portfolio.json` fixture. These are external observability, provider-idempotency, or evidence identities; they are not current Capital parent-system ownership claims and must not be cosmetically renamed without coordinated migration.

The absolute repository path `/root/projects/ordivon-market-capital-next` is also retained as a frozen Research provenance source coordinate. A 2026-09-20 host census found it in Paper1/Research Git-universe, source-linkage, episode-screening and retention-anchor records, including source-recovery-required entries. Physical rename is therefore blocked by reproducibility semantics rather than by Capital package naming.
