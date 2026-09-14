# Preservation Standard-Native R1

Date: 2026-09-14

## Decision

Preservation no longer uses an Ordivon-native maturity vocabulary or package model.

Forward boundaries:

```text
domain owner
  -> accepted object + exact authoritative bytes
       |
       +-> PAIMAS/PAIS-informed external submission profile
       |    -> E-ARK SIP 2.2.0 -> Commons-IP validation
       |
       +-> provider-native preservation intake
            -> Archivematica standard transfer
            -> provider-native PREMIS/METS/AIP/fixity/replication/recovery evidence
```

Historical `R4/R5/R6/R7` and `ACCEPTED_BOUNDED` labels remain valid only as engineering migration/graduation history. They do not state an NDSA Level, DPC RAM maturity score, CoreTrustSeal standing or repository certification.

## E-ARK workload proof

Commons-IP 2.11.3 generated an E-ARK SIP 2.2.0 from the exact R6 frozen corpus:

- 86 files;
- 4,200,279 source bytes;
- 86/86 exact SHA-256 preservation in the `ORIGINAL` representation;
- three hidden `.gitignore` files preserved;
- validation result `VALID`;
- validation errors = 0;
- E-ARK MUST failures = 0;
- three SHOULD-level metadata-layout warnings were retained as external-validator output rather than converted into private Ordivon requirements.

This proves E-ARK/Commons-IP is sufficient for the forward package/interchange semantic boundary for this workload.

## Adapter boundary

Archivematica 1.18 natively supports an ordinary directory `standardTransfer`. Therefore the forward path does not require an E-ARK-to-Archivematica conversion layer:

- **E-ARK SIP** = canonical external submission/interchange profile, created/validated when an interoperable package is required;
- **Archivematica standard transfer** = current local provider-native preservation intake over the same exact authoritative bytes;
- **BagIt** = provider-internal/engine transport and AIP packaging concern;
- no claim is made that Archivematica directly ingests E-ARK SIP.

Do not extend the old custom handoff receipt into a package ontology and do not create a private E-ARK-to-Archivematica converter.

## Maturity assessment boundary

Use external frameworks rather than a private standing:

- NDSA Levels of Digital Preservation 2.1 — technical preservation-program assessment;
- DPC RAM v3 — broader organizational preservation maturity;
- CoreTrustSeal Requirements 2026–2028 — trustworthy repository requirements/certification context;
- OAIS — archive responsibility/reference terminology.

No level/score/certification is asserted in R1. The official assessment tools must be used before such claims are made.

The official NDSA 2.1 matrix, assessment guidance and assessment XLSX are locally pinned read-only under `/opt/ordivon/external/standards/ndsa/2.1`; they are external assessment materials, not an Ordivon scoring implementation.

## Ingest orchestration boundary

Enduro v0.34.1 is the first replacement candidate if preservation ingest orchestration becomes a maintained recurring concern. It already owns preservation-domain durable workflows and requires Temporal.

It is **not locally activated now** because the current graduated path works, this workstation has no active Temporal service or Kubernetes/Tilt development substrate, and deployment would currently add more infrastructure than it removes.

Rule: **before writing new custom preservation ingest workflow/retry/decision code, pilot Enduro against the frozen E-ARK SIP fixture.**

## What remains Ordivon-specific

Only:

1. select the domain-approved object;
2. resolve exact authoritative bytes;
3. bind the object to the applicable external submission/profile policy;
4. select providers;
5. independently verify external outcomes and preserve evidence references.

Everything else stays with standards/providers unless a concrete substitution failure is demonstrated.
