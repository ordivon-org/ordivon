# B04 — Workstation Tool Binding Projection Acceptance

Date: 2026-09-21
Status: ACCEPTED

Workstation remains the natural owner of node-local exact tool materialization evidence.

B04 adds only a rebuildable declared-binding index to the existing exact binding implementation.

## Separation

`project_declared_bindings()`:
- enumerates declared professional software and managed equipment;
- is deterministic;
- does not touch the filesystem to prove availability;
- marks each row DECLARED_UNRESOLVED;
- carries a catalog digest and projection digest.

Existing `resolve_professional` / `resolve_managed` remain the exact verification path for observed executable, SHA-256, execution target and version evidence.

Runtime still owns execution admission; consuming domains own suitability and semantic success.

## Verification

Current source catalog projects 31 declared candidates:
- 19 professional software bindings;
- 12 managed-equipment bindings.

Observed projection digest:
`sha256:6995738140d84944ab3f9270a840040fcd1f5cde2210669663647d0355060850`

Focused Workstation tests: 5/5 PASS, including existing exact-binding tests.
