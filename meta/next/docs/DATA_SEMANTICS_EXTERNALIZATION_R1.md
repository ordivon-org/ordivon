# Data Semantics Externalization R1

Date: 2026-09-20  
Applies to: `scripts/data_lifecycle_github_pilot.py` and `evidence/data-lifecycle/github-pilot-r1/`

## 1. Purpose

Replace pilot-local semantic heuristics with explicit external owners and source-bound metadata.

The motivating failures were real:

1. a nullable Crossref dimension was initially treated as an always-present primary-key component;
2. columns ending in `_pct` were initially treated as if the percent unit implied a universal 0..100 validity range.

Both are category errors. A data system must distinguish:

- physical representation;
- statistical role;
- source missingness semantics;
- units of measure;
- quantity semantics;
- use-case-specific quality thresholds.

## 2. External owners

| Concern | External owner | Local role |
|---|---|---|
| statistical dimensions / measures / attributes | SDMX 3.1 | semantic structure |
| unusual / missing observation status | SDMX CL_OBS_STATUS 2.3 | status vocabulary only when source evidence exists |
| unit code | UCUM | machine unit code, e.g. `%` |
| unit / quantity vocabulary | QUDT Units 3.5.1 | semantic unit URI |
| data quality measurement | ISO/IEC 5259-2:2024 | quality-model owner; thresholds remain fitness-for-use policy |
| contract schema / keys / semanticType | Bitol ODCS 3.2.0 | executable producer/consumer contract |

No new Ordivon ontology, unit system, missing-value code list, or generic data-quality vocabulary is created.

## 3. Missingness rule

### Crossref `document_subtype`

The source dictionary makes subtype applicable only to posted-content records. Therefore:

- the source `document_subtype` column remains nullable;
- null is not rewritten as a claimed SDMX observation-status value;
- a separate physical helper `document_subtype_key` is derived only for deterministic composite-key materialization;
- the ODCS contract records that derivation.

This preserves:

```text
source semantic dimension != physical key helper
```

### SE4ALL NA values

The source supplies NA/null observations but no observation-status code. Therefore:

```text
null observed
!=
reason for null known
```

No CL_OBS_STATUS code is invented.

## 4. Unit and range rule

UCUM defines percent as a dimensionless unit scaled by 10^-2. It does not make every percent-valued quantity a mathematical proportion bounded by 100.

Therefore the executable quality layer is driven by the semantic profile:

- population share -> explicit 0..100 range;
- renewable share -> explicit 0..100 range;
- capacity share -> explicit 0..100 range;
- energy ratio -> no upper bound inferred from `%`;
- transmission/distribution loss ratio -> no upper bound inferred from `%`.

The `0.1` percentage-point tolerance used on bounded source percentages is recorded as a pilot fitness-for-use threshold, not attributed to UCUM, QUDT, SDMX, or ISO.

## 5. Contract projection

ODCS `semanticType` is now emitted explicitly:

- statistical/key dimensions -> `dimension`;
- numeric non-dimensions -> `measure`;
- other fields -> `column`.

Quality-critical SE4ALL measures also carry:

- `unitUcum`;
- `unitQudt`;
- `quantitySemantics`.

The Crossref nullable dimension and derived physical key carry their source-null and normalization metadata as contract custom properties.

## 6. Acquisition identity

Source identity and transport are now separate.

Identity:

```text
GitHub repository
+ exact Git commit
+ repository path
+ expected SHA-256
```

Transport may be canonical GitHub raw content or a mirror. A transport is accepted only if the downloaded bytes match the frozen SHA-256.

This prevents network routing/CDN choice from changing provenance.

## 7. Executable result

The same frozen data were clean-replayed after externalization.

Results:

- source SHA-256 values unchanged;
- derived Parquet SHA-256 values unchanged;
- ODCS contracts validate against official ODCS 3.2.0 schema;
- semantic measure violations: 0;
- quality standing: PASS;
- the previous `213.0434783` transmission/distribution-loss value remains preserved;
- no suffix-based percentage-range heuristic or dataset-name-specific key heuristic remains in the pilot executable.

## 8. Boundary

This R1 does not claim full SDMX dataset serialization, QUDT ontology conformance, or ISO/IEC 5259 certification.

It proves the narrower and more important migration:

```text
hand-written semantic guesses
        ->
source-bound metadata + mature external semantic owners + executable ODCS checks
```

Future domains should extend the semantic profile only where source documentation or a domain authority establishes the meaning. Unknown semantics remain unknown.
