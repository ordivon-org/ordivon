# Market Capital Standards Adoption R1

Date: 2026-09-19
Status: ACTIVE ARCHITECTURE BASELINE

## Objective

Market Capital uses authoritative financial systems and mature external components wherever they already own the required mechanism. Local code is limited to narrow mappings, policy controls, reconciliation, and evidence binding specific to this composition.

This baseline supersedes active use of locally invented LEGO/lens terminology inside Market Capital.

## External ownership matrix

| Responsibility | External standard / mature owner | Current standing | Local responsibility |
| --- | --- | --- | --- |
| Venue market/account/order truth | Authoritative OKX/Binance/provider APIs | STRONG | Thin normalization and provenance |
| Trading-engine mechanics | QuantConnect LEAN; NautilusTrader | PARTIAL | Qualification, configuration, mappings |
| Order semantics | FIX Latest / FIX Orchestra | PARTIAL | FIX 4.4 legacy compatibility projection only when explicitly required |
| FIX engine | QuickFIX/n 1.14.1 | CURRENT_STABLE | Compatibility projection and future admitted sessions |
| Accounting mechanics | TigerBeetle 0.17.9 | STRONG | Domain-to-ledger mapping and reconciliation |
| Legal entity identity | GLEIF / LEI | STRONG | Reference binding |
| Issuer disclosure | SEC EDGAR/XBRL | STRONG | Feature mapping |
| Financial messaging reference | ISO 20022 | REFERENCE_ONLY | Mapping only when post-trade integration requires it |
| FMI/settlement reference | CPMI-IOSCO PFMI | REFERENCE_ONLY | No private clearing/settlement implementation |
| Risk-data governance | BCBS 239 principles | PARTIAL_GAP | Lineage, aggregation quality and timeliness controls |
| Model-risk governance | Federal Reserve SR 26-2 (2026) | ADOPTING | Model inventory, validation standing, use limitations, monitoring |
| Market-risk methodology | Basel market-risk framework | GAP | Proportional expected-shortfall, stress and liquidity-horizon methodology |
| Observability | Prometheus/Grafana; OpenTelemetry | PARTIAL | Existing metrics; cross-signal OTel context incomplete |
| Research lineage | MLflow, Parquet, Pandera, JSON Schema | PARTIAL | Expand consistent run/model/data lineage |
| Data interchange/schema | JSON Schema 2020-12; Arrow/Parquet | GOOD | Narrow domain schemas and transformations |

## Retain

- Authoritative venue APIs as market/account/order truth.
- Network v2 as transport authority rather than application-level path selection.
- TigerBeetle for double-entry and pending-transfer mechanics.
- GLEIF and SEC/XBRL reference paths.
- Prometheus/Grafana monitoring.
- JSON Schema 2020-12 for validated configuration and artifacts.
- Read-only-first provider qualification and explicit external-write admission.

## Update

- LEAN is pinned to an older source cut; upgrades require regression qualification.
- Nautilus v2 remains a release candidate and stays qualification-only until an upstream production-suitable stable release is available and locally qualified.
- QuickFIX/n 1.14.1 is current stable, but FIX 4.4 is a legacy compatibility profile. FIX Latest and FIX Orchestra are the semantic reference.
- MLflow/Pandera/Parquet exist but are not yet uniformly bound to all quantitative research.
- Prometheus/Grafana are active; trace/log/metric context is not yet standardized end-to-end through OpenTelemetry.

## Replace or retire

- Custom LEGO/lens routing inside Market Capital.
- The custom Regime Card taxonomy as an active decision model.
- P1-P8 numbering as a financial-method authority.
- Any local stress theory that duplicates standard scenario analysis, expected shortfall, liquidity-horizon or model-validation practice.

## Model governance

Federal Reserve SR 26-2 is used proportionately as a model-governance reference, not as a claim that Market Capital is subject to banking regulation.

The operational distinction is:

- quantitative methods grounded in statistical, economic, or financial theory -> model-governance candidate;
- simple arithmetic and deterministic controls without that theoretical underpinning -> non-model calculation/control.

The canonical inventory is config/quantitative_component_inventory.json, validated by JSON Schema 2020-12.

## Risk-data direction

BCBS 239 is the reference for risk-data architecture. Upgrades should focus on authoritative source identity, lineage, completeness, accuracy, timeliness, aggregation consistency, reconciliation, and explicit compensating controls.

## Market-risk direction

Basel market-risk concepts are used proportionately rather than copied as a bank-capital engine: expected shortfall, stressed calibration, liquidity horizons, modellable/non-modellable risk-factor distinctions, and outcomes/backtesting where relevant.

## FIX direction

FIX Latest is the semantic reference. QuickFIX/n may emit FIX 4.4 only under an explicit legacy compatibility profile.

The boundary is:

FIX Latest semantics -> explicit compatibility profile -> QuickFIX/n wire representation.

## First replacement round

1. Retire the standalone custom Regime Card implementation.
2. Remove active Market Capital LEGO/lens planning artifacts.
3. Rename portfolio documentation around risk monitoring and scenario analysis.
4. Create an SR 26-2-aligned quantitative component/model inventory.
5. Decouple market observation normalization from Regime Card.
6. Delegate regression/correlation calculations to SciPy/NumPy rather than hand-coded covariance math.
7. Reframe FIX 4.4 as a legacy compatibility profile instead of the semantic owner.

## Next rounds

1. Formal model validation and outcomes monitoring for the dependence model.
2. BCBS-239-style lineage/freshness/completeness fields on risk datasets.
3. Standard expected-shortfall and stress/scenario measures using mature numerical libraries.
4. LEAN upgrade after regression qualification.
5. Nautilus requalification against a production-suitable stable v2 line when available.
6. OpenTelemetry context propagation while retaining Prometheus/Grafana backends.
7. Review remaining custom semantic/authority vocabulary and replace anything already owned by venue/FIX/accounting/policy standards.
