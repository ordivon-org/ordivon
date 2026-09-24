# Data / Learning System Current-Truth Census R1

Date: 2026-09-24
Status: **CURRENT-TRUTH SYNTHESIS / SELECTED LIFECYCLE LOOP PROVEN / NONTRIVIAL ADAPTIVE FEEDBACK OPEN**

## Result

The Ordivon data system is not a database. Its current architecture is a federation of owner-native evidence, standards-native data products, derived analytical episodes, lineage/provenance and bounded feedback:

```text
Reality
  -> owner-native observation/evidence
  -> exact identity / digest / source revision
  -> contract / validation
  -> domain-owned data product
  -> preservation + governance
  -> operational lineage (OpenLineage)
  -> semantic provenance (PROV-O)
  -> optional Experimental Episode projection
  -> evaluation / analysis
  -> decision / action
  -> outcome
  -> feedback disposition
  -> [when evidence requires] successor / policy change / ratchet
```

The last arrow is the main open empirical gap. The current Finance witness legitimately produced `NO_CHANGE_REQUIRED`; Ordivon must not fabricate a mutation just to make the loop look complete.

## Current LEGO map

| LEGO | Existing carrier | Standing | Boundary |
|---|---|---|---|
| D00 Information / decision requirement | domain studies | PARTIAL | no universal information objective |
| D01 Source identity / revision | Git/provider IDs + digest | PASS_SELECTED | processing order is not source truth |
| D02 Acquisition / raw evidence | domain owners | PASS_PARTIAL | owner-native evidence remains authority |
| D03 Contract / validation | ODCS + Artifact Dataset Contract + JSON Schema/native readers | PASS_SELECTED | format-valid != domain-valid |
| D04 Data product | ODPS 1.1 | PASS_RESEARCH_FINANCE | domain owns product metadata/lifecycle |
| D05 Discovery federation | DCAT 3 | PASS_TWO_DOMAIN | central catalog is projection only |
| D06 Governance | ODRL 2.2 + NIST PF + ISO 15489 boundary | PASS_FAIL_CLOSED_PARTIAL | unresolved rights/privacy/retention stay unresolved |
| D07 Preservation | local AIP/fixity | PASS_LOCAL_FAILURE_DOMAIN | offsite independence remains open |
| D08 Operational lineage | OpenLineage 2-0-2 | PASS_SELECTED | operational run lineage != semantic derivation |
| D09 Semantic provenance | W3C PROV-O | PASS_SELECTED | provenance supports assessment; does not make claims true |
| D10 Analytical episode | `experimental-episode-binding-r1` | PASS | derived projection != owner truth |
| D11 Observability | OTel/OTLP -> Vector/Prometheus bounded acceptance | PASS_BOUNDED | telemetry != labels/effect truth |
| D12 Evaluation / measurement | Evaluation Boundary + Meta-Improvement Measurement | PASS_PROFILE | vector before scalarization; frozen anchors |
| D13 Decision / action | Research verification + Finance bounded decision | PASS_SELECTED | decision record != external effect |
| D14 Outcome | Finance boundary preservation | PASS_TECHNICAL_PARTIAL_VALUE | broader business/scientific outcome partial |
| D15 Feedback disposition | Finance `NO_CHANGE_REQUIRED` | PASS_NO_CHANGE | no adaptive mutation is claimed |
| D16 Feedback-driven successor / ratchet | Improvement Circuit + Successor Contract available | OPEN_EMPIRICAL | no real nontrivial outcome-driven change yet |

## Existing analytical waist

`experimental-episode-binding-r1` already supplies the correct thin analytical carrier:

```text
episodeId                 stable experimental identity
projectionDigest          exact analytical projection identity
anchor / ownerRefs        exact owner-native identities
sourceRecordDigest        exact source record binding
evidenceBindings          bounded evidence-set identity
dimensions / measures     scalar analytical projection
unresolved / nonClaims    retained uncertainty and claim limits
```

This is deliberately not Runtime, Harness, study, or domain truth.

## Measurement is already present

`META_IMPROVEMENT_MEASUREMENT_R1` defines an improvement episode and a measurement vector:

```text
valid_target_yield
admitted_candidate_yield
heldout_gain_distribution
regression_rate
abstention_calibration
observation/model/token/wall-clock/compute/human costs
recovery_or_rollback_rate
```

It requires frozen evaluation anchors, comparable budgets, held-out transfer where applicable, repeated evidence and regression accounting. It explicitly prefers Pareto comparison before scalarization.

Therefore M03 Measurement Contract and much of M05 Proxy/measurement qualification should reuse Evaluation Boundary + study-owned measurement profiles rather than introducing a new global metric schema.

## Observability is already connected

Experimental Episode RW5 has accepted bounded OTel/OTLP -> Vector -> Prometheus read-back with gauges such as episode count, identity collision count and missing split/join counts. The acceptance explicitly says Prometheus is not Episode/Runtime/Harness/domain truth.

The data-observability P1 should therefore extend existing OTel/Prometheus surfaces for freshness/volume/schema/quality/lineage-break metrics only when named consumers need them; no new observability platform is justified.

## Feedback status

Current Finance post-registration evidence proves:

```text
exact product version
 -> schema-valid OpenLineage consumption
 -> decision: NO_EXECUTION_OR_DIRECTIONAL_ACTION_ADMITTED
 -> action: NO_EXTERNAL_EFFECT
 -> outcome: PASS_BOUNDARY_PRESERVED
 -> feedback: KEEP current collection/quality/model/governance policy
 -> changeRequired=false
```

This is a successful feedback loop with abstention/no-change. It is not adaptive optimization.

## D16 — exact remaining gap

The open empirical obligation is:

> Observe one real post-outcome event whose evidence requires a change to collection, quality, measurement, or model policy; bind the exact predecessor and candidate policy/configuration, freeze evaluation outside the candidate, verify required invariants, observe the post-change field outcome, and only then encode a scoped ratchet if justified.

All required architecture pieces already exist:

- Improvement Circuit Profile R1;
- Evaluation Boundary R1;
- Verification Obligation R1;
- Successor Contract R1;
- Experimental Episode R1;
- OpenLineage / PROV-O;
- domain-owned policy/configuration;
- external promotion/effect authority.

Thus the gap is **a real qualifying event**, not a missing generic service/schema/database.

## Admission rule for a nontrivial feedback change

A future D16 case is admissible only if it binds:

1. exact outcome evidence that creates the change pressure;
2. exact predecessor collection/quality/model/measurement policy;
3. a candidate change whose reason is traceable to that outcome;
4. frozen Evaluation Boundary and named negative controls;
5. exact Verification Obligations and natural verifier bindings;
6. Successor Contract mechanical closure;
7. external promotion/effect authority;
8. post-change field observation;
9. decision to retain, revert, or ratchet based on field evidence;
10. Experimental Episode / lineage projection only after owner-native evidence exists.

`changeRequired=true` without these bindings must not be accepted as proof of adaptive learning.

## Heavy infrastructure decision

Current evidence continues to falsify automatic activation of:

- Iceberg;
- Debezium;
- Beam runtime;
- Kafka/Redpanda;
- ClickHouse/QuestDB;
- Dagster;
- Great Expectations;
- OCFL;
- a permanent PostgreSQL analytical service.

These remain workload-gated, not architecture debt.

## Main residuals

1. one real nontrivial feedback-driven successor (D16);
2. broader business/scientific value outcomes beyond technical boundary preservation;
3. source-rights resolution, formal privacy assessment and authorized retention schedules;
4. independent/offsite preservation when an approved target exists;
5. broader domain adoption only with real consumers;
6. scoped freshness/quality/lineage observability where current consumers demonstrate need.
