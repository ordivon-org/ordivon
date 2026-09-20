# Ordivon Artifact Build & Delivery E2E v2

Independent source authority for Artifact Build & Delivery.

This repository was split from the historical Workstation source because artifact construction, format-specific validation, package assembly and Artifact workflow semantics are not workstation responsibilities.

The architecture is standards-first and external-first: native formats and mature validators/writers remain replaceable implementation selections. Ordivon retains only thin contracts, format-specific orchestration, evidence binding, trust gates and durable-workflow integration specific to Artifact Build & Delivery.

See `docs/artifact-build-delivery-e2e-v1.md` and `docs/artifact-build-delivery-e2e-toolchain-v1.md` for the accepted responsibility boundary and current external tool selections.

## Current standing

The repository is the accepted forward Artifact Build & Delivery source authority. The live Temporal worker, Artifact Python stable runtime and OpenXML stable validator have all been converged from this tree. See `docs/SOURCE_AUTHORITY_ACCEPTANCE_20260912.md`.
