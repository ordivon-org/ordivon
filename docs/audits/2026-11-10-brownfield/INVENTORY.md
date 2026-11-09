# INVENTORY — source tree and owner navigation

SourceCut `ef17d6879d12faa61fff3bb762b0d500d73c9113` (2026-11-10). This directory contains the full **5,002-row** path/size/hash/language/category census at `FILE_CENSUS.tsv` (all Git tracked files, not generated/node_modules/.git). Total bytes 123,199,041; static Python parse failures 0.

## Repository top-level tracked files
| Directory | Tracked files |
|---|---:|
| `services` | 1407 |
| `capabilities` | 1054 |
| `domains` | 786 |
| `platform` | 663 |
| `catalogs` | 532 |
| `packages` | 105 |
| `docs` | 104 |
| `studies` | 89 |
| `tools` | 65 |
| `.agents` | 63 |
| `extensions` | 47 |
| `apps` | 46 |
| `profiles` | 17 |
| `.github` | 13 |
| `__root__` | 9 |
| `tests` | 2 |
## Language inventory (filename based)
| Language / representation | Tracked files |
|---|---:|
| Python | 1460 |
| JSON | 1315 |
| Markdown | 849 |
| Other | 520 |
| NoExtension | 146 |
| Rust | 131 |
| YAML | 108 |
| Shell | 91 |
| TypeScript | 89 |
| GDScript | 86 |
| TOML | 50 |
| PowerShell | 25 |
| SQL | 20 |
| Lockfile | 19 |
| Lean | 18 |
| C# | 15 |
| Rego | 13 |
| TLA+ | 12 |
| TypeScript/React | 11 |
| SMT-LIB | 11 |
| HTML | 7 |
| CSS | 3 |
| JavaScript | 3 |
## Natural Owner source roots
| Owner | Root | Tracked files | implementation or other | tests | doc | contract/config/proof |
|---|---|---:|---:|---:|---:|---:|
| authority-catalog | `catalogs/authorities/` | 376 | 7 | 1 | 0 | 365 |
| capability-catalog | `catalogs/capabilities/` | 77 | 9 | 4 | 53 | 6 |
| composition | `packages/composition/` | 86 | 28 | 23 | 7 | 22 |
| control-plugin | `extensions/ordivon-control-plane/` | 2 | 0 | 0 | 0 | 2 |
| runtime | `services/runtime/` | 452 | 211 | 49 | 114 | 66 |
| host | `services/host/` | 117 | 62 | 38 | 6 | 7 |
| harness | `services/harness/` | 731 | 221 | 203 | 132 | 165 |
| gateway | `services/gateway/` | 107 | 57 | 31 | 0 | 16 |
| skills | `extensions/chatgpt-skills-mcp/` | 45 | 16 | 19 | 3 | 4 |
| security | `platform/security/` | 162 | 74 | 24 | 17 | 39 |
| workstation | `platform/workstation/` | 265 | 136 | 40 | 22 | 51 |
| network | `platform/network/` | 236 | 108 | 32 | 9 | 64 |
| artifact | `capabilities/artifact/` | 425 | 143 | 72 | 29 | 175 |
| distribution | `capabilities/distribution/` | 30 | 7 | 1 | 1 | 19 |
| media | `capabilities/media/` | 553 | 220 | 31 | 103 | 162 |
| preservation | `capabilities/preservation/` | 46 | 17 | 1 | 5 | 22 |
| game | `domains/game/` | 387 | 353 | 4 | 5 | 12 |
| capital | `domains/capital/` | 399 | 163 | 100 | 20 | 106 |
| data | `packages/data/` | 19 | 7 | 2 | 4 | 3 |
| web | `apps/web/` | 35 | 25 | 0 | 0 | 7 |
| chaoxing-autosign | `apps/chaoxing-autosign/` | 11 | 9 | 1 | 0 | 0 |

## Known modules / script entrypoints
Root: `tools/repo/owners.toml` is source navigation; `mise.toml` owns existing native verification routing, not business truth.
- `services/host`: durable collaboration Work/Space/Topic/Message, Alembic, PostgreSQL, public Host API and MCP. Host README lacks conventional front-matter; this is not by itself a failure.
- `services/runtime`: Job/Attempt/Workspace lifecycle and physical evidence; README schema_version=1, lifecycle=active.
- `services/harness`: Agent cognition, Run/Tool/Provider continuity; README schema_version=1, lifecycle=active.
- `services/gateway`: thin northbound adapter, no semantic admission authority.
- `platform/security`: explicit policy/effect evaluation and provider artifacts.
- `platform/network` and `platform/workstation`: actual environment/configuration owners.
- `capabilities/artifact, distribution, media, preservation`: distinct material/evidence/preservation responsibilities; do not merge by filename.
- `domains/capital, game`: finance and game business Owners.
- `packages/composition, data`: bounded cross-owner mechanical composition/data interoperability.
- `apps/web, chaoxing-autosign`: apps; inspect whether thin composition shells vs duplicate Owner truth.
- `catalogs/authorities, capabilities, knowledge`: semantic navigation/discovery, not current installed provider truth.
- `extensions/chatgpt-skills-mcp, ordivon-control-plane`: adapters/Skills, not default business owner.
- `tools/formal`, `tools/repo`: existing shared verification/navigation mechanics.

## Static warning inventory
No untracked worktree content is assessed. Duplicated content hashes and repeated dated docs are candidates only. Multi-language file counting is extension-based and does not certify parse or behavior for every language.

## Binary line-count correction
Binary assets do not have meaningful source line counts and are now marked with blank `lines` in the raw TSV. 64 binary files were detected by known suffix or NUL bytes; do not confuse media payload newlines with code lines.
