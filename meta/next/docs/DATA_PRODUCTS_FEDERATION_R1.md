# Data Products Federation R1

Date: 2026-09-20

## Result

Two real domain workloads now own standards-native data-product metadata:

- Research: Paper1 frozen flaky-test benchmark.
- Finance: read-only Binance + OKX public crypto shadow observation.

The domain repositories own the product and contract. `ordivon-next` owns only the federated projection.

```text
domain source
  -> ODCS 3.2.0 contract
  -> ODPS 1.1.0 product/output port
  -> DCAT 3 federated discovery
  -> PROV-O source/product/derivation graph
```

No Ordivon-specific data-product schema or catalog ontology was added.

## Research

Repository revision: `dbe832f0483f49eaceeb58e4fb935265f280cb8e`

Product: `94d0bf2c-036b-53b1-b733-14d3a5536a74`

Contract: `4596a0eb-a009-53a6-af75-02189195225b`

Frozen source: `sha256:6c2066eb1bf1824887a72c6f6df3cb5106894efde206686eb564287fe6547e50`

Observed facts:

- 87,875 rows;
- 29 projects;
- 86,200 distinct `(project,testCase)` pairs;
- 1,385 flaky rows;
- 61 downstream files in the frozen Paper1 corpus explicitly reference the exact dataset digest.

The ODCS contract intentionally does not invent a physical primary key.

The frozen robustness result `sha256:37a092e36c0d31bad0e66f7992812537b3e99abc7037d685182743df62b1e10c` contains the exact dataset digest in result rows, giving a real data -> analysis-result provenance edge.

## Finance

Repository revision: `74055044fcb72e917f33404bbe08fd902f368c44`

Product: `d14d7457-c9aa-59e0-8bf5-7783cea39c1c`

Contract: `5de34add-dca7-54eb-ada3-5e657a7c3ff3`

Frozen source: `sha256:ed5fba6227a5d997adefb6bf63717463dc75fdc8b62cfb0005804109eb0a2d7e`

Observed facts:

- Binance + OKX;
- BTC + ETH;
- 4 accepted snapshots;
- 3 measured windows;
- broker credentials used: false;
- private account data used: false;
- external financial writes attempted: false.

The product is `consumerAligned` because it packages a bounded cross-venue observation for downstream monitoring/analysis rather than mirroring one provider-native source.

Its ODPS context explicitly prohibits turning observation metadata into trade authorization, alpha/arbitrage claims, or private-account inference.

## DCAT federation

`federated-catalog.dcat.jsonld` is a W3C DCAT 3 projection with one Catalog, two Dataset resources, and two Distribution resources.

The Distribution access URLs point to domain-owned local files. The central catalog is discovery metadata only and does not become the data owner.

## PROV boundary

`product-provenance.prov.jsonld` uses W3C PROV-O.

Proven:

- Research source -> Research product version;
- Research source -> Paper1 robustness activity -> robustness result;
- Finance public-shadow evidence -> Finance product version;
- Finance capture activity -> public-shadow evidence.

Not yet proven:

- a post-registration Finance claim/decision/action that explicitly records the consumed product ID + version.

That gap stays open. Product registration is not counted as decision feedback.

## Operational conclusion

The earlier P0 `ODPS products + federated DCAT + domain adoption` is closed for the selected Research and Finance workloads.

Remaining cross-domain P0 work is narrower:

```text
rights/privacy/retention
+
exact product-version -> claim/decision/action
+
outcome -> collection/quality/model feedback
```

A catalog service remains workload-gated. Two products do not justify deploying one.
