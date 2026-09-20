# GitHub Data Lifecycle Pilot R1

Date: 2026-09-20  
Base lifecycle census: `docs/DATA_LIFECYCLE_CENSUS_R1.md`

Semantic externalization: `docs/DATA_SEMANTICS_EXTERNALIZATION_R1.md`

## Purpose

Exercise the cross-domain data lifecycle with real, externally curated GitHub datasets rather than synthetic fixtures.

The pilot uses two TidyTuesday 2026 releases pinned to one exact repository revision:

- repository: `https://github.com/rfordatascience/tidytuesday`
- source commit: `f4d1b35ca09d8c0d875451635daef9179adfc9e0`

TidyTuesday is used as a source carrier because its curation process requires downloadable public/reusable data and a data dictionary. The pilot still preserves upstream-source uncertainty and does not infer a license where one is not explicitly bound.

## Workloads

### Crossref metadata country statistics

Files:

- `member_participation_stats_by_country.csv`
- `metadata_coverage_stats_by_country.csv`

Shape after normalization:

- member table: 6,001 rows × 23 columns;
- metadata coverage table: 53,820 rows × 50 columns;
- the 50th field is the derived canonical key `document_subtype_key = coalesce(document_subtype, '')`.

The source documentation explicitly makes `document_subtype` applicable only to `posted_content`; therefore source nulls are retained and the derived key is added rather than mutating raw data.

### Sustainable Energy for All

File:

- `energy_cleaned.csv`

Shape:

- 5,271 rows × 52 columns.

A naive “all percentage fields must be 0–100” rule was falsified by real data. The pilot therefore uses field-specific bounded-percentage checks, allows a 0.1 percentage-point rounding tolerance for proportion-like metrics, and treats `transmission_and_distribution_losses_pct` as a separately interpreted metric rather than forcing it into a generic proportion constraint.

## Lifecycle exercised

```text
GitHub commit-pinned source
  -> byte digest verification
  -> immutable raw acquisition
  -> DuckDB parse/normalization
  -> Parquet materialization
  -> primary-key and domain quality checks
  -> ODCS 3.2.0 contracts
  -> DCAT 3 catalog projection
  -> OpenLineage START/COMPLETE events
  -> DuckDB analytical outputs
  -> manifest with exact content hashes
```

Raw CSV and derived Parquet are deliberately not retained in Git. They are reproducibly reacquired/rematerialized from exact Git commit + expected SHA-256. Stable source policy, semantic profile, contracts, catalog metadata, quality evidence and compact analysis outputs are versioned. Run-specific acquisition receipts and OpenLineage events are written under ignored runtime evidence directories so replay does not overwrite historical operational events.

## External-standard validation

ODCS validation:

- Bitol Open Data Contract Standard v3.2.0;
- schema source commit: `d3e1cb3e69849e05c9a7522abed9b27fb9af50d7`;
- schema SHA-256: `edb41f33ec46e84780e99872ab2bd67f074959d2bf3e9c9fc54e61f8982b0d93`;
- all three generated contracts passed the official JSON Schema.

OpenLineage validation:

- OpenLineage schema id: 2.0.2;
- source commit: `e248b98e3146ff4437df76fcb07c83913d41f727`;
- schema SHA-256: `69f68bee00b9beac88a87059c0102410e7bb05f3f43c46d02a0409831eceb0d2`;
- the frozen R1 sample contained four validated events (START + COMPLETE for Crossref and SE4ALL); current executions emit run-specific OpenLineage events under `runtime-lineage/`, which are not overwritten into stable Git products.

DCAT:

- `catalog/catalog.dcat.jsonld` uses DCAT 3 vocabulary terms for Catalog, Dataset and Distribution.
- This R1 validates JSON structure and explicit field construction but does not yet claim SHACL-level DCAT conformance.

## Quality result

Final standing: **PASS**.

- Crossref member table: no duplicate/null primary-key rows; no member-level deposit count exceeded `total_members`.
- Crossref metadata table: no duplicate/null canonical primary-key rows; no checked `with_*` metric exceeded `n_dois`.
- SE4ALL: no duplicate/null primary-key rows; no bounded percentage metric exceeded the chosen tolerance.
- Preserved warning: `access_non_solid_fuel_urban_pop_pct` reaches 100.0180988; `transmission_and_distribution_losses_pct` reaches 213.0434783 and is explicitly excluded from the generic proportion rule.

## Analysis smoke outputs

The analytical step is descriptive and exists to prove downstream consumption, not to make causal claims.

Crossref:

- 122 countries satisfy the pilot threshold of at least 1,000 DOIs at the latest source date;
- Pearson correlation between member-level ROR-deposit share and work-level ROR-metadata share in that filtered set: approximately 0.486.

SE4ALL:

- source latest year: 2010;
- 251 country rows at that year;
- unweighted country mean renewable-energy share of total final energy consumption: approximately 28.53%;
- unweighted country mean electricity access: approximately 76.15%.

These values are evidence that the complete pipeline consumed the output products. They are not promoted to policy/scientific conclusions.

## Architectural result

The pilot validates the census choice:

- DuckDB + Parquet are sufficient for this workload;
- no Kafka/Redpanda, Iceberg, ClickHouse, QuestDB or Dagster activation is justified;
- external metadata/contract/lineage standards can be layered over existing thin local execution without creating a new Ordivon data protocol.

The next useful pressure test is a substantially larger or streaming GitHub/open dataset that can falsify this thin-stack conclusion.
