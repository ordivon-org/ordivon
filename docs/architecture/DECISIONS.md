# Architecture Decision Index

This is a navigation index, not a new architectural authority or approval service. The current implementation, source revision, public contracts, consumer evidence and deployment receipts remain authoritative for their own claims.

| Decision area | Current reference | Status / use |
| --- | --- | --- |
| Deployed system topology | [CURRENT_ARCHITECTURE.md](CURRENT_ARCHITECTURE.md) | Rebuildable deployed projection; validate against actual installation |
| Repository layout migration | [STRUCTURE_R2.md](STRUCTURE_R2.md) | Partially deployed target, not current source truth |
| Owner dependency seams | [OWNER_DEPENDENCY_BOUNDARY_R1.md](OWNER_DEPENDENCY_BOUNDARY_R1.md) | Boundary guidance; check current owner/contract manifests |
| Test methods and upstream tools | [TESTING_UPSTREAM_ADOPTION_R1.md](TESTING_UPSTREAM_ADOPTION_R1.md) | Owner-scoped methodology guidance |
| Source migration acceptance | [SOURCE_MIGRATION_STANDING.md](../migration/acceptance/SOURCE_MIGRATION_STANDING.md) | Dated evidence; do not assume still current |

Before a new ADR, look for an existing decision, implementation contract, migration acceptance or superseding record. Add a new bounded decision only if a concrete unresolved choice remains; record the source cut, alternatives, rejected options, consumers, falsifiers and supersession links. Avoid turning this index into another registry.
