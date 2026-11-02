# Data Durable Preservation R1

Date: 2026-09-20

## Result

The Data Lifecycle pilots are no longer only reacquirable from GitHub. Their frozen raw bytes, derived Parquet products, runtime acquisition receipts, runtime OpenLineage events, contracts, catalog projection, quality reports, revision evidence, scripts and supporting documents have been admitted into the existing preservation system.

The accepted path is:

```text
exact data-lifecycle evidence
  -> E-ARK SIP/CSIP 2.2.0 (Commons-IP 2.11.3 create+validate)
  -> Archivematica 1.18 provider intake
     -> PREMIS/METS AIP
     -> Storage Service master
     -> Storage Service replicator
     -> Artefactual Fixity 0.8.0
```

No new Ordivon preservation package, database, receipt ontology or archive service was introduced.

## External owners

- ISO 14721:2025 OAIS: preservation reference model.
- E-ARK CSIP/SIP 2.2.0: interoperable submission package.
- Commons-IP 2.11.3: E-ARK creation and validation.
- Archivematica 1.18.0 + Storage Service: local preservation execution/AIP persistence.
- PREMIS 3.0 + METS: preservation metadata/package metadata.
- Artefactual Fixity 0.8.0: periodic Storage Service AIP fixity.
- NDSA Levels of Digital Preservation 2.1: evidence/gap assessment.
- RFC 8493: BagIt 1.0 authority boundary only.

## E-ARK submission

Canonical interoperable SIP SHA-256:

`1ab52c7380baaa6dd06af7955bfe1f992f1b1223e59dae618f28e9fc919b37ce`

Commons-IP validation produced:

- 135 PASS;
- 30 SKIP;
- 3 SHOULD-level metadata-folder warnings;
- 0 MUST failures.

The SIP contains the frozen data-lifecycle payload. OAIS permits ingest transformation from SIP to AIP, so the accepted claim concerns preserved information/content and provenance, not byte identity between SIP and AIP.

## Falsifier: ordinary zip intake

The first Archivematica transfer used `zipfile`.

It produced master AIP `cbf5ba8e-19ed-47bd-bc30-ca9189c9e172` and replica `20a0897b-ff13-492f-9493-89ccc696ad43`, whose outer AIP bytes matched and whose fixity later passed.

That is **not sufficient**.

The frozen source manifest found only 47/49 source files: both `.gitignore` files had been removed by the provider's hidden-file cleanup before ordinary ZIP package extraction.

That AIP pair is retained as negative evidence and is explicitly rejected for the exact-preservation claim.

## Accepted provider path

The existing creative-preservation corpus had already demonstrated that Archivematica's `zipped bag` intake causes package validation/extraction to occur at the correct provider stage for hidden-file survival.

R1 reused that provider path.

Important standards boundary: the current `bagit-python 1.9.0`/Archivematica adapter emits BagIt `0.97`. It is **not** claimed as RFC 8493 BagIt 1.0. E-ARK SIP 2.2.0 remains the standards-native interchange package; BagIt 0.97 is only an Archivematica provider adapter.

Accepted objects:

- Transfer: `3e436ef8-1e33-4dd3-94e4-cdb01faba513`
- Master AIP: `b482022d-9be3-44a4-847f-496adcb9014d`
- Replica AIP: `e2d63905-7355-4654-99d0-b1024de995c9`
- AIP size: 9,664,701 bytes
- Master/replica SHA-256: `43cd27dc86634fa64be4b56cf0d4720e81c7ee73c214be588cf6ce54eb2dfc15`
- Master/replica byte equality: PASS
- Frozen source files recovered exactly: **49/49 PASS**
- Hidden `.gitignore` source files: preserved
- AIP BagIt validation: PASS
- METS XML: PASS
- PREMIS namespace/events: PASS

The preserved corpus includes the previously volatile:

- raw CSV source bytes;
- derived Parquet files;
- runtime acquisition receipts;
- runtime OpenLineage START/COMPLETE events.

Therefore closing a Runtime workspace no longer destroys the only copy of the selected runtime evidence.

## Fixity

The existing scheduled preservation fixity service uses Artefactual Fixity 0.8.0.

A forced scan on 2026-09-20 scanned all six current AIPs and succeeded for all six, including the accepted Data Lifecycle master and replica.

The timer remains enabled.

## Operational boundary

This is **local durable preservation**, not an offsite disaster-recovery claim.

Master and replica use distinct Archivematica Storage Service locations but both are on the same machine/WSL failure domain.

A prior scheduled fixity run also failed while the Archivematica/Storage Service provider was stopped. After the existing compose stack was restored, the fixity scan passed.

So two residual preservation obligations remain:

1. independent failure-domain/offsite copy;
2. provider-liveness observability.

Neither justifies a new Ordivon archive protocol.

## Consequence

The previous distinction:

```text
source identity + digest
!=
durable preservation
```

is now executable.

For selected data products:

```text
source identity
 -> exact capture
 -> semantic/quality/lineage evidence
 -> E-ARK submission
 -> PREMIS/METS AIP
 -> master + replica
 -> scheduled fixity
 -> recoverable exact payload
```

This closes the local-persistence P0 while preserving explicit failure-domain limits.
