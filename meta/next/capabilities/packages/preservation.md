# Package: Digital Preservation

Last census: 2026-09-14
Standing: **READY_FOR_REAL_WORK / STANDARD-NATIVE**

## Outcome scope

Preserve selected digital objects so that exact authoritative content, preservation metadata, storage integrity and recovery evidence remain usable for the required community and time horizon without turning Ordivon into a preservation repository implementation.

## Domain-owned residual

The producing domain still owns two decisions that generic preservation software cannot infer:

1. which output is accepted as the object to preserve;
2. where the exact authoritative bytes for that accepted output are obtained.

Everything after that boundary should prefer established preservation standards and systems.

## Mature external knowledge owners

- ISO 14721:2025 OAIS for archive responsibilities/reference terminology;
- ISO 20652:2006 PAIMAS for Producer–Archive interaction/submission methodology;
- ISO 20104:2015 PAIS for formal SIP definition, packaging and validation;
- E-ARK CSIP/SIP 2.2.0 for interoperable Information Package structure;
- PREMIS/METS for preservation metadata/provenance;
- PRONOM + Siegfried for format identification;
- NDSA Levels of Digital Preservation 2.1 for technical preservation-program assessment;
- DPC RAM v3 for broader organizational maturity assessment;
- CoreTrustSeal Requirements 2026–2028 for trustworthy-repository requirements/certification context.

Historical Ordivon `R4/R5/R6/R7` labels are engineering migration/graduation history. They are **not** a preservation maturity model and must not substitute for NDSA/DPC/CoreTrustSeal assessment.

## Current local providers

- Commons-IP 2.11.3 — proven E-ARK SIP creator/validator;
- Archivematica 1.18 + Storage Service — graduated preservation engine/storage/fixity/replication/recovery path for the current corpus;
- Siegfried/PRONOM — formal format identification;
- Artefactual Fixity — API-driven periodic fixity client;
- systemd — timing/process execution only;
- Enduro — triggered replacement candidate for preservation ingest orchestration, not locally active.

## Submission/interchange routing

```text
owner-approved object + exact authoritative bytes
        |
        +--> external submission/interchange
        |      -> E-ARK SIP 2.2.0
        |      -> Commons-IP validation
        |
        +--> current local preservation engine
               -> Archivematica provider-native standard transfer
               -> provider-native AIP / PREMIS / METS / fixity
```

E-ARK SIP is the canonical external submission/interchange profile. The current local Archivematica adapter does **not** translate E-ARK into a private format and is not claimed to ingest E-ARK directly; Archivematica natively accepts ordinary source directories as a `standardTransfer`, so the same authoritative owner bytes can be submitted through the provider-native intake. BagIt remains an Archivematica-internal/engine transport concern rather than an Ordivon package ontology.

## Assessment routing

```text
technical preservation practice
  -> NDSA Levels 2.1 official assessment materials

organization/program maturity
  -> DPC RAM v3

trustworthy repository requirements/certification
  -> CoreTrustSeal 2026–2028

formal audit/certification beyond these
  -> applicable external repository/audit regime
```

Do not infer an NDSA level, DPC RAM score or CoreTrustSeal standing from historical local receipts. A formal assessment must use the external framework and its evidence requirements.

Official NDSA 2.1 assessment materials are pinned at `/opt/ordivon/external/standards/ndsa/2.1`.

## Current bounded gaps

- no independent/off-site preservation failure domain is graduated;
- pointer schema-conformance remains an upstream boundary;
- direct E-ARK ingestion by Archivematica is not established or required by the current local routing; E-ARK and Archivematica standard transfer are separate views over the same authoritative bytes;
- Enduro is not activated because a repeated durable ingest-orchestration need is not yet proven;
- no CoreTrustSeal certification is claimed.

## Acceptance workload

For future preservation changes, reuse the frozen 12-work / 86-file heterogeneous corpus and require external-standard evidence. New local semantics are allowed only after a specific mature-standard/provider substitution failure is reproduced.

## Retired local implementation — 2026-09-14

The historical `creative_forward_ingest.py` BagIt/receipt/catalog implementation and its private dependency environment have been removed from the active workstation. R4/R5 bags/receipts remain historical evidence only. Forward package semantics are E-ARK/Commons-IP; no custom preservation catalog is maintained.

## Engineering closeout — 2026-09-14

The capability is closed to architecture-driven development. The Archivematica local stack now uses Compose-native `restart: unless-stopped`; a Docker daemon restart recovered all nine services, both AIPs retained fresh fixity PASS, and scheduled Fixity remained operational. Reopen only on the workload/provider triggers listed in the final R10 migration record.
