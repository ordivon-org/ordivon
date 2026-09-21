# Media / Capital source-carrier alignment acceptance — 2026-09-21

Standing: **ACCEPTED_SOURCE_ONLY**

Scope: align the standalone source-carrier main refs for Media and Capital to the exact source revisions already frozen, validated, and imported by the monorepo migration. This record does not add new owner behavior, does not change production state, and does not retire either standalone repository.

## Capital

Before alignment:

- standalone main: 8590c3eeb7d2712a1f796a70c839a7d3cbda0ff8
- accepted migration source: 918fd86a3ebe69bb0e05835d7e4c656731da0833
- relationship: standalone main is the direct ancestor of the accepted source
- accepted source tree: 451cf539f01c5fdbc00349878a249b232d3afad4
- monorepo domains/capital tree: 451cf539f01c5fdbc00349878a249b232d3afad4

The single accepted-only commit is the Python 3.14 Ruff conformance cleanup already covered by the Wave 3 source acceptance. Capital main advanced by --ff-only to 918fd86a. The standalone main tree now equals the canonical monorepo owner tree exactly.

Existing Wave 3 owner-native evidence remains the qualification boundary:

- Python 3.14.7
- Ruff: PASS
- 201 tests: PASS
- no financial-write production cutover implied

## Media

Before alignment:

- standalone main: 300ce04ea669c0f029f7a67277a5f2e1bdb6f817
- accepted migration source: 30f6d1228a4270a68cd715ca9a7b17742478958e
- relationship: standalone main is the direct ancestor of the accepted source
- accepted source tree: ccae1747b73569bead57836e6764f12763cbb710
- original rewritten import owner tree: ccae1747b73569bead57836e6764f12763cbb710

The single accepted-only commit scopes Media to task-activated mediation and was already covered by the M2 source acceptance. Media main advanced by --ff-only to 30f6d122.

The current monorepo capabilities/media tree is deliberately not equal to the standalone Media base tree. After source import, the monorepo accepted:

1. an append-only Creative Library functional slice;
2. a forward Media refactor that hosts the projection without acquiring source truth;
3. later forward cleanup that removes workstation-lab from future atlas discovery.

Creative Library therefore acts as a Media-hosted disposable catalog/presentation projection. Historical work identity and exact source-byte authority remain owner-native. The monorepo-only overlay is intentional forward composition, not source drift and not a reason to rewrite or back-port the standalone source carrier.

Existing Media evidence remains split by exact tree identity:

- M2 frozen Media base: 155 Python tests PASS, Ruff PASS, typecheck PASS, Vite build PASS, cold-start PASS
- Creative Library integrated Media tree: 165 tests PASS, cold-start PASS, typecheck PASS, Vite build PASS, source-boundary checks PASS

## Concurrency boundary

Relevant Runtime workspaces were inspected before moving either main ref. The Media and Capital migration workspaces are detached from the source-repository main refs. The separate dirty Capital market workspace is also detached and was not modified.

## Retirement boundary

These fast-forwards reduce source-carrier drift but do not retire either old repository. Physical retirement requires a separate residual-consumer census covering active workspaces, processes, services, scripts/configuration, recovery relations, archive/provenance requirements, and rollback authority.

No deployment, service restart, credential change, trading effect, publication effect, or external side effect is authorized by this acceptance.
