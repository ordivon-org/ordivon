# Architecture Decision Index

This is a navigation index, not a new architectural authority or approval service. The current implementation, source revision, public contracts, consumer evidence and deployment receipts remain authoritative for their own claims.

| Decision area | Current reference | Status / use |
| --- | --- | --- |
| Dated deployed topology (2026-09-28) | [CURRENT_ARCHITECTURE.md](CURRENT_ARCHITECTURE.md) | Historical snapshot only; live installed source and Owner MCP status are authoritative |
| Repository layout migration | [STRUCTURE_R2.md](STRUCTURE_R2.md) | Partially deployed target, not current source truth |
| Owner dependency seams | [OWNER_DEPENDENCY_BOUNDARY_R1.md](OWNER_DEPENDENCY_BOUNDARY_R1.md) | Boundary guidance; check current owner/contract manifests |
| Test methods and upstream tools | [TESTING_UPSTREAM_ADOPTION_R1.md](TESTING_UPSTREAM_ADOPTION_R1.md) | Owner-scoped methodology guidance |
| Agent outcome contract and native acceptance | [AGENT_CONTRACT_EXECUTION_SPEC_R1.md](AGENT_CONTRACT_EXECUTION_SPEC_R1.md) | Current execution specification; Owner-native code/consumer verification remains separately required |
| Source-only classification vs Owner authority | [OWNER_MODULARITY_STRUCTURE_LIFECYCLE_PROGRAM_R1.md#8-2026-11-28-architecture-entropy-execution-checkpoint](OWNER_MODULARITY_STRUCTURE_LIFECYCLE_PROGRAM_R1.md#8-2026-11-28-architecture-entropy-execution-checkpoint) | Bounded E01 decision and execution checkpoint; source regions do not grant semantic authority |

Before a new ADR, look for an existing decision, implementation contract, migration acceptance or superseding record. Add a new bounded decision only if a concrete unresolved choice remains; record the source cut, alternatives, rejected options, consumers, falsifiers and supersession links. Avoid turning this index into another registry.
