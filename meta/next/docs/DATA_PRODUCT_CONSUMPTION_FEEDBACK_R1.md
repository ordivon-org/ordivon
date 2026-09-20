# Data Product Consumption & Feedback R1

Date: 2026-09-20

## Result

The selected Research and Finance products now have a real post-registration consumption path.

External owners remain separate:

- ODPS / ODCS: product and contract;
- DCAT 3: federated discovery;
- ODRL 2.2: governance policy;
- OpenLineage 2-0-2: operational Job/Run/Dataset events;
- W3C PROV-O: semantic derivation;
- domain evidence: claim, decision, action, outcome and feedback content.

No new Ordivon lineage or feedback ontology was introduced.

## Research

Current repository revision:

`18a8afae92ae2ef3b89d645bbcccf6db51db1b9d`

The Paper1 consumer verifies:

- product ID `94d0bf2c-036b-53b1-b733-14d3a5536a74`;
- product version `1.0.0`;
- frozen source digest `6c2066eb...`;
- pre-existing robustness-result digest `37a092e3...`;
- 6,960 / 6,960 result rows bind the exact frozen dataset digest.

The runtime lineage is intentionally:

```text
Paper1 product version
+ pre-existing robustness result
      ↓
binding-verification activity
      ↓
verification artifact
```

It does **not** claim that the verification run generated the scientific robustness result.

OpenLineage run:

`b07502e6-b0da-58ba-91e8-6e85043f8f31`

## Finance

Current repository revision:

`14885beb2b566458123dd9f273a66884fb337017`

The post-registration consumer uses the exact public-shadow product version and produces a new decision/outcome/feedback artifact.

Decision:

`NO_EXECUTION_OR_DIRECTIONAL_ACTION_ADMITTED`

Action:

`NO_EXTERNAL_EFFECT`

Outcome:

`PASS_BOUNDARY_PRESERVED`

Feedback:

- keep current public-observation collection boundary;
- keep frozen 1200 ms source/receive coherence gates;
- do not update a directional model from this product;
- keep fail-closed rights/retention governance;
- `changeRequired=false`.

This is a valid feedback disposition, not evidence of adaptive optimization. A non-trivial outcome that forces an actual policy change remains unproven.

OpenLineage run:

`db63ce70-d168-5dfd-b76f-55419d25bea6`

Decision artifact SHA-256:

`6cafaf913b639d6b4652ef34838860f78fb93b15a28faeb5891da7980ea2a402`

No external financial write or private endpoint action was performed by this consumption.

## Cross-system validation

The acceptance gate re-read the current domain repositories and proved:

- repository revisions match the central acceptance record;
- domain receipt/artifact hashes match central references;
- 4 / 4 OpenLineage events validate against the pinned OpenLineage 2-0-2 JSON Schema;
- PROV-O graph parses and contains the two post-registration consumption activities.

## P0 closure boundary

For the selected Research and Finance products:

`SelectedResearchFinanceLifecycleP0 = CLOSED_WITH_BOUNDED_EVIDENCE`

This does not mean the entire Ordivon data lifecycle is complete.

`CrossDomainDataLifecycle = PARTIAL`

Remaining P1 work includes:

- source-right resolution;
- formal privacy assessment;
- authorized retention schedules;
- independent/offsite preservation;
- broader real-domain adoption;
- business-value outcomes;
- one non-trivial feedback event that actually changes collection, quality or model policy.
