# AUDIT_SCOPE — Ordivon repo-wide Brownfield reform
SourceCut: `ef17d6879d12faa61fff3bb762b0d500d73c9113` (2026-11-10 Asia/Singapore), clean initial worktree. Scope: all 5,002 tracked files; `tools/repo/owners.toml` declares 21 natural owner roots. This audit is source truth; it does not claim installed/deployed consumer closure.

## What is allowed
Only architecture/source audit and repair of existing behavior; delete stale or duplicate assets, clarify docs, merge/relocate bounded existing modules preserving behavior. Existing Owner verification is the acceptance rail; no net-new feature, test, consumer route, universal metadata registry, product increments, or weak-model trials.

## Trust and execution
Normal source-only changes in isolated Runtime Git workspace. Do not modify live databases, credentials, provider orders, systemd installations, shared worktrees, or terminal users. All edits reversible by git diff/commit; SourceCut, tests, PR and installed reality are separate.
Current branch and immutable SourceCut are recorded before work. Prior local finance audit lives in separate worktree and is not automatically merged.

## P0 boundary: actual existing natural Owners
| Owner | Root | Tracked files | Native existing gate | README/AGENTS declared schema/lifecycle (where present) |
|---|---|---:|---|---|
| authority-catalog | `catalogs/authorities/` | 376 | `authority-catalog:verify` | catalogs/authorities/README.md (schema_version=NOT_DECLARED, lifecycle=NOT_DECLARED, owners=NOT_DECLARED) |
| capability-catalog | `catalogs/capabilities/` | 77 | `capability-catalog:verify` | catalogs/capabilities/README.md (schema_version=NOT_DECLARED, lifecycle=NOT_DECLARED, owners=NOT_DECLARED)<br>catalogs/capabilities/AGENTS.md (schema_version=NOT_DECLARED, lifecycle=NOT_DECLARED, owners=NOT_DECLARED) |
| composition | `packages/composition/` | 86 | `composition:verify` | packages/composition/README.md (schema_version=NOT_DECLARED, lifecycle=NOT_DECLARED, owners=NOT_DECLARED)<br>packages/composition/AGENTS.md (schema_version=NOT_DECLARED, lifecycle=NOT_DECLARED, owners=NOT_DECLARED) |
| control-plugin | `extensions/ordivon-control-plane/` | 2 | `control-plugin:verify` | NONE |
| runtime | `services/runtime/` | 452 | `runtime:verify` | services/runtime/README.md (schema_version=1, lifecycle=active, owners=- ordivon-runtime)<br>services/runtime/AGENTS.md (schema_version=NOT_DECLARED, lifecycle=NOT_DECLARED, owners=NOT_DECLARED) |
| host | `services/host/` | 117 | `host:verify` | services/host/README.md (schema_version=NOT_DECLARED, lifecycle=NOT_DECLARED, owners=NOT_DECLARED)<br>services/host/AGENTS.md (schema_version=NOT_DECLARED, lifecycle=NOT_DECLARED, owners=NOT_DECLARED) |
| harness | `services/harness/` | 731 | `harness:verify` | services/harness/README.md (schema_version=1, lifecycle=active, owners=- ordivon-harness) |
| gateway | `services/gateway/` | 107 | `gateway:verify` | services/gateway/README.md (schema_version=NOT_DECLARED, lifecycle=NOT_DECLARED, owners=NOT_DECLARED)<br>services/gateway/AGENTS.md (schema_version=NOT_DECLARED, lifecycle=NOT_DECLARED, owners=NOT_DECLARED) |
| skills | `extensions/chatgpt-skills-mcp/` | 45 | `skills:verify` | extensions/chatgpt-skills-mcp/README.md (schema_version=NOT_DECLARED, lifecycle=NOT_DECLARED, owners=NOT_DECLARED) |
| security | `platform/security/` | 162 | `security:verify` | platform/security/README.md (schema_version=NOT_DECLARED, lifecycle=NOT_DECLARED, owners=NOT_DECLARED) |
| workstation | `platform/workstation/` | 265 | `workstation:ci` | platform/workstation/README.md (schema_version=NOT_DECLARED, lifecycle=NOT_DECLARED, owners=NOT_DECLARED) |
| network | `platform/network/` | 236 | `network:ci` | platform/network/README.md (schema_version=NOT_DECLARED, lifecycle=NOT_DECLARED, owners=NOT_DECLARED)<br>platform/network/AGENTS.md (schema_version=NOT_DECLARED, lifecycle=NOT_DECLARED, owners=NOT_DECLARED) |
| artifact | `capabilities/artifact/` | 425 | `artifact:verify` | capabilities/artifact/README.md (schema_version=NOT_DECLARED, lifecycle=NOT_DECLARED, owners=NOT_DECLARED) |
| distribution | `capabilities/distribution/` | 30 | `distribution:verify` | capabilities/distribution/README.md (schema_version=NOT_DECLARED, lifecycle=NOT_DECLARED, owners=NOT_DECLARED) |
| media | `capabilities/media/` | 553 | `media:verify` | capabilities/media/README.md (schema_version=NOT_DECLARED, lifecycle=NOT_DECLARED, owners=NOT_DECLARED)<br>capabilities/media/AGENTS.md (schema_version=NOT_DECLARED, lifecycle=NOT_DECLARED, owners=NOT_DECLARED) |
| preservation | `capabilities/preservation/` | 46 | `preservation:verify` | capabilities/preservation/README.md (schema_version=NOT_DECLARED, lifecycle=NOT_DECLARED, owners=NOT_DECLARED) |
| game | `domains/game/` | 387 | `game:verify` | domains/game/README.md (schema_version=1, lifecycle=active, owners=[ordivon-game])<br>domains/game/AGENTS.md (schema_version=NOT_DECLARED, lifecycle=NOT_DECLARED, owners=NOT_DECLARED) |
| capital | `domains/capital/` | 399 | `capital:verify` | domains/capital/README.md (schema_version=NOT_DECLARED, lifecycle=NOT_DECLARED, owners=NOT_DECLARED) |
| data | `packages/data/` | 19 | `data:verify` | packages/data/README.md (schema_version=NOT_DECLARED, lifecycle=NOT_DECLARED, owners=NOT_DECLARED)<br>packages/data/AGENTS.md (schema_version=NOT_DECLARED, lifecycle=NOT_DECLARED, owners=NOT_DECLARED) |
| web | `apps/web/` | 35 | `web:verify` | apps/web/README.md (schema_version=NOT_DECLARED, lifecycle=NOT_DECLARED, owners=NOT_DECLARED) |
| chaoxing-autosign | `apps/chaoxing-autosign/` | 11 | `chaoxing:verify` | apps/chaoxing-autosign/README.md (schema_version=NOT_DECLARED, lifecycle=NOT_DECLARED, owners=NOT_DECLARED) |

## Critical fact owner roles
Host owns Work/Space/Topic/Message/CAS/Journal collaboration state. Runtime owns physical Job/Attempt/Workspace process/evidence/recovery. Harness owns bounded Agent Run/cognition/tool-intent continuity; Gateway is a non-authoritative adapter. Security owns policies and effect authorization; each domain owns its economic/scientific/business semantics and deployed state. Computing is a design/science responsibility in current catalogs, not assumed to have a standalone root package merely by conceptual name.

## Included and excluded
Included: all tracked files for structural inventory, active source/config/contracts/docs in every natural Owner, targeted behavioral review of high-risk representative modules, direct references and existing checks. Excluded: untracked node_modules/.venv/build objects, remote live service evidence, absolute consumer closure beyond observed code, changes to installed state.

## Honest scope declaration
Every tracked file is hashed/classified in FILE_CENSUS.tsv, but this mechanical census does not prove 5,002 separate semantic audits. Semantic conclusions below are made only for evidenced module/paths, with explicit UNKNOWN elsewhere. No new audit platform is installed.
