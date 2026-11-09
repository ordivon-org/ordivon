# Ordivon real physical repository — inventory

**Immutable input:** `ef17d6879d12faa61fff3bb762b0d500d73c9113` (2026-11-10 Asia/Shanghai).
**Tracked source files:** **5002**. Exact source path-list SHA-256: `91570c440b45b472316617b8c82f77c06cb377db58b4e38fd21ecd180be750c6`. Native exact-Git exhaustive_coverage source-path digest: `sha256:d8c073c7a240462f871f0bd69700a4cd8b1632959872598cd23f3e9177afd34b`.

## Observed top-level grammar (Git-tracked, not guessed from a desired layout)

- `services/`: 1407 files; direct child clusters: 731 harness, 452 runtime, 117 host, 107 gateway
- `capabilities/`: 1054 files; direct child clusters: 553 media, 425 artifact, 46 preservation, 30 distribution
- `domains/`: 786 files; direct child clusters: 399 capital, 387 game
- `platform/`: 663 files; direct child clusters: 265 workstation, 236 network, 162 security
- `catalogs/`: 532 files; direct child clusters: 376 authorities, 77 capabilities, 74 knowledge, 5 data-products
- `packages/`: 105 files; direct child clusters: 86 composition, 19 data
- `docs/`: 104 files; direct child clusters: 86 architecture, 14 migration, 4 start
- `studies/`: 89 files; direct child clusters: 50 data-lifecycle, 39 experimental-episodes
- `tools/`: 65 files; direct child clusters: 55 repo, 10 formal
- `.agents/`: 63 files; direct child clusters: 63 skills
- `extensions/`: 47 files; direct child clusters: 45 chatgpt-skills-mcp, 2 ordivon-control-plane
- `apps/`: 46 files; direct child clusters: 35 web, 11 chaoxing-autosign
- `profiles/`: 17 files; direct child clusters: 12 research, 5 domains
- `.github/`: 13 files; direct child clusters: 6 workflows, 4 ISSUE_TEMPLATE, 3 (root-files)
- `tests/`: 2 files; direct child clusters: 1 catalogs, 1 fixtures
- `.gitignore/`: 1 files; direct child clusters: root file
- `.gitleaksignore/`: 1 files; direct child clusters: root file
- `AGENTS.md/`: 1 files; direct child clusters: root file
- `CONTRIBUTING.md/`: 1 files; direct child clusters: root file
- `LICENSE/`: 1 files; direct child clusters: root file
- `README.md/`: 1 files; direct child clusters: root file
- `SECURITY.md/`: 1 files; direct child clusters: root file
- `mise.toml/`: 1 files; direct child clusters: root file
- `renovate.json/`: 1 files; direct child clusters: root file

## Canonical Owner roots and actual file distribution

Manifest: `tools/repo/owners.toml`; schema_version=1, 21 nonoverlapping named Owner roots; each uses its own `mise` verification and release. Current Owner roots contain **4561** tracked files; **441** paths are outside those 21 roots, including deliberately central repository docs, Skills and CI. This is **not** an automatic orphan count.

| Current Owner / root | Git files | Representative local children | Existing check | Proven README version/lifecycle |
|---|---:|---|---|---|
| authority-catalog / `catalogs/authorities/` | 376 | observations:182, records:176, scripts:5, schemas:3, evidence:2 | `authority-catalog:verify` | not declared in README header |
| capability-catalog / `catalogs/capabilities/` | 77 | providers:36, packages:13, evidence:5, ele:4, scripts:4 | `capability-catalog:verify` | not declared in README header |
| composition / `packages/composition/` | 86 | src:24, tests:23, formal:16, docs:7, policies:4 | `composition:verify` | not declared in README header |
| control-plugin / `extensions/ordivon-control-plane/` | 2 | mcp.json:1, plugin.json:1 | `control-plugin:verify` | not declared in README header |
| runtime / `services/runtime/` | 452 | crates:139, research:132, scripts:67, docs:23, formal:18 | `runtime:verify` | schema_version=1, lifecycle=active, evidence_status=not_applicable |
| host / `services/host/` | 117 | tests:38, src:37, migrations:15, docs:6, packaging:4 | `host:verify` | not declared in README header |
| harness / `services/harness/` | 731 | tests:182, evidence:139, research:97, scripts:87, src:62 | `harness:verify` | schema_version=1, lifecycle=active, evidence_status=verified |
| gateway / `services/gateway/` | 107 | tests:31, src:26, formal:18, packaging:12, planning:7 | `gateway:verify` | not declared in README header |
| skills / `extensions/chatgpt-skills-mcp/` | 45 | tests:19, src:9, docs:3, scripts:3, config:2 | `skills:verify` | not declared in README header |
| security / `platform/security/` | 162 | labs:29, tests:24, scripts:23, docs:15, src:14 | `security:verify` | not declared in README header |
| workstation / `platform/workstation/` | 265 | providers:58, tests:40, workstation:40, ansible:20, docs:16 | `workstation:ci` | not declared in README header |
| network / `platform/network/` | 236 | consumers:105, tests:32, providers:20, acceptance:16, config:10 | `network:ci` | not declared in README header |
| artifact / `capabilities/artifact/` | 425 | artifact-delivery:180, tests:72, scripts:43, docs:28, artifact_capabilities:22 | `artifact:verify` | not declared in README header |
| distribution / `capabilities/distribution/` | 30 | evidence:15, scripts:6, adapters:3, .gitignore:1, README.md:1 | `distribution:verify` | not declared in README header |
| media / `capabilities/media/` | 553 | productions:213, research:110, src:70, tests:26, scripts:21 | `media:verify` | not declared in README header |
| preservation / `capabilities/preservation/` | 46 | artifacts:32, docs:5, scripts:3, systemd:2, README.md:1 | `preservation:verify` | not declared in README header |
| game / `domains/game/` | 387 | examples:333, test:9, scripts:8, knowledge:7, research:7 | `game:verify` | schema_version=1, lifecycle=active |
| capital / `domains/capital/` | 399 | tests:100, src:65, tools:53, scripts:50, config:28 | `capital:verify` | not declared in README header |
| data / `packages/data/` | 19 | src:5, docs:4, formal:3, scripts:2, tests:2 | `data:verify` | not declared in README header |
| web / `apps/web/` | 35 | src:15, test:7, evidence:3, .gitignore:1, README.md:1 | `web:verify` | not declared in README header |
| chaoxing-autosign / `apps/chaoxing-autosign/` | 11 | chaoxing_mvp:9, README.md:1, tests:1 | `chaoxing:verify` | not declared in README header |

## Module-file evidence: canonical entrypoint + largest real nontrivial code files

File sizes are **scan priorities, not quality violations**. A lockfile or vendored scene is not a maintainable-code problem just because it is large. Hashes are the original SHA-256 prefix at the pinned SourceCut.

### authority-catalog: catalogs/authorities/ (376 tracked)
- Entrypoints: `catalogs/authorities/README.md`, `catalogs/authorities/mise.toml`, `catalogs/authorities/pyproject.toml`
- `catalogs/authorities/scripts/authority_catalog.py` — 280 newline-counted lines; SHA12 `30c82bed668e`
- `catalogs/authorities/scripts/check_authority_catalog_r1.py` — 159 newline-counted lines; SHA12 `d0b247591621`
- `catalogs/authorities/scripts/authority_catalog_sources.py` — 150 newline-counted lines; SHA12 `40da61b4df5e`
- `catalogs/authorities/scripts/authority_catalog_search.py` — 109 newline-counted lines; SHA12 `842803e15c9f`
- `catalogs/authorities/scripts/check_historical_registration.py` — 83 newline-counted lines; SHA12 `d344b48d38b4`
- Direct children: observations=182, records=176, scripts=5, schemas=3, evidence=2, .gitignore=1, README.md=1, mise.toml=1, planning=1, pyproject.toml=1

### capability-catalog: catalogs/capabilities/ (77 tracked)
- Entrypoints: `catalogs/capabilities/README.md`, `catalogs/capabilities/AGENTS.md`
- `catalogs/capabilities/ele/studies.py` — 688 newline-counted lines; SHA12 `5f263cf426b7`
- `catalogs/capabilities/scripts/verify_reasoning_providers.py` — 225 newline-counted lines; SHA12 `61a285aa9f22`
- `catalogs/capabilities/scripts/github_radar_incremental.py` — 207 newline-counted lines; SHA12 `2955a58ab496`
- `catalogs/capabilities/routing/web_interaction_route.py` — 193 newline-counted lines; SHA12 `bcb239d9a358`
- `catalogs/capabilities/scripts/compare_worktrunk_owner_consumer.py` — 186 newline-counted lines; SHA12 `d791a7d7f6a1`
- Direct children: providers=36, packages=13, evidence=5, ele=4, scripts=4, tests=4, docs=2, routing=2, AGENTS.md=1, README.md=1

### composition: packages/composition/ (86 tracked)
- Entrypoints: `packages/composition/README.md`, `packages/composition/AGENTS.md`, `packages/composition/mise.toml`, `packages/composition/pyproject.toml`
- `packages/composition/src/ordivon_composition/verification_obligation_r1.py` — 770 newline-counted lines; SHA12 `a357afa852c5`
- `packages/composition/src/ordivon_composition/verification_impact.py` — 662 newline-counted lines; SHA12 `a07ab628c8b6`
- `packages/composition/src/ordivon_composition/cognitive_circuit_r1.py` — 449 newline-counted lines; SHA12 `26ece4dc4993`
- `packages/composition/scripts/pacti_timeout_obligation_r1.py` — 286 newline-counted lines; SHA12 `4f83f9d30168`
- `packages/composition/src/ordivon_composition/successor_contract_r1.py` — 279 newline-counted lines; SHA12 `dfb2f315a11d`
- Direct children: src=24, tests=23, formal=16, docs=7, policies=4, scripts=4, profiles=2, AGENTS.md=1, README.md=1, mise.toml=1

### control-plugin: extensions/ordivon-control-plane/ (2 tracked)
- Entrypoints: no standard README/AGENTS/mise/Cargo/pyproject/package at this exact root; inspect the native packaging/parent consumer
- Direct children: mcp.json=1, plugin.json=1

### runtime: services/runtime/ (452 tracked)
- Entrypoints: `services/runtime/README.md`, `services/runtime/AGENTS.md`, `services/runtime/mise.toml`, `services/runtime/pyproject.toml`, `services/runtime/Cargo.toml`
- `services/runtime/crates/ordivon-runtime-core/src/runtime/tests.rs` — 10788 newline-counted lines; SHA12 `31372e533592`
- `services/runtime/crates/ordivon-runtime-core/src/universal/tests.rs` — 4382 newline-counted lines; SHA12 `78424c3e31eb`
- `services/runtime/crates/ordivon-runtime-core/src/runtime/integration_tests.rs` — 3840 newline-counted lines; SHA12 `36a1ad655d83`
- `services/runtime/crates/ordivon-runtime-core/src/pg_admission.rs` — 3026 newline-counted lines; SHA12 `0bb75cffec22`
- `services/runtime/crates/ordivon-runtime-core/src/runtime/windows.rs` — 2875 newline-counted lines; SHA12 `90a484b67698`
- Direct children: crates=139, research=132, scripts=67, docs=23, formal=18, packaging=11, planning=10, .github=7, tests=7, examples=4

### host: services/host/ (117 tracked)
- Entrypoints: `services/host/README.md`, `services/host/AGENTS.md`, `services/host/mise.toml`, `services/host/pyproject.toml`, `services/host/mcp-surface.json`
- `services/host/src/ordivon_host_v2/social_space_queries.py` — 342 newline-counted lines; SHA12 `be75018a4321`
- `services/host/src/ordivon_host_v2/social_contracts.py` — 327 newline-counted lines; SHA12 `e605e76128d0`
- `services/host/src/ordivon_host_v2/attention_projections.py` — 324 newline-counted lines; SHA12 `69406a35bca8`
- `services/host/src/ordivon_host_v2/mcp_social_tools.py` — 318 newline-counted lines; SHA12 `9155d2f22177`
- `services/host/src/ordivon_host_v2/social_message_queries.py` — 305 newline-counted lines; SHA12 `357ae66a3d7a`
- Direct children: tests=38, src=37, migrations=15, docs=6, packaging=4, planning=4, formal=3, .gitignore=1, .python-version=1, AGENTS.md=1

### harness: services/harness/ (731 tracked)
- Entrypoints: `services/harness/README.md`, `services/harness/mise.toml`, `services/harness/pyproject.toml`
- `services/harness/src/ordivon_harness/ordivon/run_continuity.py` — 3186 newline-counted lines; SHA12 `95b27a07b5bb`
- `services/harness/src/ordivon_harness/ordivon/loop.py` — 2366 newline-counted lines; SHA12 `ecd016f277a8`
- `services/harness/scripts/agent_automation_browserless.py` — 1937 newline-counted lines; SHA12 `8f9c849cd47e`
- `services/harness/src/ordivon_harness/ordivon/runtime_bridge.py` — 1492 newline-counted lines; SHA12 `05cb6fbf0e22`
- `services/harness/scripts/agent_automation_release.py` — 1218 newline-counted lines; SHA12 `20ecd686be04`
- Direct children: tests=182, evidence=139, research=97, scripts=87, src=62, evals=48, docs=42, systemd=14, formal=13, config=11

### gateway: services/gateway/ (107 tracked)
- Entrypoints: `services/gateway/README.md`, `services/gateway/AGENTS.md`, `services/gateway/pyproject.toml`, `services/gateway/mcp-surface.json`
- `services/gateway/src/ordivon_gateway/mcp_server.py` — 489 newline-counted lines; SHA12 `562124bf876a`
- `services/gateway/src/ordivon_gateway/upstream.py` — 426 newline-counted lines; SHA12 `7e2695cfe65d`
- `services/gateway/src/ordivon_gateway/research_routes.py` — 424 newline-counted lines; SHA12 `0fd7bec5f994`
- `services/gateway/src/ordivon_gateway/capability_catalog.py` — 386 newline-counted lines; SHA12 `b2160632d09d`
- `services/gateway/src/ordivon_gateway/capability_authz.py` — 339 newline-counted lines; SHA12 `241bb2dc94e7`
- Direct children: tests=31, src=26, formal=18, packaging=12, planning=7, systemd=6, .python-version=1, AGENTS.md=1, README.md=1, enforcement-surface.json=1

### skills: extensions/chatgpt-skills-mcp/ (45 tracked)
- Entrypoints: `extensions/chatgpt-skills-mcp/README.md`, `extensions/chatgpt-skills-mcp/mise.toml`, `extensions/chatgpt-skills-mcp/pyproject.toml`
- `extensions/chatgpt-skills-mcp/src/ordivon_skills/catalog.py` — 750 newline-counted lines; SHA12 `9fc3576cf1f8`
- `extensions/chatgpt-skills-mcp/scripts/skills_mcp.py` — 692 newline-counted lines; SHA12 `85a09948f335`
- `extensions/chatgpt-skills-mcp/src/ordivon_skills/scanner.py` — 268 newline-counted lines; SHA12 `13318d7bb28b`
- `extensions/chatgpt-skills-mcp/scripts/cloudflare_skill_route.py` — 259 newline-counted lines; SHA12 `c3c13fff512c`
- `extensions/chatgpt-skills-mcp/src/ordivon_skills/sep2640.py` — 240 newline-counted lines; SHA12 `b96ee4a99e21`
- Direct children: tests=19, src=9, docs=3, scripts=3, config=2, plugins=2, .python-version=1, README.md=1, mise.toml=1, planning=1

### security: platform/security/ (162 tracked)
- Entrypoints: `platform/security/README.md`, `platform/security/mise.toml`, `platform/security/pyproject.toml`
- `platform/security/labs/agent-admission-rs/pnpm-lock.yaml` — 688 newline-counted lines; SHA12 `8a68ea6fe296`
- `platform/security/labs/agent-admission-rs/src/principal-store.ts` — 477 newline-counted lines; SHA12 `53b5cd341ec7`
- `platform/security/labs/agent-admission-rs/src/webauthn-e2e.ts` — 477 newline-counted lines; SHA12 `5e3313e916bc`
- `platform/security/scripts/promote_browser_security_pool_lkg.py` — 453 newline-counted lines; SHA12 `130290b0b618`
- `platform/security/labs/agent-admission-rs/src/grant-store.ts` — 429 newline-counted lines; SHA12 `8ec7b9d4f67d`
- Direct children: labs=29, tests=24, scripts=23, docs=15, src=14, contracts=13, fixtures=13, policies=9, .clusterfuzzlite=3, formal=3

### workstation: platform/workstation/ (265 tracked)
- Entrypoints: `platform/workstation/README.md`, `platform/workstation/mise.toml`, `platform/workstation/pyproject.toml`
- `platform/workstation/providers/cloudflare/pnpm-lock.yaml` — 1574 newline-counted lines; SHA12 `070d8b2b8a2c`
- `platform/workstation/providers/cloudflare/scripts/ordivon_edge_release.py` — 1318 newline-counted lines; SHA12 `9ff2af1c379e`
- `platform/workstation/providers/cloudflare/scripts/ordivon_cloudflare_tofu_handoff.py` — 865 newline-counted lines; SHA12 `ee1b7f5c625b`
- `platform/workstation/workstation/input_authority_ingress.py` — 669 newline-counted lines; SHA12 `e6aaae6dd375`
- `platform/workstation/workstation/windows/jev_fastpath_provider.py` — 635 newline-counted lines; SHA12 `ba1da708e35d`
- Direct children: providers=58, tests=40, workstation=40, ansible=20, docs=16, scripts=13, inventory=12, observability=12, tofu=9, contracts=6

### network: platform/network/ (236 tracked)
- Entrypoints: `platform/network/README.md`, `platform/network/AGENTS.md`, `platform/network/mise.toml`
- `platform/network/formal/egress_policy_refinement.py` — 372 newline-counted lines; SHA12 `31a1070949eb`
- `platform/network/scripts/monitoring-sourcecut-preflight.py` — 336 newline-counted lines; SHA12 `0c2e85a8bf27`
- `platform/network/formal/control_plane_independence.py` — 302 newline-counted lines; SHA12 `02c44d942ccd`
- `platform/network/consumers/browserless/acceptance/serial-browserless.sh` — 289 newline-counted lines; SHA12 `e4d9810f1c11`
- `platform/network/Taskfile.yml` — 285 newline-counted lines; SHA12 `67331343e612`
- Direct children: consumers=105, tests=32, providers=20, acceptance=16, config=10, reference=9, substrates=8, capabilities=6, formal=6, docs=5

### artifact: capabilities/artifact/ (425 tracked)
- Entrypoints: `capabilities/artifact/README.md`, `capabilities/artifact/mise.toml`, `capabilities/artifact/pyproject.toml`
- `capabilities/artifact/artifact-delivery/node/pnpm-lock.yaml` — 863 newline-counted lines; SHA12 `19fe8a4d2074`
- `capabilities/artifact/scripts/artifact_delivery_toolchain_doctor.py` — 641 newline-counted lines; SHA12 `229514854808`
- `capabilities/artifact/scripts/artifact_oci_package.py` — 637 newline-counted lines; SHA12 `c58f9a1efa6b`
- `capabilities/artifact/artifact_operations/providers/direct_python.py` — 606 newline-counted lines; SHA12 `8a946b181261`
- `capabilities/artifact/scripts/artifact_r2_mailbox.py` — 520 newline-counted lines; SHA12 `3bf2c1d6b402`
- Direct children: artifact-delivery=180, tests=72, scripts=43, docs=28, artifact_capabilities=22, artifact_verifiers=21, artifact_core=11, planning=10, artifact_verification=9, artifact_operations=8

### distribution: capabilities/distribution/ (30 tracked)
- Entrypoints: `capabilities/distribution/README.md`, `capabilities/distribution/mise.toml`
- `capabilities/distribution/scripts/test-structure.sh` — 21 newline-counted lines; SHA12 `f740764e5b83`
- `capabilities/distribution/scripts/test-postiz-surface.sh` — 20 newline-counted lines; SHA12 `44083c7a9913`
- `capabilities/distribution/scripts/test-github-provider-readback.sh` — 17 newline-counted lines; SHA12 `92973aab1457`
- `capabilities/distribution/scripts/test-openapi-generator.sh` — 13 newline-counted lines; SHA12 `6c1c156f3803`
- `capabilities/distribution/scripts/test-rclone.sh` — 12 newline-counted lines; SHA12 `428bd23525cb`
- Direct children: evidence=15, scripts=6, adapters=3, .gitignore=1, README.md=1, docs=1, external-lock.json=1, mise.toml=1, tests=1

### media: capabilities/media/ (553 tracked)
- Entrypoints: `capabilities/media/README.md`, `capabilities/media/AGENTS.md`, `capabilities/media/mise.toml`, `capabilities/media/pyproject.toml`, `capabilities/media/package.json`
- `capabilities/media/pnpm-lock.yaml` — 3559 newline-counted lines; SHA12 `f8b67152cae0`
- `capabilities/media/scripts/creative_library.py` — 613 newline-counted lines; SHA12 `7a3191aa972b`
- `capabilities/media/src/ordivon_studio/research/grounded_scoring.py` — 431 newline-counted lines; SHA12 `491a30963c81`
- `capabilities/media/src/ordivon_studio/research/search_calibration.py` — 401 newline-counted lines; SHA12 `5f8ffe9dc265`
- `capabilities/media/src/ordivon_studio/ecology/board.py` — 387 newline-counted lines; SHA12 `1bad8a0526d5`
- Direct children: productions=213, research=110, src=70, tests=26, scripts=21, apps=19, artifacts=16, docs=16, processing=16, formal=6

### preservation: capabilities/preservation/ (46 tracked)
- Entrypoints: `capabilities/preservation/README.md`
- `capabilities/preservation/scripts/verify_source.py` — 166 newline-counted lines; SHA12 `401400447066`
- `capabilities/preservation/scripts/fixity_consumer_contract.py` — 74 newline-counted lines; SHA12 `3fd23eabe9fe`
- `capabilities/preservation/config/archivematica-preservation-r10.compose.yml` — 27 newline-counted lines; SHA12 `903d18f8c16c`
- Direct children: artifacts=32, docs=5, scripts=3, systemd=2, README.md=1, SOURCE_BOUNDARY.json=1, config=1, planning=1

### game: domains/game/ (387 tracked)
- Entrypoints: `domains/game/README.md`, `domains/game/AGENTS.md`, `domains/game/mise.toml`, `domains/game/package.json`
- `domains/game/research/autonomous-interest-r7/evaluator_reference.py` — 601 newline-counted lines; SHA12 `009467f6d27b`
- `domains/game/pnpm-lock.yaml` — 398 newline-counted lines; SHA12 `36805def1867`
- `domains/game/research/autonomous-interest-r7/study_runner_reference.py` — 397 newline-counted lines; SHA12 `24ec4540a9c2`
- `domains/game/examples/orbit-collector/src/gameplay.rs` — 299 newline-counted lines; SHA12 `76f0bc6df849`
- `domains/game/research/autonomous-interest-r7/protocol_selftest.py` — 295 newline-counted lines; SHA12 `68c229171015`
- Direct children: examples=333, test=9, scripts=8, knowledge=7, research=7, docs=6, src=4, formal=3, .gitignore=1, .ordivon=1

### capital: domains/capital/ (399 tracked)
- Entrypoints: `domains/capital/README.md`, `domains/capital/mise.toml`, `domains/capital/pyproject.toml`
- `domains/capital/src/ordivon_capital/research/pit_joint_forecast.py` — 860 newline-counted lines; SHA12 `77192e42e628`
- `domains/capital/src/ordivon_capital/governance/policy_decision.py` — 606 newline-counted lines; SHA12 `991d41de48ee`
- `domains/capital/src/ordivon_capital/research/unit_r_dca.py` — 555 newline-counted lines; SHA12 `77bd154ea7d7`
- `domains/capital/tools/jsonschema_4_26_0/differential_r18.py` — 496 newline-counted lines; SHA12 `edaef6f535f9`
- `domains/capital/src/ordivon_capital/portfolio/multistage_policy.py` — 489 newline-counted lines; SHA12 `95917ded0550`
- Direct children: tests=100, src=65, tools=53, scripts=50, config=28, evidence=26, docs=19, formal=17, contracts=12, examples=5

### data: packages/data/ (19 tracked)
- Entrypoints: `packages/data/README.md`, `packages/data/AGENTS.md`, `packages/data/mise.toml`
- `packages/data/src/ordivon_data/odps_projection.py` — 181 newline-counted lines; SHA12 `b88acf393720`
- `packages/data/src/ordivon_data/catalog.py` — 177 newline-counted lines; SHA12 `580329137634`
- `packages/data/scripts/inspect_federation.py` — 134 newline-counted lines; SHA12 `c1c2c56afe91`
- `packages/data/src/ordivon_data/local_evidence.py` — 111 newline-counted lines; SHA12 `971f4d42e19e`
- `packages/data/scripts/project_owned_products.py` — 89 newline-counted lines; SHA12 `e988d5219f46`
- Direct children: src=5, docs=4, formal=3, scripts=2, tests=2, AGENTS.md=1, README.md=1, mise.toml=1

### web: apps/web/ (35 tracked)
- Entrypoints: `apps/web/README.md`, `apps/web/mise.toml`, `apps/web/package.json`
- `apps/web/pnpm-lock.yaml` — 1115 newline-counted lines; SHA12 `e20ec41fe970`
- `apps/web/src/store.ts` — 810 newline-counted lines; SHA12 `5f11322625b5`
- `apps/web/src/app.ts` — 721 newline-counted lines; SHA12 `ec49b263eefc`
- `apps/web/src/webauthn.ts` — 463 newline-counted lines; SHA12 `47dbee43bbc4`
- `apps/web/src/store-row-projections.ts` — 187 newline-counted lines; SHA12 `bf167852bf66`
- Direct children: src=15, test=7, evidence=3, .gitignore=1, README.md=1, agent-native-e2e.sh=1, browser-e2e.sh=1, mise.toml=1, package.json=1, planning=1

### chaoxing-autosign: apps/chaoxing-autosign/ (11 tracked)
- Entrypoints: `apps/chaoxing-autosign/README.md`
- `apps/chaoxing-autosign/chaoxing_mvp/engine.py` — 183 newline-counted lines; SHA12 `df6304fc0007`
- `apps/chaoxing-autosign/chaoxing_mvp/ledger.py` — 166 newline-counted lines; SHA12 `dddbb4fab053`
- `apps/chaoxing-autosign/chaoxing_mvp/models.py` — 122 newline-counted lines; SHA12 `472907a13152`
- `apps/chaoxing-autosign/chaoxing_mvp/adapters.py` — 75 newline-counted lines; SHA12 `1956320663e3`
- `apps/chaoxing-autosign/chaoxing_mvp/runner.py` — 67 newline-counted lines; SHA12 `ed71ee4020f6`
- Direct children: chaoxing_mvp=9, README.md=1, tests=1

## Existing native exhaustive source analysis (did NOT create a new scanner)

- `tools/repo/exhaustive_coverage.py --source-cut <40hex> --summary`: 5002/5002 source paths accounted for. This is *structural classification* and explicitly `proofReuseAdmissible=false`.
- Native reported source zones: 24; its 376 UNASSIGNED are to **this semantic-zone projection**, not necessarily missing natural Owner or untracked source. 55 files explicitly map to repository-mechanics region and 10 to formal source region.
- Existing derived plan map: 18 plan files, 160 declared nodes, 182 declared local endpoint edges; 9 reused local IDs are candidates scoped by plan, **not proof of real identity collision**. Do not create another LEGO registry.
- Native Python AST hints: 1460 Git Python paths; 2359 static candidate edges; 83 dynamic syntax sites; 8988 unresolved statements. These are not dynamic import resolution or physical consumers.
- Whole-repo existing `tools/repo/check_owner_boundaries.py`: active_files=2320, packages=10, seams=31, references=38, **valid**. Declared contract graph has 17 distinct directed Owner pairs, no multi-Owner SCC **within that explicitly declared graph**.

## Source consumer and language caveats

- A Git path contains no runtime proof; an installed unit or Helm/Podman/CDN resource may consume a dynamically selected source without a literal import.
- Repository dates and versions are per Owner. Absence of a frontmatter `schema_version` does not imply invalid contract; check the Owner's protocol and implementation itself.
- Some `domains/game/examples/` files are upstream/vendored inputs rather than authored logic; `catalogs/authorities/observations` and `capabilities/media/productions` are records/assets with their own origin. Keep different content forms separate.
- The *complete 5,002-path raw census* is reproducible from the immutable Git source with `git ls-tree -r --name-only ef17d6879d12faa61fff3bb762b0d500d73c9113`, plus the native exact-Git tool above. This curated document enumerates every **top-level directory** and each **Owner module**, and examines its principal files; it does not claim that 5,002 source bodies have all had independent semantic review.
