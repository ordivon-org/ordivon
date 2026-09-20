# Market Capital Standards Adoption R3

Date: 2026-09-19
Status: SUPERSEDED BY STANDARDS_ADOPTION_R4

## Rule

LEGO decomposition is an analysis technique only. It is not an owned financial architecture. After decomposition, each responsibility is assigned to an authoritative provider, mature implementation, industry standard, or a narrowly justified local seam.

## R3 replacements

### Execution policy

- OPA/Rego is the sole policy decision point.
- Python is only a fail-closed policy enforcement point.
- duplicate execution-policy logic was removed from Python and Prometheus export code.
- the documentary external-boundary map is no longer loaded by the execution-policy path.

### Quantitative/model governance

- Federal Reserve SR 26-2 is the proportional model-risk governance reference.
- active quantitative outputs use registered `componentId` values.
- use restrictions and validation obligations live in the component/model inventory rather than being repeated as `truthRole`, `tradeRecommendationProduced`, `causalStanding`, or similar narrative fields in every artifact.
- only one active component is currently classified as a quantitative model: historical dependence analysis; its status is `VALIDATION_REQUIRED`.

### Unvalidated heuristics removed

- dependence analysis no longer applies locally invented HIGH/LOW/STABLE threshold classifications.
- repeated microstructure analysis no longer applies a default 0.75 persistence threshold or BUY/SELL persistence labels.
- both paths now emit measured statistics only.

### Risk-data governance

- BCBS 239 principles are used proportionately as the risk-data engineering reference.
- cross-venue public observations expose source authority, completeness, timeliness/clock agreement, bounded comparison scope, and lineage.
- the custom `sameCutScope` ontology is removed from active source.

### Prospective validation

- the former `causal_shadow` component is retired from active source/config/scripts/tests.
- the replacement is `prospective_validation`: a frozen decision can use only strictly post-decision aligned holdout sessions.
- post-decision timing is treated as leakage prevention, not causal identification.
- execution/FIX eligibility requirements are no longer mixed into the prospective-data control.

### Historical validation data

- the former `market_data_admission` causal-standing field is replaced by explicit validation purpose and prohibited inference.
- historical Nasdaq bars are scoped to execution-mechanics/data-plumbing validation and cannot establish strategy performance.

## Ownership after R3

| Responsibility | Owner | Local seam |
| --- | --- | --- |
| Venue/account/order reality | provider APIs | normalization/reconciliation |
| Trading mechanics | LEAN / NautilusTrader | qualification/configuration |
| Order semantics | FIX Latest / FIX Orchestra | explicit compatibility mapping |
| Execution policy | OPA/Rego | policy input + PEP |
| Accounting | TigerBeetle | identity mapping/reconciliation |
| Model governance | SR 26-2 reference | inventory + validation status |
| Risk-data quality | BCBS 239 reference | concrete quality/lineage checks |
| Numerical statistics | NumPy/SciPy | sample/window construction |
| Research lineage | MLflow/Parquet/Pandera | domain bindings |
| Monitoring | Prometheus/Grafana; OTel direction | domain metrics |

## Deliberately retained local seams

The following are not removed merely because they are local:

- venue-native order/fill normalization to FIX lifecycle vocabulary;
- authoritative reconciliation to TigerBeetle POST/VOID/NO_MUTATION instructions;
- deterministic provider identity mapping needed for TigerBeetle integration;
- explicit user/policy risk limits;
- provider-specific read-model normalization.

They remain only while no external owner can replace them without losing required identity, reconciliation, or fail-closed behavior.

## Next substitution targets

1. Validate the historical dependence model with outcomes monitoring rather than inventing a new classifier.
2. Add standard tail-risk/scenario measures (expected shortfall, stressed scenarios, liquidity horizons) through mature numerical libraries.
3. Extend BCBS-239-style lineage/freshness/completeness controls across remaining risk datasets.
4. Requalify newer LEAN/Nautilus upstream versions through differential regression.
5. Introduce OpenTelemetry context propagation where it reduces bespoke provenance plumbing.
6. Continue reviewing TigerBeetle identity/reconciliation mapping, but replace it only if a mature provider-native mechanism can preserve the same safety properties.
