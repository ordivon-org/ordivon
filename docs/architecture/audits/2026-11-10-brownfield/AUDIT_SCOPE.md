# AUDIT_SCOPE — Ordivon 当前源码存量审计

**Phase 0 status:** SOURCE scope frozen; semantic review ongoing.
**Exact source:** Ordivon GitHub origin/main `ef17d6879d12faa61fff3bb762b0d500d73c9113`, 2026-11-10 Asia/Singapore.
**Audit worktree:** `ws-gpt6-phases0-5-brownfield-audit-20261110`, independent of shared primary checkout.
**In scope:** every one of the 5,002 current tracked paths, 21 registered Owners, their tests, docs, schemas, manifests, research and actual consumers. Deep semantic analysis requires concrete source evidence, not a mechanically enumerated path.
**Excluded:** ignored caches, unmounted external Git trees, runtime secrets, production PostgreSQL mutations, new features, test expansion, new consumers, new mandatory policy/control systems.
**Previously delivered candidate:** PR #2012 (source `9bda50db4b3413d1a741740613e6383e24c39c83`) repairs current repo inventory and drifted tests; OPEN at this baseline, not a merged fact.

## Actual root structure

```text
ordivon/
  .agents/skills/                     procedural Agent skills
  .github/workflows/                  existing GitHub CI
  apps/                               web, chaoxing-autosign
  services/                           runtime, host, harness, gateway
  platform/                           network, security, workstation
  capabilities/                       artifact, media, preservation, distribution
  domains/                            capital, game
  packages/                           composition, data
  catalogs/                           authorities, capabilities, knowledge, data-products
  profiles/                           domains, research
  studies/                            experimental-episodes, data-lifecycle
  docs/   tools/   tests/
```

The `docs/architecture/STRUCTURE_R2.md` proposed root grammar is PARTIALLY deployed. Source directories are location, not semantic ownership. Do not invent a top-level `computing/` tree. Computing is represented in existing composition, formal tools and bounded domain source, not a separate durable owner.

## Existing natural Owners, versions and native tasks

The following table is generated strictly from `tools/repo/owners.toml` and the **current Owner README frontmatter**, where available. Not every Owner declares a comparable `schema_version` or lifecycle; do not fabricate one. `owners.toml` itself has `schema_version = 1` and `truth_role = repository-mechanics-only-not-domain-authority`.

| Owner | Root | Tracked paths | README schema_version | README lifecycle | Native task |
|---|---|---:|---|---|---|
| authority-catalog | `catalogs/authorities/` | 376 | not declared | not declared | `authority-catalog:verify` |
| capability-catalog | `catalogs/capabilities/` | 77 | not declared | not declared | `capability-catalog:verify` |
| composition | `packages/composition/` | 86 | not declared | not declared | `composition:verify` |
| control-plugin | `extensions/ordivon-control-plane/` | 2 | not declared | not declared | `control-plugin:verify` |
| runtime | `services/runtime/` | 452 | 1 | active | `runtime:verify` |
| host | `services/host/` | 117 | not declared | not declared | `host:verify` |
| harness | `services/harness/` | 731 | 1 | active | `harness:verify` |
| gateway | `services/gateway/` | 107 | not declared | not declared | `gateway:verify` |
| skills | `extensions/chatgpt-skills-mcp/` | 45 | not declared | not declared | `skills:verify` |
| security | `platform/security/` | 162 | not declared | not declared | `security:verify` |
| workstation | `platform/workstation/` | 265 | not declared | not declared | `workstation:ci` |
| network | `platform/network/` | 236 | not declared | not declared | `network:ci` |
| artifact | `capabilities/artifact/` | 425 | not declared | not declared | `artifact:verify` |
| distribution | `capabilities/distribution/` | 30 | not declared | not declared | `distribution:verify` |
| media | `capabilities/media/` | 553 | not declared | not declared | `media:verify` |
| preservation | `capabilities/preservation/` | 46 | not declared | not declared | `preservation:verify` |
| game | `domains/game/` | 387 | 1 | active | `game:verify` |
| capital | `domains/capital/` | 399 | not declared | not declared | `capital:verify` |
| data | `packages/data/` | 19 | not declared | not declared | `data:verify` |
| web | `apps/web/` | 35 | not declared | not declared | `web:verify` |
| chaoxing-autosign | `apps/chaoxing-autosign/` | 11 | not declared | not declared | `chaoxing:verify` |

## State authority / schema boundary

- **Runtime** (`services/runtime`): physical Workspace/Job/Attempt, reservation, execution/effect receipts; current source README declares active. Its PostgreSQL Registry schema is distinct from YAML frontmatter schema_version.
- **Host** (`services/host`): PostgreSQL Work revision/CAS, Space/Topic/Message/Attention, continuity collaboration. SQL migrations under `services/host/migrations/versions/` are authoritative *source history*, not live schema readback.
- **Harness** (`services/harness`): Agent Run, model/provider Tool continuity; current README declares active; its persisted Journal/storage has its own source contracts.
- **Gateway** (`services/gateway`): non-authoritative MCP route projection; configured routes do not prove reachable owners.
- **Security, Network and Workstation**: identity/authority; network transport; native systemd/Podman/Ansible/OpenTofu/Temporal operations respectively, each at its own scope.
- **Artifact / Media / Preservation**: byte-level digital output verification, native media production, native fixity/preservation respectively; content-equality does not prove provenance equivalence.
- **Capital/Game**: actual finance/game domain semantics; Research does not transfer trading authority to Runtime, and Engine examples do not automatically mean released gameplay.
- **Catalogs/Composition/Data/Skills**: discovery and task-local evaluation, not a universal provider of domain truth.

## Audit-to-action rules

1. Read Git source/actual entrypoint + current consumers before making a call.
2. Tie every proposed change to exact path:line, existing contract and natural Owner; categorize `REMOVE / REUSE / COMPOSE / REFACTOR / KEEP / UNKNOWN`.
3. No new functionality, tests, consumer wiring, deployment or owner; preserve static and runtime contracts.
4. Existing `tools/repo/check_owner_boundaries.py`, `check_structure_r2.py`, `check_architecture_docs.py`, Owner `mise` and GitHub protected main are verification/publication seams; do not install Nx or another generic governance daemon.
5. For effects, SOURCE_PASS is not INSTALLED/CONSUMED. Unknown external consumers remain UNKNOWN.
6. Space discussion is a peer-review channel, not an approval authority. Handoff: `status; SourceCut; owner; done; evidence; unresolved; next; claim boundary`.
7. Existing files `AGENTS.md`, `CONTRIBUTING.md`, `docs/architecture/STRUCTURE_R2.md`, `tools/repo/owners.toml`, `tools/repo/dependency_contracts.toml` are the source hierarchy.

## Phase 0 closure

- [x] Verified exact Git source and root source grammar.
- [x] Identified 21 current registered owner source partitions and native task names.
- [x] Separated README frontmatter schema from Owner data, migrations and lifecycle facts.
- [x] Locked admissible architecture criteria in `MODERN_CRITERIA.md`.
- [ ] Full 5,002-file **semantic consumer closure**, not implied by full path inventory.
