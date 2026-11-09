# INVENTORY — tracked-file source audit

Frozen SourceCut: ef17d6879d12faa61fff3bb762b0d500d73c9113. Physical file identities are enumerated in FILE_INVENTORY.csv; semantic consumer closure is not assumed.

Tracked file count: 5002
Python AST parsed: 1460; errors: 0
SHA duplicate groups: 23, duplicate files: 65

## Natural Owner root map

| Owner | Tracked | Bytes | Root | Real entry files |
|---|---:|---:|---|---|
| authority-catalog | 376 | 419955 | catalogs/authorities/ | README.md, mise.toml, pyproject.toml |
| capability-catalog | 77 | 456251 | catalogs/capabilities/ | AGENTS.md, README.md |
| composition | 86 | 773372 | packages/composition/ | AGENTS.md, README.md, mise.toml, pyproject.toml |
| control-plugin | 2 | 576 | extensions/ordivon-control-plane/ |  |
| runtime | 452 | 7593300 | services/runtime/ | AGENTS.md, README.md, mise.toml, pyproject.toml, Cargo.toml |
| host | 117 | 767309 | services/host/ | AGENTS.md, README.md, mise.toml, pyproject.toml |
| harness | 731 | 9119462 | services/harness/ | README.md, mise.toml, pyproject.toml |
| gateway | 107 | 714119 | services/gateway/ | AGENTS.md, README.md, pyproject.toml |
| skills | 45 | 409852 | extensions/chatgpt-skills-mcp/ | README.md, mise.toml, pyproject.toml |
| security | 162 | 702613 | platform/security/ | README.md, mise.toml, pyproject.toml |
| workstation | 265 | 1173660 | platform/workstation/ | README.md, mise.toml, pyproject.toml |
| network | 236 | 841287 | platform/network/ | AGENTS.md, README.md, mise.toml |
| artifact | 425 | 2312415 | capabilities/artifact/ | README.md, mise.toml, pyproject.toml |
| distribution | 30 | 40061 | capabilities/distribution/ | README.md, mise.toml |
| media | 553 | 83900206 | capabilities/media/ | AGENTS.md, README.md, mise.toml, pyproject.toml, package.json |
| preservation | 46 | 2175603 | capabilities/preservation/ | README.md |
| game | 387 | 4138973 | domains/game/ | AGENTS.md, README.md, mise.toml, package.json |
| capital | 399 | 2261295 | domains/capital/ | README.md, mise.toml, pyproject.toml |
| data | 19 | 113545 | packages/data/ | AGENTS.md, README.md, mise.toml |
| web | 35 | 226469 | apps/web/ | README.md, mise.toml, package.json |
| chaoxing-autosign | 11 | 36264 | apps/chaoxing-autosign/ | README.md |

## Tracked first/second-level directory census

- .agents/skills/: 63 files
- .github/CODEOWNERS/: 1 files
- .github/ISSUE_TEMPLATE/: 4 files
- .github/PULL_REQUEST_TEMPLATE.md/: 1 files
- .github/dependabot.yml/: 1 files
- .github/workflows/: 6 files
- .gitignore/: 1 files
- .gitleaksignore/: 1 files
- AGENTS.md/: 1 files
- CONTRIBUTING.md/: 1 files
- LICENSE/: 1 files
- README.md/: 1 files
- SECURITY.md/: 1 files
- apps/chaoxing-autosign/: 11 files
- apps/web/: 35 files
- capabilities/artifact/: 425 files
- capabilities/distribution/: 30 files
- capabilities/media/: 553 files
- capabilities/preservation/: 46 files
- catalogs/authorities/: 376 files
- catalogs/capabilities/: 77 files
- catalogs/data-products/: 5 files
- catalogs/knowledge/: 74 files
- docs/architecture/: 86 files
- docs/migration/: 14 files
- docs/start/: 4 files
- domains/capital/: 399 files
- domains/game/: 387 files
- extensions/chatgpt-skills-mcp/: 45 files
- extensions/ordivon-control-plane/: 2 files
- mise.toml/: 1 files
- packages/composition/: 86 files
- packages/data/: 19 files
- platform/network/: 236 files
- platform/security/: 162 files
- platform/workstation/: 265 files
- profiles/domains/: 5 files
- profiles/research/: 12 files
- renovate.json/: 1 files
- services/gateway/: 107 files
- services/harness/: 731 files
- services/host/: 117 files
- services/runtime/: 452 files
- studies/data-lifecycle/: 50 files
- studies/experimental-episodes/: 39 files
- tests/catalogs/: 1 files
- tests/fixtures/: 1 files
- tools/formal/: 10 files
- tools/repo/: 55 files

## File content-role hints

| Hint | Tracked files |
|---|---:|
| config-contract | 1175 |
| source | 1115 |
| test | 715 |
| doc | 588 |
| other | 434 |
| research-experiment | 415 |
| evidence | 330 |
| formal | 115 |
| media-asset | 78 |
| schema-migration | 37 |

## Exact duplicate-byte source paths (examples)

- capabilities/artifact/.python-version; capabilities/artifact/artifact-delivery/python-uv/.python-version; capabilities/media/.python-version; domains/capital/.python-version; ...
- LICENSE; capabilities/media/LICENSE; domains/game/LICENSE; services/harness/LICENSE; ...
- capabilities/media/productions/archive-archipelago-001/evidence/chromium-console-keyboard-r3.json; capabilities/media/productions/archive-archipelago-001/evidence/chromium-console-mobile-r2.json; capabilities/media/productions/archive-archipelago-001/evidence/chromium-console-r2.json; capabilities/media/productions/archive-archipelago-001/evidence/chromium-console-touch-r4.json; ...
- domains/capital/artifacts/.gitkeep; domains/game/examples/beacon-relay/screenshots/.gdignore; platform/security/artifacts/.gitkeep; services/harness/fixtures/harness-replacement-repository-repair-v1/artifacts/.gitkeep; ...
- platform/workstation/systemd/service-profiles/loki.service.d/20-ordivon-observability-heavy.conf; platform/workstation/systemd/service-profiles/netdata.service.d/20-ordivon-observability-heavy.conf; platform/workstation/systemd/service-profiles/vector.service.d/20-ordivon-observability-heavy.conf
- capabilities/media/productions/archive-archipelago-001/render/archive-archipelago-001.png; capabilities/media/productions/live-relay-001/source/archive-archipelago-001.png
- capabilities/media/productions/convergence-object-001/render/convergence-object-001.png; capabilities/media/productions/live-relay-001/source/convergence-object-001.png
- domains/capital/tools/legacy_replay/lean_wave_b/algorithm/packages.lock.json; domains/capital/tools/quickfixn_1_14_1/fix44-projector/packages.lock.json
- domains/capital/tools/okx_official_cli/.gitignore; platform/security/contracts/agent-request-verifier-v1/.gitignore
- domains/game/examples/kenney-visual-composition/.gitignore; domains/game/examples/room-encounter/.gitignore
- domains/game/examples/native-composition/assets/kenney-ui-audio/click1.wav; domains/game/examples/room-encounter/assets/click1.wav
- domains/game/examples/native-composition/assets/kenney-ui-audio/click2.wav; domains/game/examples/room-encounter/assets/click2.wav
- platform/security/contracts/agent-request-verifier-v1/patches/oauth4webapi@3.8.8.patch; platform/security/labs/agent-admission-rs/patches/oauth4webapi@3.8.8.patch
- platform/security/contracts/agent-request-verifier-v1/pnpm-workspace.yaml; platform/security/labs/agent-admission-rs/pnpm-workspace.yaml
- platform/security/contracts/agent-request-verifier-v1/tsconfig.json; platform/security/labs/agent-admission-rs/tsconfig.json

## Concrete consumer distinction

- services/runtime/scripts/backup.py is referenced in existing recovery documentation and operational tests: preserve until Runtime confirms live semantics and authoritative archive needs.
- services/harness/src/ordivon_harness/sqlite_store.py retains current tests and experiment read paths, although production PostgreSQL is desired: no age-based deletion.
- services/harness/evals/fresh_agent_ab/run_live_v1.py and run_live_v2_currentness.py import a removed capability_discovery source module. Parallel PR #2009 separately retires these scripts while keeping preregistration, raw result, and CLOSEOUT. This audit does not duplicate its code change.
- Legacy Capital Replay files have registry and test consumers; tests are not production truth but preserve replay contract.
- Binary Media assets have real content/source identity; same content hash does not mean interchangeable right or consumer.

## What this inventory does and does not establish

It has read every tracked file and recorded owner-role/hash and Python syntax, not exhaustively understood every dynamic consumer. FILE_INVENTORY.csv marks each row SEMANTIC_REVIEW_PENDING. Module judgments are in AUDIT_REPORT; each proposed deletion requires an actual source/consumer trace.
