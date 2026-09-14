# Creative Preservation Standards Migration R8

Date: 2026-09-14

## Purpose

R8 is a **deletion/replacement migration**, not a new preservation maturity stage. R4-R7 demonstrated useful engineering facts; R8 removes remaining private preservation semantics where mature external standards now have a proven substitute.

## Standard package boundary

The forward external submission/interchange profile is now **E-ARK SIP 2.2.0 on E-ARK CSIP 2.2.0**, with Commons-IP 2.11.3 as the local proven creator/validator.

The exact frozen 12-work / 86-file corpus was packaged as one E-ARK SIP. Commons-IP returned:

```text
result      VALID
errors      0
MUST failed 0
```

The three failed recommendations are SHOULD-level metadata-folder recommendations. They remain validator-native evidence; R8 does not convert them into Ordivon package rules.

After removing Commons-IP's preserved input directory prefix, all 86 `ORIGINAL` files are SHA-256 byte-identical to the source and all three hidden `.gitignore` files survive.

## What was replaced

- custom preservation maturity language -> NDSA Levels 2.1 / DPC RAM v3 / CoreTrustSeal 2026–2028 assessment contexts;
- custom submission/package semantics -> E-ARK SIP/CSIP;
- custom package validation -> Commons-IP.

Historical R4-R7 standings remain evidence about the exact engineering experiments performed. They no longer define forward preservation maturity.

## What remains domain-local

Only the producing owner can decide which output is accepted and how its exact authoritative bytes are resolved. Git/CAS resolution therefore remains a thin owner adapter.

BagIt remains the current transport/Archivematica intake adapter. It is no longer treated as the canonical preservation package model.

## Enduro decision

Enduro v0.34.1 is registered as the first replacement candidate for recurring preservation ingest orchestration. It is not deployed now: the current path already works, no active Temporal service exists, and the upstream development environment would require adding Kubernetes/Tilt infrastructure solely for architectural cleanliness.

Before writing any new custom preservation ingest workflow/retry/decision code, pilot Enduro using this same E-ARK SIP fixture.

## Maturity non-claim

R8 intentionally assigns no NDSA Level, DPC RAM score or CoreTrustSeal status. Formal assessment must use the external frameworks' own current tools and evidence rules.

The official NDSA 2.1 matrix, guidance PDF and assessment XLSX have been pinned under `/opt/ordivon/external/standards/ndsa/2.1`. No cells have been filled and no Level has been inferred automatically.

Machine migration evidence: `artifacts/creative-preservation/standards-r8/migration-r8.json`.
