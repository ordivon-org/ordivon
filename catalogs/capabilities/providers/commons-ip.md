# Provider: Commons-IP

Status: **LOCALLY PROVEN / E-ARK PACKAGE CREATOR + VALIDATOR**
Role: mature E-ARK Information Package construction and conformance validation provider.

## Current upstream/local identity

- project: `keeps/commons-ip`;
- version: `2.11.3`;
- release date: 2026-07-22;
- tag commit: `2c80cd9cfec63e3efa0fea6b9dcf7ef9fccbe97a`;
- installed JAR: `/opt/ordivon/external/commons-ip/2.11.3/commons-ip2-cli-2.11.3.jar`;
- official release SHA-256: `ac3e93d0fc74be553b6a38afc0fa91a1504ac0f56ceab5c6684ab4d662dc30f9`;
- E-ARK support observed in the CLI: SIP 2.0.4, 2.1.0 and 2.2.0; current default 2.2.0.

## R8 proof

The frozen Creative Preservation corpus was converted into one E-ARK SIP 2.2.0 and validated by Commons-IP itself.

Evidence:

- 86 source files / 4,200,279 bytes;
- all 86 exact original SHA-256 values survive in the `ORIGINAL` representation;
- all three hidden `.gitignore` files survive;
- validator summary: `VALID`, errors = 0;
- E-ARK MUST requirements: 0 failures;
- three SHOULD-level metadata-layout warnings remain and are not upgraded into Ordivon-specific package rules.

The SIP is an interoperability proof and migration fixture, not a new Ordivon package format.

## Boundary

Commons-IP owns E-ARK package construction/validation mechanics. Ordivon may select source bytes and choose the applicable submission profile, but must not copy E-ARK METS/package semantics into a private schema.

The current Archivematica 1.18 production path still receives a BagIt/ZIP engine-specific handoff. E-ARK is now the **canonical external submission/interchange profile**, while BagIt remains a transport/engine adapter until an E-ARK-consuming ingest path is graduated.
