# Module Definition Template v2

## Purpose

This template upgrades the earlier task-first system into a module-definition system that starts from philosophy and ownership.

Use it when a piece of work is large enough to be treated as a module or sub-module rather than a one-off task.

It exists to force this order:

1. what do we believe?
2. which layer owns that belief?
3. is this `Core`, `Pack`, or `Adapter`?
4. what may this module never do?

## When To Use This

Use this template for:

- new modules
- module rewrites
- staged extraction work
- registry/contract work
- pack/adapters ownership changes
- any task that risks re-injecting finance, Hermes, or hint-as-truth drift

## Template

```text
# [Module Name]

## 1. Identity
- Layer:
- Type: Core / Pack / Adapter
- Status: Proposed / In Progress / Done / Frozen
- Priority: P0 / P1 / P2
- Owner:
- Date:

## 2. Philosophy
- Primary doctrine carried:
- Secondary doctrine carried:
- Why this module exists as a philosophical constraint:

## 3. Role
- What this module is responsible for:
- What system gap it closes:
- What reusable asset it should leave behind:

## 4. Ownership
- System owner:
- Truth owner:
- Policy owner:
- Runtime/adapter owner:
- Domain owner if any:

## 5. Classification
- Why this is Core / Pack / Adapter:
- Why it is not one of the other two:
- What stable law or domain concern it represents:

## 6. Affected Chain
- Primary chain:
- Upstream input:
- Downstream effect:
- What becomes more real after this module:

## 7. Invariant
- Main invariant:
- Secondary invariants:
- Truth boundary preserved:
- Hint/policy boundary preserved:

## 8. Wrong Placement To Avoid
- 
- 
- 

## 9. Not Doing
- 
- 
- 

## 10. Immediate Action
1.
2.
3.

## 11. Required Test Pack
- Unit:
- Integration:
- Failure-path:
- Invariant:

## 12. Done Criteria
- [ ]
- [ ]
- [ ]
- [ ]

## 13. Next Unlock
- 
```

## Field Guidance

### `Primary doctrine carried`

Choose the main design doctrine this module exists to enforce, for example:

- intelligence is not sovereignty
- truth must exist separately
- failure must become structure
- latent and deterministic work must be separated
- reachability must be verifiable
- long-running means recoverable
- the frontend is a supervision surface
- core must stay stable while domain and adapters stay replaceable

### `Type`

Use strict meanings:

- `Core`: stable system law or cross-domain primitive
- `Pack`: domain-owned meaning, defaults, policy overlays, or domain surfaces
- `Adapter`: replaceable external/runtime/integration implementation

### `Owner`

Owner means the layer or boundary that is allowed to define semantics, not just the file path where code lives.

### `Invariant`

Each module must have at least one invariant that can fail.

Good examples:

- hint must not be promoted into truth
- fallback must not masquerade as success
- finance semantics must not flow back into core
- provider must not become system identity

### `Wrong Placement To Avoid`

This section is mandatory.

It should explicitly name architectural mistakes this module must not commit.

Good examples:

- do not put wake/resume in intelligence
- do not put review supervision semantics in domains
- do not let Hermes provider path own runtime behavior

## Minimal Example

```text
# Hermes Provider Alias Cleanup

## 1. Identity
- Layer: Adapter Layer
- Type: Adapter
- Status: Done
- Priority: P1
- Owner: adapters/runtimes
- Date: 2026-04-22

## 2. Philosophy
- Primary doctrine carried: core must stay stable while domain and adapters stay replaceable
- Secondary doctrine carried: intelligence is not sovereignty
- Why this module exists as a philosophical constraint:
  - provider compatibility paths must not regain runtime ownership

## 3. Role
- What this module is responsible for:
  - reduce legacy provider path to compatibility alias only
- What system gap it closes:
  - older provider import path still looked like the runtime owner
- What reusable asset it should leave behind:
  - clearer adapter-owned runtime boundary

## 4. Ownership
- System owner: adapter layer
- Truth owner: none
- Policy owner: none
- Runtime/adapter owner: adapters/runtimes/hermes
- Domain owner if any: none

## 5. Classification
- Why this is Adapter:
  - it governs replaceable runtime integration ownership
- Why it is not one of the other two:
  - it is neither cross-domain primitive nor finance-domain meaning
- What stable law or domain concern it represents:
  - adapter-owned runtime implementation

## 6. Affected Chain
- Primary chain: analyze -> runtime resolution -> Hermes runtime
- Upstream input: reasoning provider selection
- Downstream effect: runtime-backed analyze and health behavior
- What becomes more real after this module:
  - Hermes compatibility path stops pretending to be a runtime owner

## 7. Invariant
- Main invariant:
  - provider compatibility path must not own runtime behavior
- Secondary invariants:
  - adapter remains runtime owner
  - provider does not become system identity
- Truth boundary preserved:
  - yes
- Hint/policy boundary preserved:
  - yes

## 8. Wrong Placement To Avoid
- Do not move task logic into adapters
- Do not let apps/api construct Hermes runtime details directly
- Do not restore behavior to the legacy provider path

## 9. Not Doing
- No new runtime provider
- No task relocation
- No full adapter reorganization
```

## Usage Rule

Use this template before implementation whenever the work is module-shaped.

Use the older task template system for smaller execution tasks inside an already-defined module.
