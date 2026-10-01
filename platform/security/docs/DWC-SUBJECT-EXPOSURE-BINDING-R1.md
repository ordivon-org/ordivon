# DWC Subject & Exposure Binding R1

Date: 2026-10-01
Status: DW01 CANDIDATE / TASK-LOCAL PROJECTION / NO ASSET REGISTRY

## Decision

DW01 does not create a CMDB, asset daemon, product ontology, scanner, or global exposure truth.

It composes exact observations from natural owners into one digest-bound defense-epoch projection:

    owner-native product/component identity
    + deployed-instance identity
    + exact version/config observations
    + service/endpoint observations
    + point-in-time or owner-declared currentness
            |
            v
    DWC SubjectExposureSnapshot
            |
            v
    DW02 applicability binding

The snapshot is disposable and rebuildable. Every input observation remains attributable to its owner and source reference.

## External alignment

DW01 uses mature external concepts by reference rather than copying their registries:

- NIST CSF 2.0 ID.AM for hardware/software/service/system inventory and authorized communication/data-flow outcomes.
- NIST SP 800-53 CM-8 for system-component inventory accountability and organization-selected granularity.
- CycloneDX 1.7 component/service identities where an SBOM or Service BOM is already the natural owner; purl, CPE, SWID, hashes and service endpoints remain provider-native values.
- NIST CPE 2.3 only when a vulnerability/product source naturally supplies CPE. DW01 does not turn CPE into deployed-instance identity.
- OpenTelemetry Resource/Semantic Conventions for service namespace/name/version/instance identifiers when telemetry owners already provide them.
- CSAF 2.0 product-tree/product IDs when DW02 later binds vendor advisory product status.

No one identifier is universal: product identity, software component identity, deployed service instance and reachable endpoint are separate facts.

## Input observation law

Every identity or exposure observation names:

- observation ID;
- natural owner;
- source reference;
- source kind;
- currentness standing;
- optional observation time;
- evidence references.

Identity observations additionally bind a task-local dimension to an opaque scheme/value identity reference.

Exposure observations bind:

- surface ID;
- endpoint reference;
- probe origin scope;
- optional transport;
- reachability: REACHABLE, UNREACHABLE, or UNKNOWN.

UNREACHABLE means only that this exact observation did not reach this exact surface from this exact origin. It is never promoted to globally NOT_EXPOSED.

## Currentness law

DW01 reuses the established Ordivon currentness vocabulary:

- CURRENT_DECLARED
- POINT_IN_TIME_OBSERVED
- HISTORICAL_NOT_CURRENT
- CURRENTNESS_UNKNOWN

The projection does not mint any of these. The caller supplies owner-derived or current point-in-time evidence.

A snapshot can remain mechanically complete while carrying a MIXED_HORIZON; downstream consumers must decide whether that horizon is admissible for their claim.

## Mechanical coverage

The caller names required identity dimensions and expected exposure surfaces.

DW01 projects per-item coverage and a mechanical binding standing:

- COMPLETE
- INCOMPLETE
- CURRENTNESS_UNKNOWN
- HISTORICAL_ONLY

This standing means only that the caller-requested binding inputs are mechanically present/current enough to be carried forward. It is not vulnerability applicability, security acceptance, asset completeness, or risk.

## Invalidation

Every normalized observation has a canonical digest. The snapshot carries sorted input observation digests and a canonical snapshot digest.

A changed owner observation therefore changes the snapshot identity. Dependency-aware invalidation belongs to DW10; DW01 does not run a background monitor or invalidate other work by itself.

## Non-claims

DW01 does not establish:

- organization-wide asset inventory completeness;
- vulnerability applicability;
- global internet exposure;
- security posture;
- authorization;
- effect permission;
- domain acceptance;
- permanent freshness.

It deliberately preserves UNKNOWN, mixed observation horizons, and owner-specific identity schemes.
