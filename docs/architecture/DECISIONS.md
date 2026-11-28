# Architecture Decision Index

This is a navigation index, not a new architectural authority or approval service. The current implementation, source revision, public contracts, consumer evidence and deployment receipts remain authoritative for their own claims.

| Decision area | Current reference | Status / use |
| --- | --- | --- |
| Dated deployed topology (2026-09-28) | [CURRENT_ARCHITECTURE.md](CURRENT_ARCHITECTURE.md) | Historical snapshot only; live installed source and Owner MCP status are authoritative |
| Repository layout migration | [STRUCTURE_R2.md](STRUCTURE_R2.md) | Partially deployed target, not current source truth |
| Owner dependency seams | [OWNER_DEPENDENCY_BOUNDARY_R1.md](OWNER_DEPENDENCY_BOUNDARY_R1.md) | Boundary guidance; check current owner/contract manifests |
| Whole-repository architectural convergence | [OWNER_MODULARITY_STRUCTURE_LIFECYCLE_PROGRAM_R1.md](OWNER_MODULARITY_STRUCTURE_LIFECYCLE_PROGRAM_R1.md) | Existing stock-first execution program; preserve real consumers, use risk-tiered verification, and retire superseded implementations |
| Test methods and upstream tools | [TESTING_UPSTREAM_ADOPTION_R1.md](TESTING_UPSTREAM_ADOPTION_R1.md) | Owner-scoped methodology guidance |
| Agent outcome contract and native acceptance | [AGENT_CONTRACT_EXECUTION_SPEC_R1.md](AGENT_CONTRACT_EXECUTION_SPEC_R1.md) | Current execution specification; Owner-native code/consumer verification remains separately required |

Before a new ADR, look for an existing decision, implementation contract, migration acceptance or superseding record. Add a new bounded decision only if a concrete unresolved choice remains; record the source cut, alternatives, rejected options, consumers, falsifiers and supersession links. Avoid turning this index into another registry.


## Architecture convergence checkpoint — 2026-11-28

This is a dated execution coordinate, not a second task registry. Continue the
existing program and natural Owner work/PRs. The user-directed target is one
authoritative implementation per business concept, deep modules, explicit
dependency direction, local change, safe deletion and enforceable contracts.
Preserve externally observable behavior and existing authorization boundaries.

- Baseline: Git main `08d72a93cecc8bbd43ecf87653eeb6777ae8065a`;
  5,908 tracked paths and 21 registered Owners. The existing Owner-boundary
  guard passed (3,001 active files, 44 declared seams, 53 references).
  The 22 distinct declared directions include two nontrivial strongly
  connected components when test/research seams are included; the five
  public/read-only projection directions contain no cycle. This is a bounded
  declared-source graph, not a complete dynamic call or state-write census.
- Completed source slice: [Harness PR #2991](https://github.com/ordivon-org/ordivon/pull/2991),
  commit `3d28bd0f27ae1afa5f1d6adf62290e27f0dc4d74`.
  Reuse the already-documented `wake_turn_contract.py` value validators,
  remove the two duplicate implementations, retain real import consumers
  and domain-specific exceptions. Baseline 105 passed; candidate 106 passed
  and 5 subtests; 51 disposable-PostgreSQL cases skipped in both runs.
  The new regression failed before the change and passed afterward.
  This is source delivery, not merged or installed acceptance.
- Existing next work: use the active
  [risk-tiered policy PR #2904](https://github.com/ordivon-org/ordivon/pull/2904)
  instead of opening a competing program revision. Examine actual
  compile/runtime versus test/research dependency edges, finish existing
  replacement and retirement branches before new redesigns, and qualify
  preserved public consumers before removal. Keep independent release
  carriers and historical migrations unless their actual distribution or
  replay obligations can be preserved by a simpler implementation.

Do not duplicate this checkpoint in an additional architecture database.
The existing program, Git changes, protected CI, and Host collaboration
receipts carry the remaining execution obligations.
