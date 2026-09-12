# Ordivon Artifact Build & Delivery E2E v2

Independent source authority for Artifact Build & Delivery.

This repository was split from the historical Workstation source because artifact construction, format-specific validation, package assembly and Artifact workflow semantics are not workstation responsibilities.

The architecture is standards-first and external-first: native formats and mature validators/writers remain replaceable implementation selections. Ordivon retains only the thin contracts, format-specific orchestration, evidence binding, trust gates and durable-workflow integration that are specific to Artifact Build & Delivery.

See  and  for the accepted responsibility boundary and current external tool selections.
