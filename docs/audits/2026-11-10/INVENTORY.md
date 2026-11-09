# Ordivon frozen full-file inventory — 2026-11-10

SourceCut: ef17d6879d12faa61fff3bb762b0d500d73c9113. This is 5002/5002 tracked-file metadata inventory, not manual semantic validation of every implementation. Each file has a path, Owner, module, role, bytes, line count, SHA-256, parse observation and review hint in FILE_LEDGER.tsv. DEPENDENCY_SIGHTINGS.tsv has 1606 bounded import/use token sightings; these are *not* an exact directed runtime graph.

## Root and current natural owners

The root contains: apps, capabilities, catalogs, docs, domains, extensions, packages, platform, profiles, services, studies, tests, tools; .agents and .github supply method/CI. tools/repo/owners.toml schema_version 1 declares 21 owner roots and 2 source-regions; many crosscutting docs/Skills are deliberately unowned semantic content (441 root-crosscut files).

| Owner | Git root | Files | Source files | Tests | Documents | Schemas/formal | Top code/asset areas |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| authority-catalog | catalogs/authorities/ | 376 | 5 | 1 | 1 | 365 | records/iso (33), records/ietf (16), records/iso-iec (9) |
| capability-catalog | catalogs/capabilities/ | 77 | 8 | 4 | 58 | 7 | <root> (4), artifact/README.md (1), docs/EXTERNAL_CAPABILITY_EVALUATION_R1.md (1) |
| composition | packages/composition/ | 86 | 14 | 23 | 11 | 22 | src/ordivon_composition (24), <root> (5), policies/research-adopted-r1 (4) |
| control-plugin | extensions/ordivon-control-plane/ | 2 | 0 | 0 | 0 | 2 | <root> (2) |
| runtime | services/runtime/ | 452 | 168 | 49 | 123 | 52 | crates/ordivon-runtime-core (115), research/foundations (71), research/programme (39) |
| host | services/host/ | 117 | 54 | 38 | 8 | 7 | src/ordivon_host_v2 (37), migrations/versions (13), <root> (9) |
| harness | services/harness/ | 731 | 183 | 203 | 141 | 156 | src/ordivon_harness (60), evidence/browser-security (26), evidence/system1-decision (18) |
| gateway | services/gateway/ | 107 | 40 | 31 | 2 | 16 | src/ordivon_gateway (26), <root> (7), packaging/windows (7) |
| skills | extensions/chatgpt-skills-mcp/ | 45 | 12 | 19 | 4 | 4 | src/ordivon_skills (9), <root> (5), tests/fixtures (3) |
| security | platform/security/ | 162 | 58 | 28 | 21 | 34 | labs/agent-admission-rs (29), src/ordivon_security_v2 (14), contracts/agent-request-verifier-v1 (11) |
| workstation | platform/workstation/ | 265 | 83 | 43 | 35 | 18 | providers/cloudflare (58), workstation/providers (18), tofu/agent-birth-handoff (8) |
| network | platform/network/ | 236 | 59 | 32 | 31 | 34 | consumers/finance (15), consumers/codex (14), consumers/browserless (11) |
| artifact | capabilities/artifact/ | 425 | 132 | 72 | 30 | 174 | artifact-delivery/shadow-contracts (36), artifact-delivery/shadow-v2 (29), artifact-delivery/shadow-bindings (20) |
| distribution | capabilities/distribution/ | 30 | 6 | 1 | 2 | 19 | <root> (4), adapters/openapi-generator.json (1), adapters/postiz.json (1) |
| media | capabilities/media/ | 553 | 129 | 31 | 136 | 162 | src/ordivon_studio (70), research/expression (69), productions/archive-archipelago-001 (57) |
| preservation | capabilities/preservation/ | 46 | 2 | 1 | 6 | 21 | artifacts/creative-preservation (32), <root> (2), config/archivematica-preservation-r10.compose.yml (1) |
| game | domains/game/ | 387 | 33 | 13 | 19 | 11 | examples/room-encounter (238), examples/beacon-relay (59), examples/native-composition (19) |
| capital | domains/capital/ | 399 | 87 | 100 | 27 | 94 | src/ordivon_capital (65), tools/nautilus_rc4 (16), tools/legacy_replay (13) |
| data | packages/data/ | 19 | 7 | 2 | 6 | 3 | src/ordivon_data (5), <root> (3), docs/AGENT.md (1) |
| web | apps/web/ | 35 | 18 | 5 | 1 | 7 | <root> (9), evidence/AGENT-AUTHORITY-BROWSER-E2E-R1.json (1), evidence/AGENT-NATIVE-WEBSITE-E2E-R1.json (1) |
| chaoxing-autosign | apps/chaoxing-autosign/ | 11 | 9 | 1 | 1 | 0 | <root> (1), chaoxing_mvp/__init__.py (1), chaoxing_mvp/adapters.py (1) |
| root-crosscut | .agents/docs/profiles/tools/studies/.github and root | 441 | 44 | 39 | 244 | 74 | crosscut method/CI/navigation |

## File-kind/parse facts

- source: 1151
- test: 736
- documentation: 907
- config-or-build: 156
- contract-data-or-formal: 1282
- lock-or-asset: 77
- other-tracked: 693
- parse observation ast-ok: 1460
- parse observation json-ok: 1315
- parse observation lexically-scanned: 240
- parse observation not-applicable: 617
- parse observation toml-ok: 50
- parse observation utf8-ok: 1320

Parsing and simple import-token sightings are insufficient to certify boundary conformance. The native tool tools/repo/check_owner_boundaries.py is the stronger policy check; its current observed success is recorded in AUDIT_REPORT.md.

## Source-first entrypoints and lifecycle

- authority-catalog: catalogs/authorities/README.md; source schema_version=not-declared, declared lifecycle=not-declared; effective installed state must be queried separately.
- capability-catalog: catalogs/capabilities/README.md; source schema_version=not-declared, declared lifecycle=not-declared; effective installed state must be queried separately.
- composition: packages/composition/README.md; source schema_version=not-declared, declared lifecycle=not-declared; effective installed state must be queried separately.
- runtime: services/runtime/README.md; source schema_version=1, declared lifecycle=active; effective installed state must be queried separately.
- host: services/host/README.md; source schema_version=not-declared, declared lifecycle=not-declared; effective installed state must be queried separately.
- harness: services/harness/README.md; source schema_version=1, declared lifecycle=active; effective installed state must be queried separately.
- gateway: services/gateway/README.md; source schema_version=not-declared, declared lifecycle=not-declared; effective installed state must be queried separately.
- skills: extensions/chatgpt-skills-mcp/README.md; source schema_version=not-declared, declared lifecycle=not-declared; effective installed state must be queried separately.
- security: platform/security/README.md; source schema_version=not-declared, declared lifecycle=not-declared; effective installed state must be queried separately.
- workstation: platform/workstation/README.md; source schema_version=not-declared, declared lifecycle=not-declared; effective installed state must be queried separately.
- network: platform/network/README.md; source schema_version=not-declared, declared lifecycle=not-declared; effective installed state must be queried separately.
- artifact: capabilities/artifact/README.md; source schema_version=not-declared, declared lifecycle=not-declared; effective installed state must be queried separately.
- distribution: capabilities/distribution/README.md; source schema_version=not-declared, declared lifecycle=not-declared; effective installed state must be queried separately.
- media: capabilities/media/README.md; source schema_version=not-declared, declared lifecycle=not-declared; effective installed state must be queried separately.
- preservation: capabilities/preservation/README.md; source schema_version=not-declared, declared lifecycle=not-declared; effective installed state must be queried separately.
- game: domains/game/README.md; source schema_version=1, declared lifecycle=active; effective installed state must be queried separately.
- capital: domains/capital/README.md; source schema_version=not-declared, declared lifecycle=not-declared; effective installed state must be queried separately.
- data: packages/data/README.md; source schema_version=not-declared, declared lifecycle=not-declared; effective installed state must be queried separately.
- web: apps/web/README.md; source schema_version=not-declared, declared lifecycle=not-declared; effective installed state must be queried separately.
- chaoxing-autosign: apps/chaoxing-autosign/README.md; source schema_version=not-declared, declared lifecycle=not-declared; effective installed state must be queried separately.

## High-density and volatile paths for human semantic follow-up

| Source file | Owner | Lines | Review obligation |
| --- | --- | ---: | --- |
| services/runtime/crates/ordivon-runtime-core/src/runtime/tests.rs | runtime | 10788 | interface depth, true callers, duplicated responsibility; size alone is not a defect |
| services/runtime/crates/ordivon-runtime-core/src/universal/tests.rs | runtime | 4382 | interface depth, true callers, duplicated responsibility; size alone is not a defect |
| services/runtime/crates/ordivon-runtime-core/src/runtime/integration_tests.rs | runtime | 3840 | interface depth, true callers, duplicated responsibility; size alone is not a defect |
| services/harness/src/ordivon_harness/ordivon/run_continuity.py | harness | 3186 | interface depth, true callers, duplicated responsibility; size alone is not a defect |
| services/runtime/crates/ordivon-runtime-core/src/pg_admission.rs | runtime | 3026 | interface depth, true callers, duplicated responsibility; size alone is not a defect |
| services/runtime/platform/windows/Ordivon.WindowsJobLauncher.cs | runtime | 2966 | interface depth, true callers, duplicated responsibility; size alone is not a defect |
| services/runtime/crates/ordivon-runtime-core/src/runtime/windows.rs | runtime | 2875 | interface depth, true callers, duplicated responsibility; size alone is not a defect |
| services/runtime/crates/ordivon-runtime-mcp/src/server/tests.rs | runtime | 2602 | interface depth, true callers, duplicated responsibility; size alone is not a defect |
| tools/repo/check_architecture_docs.py | root-crosscut | 2524 | interface depth, true callers, duplicated responsibility; size alone is not a defect |
| services/runtime/scripts/mcp_e2e.py | runtime | 2376 | interface depth, true callers, duplicated responsibility; size alone is not a defect |
| services/harness/src/ordivon_harness/ordivon/loop.py | harness | 2366 | interface depth, true callers, duplicated responsibility; size alone is not a defect |
| services/runtime/crates/ordivon-runtime-core/src/runtime/types.rs | runtime | 2097 | interface depth, true callers, duplicated responsibility; size alone is not a defect |
| services/runtime/crates/ordivon-runtime-core/src/bin/ordivon-runtime-windows-deploy.rs | runtime | 2089 | interface depth, true callers, duplicated responsibility; size alone is not a defect |
| tools/repo/exhaustive_coverage.py | root-crosscut | 2052 | interface depth, true callers, duplicated responsibility; size alone is not a defect |
| services/harness/scripts/agent_automation_browserless.py | harness | 1937 | interface depth, true callers, duplicated responsibility; size alone is not a defect |
| services/runtime/crates/ordivon-runtime-core/src/runtime/engine.rs | runtime | 1860 | interface depth, true callers, duplicated responsibility; size alone is not a defect |
| services/runtime/crates/ordivon-runtime-core/src/runtime/inspection/operator.rs | runtime | 1813 | interface depth, true callers, duplicated responsibility; size alone is not a defect |
| services/runtime/crates/ordivon-runtime-core/src/universal/runner.rs | runtime | 1811 | interface depth, true callers, duplicated responsibility; size alone is not a defect |
| services/runtime/crates/ordivon-runtime-core/src/runtime/registry.rs | runtime | 1556 | interface depth, true callers, duplicated responsibility; size alone is not a defect |
| services/harness/src/ordivon_harness/ordivon/runtime_bridge.py | harness | 1492 | interface depth, true callers, duplicated responsibility; size alone is not a defect |
| services/runtime/crates/ordivon-runtime-mcp/src/main.rs | runtime | 1475 | interface depth, true callers, duplicated responsibility; size alone is not a defect |
| services/runtime/crates/ordivon-runtime-core/src/runtime/repair.rs | runtime | 1348 | interface depth, true callers, duplicated responsibility; size alone is not a defect |
| services/runtime/crates/ordivon-runtime-core/src/universal/workspace/close_recovery.rs | runtime | 1322 | interface depth, true callers, duplicated responsibility; size alone is not a defect |
| platform/workstation/providers/cloudflare/scripts/ordivon_edge_release.py | workstation | 1318 | interface depth, true callers, duplicated responsibility; size alone is not a defect |
| services/runtime/scripts/verify_formal_trace.py | runtime | 1266 | interface depth, true callers, duplicated responsibility; size alone is not a defect |

## Observed limits

- Game examples include vendored Dialogue Manager; count vendored/license materials before any deletion. Media includes binary project/production assets; filename-only heuristics cannot delete original materials.
- Runtime contains real PG authority and legacy SQLite compatibility source; current PG admission does not prove every SQLite read/history consumer can be removed.
- Workstation/Network/Systemd paths are installed/operated surfaces, not pure source; an inactive service today is not a proven dead implementation.
- Artifact includes actual Temporal worker and Zot consumer. Isolated unconsumed R2 mailbox is an independent Owner candidate, not evidence that rclone implements equivalent temporary-credential semantics.
- Host PG Work and Runtime Job are different; Harness trace memory is not a shared global Journal/CAS.
- This per-file ledger is full *coverage of source metadata*; high-priority modules have additional source-specific findings in AUDIT_REPORT.md, not a claim of 5002 deep human reviews.
