# Ordivon Repository Structure R2

Date: 2026-09-22
Status: **PARTIALLY DEPLOYED — S0 + S1A + S1B + S2A + S2B**

Machine-readable companion: `docs/architecture/structure-r2-transition-r1.json`.

## Decision

Repository placement is an engineering-navigation mechanism, not the Ordivon ontology.
The current `services/`, `platform/`, `capabilities/`, `domains/`, and `meta/` roots encode
contextual classifications into physical paths. R2 separates four grammars instead:

1. **Repository grammar** — where maintained source lives.
2. **Contract grammar** — which public seam consumers may depend on.
3. **Circuit grammar** — task-local method/capability/provider/authority binding.
4. **Authority/evidence grammar** — who may establish a claim and which evidence can support it.

No directory name transfers semantic authority.

## Target root grammar

```text
ordivon/
├── .agents/skills/   # procedural Agent knowledge
├── apps/             # user/product composition surfaces
├── packages/         # bounded maintained source units
├── extensions/       # optional / compatibility / consumer-specific integrations
├── catalogs/         # non-authoritative discovery metadata and rebuildable projections
├── profiles/         # reusable non-runtime composition/domain profiles
├── studies/          # study-scoped scientific authority when colocated here
├── deploy/           # node/deployment realization
├── docs/             # repository-level documentation
├── tests/            # repository-level integration/E2E only
├── tools/            # repository/operator mechanics
└── third_party/      # intentionally vendored upstream source only
```

These are placement classes, not component types. `packages/game` does not make Game
permanently a Domain or non-Domain; `packages/security` does not make Security permanently
a Platform or Capability; `packages/runtime` does not make Runtime's semantic identity
"Service".

## Package rule

A package is a bounded maintained source unit with a coherent public seam and verification
boundary. It is not an ontology class.

Preferred package-local grammar, only where the responsibility exists:

```text
packages/<name>/
├── AGENTS.md
├── README.md
├── contracts/        # public types/schemas/protocols only
├── src/              # owner implementation
├── providers/        # only after real replaceable-provider pressure
├── adapters/         # external-form normalization when needed
└── tests/            # owner-native verification
```

Do not create empty symmetry directories.

## Contract dependency law

Preferred cross-unit dependency:

```text
Consumer -> Public Contract -> Natural Owner / Provider
```

not:

```text
Consumer -> Provider implementation internals
```

Contracts remain owner-local; R2 creates no root `contracts/` authority. Provider
implementations remain contract-local or extension-local; R2 creates no global
`providers/` registry.

## Source topology is not runtime topology

Runtime composition remains task-local and is represented by the existing Cognitive
Circuit contract. A Circuit may include entities with no Ordivon source package at all:
external providers, standards, Git, Cloudflare, an exchange, a venue, a Human reviewer,
or another natural authority.

```text
Source Module != LEGO
Repository topology != Circuit topology
Default Provider != Capability
Discovery != Authority
Execution success != semantic success
```

## `meta/next` split

The historical `meta/next` tree contains several engineering forms and must not be moved
wholesale:

- Cognitive Circuit / Interface compatibility / generic Composition Gate mechanics
  -> `packages/composition`;
- canonical Agent Skills -> `.agents/skills`;
- portable control Plugin -> `extensions/ordivon-control-plane`;
- authority and capability discovery metadata -> `catalogs/`;
- domain/composition profiles -> `profiles/`;
- reusable knowledge mappings -> non-authoritative catalog/profile data;
- experiments, evidence, planning, and migrations -> only to their real owner, study,
  test fixture, or repository history when a concrete consumer justifies retention.

There is no permanent `meta` runtime layer in the target structure.

## Verification ownership

`packages/composition` owns only generic mechanical Circuit/Gate/interface evaluation.
Seam-specific verification remains near the concrete consumer/composition/study:

```text
owner-native evidence
    -> seam-specific adapter
    -> generic Composition Gate Result
    -> task-local mechanical closure
```

No universal verifier or global evidence registry is introduced.

## Migration laws

1. Root stays boring.
2. Placement is not identity.
3. Package means source locality, not semantic type.
4. Source topology is not runtime topology.
5. Consumers depend on public contracts, not provider internals.
6. Default provider is not the capability.
7. Optional/compatibility growth stays at the edge.
8. Skills teach; they do not authorize.
9. Runtime state stays outside source truth.
10. Capability exposure is task-compiled rather than globally injected.
11. Verification remains owner/seam-specific.
12. Natural authority and Reality remain outside repository/composition machinery.
13. Source relocation and semantic refactoring are separate changes.
14. No wave may silently merge lockfiles, databases, release lifecycles, or authority.

## Waves

- **S0 — Freeze:** contract, machine mapping, checker and falsification tests. No source moves.
- **S1A — Composition implementation extraction:** generic Cognitive Circuit / Interface R2 /
  Composition Gate implementation, schemas, owner docs, and owner-native tests move to
  `packages/composition`; historical Next Python entrypoints remain thin compatibility facades.
- **S1B — Composition consumer cutover:** migrate remaining Next consumers to the public
  `ordivon-composition` package API and retire facades only when no real consumer requires them.
- **S2A — Control Plugin edge:** portable control Plugin source -> `extensions/ordivon-control-plane`.
- **S2B — Canonical Skill source:** **DEPLOYED** — project Skills -> root `.agents/skills`.
- **S2C — ChatGPT Skills compatibility edge:** temporary Skills MCP owner ->
  `extensions/chatgpt-skills-mcp`.
- **S3 — Durable owners:** Gateway, Runtime, Host, Harness -> `packages/`, one at a time.
- **S4 — Security/Network/deployment:** bounded reusable source -> `packages/`; Workstation
  deployment realization -> `deploy/workstation`.
- **S5 — Discovery/profile split:** non-authoritative discovery -> `catalogs/`; reusable
  profiles -> `profiles/`.
- **S6 — Artifact/Distribution/Media/Preservation:** relocate one owner at a time.
- **S7 — Game/Capital:** relocate source without changing semantic authority.
- **S8 — Dependency guard evolution:** strengthen public-contract dependency checks only
  where real language/package edges justify it.
- **S9 — Closure:** remove empty legacy category roots and generate navigation views.

Every relocation wave preserves behavior first and requires owner-native verification before
integration. Relocation alone does not change public API, authority, state, release identity,
or domain acceptance.

## Explicit non-goals

R2 does not introduce a universal registry, root contract authority, global provider
registry, universal verifier, Agent Service replacement, workflow engine, Task database, or
a requirement that external natural owners be mirrored as local packages.

## Current standing

S0 is deployed repository mechanics. S1A extracted the generic Composition implementation
into the independent `packages/composition` source owner. S1B migrated the remaining Next
consumers to the declared public `ordivon_composition` package API and retired the historical
Python compatibility facades after repository-wide inventory found no external path callers.
R3 seam-specific verifiers, Admission dogfood, and task-local bindings remain with Next.
S2A relocates only the portable control Plugin package bytes to the repository extension
boundary; Next remains its release/materialization consumer. Therefore S1 and S2A are closed,
while S2B-S9 remain open.

For every still-unmigrated owner, current paths in `CURRENT_ARCHITECTURE.md`,
`tools/repo/owners.toml`, `dependency_contracts.toml`, root `mise.toml`, and owner deployment
configuration remain authoritative. Structure R2 never infers deployment relocation from a
planned target path.
