# Provider: Artifact v2

- Source: `/root/projects/ordivon-artifact-v2`
- Observed revision: `e06b17a517c4`
- Current standing: accepted forward source authority for Artifact Build & Delivery
- Role: artifact construction/validation/package/delivery preparation capability provider
- Migration mode: metadata/evidence registration only

## Characteristics worth preserving

- standards-first and external-validator-first;
- no universal document AST;
- native/provider formats remain authoritative where appropriate;
- OCI/OPA used instead of custom package/gate machinery where possible;
- SLSA/in-toto provenance used rather than private provenance schema;
- formal visual/accessibility/release gates remain independent and fail closed.

## Boundary

Artifact build success does not imply release readiness or distribution/provider acceptance.
