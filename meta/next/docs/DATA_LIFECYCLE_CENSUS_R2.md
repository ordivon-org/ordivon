# Data Lifecycle Census R2

Date: 2026-09-20

R2 supersedes the status projection in R1; R1 remains historical evidence.

## Current standing

`ProjectScopedDataWork = READY`

`CrossDomainDataLifecycle = PARTIAL`

R2 records that the earlier generic GitHub/temporal pilots now prove acquisition, semantic validation, quality, entity/reference handling, operational lineage, revision semantics and **local durable preservation**. The cross-domain system is still incomplete because real Research/Finance data products, federated catalog/product metadata, rights/retention, semantic provenance, exact decision binding and outcome-feedback are not closed.

## Lifecycle standing

| Stage | R2 standing | Priority |
|---|---|---|
| 0. information-decision-requirement | PARTIAL | P1 |
| 1. source-discovery | KEEP_PARTIAL | P1 |
| 2. acquisition | PILOT_PROVEN_DOMAIN_PARTIAL | P1 |
| 3. ingestion | PARTIAL | P2 |
| 4. raw-preservation | PASS_LOCAL_DURABLE_PRESERVATION | P1 |
| 5. parse-normalize | KEEP_PARTIAL | P1 |
| 6. clean-validate | KEEP | P1 |
| 7. integration-entity-resolution | PILOT_PROVEN_CROSS_DOMAIN_PARTIAL | P1 |
| 8. metadata-catalog | PILOT_PROVEN_CROSS_DOMAIN_MISSING | P0 |
| 9. provenance-lineage | PILOT_PROVEN_DURABLE_CROSS_DOMAIN_PARTIAL | P0 |
| 10. data-contract-product | ODCS_PILOT_PROVEN_ODPS_MISSING | P0 |
| 11. exploration-analytics | KEEP | P1 |
| 12. modeling-synthesis | KEEP_PARTIAL | P1 |
| 13. serving-retrieval | PARTIAL | P2 |
| 14. decision-action | KEEP_PARTIAL_EXACT_PRODUCT_BINDING_MISSING | P0 |
| 15. outcome-measurement | PARTIAL | P0 |
| 16. feedback-recollection | MISSING | P0 |

## P0 queue

1. **catalog-products** — Create real ODPS data products and a federated DCAT projection for Research and Finance; do not deploy a catalog service unless file/index scale proves necessary.
2. **domain-adoption** — Make one real Research flow and one real Finance witness flow emit ODCS/DCAT/OpenLineage product/version bindings.
3. **semantic-provenance** — Add W3C PROV for claim/knowledge derivations where operational OpenLineage is insufficient.
4. **rights-privacy-retention** — Bind owner/license/permitted-use/PII/sensitivity/retention/deletion policy to products before social-platform collection expands.
5. **decision-outcome-feedback** — Bind exact consumed product/version to claim/decision/action, then persist outcome-driven changes back to collection/quality/model policy.

## Preservation update

See:

- `docs/DATA_DURABLE_PRESERVATION_R1.md`
- `evidence/data-lifecycle/preservation-r1/acceptance.json`
- `evidence/data-lifecycle/preservation-r1/ndsa-2.1-assessment.json`

The preservation P0 has moved from “reacquirable-only” to “local durable preservation proven.” Independent-site/offsite resilience remains P1.

## Explicit non-gaps

Iceberg, Debezium, Beam runtime, Kafka/Redpanda, ClickHouse, QuestDB, Dagster, Great Expectations and OCFL remain workload-gated. Their absence is not counted as lifecycle debt.
