# Ordivon Execution Fabric R1

Status: RETIRED 2026-09-19

Execution Fabric R1 was an experimental decomposition vocabulary. It is no longer a Runtime
schema or architecture authority.

The experiment was useful for exposing several separations:
- capability is not authorization;
- OS privilege is not identity;
- Runtime physical execution is not workflow orchestration;
- provider availability is not semantic completion;
- desired/current reconciliation belongs to the state owner.

Those lessons survive through standards-first boundaries, not through an Ordivon ontology.

The former ordivon-runtime-spi crate and runtime.describe.executionFabric projection were
deleted after consumer audit found no external repository consumer and no irreducible state.

Use Runtime's native runtime.describe node/target/provider fields for Runtime facts and route
other concerns to their mature owners.
