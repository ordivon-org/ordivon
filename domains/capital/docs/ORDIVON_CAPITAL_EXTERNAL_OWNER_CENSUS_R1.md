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
2. **Physical repository name** — the source repository path may retain the historical `ordivon-market-capital-next` name while active external references exist; semantic package/project identity is now Ordivon Capital. Rename only after an explicit caller/workspace reference census, not by introducing a compatibility symlink as permanent debt.

## Non-goals

Ordivon Capital does not claim ISO, Basel, IFRS, PFMI, or other regulatory certification/compliance merely because those standards are referenced. It does not own venue mechanics, legal settlement truth, external-account ownership, investment suitability, or production-trading authorization.
