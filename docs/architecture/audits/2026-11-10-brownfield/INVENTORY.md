# INVENTORY — exact tracked Git source tree and module perimeter

**Phase 1 / mechanical census:** complete at `ef17d6879d12faa61fff3bb762b0d500d73c9113`, no code changes during this observation.
**Scope:** `git ls-files -z` is the input; no invented directories, ignored build outputs, `node_modules` or untracked secrets. Git source tree is not the deployment file system.

Tracked paths: **5002**. Checked stat bytes: **123,199,041**. This is a complete SOURCE name/physical-size enumeration, **not a 5,002-file semantic read or dynamic consumer proof**.

## Source roots

| Physical root | Tracked paths | Most common file extensions | Representative source categories |
|---|---:|---|---|
| `services` | 1407 | .py=593, .md=271, .json=237 | bounded Runtime / Host / Harness / Gateway code, formal contracts, tests, packaging |
| `capabilities` | 1054 | .json=374, .py=324, .md=171 | Artifact / Media / Preservation / Distribution owners and source/evidence assets |
| `domains` | 786 | .py=196, .json=100, .uid=89 | Capital and Game native domain code, examples, planning and history |
| `platform` | 663 | .py=180, .md=86, .json=77 | Workstation native ops, Network provider/consumer configs, Security contracts |
| `catalogs` | 532 | .json=386, .md=122, .py=18 | non-authoritative authority / capability / knowledge / data-product projections |
| `packages` | 105 | .py=41, .json=22, .md=17 | Composition and Data bounded shared libraries |
| `docs` | 104 | .md=58, .json=46 | architecture, migration and start reference/history |
| `studies` | 89 | .json=42, .py=26, .jsonld=6 | data lifecycle, experimental episodes |
| `tools` | 65 | .py=42, .sh=9, .toml=3 | repository mechanics and existing formal tooling |
| `.agents` | 63 | .md=62, .py=1 | Skills packages and source instructions |
| `extensions` | 47 | .py=28, .json=9, .md=4 | Skills MCP and thin control extension |
| `apps` | 46 | .ts=22, .py=10, .json=6 | Web and Chaoxing app entrypoints |
| `profiles` | 17 | .json=13, .md=4 | domain/research reference profiles |
| `.github` | 13 | .yml=11, (none)=1, .md=1 | native CI and governance |
| `(root)` | 9 | .md=4, (none)=3, .toml=1 | Git, README, AGENTS, contribution and task manifests |
| `tests` | 2 | .py=1, .json=1 | root-level integration helpers |

## Language/file classification

| Extension | Count |
|---|---:|
| `.py` | 1460 |
| `.json` | 1315 |
| `.md` | 849 |
| `(none)` | 146 |
| `.rs` | 131 |
| `.sh` | 91 |
| `.ts` | 89 |
| `.uid` | 89 |
| `.gd` | 86 |
| `.yml` | 69 |
| `.service` | 51 |
| `.toml` | 50 |
| `.png` | 44 |
| `.cfg` | 44 |
| `.yaml` | 39 |
| `.tscn` | 36 |
| `.import` | 32 |
| `.ps1` | 25 |
| `.sql` | 20 |
| `.conf` | 20 |
| `.lock` | 19 |
| `.svg` | 19 |
| `.lean` | 18 |
| `.target` | 17 |
| `.txt` | 16 |
| `.cs` | 15 |
| `.xml` | 15 |
| `.rego` | 13 |
| `.mdx` | 12 |
| `.tla` | 12 |
| `.tsx` | 11 |
| `.smt2` | 11 |
| `.timer` | 8 |
| `.jsonld` | 8 |
| `.html` | 7 |
| `.container` | 7 |
| `.wav` | 7 |
| `.tres` | 7 |
| `.mjs` | 6 |
| `.example` | 5 |

## High-impact entrypoints and specialized source roles

- Physical Runtime: `services/runtime/Cargo.toml`, `services/runtime/crates/ordivon-runtime-core/src/runtime/{engine.rs,types.rs,tests.rs}`, `services/runtime/AGENTS.md`.
- Host Work/Social: `services/host/src/ordivon_host_v2/{work_store.py,work_queries.py,social_store.py}`, `services/host/migrations/versions/`, `services/host/README.md`.
- Harness Run: `services/harness/src/ordivon_harness/ordivon/{loop.py,run_continuity.py}`, `services/harness/src/ordivon_harness/{postgres_store.py,sqlite_store.py}`.
- Gateway: `services/gateway/src/ordivon_gateway/{mcp_server.py,upstream.py}`, `services/gateway/mcp-surface.json`.
- Workstation native: `platform/workstation/{ansible,tofu,postgresql,systemd,providers}`; Network `platform/network/{substrates,providers,consumers}`; Security `platform/security/{contracts,src,policies}`.
- Artifact source/evidence: `capabilities/artifact/{artifact_core,artifact_operations,artifact_verification,artifact_trust,artifact_verifiers}`.
- Media rendering and original bytes: `capabilities/media/{src,creative-library,productions,research,processing,apps}`.
- Capital modeling and provider contracts: `domains/capital/{src,formal,contracts,schema,tools,config}`; Game `domains/game/{src,examples,formal,knowledge}`.
- Shared libraries: `packages/composition/src/ordivon_composition/` and `packages/data/src/`; Web entrypoint `apps/web/src/`; Skills MCP `extensions/chatgpt-skills-mcp/src/`.
- Repo/LEGO navigation: `tools/repo/{owners.toml,dependency_contracts.toml,check_owner_boundaries.py,check_architecture_docs.py,exhaustive_coverage.py}`.

## Potential legacy/experimental/source-record regions (NOT automatically deletable)

- `services/harness/{evals,evidence,research}` includes historical bounded experiment inputs and source receipts; some remain real test consumers.
- `capabilities/media/{productions,artifacts,research}` includes versioned production masters, source and evidence; an identical PNG in two packages is not necessarily redundant provenance.
- `domains/capital/tools/legacy_replay/` is explicitly historical but may be consumed by fixtures or replay.
- `domains/game/examples/` contains packaged examples, vendor assets and native Godot/Bevy mechanics; directory name does not equal unused product.
- `docs/architecture/evidence/` has historical claims that must never be silently replaced by present conclusions.
- `platform/security/contracts` and `platform/security/labs` contain some identical small files but distinct experimental versus contract packaging.
- `services/harness/src/ordivon_harness/sqlite_store.py` is **not** safe to delete from ‘PG-first’ alone; current scripts still import it.

## Complete nested SOURCE tree (all 5,002 tracked paths)

```text
ordivon/
  ├── .agents
  │   └── skills
  │       ├── artifact-work
  │       │   ├── references
  │       │   │   ├── audio.md
  │       │   │   ├── consumer-acceptance.md
  │       │   │   ├── dataset.md
  │       │   │   ├── design-3d.md
  │       │   │   ├── geospatial.md
  │       │   │   ├── moving-image.md
  │       │   │   ├── presentation.md
  │       │   │   ├── software-release.md
  │       │   │   └── still-image.md
  │       │   └── SKILL.md
  │       ├── causal-intervention
  │       │   └── SKILL.md
  │       ├── ck-design
  │       │   └── SKILL.md
  │       ├── compositional-contracts
  │       │   └── SKILL.md
  │       ├── design-structure-matrix
  │       │   └── SKILL.md
  │       ├── enterprise-work
  │       │   └── SKILL.md
  │       ├── evidence-calibrated-dialogue
  │       │   └── SKILL.md
  │       ├── evolutionary-search
  │       │   └── SKILL.md
  │       ├── exploration-policy
  │       │   └── SKILL.md
  │       ├── external-capability-evaluation
  │       │   └── SKILL.md
  │       ├── external-world-evidence-review
  │       │   └── SKILL.md
  │       ├── feedback-control
  │       │   └── SKILL.md
  │       ├── feedback-grounded-repair
  │       │   └── SKILL.md
  │       ├── finance-demo-execution
  │       │   └── SKILL.md
  │       ├── finance-experiment-review
  │       │   └── SKILL.md
  │       ├── finance-paper-investment
  │       │   └── SKILL.md
  │       ├── finance-paper-risk-review
  │       │   └── SKILL.md
  │       ├── finance-pit-joint-forecast
  │       │   └── SKILL.md
  │       ├── fmea-fta
  │       │   └── SKILL.md
  │       ├── gateway-formal-routing
  │       │   └── SKILL.md
  │       ├── information-flow-analysis
  │       │   └── SKILL.md
  │       ├── media-native-processing
  │       │   └── SKILL.md
  │       ├── media-studio-navigation
  │       │   └── SKILL.md
  │       ├── method-router
  │       │   ├── references
  │       │   │   ├── agent-engineering-delivery.md
  │       │   │   ├── innovation-lens-routing.md
  │       │   │   ├── method-map.md
  │       │   │   └── representation-first.md
  │       │   └── SKILL.md
  │       ├── minimum-sufficient-representation
  │       │   └── SKILL.md
  │       ├── mobile-app-security
  │       │   ├── references
  │       │   │   └── top3-upstream-notes.md
  │       │   └── SKILL.md
  │       ├── natural-chinese-writing
  │       │   └── SKILL.md
  │       ├── ordivon-security-owner
  │       │   └── SKILL.md
  │       ├── organizational-cybernetics
  │       │   └── SKILL.md
  │       ├── ppt-master
  │       │   └── SKILL.md
  │       ├── project-kernel-decomposition
  │       │   ├── references
  │       │   │   ├── decomposition-contract.md
  │       │   │   └── node-graph-contract.md
  │       │   └── SKILL.md
  │       ├── recursive-lego-calculus
  │       │   ├── references
  │       │   │   ├── consumer-rooted-retirement.md
  │       │   │   ├── formal-model.md
  │       │   │   ├── formal-thinking-legos-human-agent.md
  │       │   │   └── owner-provider-human-agent.md
  │       │   └── SKILL.md
  │       ├── research-claim-framing
  │       │   └── SKILL.md
  │       ├── research-publication-closure
  │       │   └── SKILL.md
  │       ├── research-publication-perceptual-conformance
  │       │   └── SKILL.md
  │       ├── skill-supply-chain-audit
  │       │   ├── references
  │       │   │   └── skillspector-contract.md
  │       │   └── SKILL.md
  │       ├── stpa
  │       │   └── SKILL.md
  │       ├── systems-engineering
  │       │   └── SKILL.md
  │       ├── task-space-reentry
  │       │   ├── references
  │       │   │   └── task-packet.md
  │       │   ├── scripts
  │       │   │   └── check_obligation_handoff.py
  │       │   └── SKILL.md
  │       └── web-provider-routing
  │           └── SKILL.md
  ├── .github
  │   ├── ISSUE_TEMPLATE
  │   │   ├── bug_report.yml
  │   │   ├── config.yml
  │   │   ├── feature_request.yml
  │   │   └── game-player-feedback.yml
  │   ├── workflows
  │   │   ├── ci.yml
  │   │   ├── codeql.yml
  │   │   ├── game-factory.yml
  │   │   ├── game-orbit-factory.yml
  │   │   ├── game-rules-proof.yml
  │   │   └── runtime-release.yml
  │   ├── CODEOWNERS
  │   ├── dependabot.yml
  │   └── PULL_REQUEST_TEMPLATE.md
  ├── apps
  │   ├── chaoxing-autosign
  │   │   ├── chaoxing_mvp
  │   │   │   ├── __init__.py
  │   │   │   ├── adapters.py
  │   │   │   ├── cli.py
  │   │   │   ├── engine.py
  │   │   │   ├── ledger.py
  │   │   │   ├── models.py
  │   │   │   ├── policy.py
  │   │   │   ├── ports.py
  │   │   │   └── runner.py
  │   │   ├── tests
  │   │   │   └── test_chaoxing_autosign_mvp.py
  │   │   └── README.md
  │   └── web
  │       ├── evidence
  │       │   ├── AGENT-AUTHORITY-BROWSER-E2E-R1.json
  │       │   ├── AGENT-NATIVE-WEBSITE-E2E-R1.json
  │       │   └── HUMAN-RAIL-BROWSER-E2E-R1.json
  │       ├── planning
  │       │   └── lego-plan-r1.json
  │       ├── src
  │       │   ├── agent-authority.ts
  │       │   ├── app.ts
  │       │   ├── browser-request-boundary.ts
  │       │   ├── config.ts
  │       │   ├── errors.ts
  │       │   ├── identity-digests.ts
  │       │   ├── model.ts
  │       │   ├── security-agent-verifier.ts
  │       │   ├── server.ts
  │       │   ├── store-agent-grants.ts
  │       │   ├── store-row-projections.ts
  │       │   ├── store-schema.ts
  │       │   ├── store-sessions.ts
  │       │   ├── store.ts
  │       │   └── webauthn.ts
  │       ├── test
  │       │   ├── agent-authority.test.ts
  │       │   ├── agent-native-e2e.ts
  │       │   ├── app.test.ts
  │       │   ├── browser-e2e.ts
  │       │   ├── store-rows.test.ts
  │       │   ├── store-schema.test.ts
  │       │   └── verification-entry.test.ts
  │       ├── .gitignore
  │       ├── agent-native-e2e.sh
  │       ├── browser-e2e.sh
  │       ├── mise.toml
  │       ├── package.json
  │       ├── pnpm-lock.yaml
  │       ├── pnpm-workspace.yaml
  │       ├── README.md
  │       └── tsconfig.json
  ├── capabilities
  │   ├── artifact
  │   │   ├── artifact-delivery
  │   │   │   ├── consumer-acceptance
  │   │   │   │   ├── game-godot-production-smoke-linux-elf-r1.json
  │   │   │   │   ├── game-station-zero-aseprite-horizontal-sheet-r1.json
  │   │   │   │   ├── game-station-zero-ogg-vorbis-r1.json
  │   │   │   │   ├── game-station-zero-still-image-r1.json
  │   │   │   │   ├── game-station-zero-svg-static-r1.json
  │   │   │   │   ├── game-station-zero-tiled-tmj-r1.json
  │   │   │   │   ├── game-veilwild-glb-material-scene-r1.json
  │   │   │   │   ├── game-veilwild-glb-skinned-animation-r1.json
  │   │   │   │   └── game-veilwild-wave-pcm16-r1.json
  │   │   │   ├── examples
  │   │   │   │   ├── document-r1.json
  │   │   │   │   ├── pdf-accessible-r1.json
  │   │   │   │   ├── pdf-fixed-r1.json
  │   │   │   │   ├── pdu-sdu-presentation-r1.json
  │   │   │   │   ├── presentation-local-development-r1.json
  │   │   │   │   ├── presentation-local-development-request-r1.json
  │   │   │   │   ├── presentation-local-development-source-r1.json
  │   │   │   │   ├── presentation-native-smoke-request-r1.json
  │   │   │   │   ├── presentation-native-smoke-source-r1.json
  │   │   │   │   ├── presentation-ultrawide-34x10-r1.json
  │   │   │   │   ├── spreadsheet-r1.json
  │   │   │   │   ├── web-r1.json
  │   │   │   │   ├── web-smoke-request-r1.json
  │   │   │   │   └── web-smoke-source-r1.html
  │   │   │   ├── golden
  │   │   │   │   ├── pdu-sdu-34x10-r1
  │   │   │   │   │   ├── pdu-sdu-34x10-acceptance-lineage-r1.json
  │   │   │   │   │   ├── pdu-sdu-34x10-acceptance-r2.json
  │   │   │   │   │   ├── pdu-sdu-34x10-deck-migration-evidence-r1.json
  │   │   │   │   │   ├── pdu-sdu-34x10-deck-reference-map-r1.json
  │   │   │   │   │   ├── pdu-sdu-34x10-deck-semantic-overlay-r1.json
  │   │   │   │   │   ├── pdu-sdu-34x10-determinism-evidence-r1.json
  │   │   │   │   │   ├── pdu-sdu-34x10-opc-member-projection-r2.json
  │   │   │   │   │   ├── pdu-sdu-34x10-runtime-input-set-r1.json
  │   │   │   │   │   ├── pdu-sdu-34x10-runtime-package-input-set-r2.json
  │   │   │   │   │   ├── pdu-sdu-34x10-slide01-migration-evidence-r1.json
  │   │   │   │   │   ├── pdu-sdu-34x10-slide01-reference-map-r1.json
  │   │   │   │   │   └── pdu-sdu-34x10-slide01-semantic-overlay-r1.json
  │   │   │   │   ├── pdu-sdu-r1-font-repair.json
  │   │   │   │   └── pdu-sdu-r1.manifest.json
  │   │   │   ├── node
  │   │   │   │   ├── package.json
  │   │   │   │   ├── pnpm-lock.yaml
  │   │   │   │   ├── pnpm-workspace.yaml
  │   │   │   │   ├── probe.mjs
  │   │   │   │   ├── verify_ogg_vorbis.mjs
  │   │   │   │   └── verify_svg_static.mjs
  │   │   │   ├── openxml-nix
  │   │   │   │   ├── flake.lock
  │   │   │   │   └── flake.nix
  │   │   │   ├── openxml-validator
  │   │   │   │   ├── ArtifactOpenXmlValidator.csproj
  │   │   │   │   └── Program.cs
  │   │   │   ├── policy
  │   │   │   │   └── release.rego
  │   │   │   ├── python-uv
  │   │   │   │   ├── .python-version
  │   │   │   │   ├── pyproject.toml
  │   │   │   │   └── uv.lock
  │   │   │   ├── shadow-bindings
  │   │   │   │   ├── audio-flac-pcm16-local-r1.json
  │   │   │   │   ├── audio-ogg-vorbis-local-r1.json
  │   │   │   │   ├── audio-wave-pcm16-local-r1.json
  │   │   │   │   ├── cad-step-solid-local-r1.json
  │   │   │   │   ├── dataset-parquet-flat-local-r1.json
  │   │   │   │   ├── design-2d-aseprite-local-r1.json
  │   │   │   │   ├── design-2d-tiled-tmj-local-r1.json
  │   │   │   │   ├── design-3d-glb-material-scene-local-r1.json
  │   │   │   │   ├── design-3d-glb-skinned-animation-local-r1.json
  │   │   │   │   ├── design-3d-glb-static-mesh-local-r1.json
  │   │   │   │   ├── eda-kicad-pcb-local-r1.json
  │   │   │   │   ├── eda-spice-transient-local-r1.json
  │   │   │   │   ├── geospatial-geopackage-point-local-r1.json
  │   │   │   │   ├── message-internet-text-local-r1.json
  │   │   │   │   ├── moving-image-matroska-ffv1-local-r1.json
  │   │   │   │   ├── software-release-linux-elf-executable-local-r1.json
  │   │   │   │   ├── software-release-oci-image-local-r1.json
  │   │   │   │   ├── still-image-png-srgb-local-r1.json
  │   │   │   │   ├── still-image-svg-static-local-r1.json
  │   │   │   │   └── web-archive-warc-response-local-r1.json
  │   │   │   ├── shadow-contracts
  │   │   │   │   ├── game-station-zero-ogg-vorbis-r1
  │   │   │   │   │   ├── aftermath.json
  │   │   │   │   │   ├── commit.json
  │   │   │   │   │   └── plan-ready.json
  │   │   │   │   ├── audio-flac-contract-v1.schema.json
  │   │   │   │   ├── audio-flac-pcm16-smoke-r1.json
  │   │   │   │   ├── audio-ogg-vorbis-contract-v1.schema.json
  │   │   │   │   ├── audio-wave-pcm16-contract-v1.schema.json
  │   │   │   │   ├── audio-wave-pcm16-game-smoke-r1.json
  │   │   │   │   ├── cad-step-solid-contract-v1.schema.json
  │   │   │   │   ├── dataset-contract-v1.schema.json
  │   │   │   │   ├── dataset-parquet-flat-smoke-r1.json
  │   │   │   │   ├── design-2d-aseprite-sheet-contract-v1.schema.json
  │   │   │   │   ├── design-2d-tiled-tmj-contract-v1.schema.json
  │   │   │   │   ├── design-3d-glb-contract-v1.schema.json
  │   │   │   │   ├── design-3d-glb-material-scene-contract-v1.schema.json
  │   │   │   │   ├── design-3d-glb-material-scene-game-smoke-r1.json
  │   │   │   │   ├── design-3d-glb-skinned-animation-contract-v1.schema.json
  │   │   │   │   ├── design-3d-glb-skinned-animation-game-smoke-r1.json
  │   │   │   │   ├── design-3d-glb-static-mesh-smoke-r1.json
  │   │   │   │   ├── eda-kicad-pcb-contract-v1.schema.json
  │   │   │   │   ├── eda-spice-transient-measure-contract-v1.schema.json
  │   │   │   │   ├── game-station-zero-expression-aseprite-sheet-r1.json
  │   │   │   │   ├── game-station-zero-specialists-aseprite-sheet-r1.json
  │   │   │   │   ├── game-station-zero-tiled-tmj-r1.json
  │   │   │   │   ├── geospatial-geopackage-point-smoke-r1.json
  │   │   │   │   ├── geospatial-vector-contract-v1.schema.json
  │   │   │   │   ├── message-internet-text-contract-v1.schema.json
  │   │   │   │   ├── message-internet-text-smoke-r1.json
  │   │   │   │   ├── moving-image-ffv1-contract-v1.schema.json
  │   │   │   │   ├── moving-image-matroska-ffv1-smoke-r1.json
  │   │   │   │   ├── software-release-linux-elf-contract-v1.schema.json
  │   │   │   │   ├── software-release-linux-elf-game-godot-smoke-r1.json
  │   │   │   │   ├── software-release-oci-contract-v1.schema.json
  │   │   │   │   ├── software-release-oci-image-smoke-r1.json
  │   │   │   │   ├── web-archive-warc-response-contract-v1.schema.json
  │   │   │   │   └── web-archive-warc-response-smoke-r1.json
  │   │   │   ├── shadow-profiles
  │   │   │   │   ├── audio-flac-pcm16-r1.json
  │   │   │   │   ├── audio-ogg-vorbis-r1.json
  │   │   │   │   ├── audio-wave-pcm16-r1.json
  │   │   │   │   ├── dataset-parquet-flat-r1.json
  │   │   │   │   ├── design-2d-aseprite-horizontal-sheet-r1.json
  │   │   │   │   ├── design-2d-tiled-tmj-object-map-r1.json
  │   │   │   │   ├── design-3d-glb-material-scene-r1.json
  │   │   │   │   ├── design-3d-glb-skinned-animation-r1.json
  │   │   │   │   ├── design-3d-glb-static-mesh-r1.json
  │   │   │   │   ├── design-3d-step-solid-r1.json
  │   │   │   │   ├── eda-kicad-pcb-gerber-r1.json
  │   │   │   │   ├── eda-spice-transient-measure-r1.json
  │   │   │   │   ├── geospatial-geopackage-point-r1.json
  │   │   │   │   ├── message-internet-text-r1.json
  │   │   │   │   ├── moving-image-matroska-ffv1-v3-r1.json
  │   │   │   │   ├── software-release-linux-elf-executable-r1.json
  │   │   │   │   ├── software-release-oci-image-r1.json
  │   │   │   │   ├── still-image-png-srgb-r1.json
  │   │   │   │   ├── still-image-svg-static-r1.json
  │   │   │   │   └── web-archive-warc-response-r1.json
  │   │   │   ├── shadow-v2
  │   │   │   │   ├── examples
  │   │   │   │   │   ├── audio-flac-pcm16-r1-v2.json
  │   │   │   │   │   ├── audio-ogg-vorbis-r1-v2.json
  │   │   │   │   │   ├── audio-wave-pcm16-r1-v2.json
  │   │   │   │   │   ├── dataset-parquet-flat-r1-v2.json
  │   │   │   │   │   ├── design-2d-aseprite-horizontal-sheet-r1-v2.json
  │   │   │   │   │   ├── design-2d-tiled-tmj-object-map-r1-v2.json
  │   │   │   │   │   ├── design-3d-glb-material-scene-r1-v2.json
  │   │   │   │   │   ├── design-3d-glb-skinned-animation-r1-v2.json
  │   │   │   │   │   ├── design-3d-glb-static-mesh-r1-v2.json
  │   │   │   │   │   ├── design-3d-step-solid-r1-v2.json
  │   │   │   │   │   ├── document-r1-v2.json
  │   │   │   │   │   ├── eda-kicad-pcb-gerber-r1-v2.json
  │   │   │   │   │   ├── eda-spice-transient-measure-r1-v2.json
  │   │   │   │   │   ├── geospatial-geopackage-point-r1-v2.json
  │   │   │   │   │   ├── message-internet-text-r1-v2.json
  │   │   │   │   │   ├── moving-image-matroska-ffv1-v3-r1-v2.json
  │   │   │   │   │   ├── pdf-accessible-r1-v2.json
  │   │   │   │   │   ├── pdf-fixed-r1-v2.json
  │   │   │   │   │   ├── pdu-sdu-presentation-r1-v2.json
  │   │   │   │   │   ├── presentation-local-development-r1-v2.json
  │   │   │   │   │   ├── presentation-ultrawide-34x10-r1-v2.json
  │   │   │   │   │   ├── software-release-linux-elf-executable-r1-v2.json
  │   │   │   │   │   ├── software-release-oci-image-r1-v2.json
  │   │   │   │   │   ├── spreadsheet-r1-v2.json
  │   │   │   │   │   ├── still-image-png-srgb-r1-v2.json
  │   │   │   │   │   ├── still-image-svg-static-r1-v2.json
  │   │   │   │   │   ├── web-archive-warc-response-r1-v2.json
  │   │   │   │   │   └── web-r1-v2.json
  │   │   │   │   └── profile-v2-mapping-manifest-r1.json
  │   │   │   ├── verification
  │   │   │   │   └── request-v1.schema.json
  │   │   │   ├── artifact-python-runtime-v1.lock.json
  │   │   │   ├── build-capability-bindings-v1.json
  │   │   │   ├── cad-toolchain-r1.lock.json
  │   │   │   ├── capability-bindings-v1.json
  │   │   │   ├── mise.toml
  │   │   │   ├── opc-member-projection-v1.schema.json
  │   │   │   ├── openxml-assurance-fault-taxonomy-v1.json
  │   │   │   ├── openxml-assurance-method-v1.json
  │   │   │   ├── openxml-external-evidence-r1.json
  │   │   │   ├── openxml-runtime-v1.lock.json
  │   │   │   ├── ppt-master-provider-v1.lock.json
  │   │   │   ├── presentation-semantic-svg-source-v1.schema.json
  │   │   │   ├── presentation-source-v1.schema.json
  │   │   │   ├── profile-v1.schema.json
  │   │   │   ├── profile-v2.shadow.schema.json
  │   │   │   ├── r2-mailbox-v1.schema.json
  │   │   │   ├── request-v1.schema.json
  │   │   │   ├── sigstore-local-signing-config-v1.json
  │   │   │   ├── taxonomy-v1.json
  │   │   │   ├── toolchain-r1.lock.json
  │   │   │   ├── toolchain-v1.lock.json
  │   │   │   ├── toolchain-v1.plan.json
  │   │   │   └── vsa-trust-policy-v1.schema.json
  │   │   ├── artifact_capabilities
  │   │   │   ├── presentation
  │   │   │   │   ├── __init__.py
  │   │   │   │   ├── admission.py
  │   │   │   │   ├── canonicalization.py
  │   │   │   │   ├── common.py
  │   │   │   │   ├── ppt_master.py
  │   │   │   │   ├── python_pptx.py
  │   │   │   │   └── reference_projection.py
  │   │   │   ├── publication
  │   │   │   │   ├── __init__.py
  │   │   │   │   ├── attestation.py
  │   │   │   │   ├── contract.py
  │   │   │   │   ├── geometry.py
  │   │   │   │   ├── inventory.py
  │   │   │   │   ├── observer_task.py
  │   │   │   │   ├── perceptual.py
  │   │   │   │   ├── probe.py
  │   │   │   │   ├── provider_adapter.py
  │   │   │   │   ├── semantic_layout.py
  │   │   │   │   └── visual.py
  │   │   │   ├── __init__.py
  │   │   │   ├── dispatch.py
  │   │   │   ├── document.py
  │   │   │   └── passthrough.py
  │   │   ├── artifact_core
  │   │   │   ├── __init__.py
  │   │   │   ├── admission.py
  │   │   │   ├── bindings.py
  │   │   │   ├── build_bindings.py
  │   │   │   ├── build_planning.py
  │   │   │   ├── contracts.py
  │   │   │   ├── input_snapshot.py
  │   │   │   ├── json_validation.py
  │   │   │   ├── profile_refinement.py
  │   │   │   ├── profile_v1.py
  │   │   │   └── profiles.py
  │   │   ├── artifact_evidence
  │   │   │   ├── __init__.py
  │   │   │   ├── delivery.py
  │   │   │   └── snapshot.py
  │   │   ├── artifact_operations
  │   │   │   ├── providers
  │   │   │   │   ├── __init__.py
  │   │   │   │   ├── common.py
  │   │   │   │   ├── direct_python.py
  │   │   │   │   └── oci_toolchain.py
  │   │   │   ├── __init__.py
  │   │   │   ├── contract.py
  │   │   │   ├── executor.py
  │   │   │   └── receipt.py
  │   │   ├── artifact_trust
  │   │   │   ├── __init__.py
  │   │   │   ├── cosign_toolchain.py
  │   │   │   ├── provenance.py
  │   │   │   ├── sigstore_bundle.py
  │   │   │   ├── trust_policy.py
  │   │   │   ├── verification_summary.py
  │   │   │   └── vsa.py
  │   │   ├── artifact_verification
  │   │   │   ├── formal
  │   │   │   │   ├── verify_claim_coverage.py
  │   │   │   │   ├── verify_native_identity.py
  │   │   │   │   └── verify_profile_refinement.py
  │   │   │   ├── __init__.py
  │   │   │   ├── claim_coverage.py
  │   │   │   ├── evidence.py
  │   │   │   ├── native_identity.py
  │   │   │   ├── stage.py
  │   │   │   └── tool_identity.py
  │   │   ├── artifact_verifiers
  │   │   │   ├── document
  │   │   │   │   ├── __init__.py
  │   │   │   │   ├── dependencies.py
  │   │   │   │   ├── semantics.py
  │   │   │   │   └── toolchain.py
  │   │   │   ├── openxml
  │   │   │   │   ├── __init__.py
  │   │   │   │   ├── toolchain.py
  │   │   │   │   └── validator.py
  │   │   │   ├── pdf
  │   │   │   │   ├── __init__.py
  │   │   │   │   ├── conformance.py
  │   │   │   │   ├── structural.py
  │   │   │   │   └── toolchain.py
  │   │   │   ├── presentation
  │   │   │   │   ├── __init__.py
  │   │   │   │   ├── gate.py
  │   │   │   │   ├── inspection.py
  │   │   │   │   └── semantics.py
  │   │   │   ├── web
  │   │   │   │   ├── node
  │   │   │   │   │   └── verify_html.mjs
  │   │   │   │   ├── __init__.py
  │   │   │   │   ├── browser.py
  │   │   │   │   ├── conformance.py
  │   │   │   │   └── toolchain.py
  │   │   │   └── __init__.py
  │   │   ├── config
  │   │   │   ├── zot
  │   │   │   │   └── local-registry-r1.json
  │   │   │   └── artifact-r2-mailbox-r1.json
  │   │   ├── docs
  │   │   │   ├── artifact-build-delivery-e2e-authoring-orchestration-v1.md
  │   │   │   ├── artifact-build-delivery-e2e-toolchain-v1.md
  │   │   │   ├── artifact-build-delivery-e2e-v1.md
  │   │   │   ├── ARTIFACT_CAD_ADMISSION_BOUNDARY_R1.md
  │   │   │   ├── ARTIFACT_CAPABILITY_DECOMPOSITION_WAVE_A15_R1.md
  │   │   │   ├── ARTIFACT_CLAIM_COVERAGE_FORMAL_R1.md
  │   │   │   ├── ARTIFACT_FAMILY_AUDIO_OGG_VORBIS_R1.md
  │   │   │   ├── ARTIFACT_FAMILY_AUDIO_R1.md
  │   │   │   ├── ARTIFACT_FAMILY_AUDIO_WAVE_PCM16_R1.md
  │   │   │   ├── ARTIFACT_FAMILY_DATASET_R1.md
  │   │   │   ├── ARTIFACT_FAMILY_DESIGN_2D_ASEPRITE_R1.md
  │   │   │   ├── ARTIFACT_FAMILY_DESIGN_2D_TILED_R1.md
  │   │   │   ├── ARTIFACT_FAMILY_DESIGN_3D_R1.md
  │   │   │   ├── ARTIFACT_FAMILY_EDA_R1.md
  │   │   │   ├── ARTIFACT_FAMILY_GEOSPATIAL_R1.md
  │   │   │   ├── ARTIFACT_FAMILY_MESSAGE_R1.md
  │   │   │   ├── ARTIFACT_FAMILY_MOVING_IMAGE_R1.md
  │   │   │   ├── ARTIFACT_FAMILY_SOFTWARE_RELEASE_ELF_R1.md
  │   │   │   ├── ARTIFACT_FAMILY_SOFTWARE_RELEASE_R1.md
  │   │   │   ├── ARTIFACT_FAMILY_STILL_IMAGE_R1.md
  │   │   │   ├── ARTIFACT_FAMILY_STILL_IMAGE_SVG_R1.md
  │   │   │   ├── ARTIFACT_FAMILY_WEB_ARCHIVE_R1.md
  │   │   │   ├── ARTIFACT_PROFILE_AUTHORITY_REFINEMENT_R1.md
  │   │   │   ├── ARTIFACT_R2_S1_EVALUATION_PRESSURE_R1.md
  │   │   │   ├── ARTIFACT_R2_S1B_CLAIM_RESULTS_PRESSURE_R1.md
  │   │   │   ├── ARTIFACT_REDECOMPOSITION_R1.md
  │   │   │   ├── ARTIFACT_VERIFICATION_SERVICE_R1.md
  │   │   │   └── SOURCE_AUTHORITY_ACCEPTANCE_20260912.md
  │   │   ├── planning
  │   │   │   ├── prototypes
  │   │   │   │   ├── claim_results_adapter_r1.py
  │   │   │   │   ├── evidence_observation_r1.py
  │   │   │   │   ├── standing_decision_r1.py
  │   │   │   │   └── verifier_plugin_contract_r2.py
  │   │   │   ├── claim-results-adapter-pressure-r1.json
  │   │   │   ├── evaluation-model-pressure-r1.json
  │   │   │   ├── evidence-standing-pressure-r1.json
  │   │   │   ├── lego-plan-r2.json
  │   │   │   ├── standing-decision-pressure-r1.json
  │   │   │   └── verifier-plugin-result-r2-candidate.schema.json
  │   │   ├── scripts
  │   │   │   ├── artifact_agent_surface.py
  │   │   │   ├── artifact_aseprite.py
  │   │   │   ├── artifact_audio.py
  │   │   │   ├── artifact_cad_step.py
  │   │   │   ├── artifact_dataset.py
  │   │   │   ├── artifact_deliver_html.py
  │   │   │   ├── artifact_delivery_toolchain_doctor.py
  │   │   │   ├── artifact_design3d.py
  │   │   │   ├── artifact_eda.py
  │   │   │   ├── artifact_geospatial.py
  │   │   │   ├── artifact_message.py
  │   │   │   ├── artifact_moving_image.py
  │   │   │   ├── artifact_oci_package.py
  │   │   │   ├── artifact_ogg_vorbis.py
  │   │   │   ├── artifact_openxml_dotnet_wrapper.py
  │   │   │   ├── artifact_openxml_environment.py
  │   │   │   ├── artifact_openxml_external_evidence.py
  │   │   │   ├── artifact_openxml_validator_wrapper.py
  │   │   │   ├── artifact_profile_v2.py
  │   │   │   ├── artifact_python_environment.py
  │   │   │   ├── artifact_python_wrapper.py
  │   │   │   ├── artifact_r2_mailbox.py
  │   │   │   ├── artifact_registry_doctor.py
  │   │   │   ├── artifact_software_release.py
  │   │   │   ├── artifact_software_release_elf.py
  │   │   │   ├── artifact_spice.py
  │   │   │   ├── artifact_still_image.py
  │   │   │   ├── artifact_svg.py
  │   │   │   ├── artifact_temporal_deploy.py
  │   │   │   ├── artifact_temporal_launch.py
  │   │   │   ├── artifact_temporal_support.py
  │   │   │   ├── artifact_temporal_worker.py
  │   │   │   ├── artifact_temporal_workflow.py
  │   │   │   ├── artifact_tiled.py
  │   │   │   ├── artifact_verify.py
  │   │   │   ├── artifact_wave.py
  │   │   │   ├── artifact_web_archive.py
  │   │   │   ├── cad_step_inspect.cpp
  │   │   │   ├── powerpoint_render_worker.ps1
  │   │   │   ├── publication_carrier_verify.py
  │   │   │   ├── publication_perceptual_probe.py
  │   │   │   ├── publication_perceptual_provider_exec.py
  │   │   │   └── publication_perceptual_verify.py
  │   │   ├── systemd
  │   │   │   ├── ordivon-artifact-temporal-worker.service
  │   │   │   └── ordivon-artifact-v2-zot-r1.container
  │   │   ├── tests
  │   │   │   ├── fixtures
  │   │   │   │   └── cad
  │   │   │   │       ├── block-through-hole-contract.json
  │   │   │   │       └── block-through-hole.step
  │   │   │   ├── test_artifact_agent_surface.py
  │   │   │   ├── test_artifact_aseprite.py
  │   │   │   ├── test_artifact_audio.py
  │   │   │   ├── test_artifact_binding_authority.py
  │   │   │   ├── test_artifact_cad_step.py
  │   │   │   ├── test_artifact_claim_results_adapter_r1.py
  │   │   │   ├── test_artifact_consumer_acceptance.py
  │   │   │   ├── test_artifact_core_registry.py
  │   │   │   ├── test_artifact_dataset.py
  │   │   │   ├── test_artifact_decomposition_a10.py
  │   │   │   ├── test_artifact_decomposition_a11.py
  │   │   │   ├── test_artifact_decomposition_a12.py
  │   │   │   ├── test_artifact_decomposition_a13.py
  │   │   │   ├── test_artifact_decomposition_a15.py
  │   │   │   ├── test_artifact_decomposition_a2.py
  │   │   │   ├── test_artifact_decomposition_a3.py
  │   │   │   ├── test_artifact_decomposition_a4.py
  │   │   │   ├── test_artifact_decomposition_a5.py
  │   │   │   ├── test_artifact_decomposition_a6.py
  │   │   │   ├── test_artifact_decomposition_a7.py
  │   │   │   ├── test_artifact_decomposition_a8.py
  │   │   │   ├── test_artifact_decomposition_a9.py
  │   │   │   ├── test_artifact_deliver_html.py
  │   │   │   ├── test_artifact_delivery.py
  │   │   │   ├── test_artifact_delivery_toolchain_doctor.py
  │   │   │   ├── test_artifact_design3d.py
  │   │   │   ├── test_artifact_development_fixture.py
  │   │   │   ├── test_artifact_eda.py
  │   │   │   ├── test_artifact_evaluation_pressure_r1.py
  │   │   │   ├── test_artifact_evidence_observation_lossless_r1.py
  │   │   │   ├── test_artifact_evidence_standing_pressure_r1.py
  │   │   │   ├── test_artifact_geospatial.py
  │   │   │   ├── test_artifact_input_snapshot.py
  │   │   │   ├── test_artifact_legacy_digest_consumers.py
  │   │   │   ├── test_artifact_message.py
  │   │   │   ├── test_artifact_moving_image.py
  │   │   │   ├── test_artifact_native_identity.py
  │   │   │   ├── test_artifact_oci_package.py
  │   │   │   ├── test_artifact_oci_toolchain.py
  │   │   │   ├── test_artifact_ogg_vorbis.py
  │   │   │   ├── test_artifact_opc_projection.py
  │   │   │   ├── test_artifact_openxml_assurance.py
  │   │   │   ├── test_artifact_openxml_environment.py
  │   │   │   ├── test_artifact_openxml_external_evidence.py
  │   │   │   ├── test_artifact_operation_receipt_contract_r1.py
  │   │   │   ├── test_artifact_profile_authority.py
  │   │   │   ├── test_artifact_profile_v2.py
  │   │   │   ├── test_artifact_publication_carrier_r1.py
  │   │   │   ├── test_artifact_publication_geometry_semantic_r1.py
  │   │   │   ├── test_artifact_publication_observer_task_r1.py
  │   │   │   ├── test_artifact_publication_perceptual_r1.py
  │   │   │   ├── test_artifact_publication_provider_adapter_r1.py
  │   │   │   ├── test_artifact_python_currentness_contract.py
  │   │   │   ├── test_artifact_python_environment.py
  │   │   │   ├── test_artifact_r2_mailbox.py
  │   │   │   ├── test_artifact_redecomposition_r1.py
  │   │   │   ├── test_artifact_registry_doctor.py
  │   │   │   ├── test_artifact_software_release.py
  │   │   │   ├── test_artifact_software_release_elf.py
  │   │   │   ├── test_artifact_spice.py
  │   │   │   ├── test_artifact_stage_missing_validator.py
  │   │   │   ├── test_artifact_standing_decision_pressure_r1.py
  │   │   │   ├── test_artifact_still_image.py
  │   │   │   ├── test_artifact_svg.py
  │   │   │   ├── test_artifact_temporal_contract.py
  │   │   │   ├── test_artifact_tiled.py
  │   │   │   ├── test_artifact_tool_identity.py
  │   │   │   ├── test_artifact_verify.py
  │   │   │   ├── test_artifact_wave.py
  │   │   │   └── test_artifact_web_archive.py
  │   │   ├── .gitignore
  │   │   ├── .python-version
  │   │   ├── MIGRATION_PROVENANCE.md
  │   │   ├── mise.toml
  │   │   ├── pyproject.toml
  │   │   ├── README.md
  │   │   └── uv.lock
  │   ├── distribution
  │   │   ├── adapters
  │   │   │   ├── openapi-generator.json
  │   │   │   ├── postiz.json
  │   │   │   └── rclone.json
  │   │   ├── docs
  │   │   │   └── R8-DURABLE-INTEGRATION-PORT.md
  │   │   ├── evidence
  │   │   │   ├── r1-validation-20260911.json
  │   │   │   ├── r10-game-steam-free-preflight-20260913.json
  │   │   │   ├── r2-github-public-read-envelope.json
  │   │   │   ├── r2-github-public-read-source.json
  │   │   │   ├── r2-validation-20260911.json
  │   │   │   ├── r3-github-create-issue-intent.json
  │   │   │   ├── r3-validation-20260911.json
  │   │   │   ├── r4-github-create-issue-approval-request.json
  │   │   │   ├── r4-validation-20260912.json
  │   │   │   ├── r5-carrier-coverage-20260912.json
  │   │   │   ├── r6-validation-20260912.json
  │   │   │   ├── r7-artifact-development-publication-intent.json
  │   │   │   ├── r7-validation-20260912.json
  │   │   │   ├── r8-validation-20260912.json
  │   │   │   └── r9-write-admission-20260912.json
  │   │   ├── scripts
  │   │   │   ├── test-external-carriers.sh
  │   │   │   ├── test-github-provider-readback.sh
  │   │   │   ├── test-openapi-generator.sh
  │   │   │   ├── test-postiz-surface.sh
  │   │   │   ├── test-rclone.sh
  │   │   │   └── test-structure.sh
  │   │   ├── tests
  │   │   │   └── fixtures
  │   │   │       └── provider-openapi.yaml
  │   │   ├── .gitignore
  │   │   ├── external-lock.json
  │   │   ├── mise.toml
  │   │   └── README.md
  │   ├── media
  │   │   ├── apps
  │   │   │   ├── motion-remotion
  │   │   │   │   ├── src
  │   │   │   │   │   ├── exact-close-composition.tsx
  │   │   │   │   │   ├── game-station-zero-affect-expression.tsx
  │   │   │   │   │   ├── index.ts
  │   │   │   │   │   ├── request-replay-composition.tsx
  │   │   │   │   │   ├── root.tsx
  │   │   │   │   │   ├── runtime-demo-receipt.ts
  │   │   │   │   │   ├── runtime-flow-composition.tsx
  │   │   │   │   │   ├── runtime-introduction-master-composition.tsx
  │   │   │   │   │   ├── runtime-response-loss-expression.tsx
  │   │   │   │   │   └── security-ae0-epistemic-expression.tsx
  │   │   │   │   ├── package.json
  │   │   │   │   ├── remotion.config.ts
  │   │   │   │   └── tsconfig.json
  │   │   │   └── preview
  │   │   │       ├── src
  │   │   │       │   ├── app.tsx
  │   │   │       │   ├── main.tsx
  │   │   │       │   └── styles.css
  │   │   │       ├── index.html
  │   │   │       ├── package.json
  │   │   │       └── vite.config.ts
  │   │   ├── artifacts
  │   │   │   ├── creative-archive
  │   │   │   │   └── historical-works-r2-source-complete.json
  │   │   │   └── creative-library
  │   │   │       ├── derived
  │   │   │       │   ├── cad-cross-work-derived-preview-r1.json
  │   │   │       │   ├── game--look-away-garden.png
  │   │   │       │   ├── game--seen-not-approved-pcb.svg
  │   │   │       │   ├── game--signal-garden-evidence-petals.png
  │   │   │       │   ├── game--three-color-night-shift.png
  │   │   │       │   ├── godot-derived-previews-r1.json
  │   │   │       │   ├── kicad-derived-preview-r1.json
  │   │   │       │   ├── manifest-v1.json
  │   │   │       │   ├── media--alignment-field.png
  │   │   │       │   └── workstation--signal-garden-cam-encoder.png
  │   │   │       ├── evidence
  │   │   │       │   ├── acceptance-r1.json
  │   │   │       │   ├── acceptance-r2.json
  │   │   │       │   ├── friction-glb-presentation-kind-r1.json
  │   │   │       │   └── home.png
  │   │   │       └── catalog-v1.json
  │   │   ├── creative-library
  │   │   │   ├── web
  │   │   │   │   ├── app.js
  │   │   │   │   ├── index.html
  │   │   │   │   └── styles.css
  │   │   │   ├── README.md
  │   │   │   └── SOURCE_BOUNDARY.json
  │   │   ├── docs
  │   │   │   ├── resolve-compatibility
  │   │   │   │   ├── resolve-free-21.0.3.7.json
  │   │   │   │   ├── resolve-free-21.0.3.7.md
  │   │   │   │   └── runtime-introduction-assembly-conform-21.0.3.7.json
  │   │   │   ├── artifact-perception.md
  │   │   │   ├── authority.md
  │   │   │   ├── capability-reference.md
  │   │   │   ├── creative-capability-core.md
  │   │   │   ├── directory-audit.md
  │   │   │   ├── fast-inner-loop.md
  │   │   │   ├── human-guide.md
  │   │   │   ├── media-model.md
  │   │   │   ├── production-cognition.md
  │   │   │   ├── resolve-native.md
  │   │   │   ├── review-consumption.md
  │   │   │   ├── storage-layout.md
  │   │   │   └── technical-baseline.md
  │   │   ├── formal
  │   │   │   ├── CreativeLibraryAcceptance.lean
  │   │   │   ├── LoudnessProfileSafety.smt2
  │   │   │   ├── MediaNativeProcessingAdmission.lean
  │   │   │   ├── ProductionDependencyImpact.lean
  │   │   │   ├── ProductionOutputByteIdentity.lean
  │   │   │   └── README.md
  │   │   ├── packages
  │   │   │   ├── identity
  │   │   │   │   ├── scripts
  │   │   │   │   │   └── build-tokens.ts
  │   │   │   │   ├── tokens
  │   │   │   │   │   └── baseline.tokens.json
  │   │   │   │   └── package.json
  │   │   │   └── visuals
  │   │   │       ├── src
  │   │   │       │   ├── index.ts
  │   │   │       │   └── runtime-flow.tsx
  │   │   │       └── package.json
  │   │   ├── planning
  │   │   │   └── lego-plan-r1.json
  │   │   ├── play
  │   │   │   └── media-ecology-20260830
  │   │   │       ├── board-snapshot.json
  │   │   │       ├── browser-check.py
  │   │   │       ├── build.py
  │   │   │       ├── daily-cabinet.collection.json
  │   │   │       ├── projection.json
  │   │   │       └── README.md
  │   │   ├── processing
  │   │   │   ├── bin
  │   │   │   │   ├── otiotool-pinned.sh
  │   │   │   │   ├── probe-audio.sh
  │   │   │   │   ├── probe-av.sh
  │   │   │   │   ├── probe-otio.sh
  │   │   │   │   ├── probe-timed-text.sh
  │   │   │   │   └── ttconv-pinned.sh
  │   │   │   ├── profiles
  │   │   │   │   ├── audio-program-48k-mono-lufs23.json
  │   │   │   │   ├── av-sdr-web-1080p30-noaudio.json
  │   │   │   │   ├── otio-runtime-introduction-v2.json
  │   │   │   │   └── timed-text-runtime-introduction-en.json
  │   │   │   ├── tests
  │   │   │   │   ├── audio-smoke.sh
  │   │   │   │   ├── otio-smoke.sh
  │   │   │   │   ├── smoke.sh
  │   │   │   │   ├── test_processing_tool_resolution.py
  │   │   │   │   └── timedtext-smoke.sh
  │   │   │   └── README.md
  │   │   ├── productions
  │   │   │   ├── archive-archipelago-001
  │   │   │   │   ├── evidence
  │   │   │   │   │   ├── artifact-browser-matrix-r2.json
  │   │   │   │   │   ├── artifact-browser-matrix-r3.json
  │   │   │   │   │   ├── artifact-browser-matrix-r4.json
  │   │   │   │   │   ├── artifact-vnu-r2.json
  │   │   │   │   │   ├── artifact-vnu-r3.json
  │   │   │   │   │   ├── artifact-vnu-r4.json
  │   │   │   │   │   ├── chromium-console-keyboard-r3.json
  │   │   │   │   │   ├── chromium-console-mobile-r2.json
  │   │   │   │   │   ├── chromium-console-r2.json
  │   │   │   │   │   ├── chromium-console-touch-r4.json
  │   │   │   │   │   ├── chromium-final-console-r2.json
  │   │   │   │   │   ├── chromium-final-interaction-r2.json
  │   │   │   │   │   ├── chromium-interaction-r2.json
  │   │   │   │   │   ├── chromium-mobile-pan-r2.json
  │   │   │   │   │   ├── collaboration-polish-r2.json
  │   │   │   │   │   ├── consumption-evidence.json
  │   │   │   │   │   ├── friction-gpkg-determinism.json
  │   │   │   │   │   ├── friction-interactive-accessibility.json
  │   │   │   │   │   ├── friction-interactive-html-conformance.json
  │   │   │   │   │   ├── friction-interactive-keyboard-focus.json
  │   │   │   │   │   ├── friction-interactive-mobile-density.json
  │   │   │   │   │   ├── friction-interactive-svg-append.json
  │   │   │   │   │   ├── friction-interactive-touch-targets.json
  │   │   │   │   │   ├── friction-playwright-config-cli.json
  │   │   │   │   │   ├── friction-production-schema.json
  │   │   │   │   │   ├── friction.json
  │   │   │   │   │   ├── keyboard-focus-baseline-r3.json
  │   │   │   │   │   ├── keyboard-focus-verified-r3.json
  │   │   │   │   │   ├── touch-accessibility-gates-r4.json
  │   │   │   │   │   └── touch-target-baseline-r4.json
  │   │   │   │   ├── interactive
  │   │   │   │   │   ├── app.js
  │   │   │   │   │   ├── archive-archipelago-001.html
  │   │   │   │   │   ├── chromium-desktop-final-r2.png
  │   │   │   │   │   ├── chromium-keyboard-search-r3.png
  │   │   │   │   │   ├── chromium-mobile-final-r2.png
  │   │   │   │   │   ├── chromium-mobile-r2.png
  │   │   │   │   │   ├── chromium-mobile-r2b.png
  │   │   │   │   │   ├── chromium-mobile-search-r3.png
  │   │   │   │   │   ├── chromium-touch-r4-final.png
  │   │   │   │   │   ├── data.js
  │   │   │   │   │   ├── index.html
  │   │   │   │   │   └── styles.css
  │   │   │   │   ├── render
  │   │   │   │   │   ├── archive-archipelago-001.gpkg
  │   │   │   │   │   ├── archive-archipelago-001.png
  │   │   │   │   │   ├── archive-archipelago-001.svg
  │   │   │   │   │   ├── build-manifest.json
  │   │   │   │   │   ├── owners.geojson
  │   │   │   │   │   ├── relations.geojson
  │   │   │   │   │   └── works.geojson
  │   │   │   │   ├── source
  │   │   │   │   │   ├── creative-library-catalog-v1.json
  │   │   │   │   │   └── workstation-revision.txt
  │   │   │   │   ├── build.sh
  │   │   │   │   ├── build_interactive.py
  │   │   │   │   ├── claims.json
  │   │   │   │   ├── generate.py
  │   │   │   │   ├── production.json
  │   │   │   │   └── README.md
  │   │   │   ├── browser-perception-note
  │   │   │   │   ├── evidence
  │   │   │   │   │   └── browser-review.receipt.json
  │   │   │   │   ├── claims.json
  │   │   │   │   ├── cognition.md
  │   │   │   │   ├── production.json
  │   │   │   │   └── story.mdx
  │   │   │   ├── convergence-object-001
  │   │   │   │   ├── render
  │   │   │   │   │   ├── convergence-object-001.glb
  │   │   │   │   │   └── convergence-object-001.png
  │   │   │   │   ├── source
  │   │   │   │   │   ├── convergence-object-001-roundtrip.blend
  │   │   │   │   │   └── convergence-object-001.blend
  │   │   │   │   ├── build.py
  │   │   │   │   ├── claims.json
  │   │   │   │   ├── consumption-evidence.json
  │   │   │   │   ├── friction-blender-backup-carriers.json
  │   │   │   │   ├── friction-blender-engine.json
  │   │   │   │   ├── friction-headless-audio.json
  │   │   │   │   ├── friction-production-3d-kind.json
  │   │   │   │   ├── production.json
  │   │   │   │   ├── README.md
  │   │   │   │   ├── roundtrip-receipt.json
  │   │   │   │   └── verify_import.py
  │   │   │   ├── convergence-sonic-ident
  │   │   │   │   ├── render
  │   │   │   │   │   ├── convergence-archive.flac
  │   │   │   │   │   ├── convergence-delivery.ogg
  │   │   │   │   │   ├── convergence-master.wav
  │   │   │   │   │   ├── convergence-source.wav
  │   │   │   │   │   └── convergence-waveform.png
  │   │   │   │   ├── claims.json
  │   │   │   │   ├── consumption-evidence.json
  │   │   │   │   ├── friction-validation-env.json
  │   │   │   │   ├── friction.json
  │   │   │   │   ├── generate.py
  │   │   │   │   ├── operation-lineage.json
  │   │   │   │   ├── production.json
  │   │   │   │   └── README.md
  │   │   │   ├── fishing-fable-lego-study-r1
  │   │   │   │   ├── claims.json
  │   │   │   │   ├── formal-writing-contracts-r1.md
  │   │   │   │   ├── production.json
  │   │   │   │   ├── story-archival-reconstruction.md
  │   │   │   │   ├── writing-issue-census-r1.md
  │   │   │   │   └── writing-lego-research-dossier-r1.md
  │   │   │   ├── friction-loop-field-zine
  │   │   │   │   ├── inspect
  │   │   │   │   │   └── contact-sheet.png
  │   │   │   │   ├── render
  │   │   │   │   │   └── make-things-find-friction-field-note-001.pdf
  │   │   │   │   ├── claims.json
  │   │   │   │   ├── consumption-evidence.json
  │   │   │   │   ├── friction-typst-authoring.json
  │   │   │   │   ├── friction-typst-markup.json
  │   │   │   │   ├── production.json
  │   │   │   │   ├── README.md
  │   │   │   │   └── source.typ
  │   │   │   ├── live-relay-001
  │   │   │   │   ├── artifact-evidence
  │   │   │   │   │   ├── verifier
  │   │   │   │   │   │   ├── ffprobe.json
  │   │   │   │   │   │   ├── mediaconch-implementation.xml
  │   │   │   │   │   │   └── mediainfo.xml
  │   │   │   │   │   ├── moving-image-contract.json
  │   │   │   │   │   └── moving-image-verification.json
  │   │   │   │   ├── evidence
  │   │   │   │   │   ├── final-qc
  │   │   │   │   │   │   ├── contact-sheet.png
  │   │   │   │   │   │   ├── ffprobe.json
  │   │   │   │   │   │   └── summary.json
  │   │   │   │   │   ├── friction-controller-pre-finally-r1.json
  │   │   │   │   │   └── obs-session-final.json
  │   │   │   │   ├── program
  │   │   │   │   │   ├── 00-signal.png
  │   │   │   │   │   ├── 01-archive.png
  │   │   │   │   │   ├── 02-object.png
  │   │   │   │   │   └── 03-constellation.png
  │   │   │   │   ├── render
  │   │   │   │   │   ├── live-relay-001-master.mkv
  │   │   │   │   │   ├── live-relay-001-poster.png
  │   │   │   │   │   └── live-relay-001-source.mp4
  │   │   │   │   ├── source
  │   │   │   │   │   ├── archive-archipelago-001.png
  │   │   │   │   │   ├── convergence-object-001.png
  │   │   │   │   │   ├── provenance.json
  │   │   │   │   │   ├── source-manifest.json
  │   │   │   │   │   ├── system-constellation-field-crop.png
  │   │   │   │   │   └── system-constellation-poster-001.png
  │   │   │   │   ├── .gitattributes
  │   │   │   │   ├── claims.json
  │   │   │   │   ├── consumption-evidence.json
  │   │   │   │   ├── manifest.sha256
  │   │   │   │   ├── production.json
  │   │   │   │   ├── README.md
  │   │   │   │   └── run-live-relay.ps1
  │   │   │   ├── mhs-hardware-boundary
  │   │   │   │   ├── evidence
  │   │   │   │   │   ├── fresh-consumer-v1-carrier-failure.json
  │   │   │   │   │   ├── fresh-consumer-v2-freeform.json
  │   │   │   │   │   ├── owner-disposition.json
  │   │   │   │   │   ├── revised-firstpass-v1.json
  │   │   │   │   │   └── revised-owner-audit.json
  │   │   │   │   ├── claims.json
  │   │   │   │   ├── cognition.md
  │   │   │   │   ├── production.json
  │   │   │   │   └── story.mdx
  │   │   │   ├── ordivon-book-v0
  │   │   │   │   ├── portable
  │   │   │   │   │   ├── portable-pdf.receipt.json
  │   │   │   │   │   └── render_pdf.py
  │   │   │   │   ├── book.mdx
  │   │   │   │   ├── chapter-02.mdx
  │   │   │   │   ├── chapter-03.mdx
  │   │   │   │   ├── chapter-04.mdx
  │   │   │   │   ├── chapter-05.mdx
  │   │   │   │   ├── chapter-06.mdx
  │   │   │   │   ├── chapter-07.mdx
  │   │   │   │   ├── claims.json
  │   │   │   │   ├── cognition.md
  │   │   │   │   ├── constitution.md
  │   │   │   │   ├── consumption-audit.md
  │   │   │   │   ├── external-methods.md
  │   │   │   │   ├── future-horizon-laboratory.mdx
  │   │   │   │   ├── production.json
  │   │   │   │   ├── source-map.md
  │   │   │   │   └── story.mdx
  │   │   │   ├── ordivon-system-constellation-atlas
  │   │   │   │   ├── render
  │   │   │   │   │   ├── ordivon-system-constellation.gpkg
  │   │   │   │   │   ├── ordivon-system-constellation.png
  │   │   │   │   │   └── ordivon-system-constellation.svg
  │   │   │   │   ├── source
  │   │   │   │   │   ├── repositories.geojson
  │   │   │   │   │   └── repositories.json
  │   │   │   │   ├── claims.json
  │   │   │   │   ├── consumption-evidence.json
  │   │   │   │   ├── friction.json
  │   │   │   │   ├── generate.py
  │   │   │   │   ├── manifest.sha256
  │   │   │   │   ├── production.json
  │   │   │   │   └── README.md
  │   │   │   ├── runtime-introduction
  │   │   │   │   ├── evidence
  │   │   │   │   │   ├── media-v2-audio-declaration-parity-r6.json
  │   │   │   │   │   ├── media-v2-picture-lineage-recheck-r7.json
  │   │   │   │   │   ├── narration-rate-pressure-20260824.json
  │   │   │   │   │   ├── narration-sapi.receipt.json
  │   │   │   │   │   ├── r2-replica.receipt.json
  │   │   │   │   │   └── runtime-demo.receipt.json
  │   │   │   │   ├── history
  │   │   │   │   │   └── cognition-through-p4.md
  │   │   │   │   ├── script
  │   │   │   │   │   ├── narration.en.md
  │   │   │   │   │   └── narration.zh.md
  │   │   │   │   ├── timed-text
  │   │   │   │   │   ├── standard
  │   │   │   │   │   │   ├── narration.en.srt
  │   │   │   │   │   │   ├── narration.en.ttml
  │   │   │   │   │   │   ├── narration.en.vtt
  │   │   │   │   │   │   └── README.md
  │   │   │   │   │   └── narration.en.json
  │   │   │   │   ├── timeline
  │   │   │   │   │   ├── assembly.v0.otio
  │   │   │   │   │   ├── assembly.v1.otio
  │   │   │   │   │   ├── assembly.v2.otio
  │   │   │   │   │   └── README.md
  │   │   │   │   ├── assets.json
  │   │   │   │   ├── claims.json
  │   │   │   │   ├── cognition.md
  │   │   │   │   ├── plan.md
  │   │   │   │   ├── production.json
  │   │   │   │   ├── README.md
  │   │   │   │   └── story.mdx
  │   │   │   ├── site-social-card
  │   │   │   │   ├── output
  │   │   │   │   │   └── opengraph-image.png
  │   │   │   │   ├── source
  │   │   │   │   │   └── opengraph-image.svg
  │   │   │   │   ├── assets.json
  │   │   │   │   ├── claims.json
  │   │   │   │   ├── cognition.md
  │   │   │   │   ├── production.json
  │   │   │   │   └── README.md
  │   │   │   └── studio-expression-card
  │   │   │       ├── output
  │   │   │       │   └── card.png
  │   │   │       ├── source
  │   │   │       │   └── card.svg
  │   │   │       ├── assets.json
  │   │   │       ├── claims.json
  │   │   │       ├── cognition.md
  │   │   │       ├── production.json
  │   │   │       └── README.md
  │   │   ├── research
  │   │   │   ├── equipment
  │   │   │   │   ├── evidence
  │   │   │   │   │   ├── af0-af9-agent-first-friction-20260816.json
  │   │   │   │   │   ├── e0-e7-20260813.json
  │   │   │   │   │   ├── e5-hardware-20260813.json
  │   │   │   │   │   └── e8-capability-expansion-20260814.json
  │   │   │   │   ├── experiments
  │   │   │   │   │   ├── af4_blender_exit0_fault.py
  │   │   │   │   │   ├── af8_blender_micro.py
  │   │   │   │   │   ├── af8_deterministic_still.svg
  │   │   │   │   │   ├── e0-e7-equipment-world.md
  │   │   │   │   │   └── e8-capability-expansion-consumption.md
  │   │   │   │   ├── equipment-world.json
  │   │   │   │   ├── PROVIDER-FIRST-PF0.md
  │   │   │   │   ├── README.md
  │   │   │   │   └── sources.json
  │   │   │   ├── expression
  │   │   │   │   ├── evidence
  │   │   │   │   │   ├── m7-foundational-media-20260813.json
  │   │   │   │   │   ├── mhs-agent-hardware-boundary-20260829.md
  │   │   │   │   │   ├── r0-r3-cultural-observatory-20260811.json
  │   │   │   │   │   ├── r4-rich-perception-20260811.json
  │   │   │   │   │   ├── r5-grounded-meaning-20260811.json
  │   │   │   │   │   └── r6-creative-alpha-20260811.json
  │   │   │   │   ├── experiments
  │   │   │   │   │   ├── a31-runtime-response-loss.md
  │   │   │   │   │   ├── a32-adversarial-epistemics.md
  │   │   │   │   │   ├── a32-security-ae0-evidence.json
  │   │   │   │   │   ├── a33-station-zero-affect-evidence.json
  │   │   │   │   │   ├── a33-station-zero-affect.md
  │   │   │   │   │   ├── m7-foundational-media.md
  │   │   │   │   │   ├── r0-r3-cultural-observatory.md
  │   │   │   │   │   ├── r4-rich-perception.md
  │   │   │   │   │   ├── r5-grounded-meaning.md
  │   │   │   │   │   └── r6-creative-alpha.md
  │   │   │   │   ├── foundations
  │   │   │   │   │   ├── media-deep-foundations-mf0-mf9-closeout-and-domain-coverage-handoff-20260818.md
  │   │   │   │   │   ├── media-foundations-mf0-mf7-closeout-20260817.md
  │   │   │   │   │   ├── media-foundations-mf2h-20260817.md
  │   │   │   │   │   ├── media-foundations-mf2i-20260817.md
  │   │   │   │   │   ├── media-foundations-mf3i-20260817.md
  │   │   │   │   │   ├── media-foundations-mf4k-20260817.md
  │   │   │   │   │   ├── media-foundations-mf5i-20260817.md
  │   │   │   │   │   ├── media-foundations-mf6f-20260817.md
  │   │   │   │   │   ├── media-foundations-mf7h-20260817.md
  │   │   │   │   │   ├── media-foundations-mf8-agency-v1-20260818.md
  │   │   │   │   │   ├── media-foundations-mf9-experience-v1-20260818.md
  │   │   │   │   │   ├── media-round-c-through-d-e-fresh-continent-final-closeout-20260818.md
  │   │   │   │   │   ├── media-round-d-a-infrastructural-environmental-elemental-mediation-boundary-test-20260818.md
  │   │   │   │   │   ├── media-round-d-b-operative-executable-mediation-reducibility-20260818.md
  │   │   │   │   │   ├── media-round-d-c-interface-affordance-action-coupling-reducibility-20260818.md
  │   │   │   │   │   ├── media-round-d-d-mediated-presence-telepresence-teleaction-embodiment-reducibility-20260818.md
  │   │   │   │   │   ├── media-round-d-e-datafication-legibility-metricization-reducibility-20260818.md
  │   │   │   │   │   ├── media-whole-domain-fresh-unknown-continent-rescan-round-c-20260818.md
  │   │   │   │   │   ├── media-whole-domain-round-b-a-communication-reducibility-20260818.md
  │   │   │   │   │   ├── media-whole-domain-round-b-b-encounter-exposure-reducibility-20260818.md
  │   │   │   │   │   ├── media-whole-domain-round-b-c-convention-protocol-interoperability-reducibility-20260818.md
  │   │   │   │   │   ├── media-whole-domain-round-b-d-publicness-addressability-publication-reducibility-20260818.md
  │   │   │   │   │   ├── media-whole-domain-round-b-e-artifact-work-edition-performance-generative-identity-reducibility-20260818.md
  │   │   │   │   │   ├── media-whole-domain-round-b-f-selection-gatekeeping-visibility-allocation-reducibility-20260818.md
  │   │   │   │   │   ├── media-whole-domain-round-b-g-meaning-pragmatics-context-preservation-reducibility-20260818.md
  │   │   │   │   │   ├── media-whole-domain-round-b-h-inscription-fixation-materialization-reducibility-20260818.md
  │   │   │   │   │   ├── media-whole-domain-round-b-i-authorship-creation-attribution-reducibility-20260818.md
  │   │   │   │   │   ├── media-whole-domain-round-b-j-archive-preservation-responsibility-reducibility-20260818.md
  │   │   │   │   │   ├── media-whole-domain-round-b-k-audience-public-formation-reducibility-20260818.md
  │   │   │   │   │   ├── media-whole-domain-round-b-l-reflexive-mediation-ecology-reducibility-20260818.md
  │   │   │   │   │   ├── media-whole-domain-round-b-m-translation-remediation-reducibility-20260818.md
  │   │   │   │   │   ├── media-whole-domain-unexplored-space-search-round-a-20260818.md
  │   │   │   │   │   └── README.md
  │   │   │   │   ├── profiles
  │   │   │   │   │   ├── audio.md
  │   │   │   │   │   ├── index.json
  │   │   │   │   │   ├── interactive.md
  │   │   │   │   │   ├── motion-video.md
  │   │   │   │   │   ├── README.md
  │   │   │   │   │   ├── still-visual.md
  │   │   │   │   │   └── writing.md
  │   │   │   │   ├── aesthetic-model.md
  │   │   │   │   ├── context.json
  │   │   │   │   ├── creative-system.md
  │   │   │   │   ├── cultural-observatory.md
  │   │   │   │   ├── evidence-map.md
  │   │   │   │   ├── knowledge-model.md
  │   │   │   │   ├── m7-foundational-media-program.md
  │   │   │   │   ├── m7-world-model-audit.md
  │   │   │   │   ├── media-topology.md
  │   │   │   │   ├── media-world-model.json
  │   │   │   │   ├── protocol.md
  │   │   │   │   ├── README.md
  │   │   │   │   └── sources.json
  │   │   │   └── media
  │   │   │       ├── authority
  │   │   │       │   ├── publications
  │   │   │       │   │   └── e26649a077eacfd0964e0d6ace7a3454d27c60ebcc96251dbb9b1861d867823e.json
  │   │   │       │   ├── CURRENT.json
  │   │   │       │   └── MEDIA-OWNER-PUBLICATION-ACCEPTANCE-20260819.json
  │   │   │       ├── bridges
  │   │   │       │   └── README.md
  │   │   │       ├── core
  │   │   │       │   ├── FOUNDATION-FAMILIES.md
  │   │   │       │   └── README.md
  │   │   │       ├── coverage
  │   │   │       │   └── README.md
  │   │   │       ├── derived
  │   │   │       │   ├── DATAFICATION-LEGIBILITY-METRICIZATION.md
  │   │   │       │   ├── README.md
  │   │   │       │   ├── ROUND-B-PROFILES.md
  │   │   │       │   └── ROUND-D-PROFILES.md
  │   │   │       ├── engineering-consumption
  │   │   │       │   ├── fixtures
  │   │   │       │   │   ├── finance-qb6-metric-legibility-dogfood.md
  │   │   │       │   │   ├── finance-qb6-metric-legibility-lineage.json
  │   │   │       │   │   ├── host-task-rev3-agent.json
  │   │   │       │   │   ├── host-task-rev3-dogfood.md
  │   │   │       │   │   ├── host-task-rev3-human.md
  │   │   │       │   │   ├── studio-expression-card-dogfood.md
  │   │   │       │   │   ├── studio-expression-card-lineage.json
  │   │   │       │   │   ├── web-m7-trajectory-dogfood.md
  │   │   │       │   │   └── web-m7-trajectory-lineage.json
  │   │   │       │   ├── OMPC-CONFORMANCE-v0.md
  │   │   │       │   ├── OMPC-v0.md
  │   │   │       │   └── README.md
  │   │   │       ├── evidence
  │   │   │       │   └── README.md
  │   │   │       ├── history
  │   │   │       │   └── README.md
  │   │   │       ├── negative
  │   │   │       │   └── README.md
  │   │   │       ├── creative-delivery-bridges.json
  │   │   │       └── README.md
  │   │   ├── schemas
  │   │   │   ├── asset.schema.json
  │   │   │   ├── claims.schema.json
  │   │   │   ├── operation-lineage.schema.json
  │   │   │   ├── production.schema.json
  │   │   │   ├── runtime-demo-receipt.schema.json
  │   │   │   └── timed-text.schema.json
  │   │   ├── scripts
  │   │   │   ├── build-creative-index.py
  │   │   │   ├── build_sapi_narration.py
  │   │   │   ├── creative_library.py
  │   │   │   ├── materialize-python.py
  │   │   │   ├── owner-environment
  │   │   │   ├── produce-internet-message.py
  │   │   │   ├── produce-parquet.py
  │   │   │   ├── produce-warc-response.py
  │   │   │   ├── require-js-deps.mjs
  │   │   │   ├── require-python-deps.py
  │   │   │   ├── resolve-native-produce.py
  │   │   │   ├── run-e6-equipment-dogfood.py
  │   │   │   ├── run-e7-equipment-economics.py
  │   │   │   ├── run-m7-foundational-media.py
  │   │   │   ├── run-r4-article-experiment.py
  │   │   │   ├── run-r4-media-experiment.py
  │   │   │   ├── run-r5-grounded-meaning.py
  │   │   │   ├── run-r6-creative-alpha.py
  │   │   │   ├── run-r6-creative-validity.py
  │   │   │   ├── studio-agent-surface.py
  │   │   │   └── synthesize-sapi-cues.ps1
  │   │   ├── src
  │   │   │   └── ordivon_studio
  │   │   │       ├── cli_handlers
  │   │   │       │   ├── __init__.py
  │   │   │       │   ├── ecology.py
  │   │   │       │   ├── equipment.py
  │   │   │       │   └── media.py
  │   │   │       ├── ecology
  │   │   │       │   ├── __init__.py
  │   │   │       │   ├── board.py
  │   │   │       │   ├── collection.py
  │   │   │       │   ├── contracts.py
  │   │   │       │   └── feed.py
  │   │   │       ├── research
  │   │   │       │   ├── __init__.py
  │   │   │       │   ├── creative_analysis.py
  │   │   │       │   ├── creative_observer.py
  │   │   │       │   ├── creative_protocol.py
  │   │   │       │   ├── foundational_media.py
  │   │   │       │   ├── grounded_av_tasks.py
  │   │   │       │   ├── grounded_contracts.py
  │   │   │       │   ├── grounded_evidence.py
  │   │   │       │   ├── grounded_provider.py
  │   │   │       │   ├── grounded_scoring.py
  │   │   │       │   ├── grounded_text_tasks.py
  │   │   │       │   ├── guardian_article.py
  │   │   │       │   ├── null_attack_scoring.py
  │   │   │       │   ├── search_calibration.py
  │   │   │       │   ├── trial_ledger.py
  │   │   │       │   └── trial_registration.py
  │   │   │       ├── __init__.py
  │   │   │       ├── agent_dependencies.py
  │   │   │       ├── agent_processing.py
  │   │   │       ├── agent_productions.py
  │   │   │       ├── agent_surface.py
  │   │   │       ├── agent_surface_contracts.py
  │   │   │       ├── assets.py
  │   │   │       ├── cli.py
  │   │   │       ├── cloudflare_r2.py
  │   │   │       ├── cloudflare_r2_transport.py
  │   │   │       ├── creative_index.py
  │   │   │       ├── creative_index_artifact.py
  │   │   │       ├── creative_index_library.py
  │   │   │       ├── creative_index_source_utils.py
  │   │   │       ├── equipment.py
  │   │   │       ├── equipment_capabilities.py
  │   │   │       ├── equipment_discovery.py
  │   │   │       ├── equipment_evaluation.py
  │   │   │       ├── equipment_plan.py
  │   │   │       ├── equipment_plan_contracts.py
  │   │   │       ├── equipment_plan_delivery.py
  │   │   │       ├── figma_provider.py
  │   │   │       ├── learning_context.py
  │   │   │       ├── models.py
  │   │   │       ├── observatory.py
  │   │   │       ├── observatory_analysis.py
  │   │   │       ├── observatory_apple_music.py
  │   │   │       ├── observatory_contracts.py
  │   │   │       ├── observatory_guardian.py
  │   │   │       ├── observatory_hacker_news.py
  │   │   │       ├── observatory_source.py
  │   │   │       ├── operation_impact.py
  │   │   │       ├── perception.py
  │   │   │       ├── perception_profiles.py
  │   │   │       ├── perception_selection.py
  │   │   │       ├── perception_video_io.py
  │   │   │       ├── production_context.py
  │   │   │       ├── production_validation.py
  │   │   │       ├── qc.py
  │   │   │       ├── review.py
  │   │   │       ├── rich_perception.py
  │   │   │       ├── rich_perception_comparison.py
  │   │   │       ├── runtime_receipt_validation.py
  │   │   │       ├── timed_text.py
  │   │   │       └── video.py
  │   │   ├── tests
  │   │   │   ├── test_agent_processing.py
  │   │   │   ├── test_agent_surface.py
  │   │   │   ├── test_assets.py
  │   │   │   ├── test_cloudflare_r2.py
  │   │   │   ├── test_creative_alpha.py
  │   │   │   ├── test_creative_index.py
  │   │   │   ├── test_creative_library.py
  │   │   │   ├── test_ecology.py
  │   │   │   ├── test_equipment.py
  │   │   │   ├── test_expression_context.py
  │   │   │   ├── test_figma_provider.py
  │   │   │   ├── test_foundational_media.py
  │   │   │   ├── test_grounded_meaning.py
  │   │   │   ├── test_learning_context.py
  │   │   │   ├── test_models.py
  │   │   │   ├── test_observatory.py
  │   │   │   ├── test_operation_impact.py
  │   │   │   ├── test_perception.py
  │   │   │   ├── test_production_context.py
  │   │   │   ├── test_qc.py
  │   │   │   ├── test_research_validity.py
  │   │   │   ├── test_review.py
  │   │   │   ├── test_rich_perception.py
  │   │   │   ├── test_system_constellation_atlas.py
  │   │   │   ├── test_timed_text.py
  │   │   │   └── test_video.py
  │   │   ├── .env.example
  │   │   ├── .gitignore
  │   │   ├── .node-version
  │   │   ├── .python-version
  │   │   ├── AGENTS.md
  │   │   ├── LICENSE
  │   │   ├── MEDIA.md
  │   │   ├── mise.toml
  │   │   ├── package.json
  │   │   ├── pnpm-lock.yaml
  │   │   ├── pnpm-workspace.yaml
  │   │   ├── pyproject.toml
  │   │   ├── README.md
  │   │   ├── STUDIO.md
  │   │   ├── tsconfig.json
  │   │   └── uv.lock
  │   └── preservation
  │       ├── artifacts
  │       │   └── creative-preservation
  │       │       ├── archivematica-r6
  │       │       │   └── acceptance-r6.json
  │       │       ├── closeout-r10
  │       │       │   └── closeout-r10.json
  │       │       ├── forward-r1
  │       │       │   └── acceptance-r4.json
  │       │       ├── forward-r2
  │       │       │   ├── acceptance-r5.json
  │       │       │   ├── handoffs-r5.json
  │       │       │   └── resolver-census-r5.json
  │       │       ├── operations-r7
  │       │       │   └── acceptance-r7.json
  │       │       ├── pilot-r1
  │       │       │   ├── a3m-mets
  │       │       │   │   ├── game-adaptive-query-bench.xml
  │       │       │   │   ├── game-batch-zero.xml
  │       │       │   │   ├── game-look-away-garden.xml
  │       │       │   │   ├── game-nine-wells.xml
  │       │       │   │   ├── game-seen-not-approved-pcb.xml
  │       │       │   │   ├── game-signal-garden-evidence-petals.xml
  │       │       │   │   ├── media-almost-arriving.xml
  │       │       │   │   ├── media-gesture-orrery.xml
  │       │       │   │   ├── media-one-bell-three-rooms.xml
  │       │       │   │   ├── web-article-the-future-will-not-wait.xml
  │       │       │   │   ├── web-note-semantic-core-after-measurement.xml
  │       │       │   │   └── workstation-signal-seed.xml
  │       │       │   ├── a3m-bagit-zip-12work-METS-summary.json
  │       │       │   ├── a3m-bagit-zip-12work-METS.xml
  │       │       │   ├── a3m-bagit-zip-12work-v1.json
  │       │       │   ├── a3m-bagit-zip-hidden-v1.json
  │       │       │   ├── a3m-pilot-pass1.json
  │       │       │   ├── a3m-premis-fixity-v1.json
  │       │       │   ├── acceptance-r1.json
  │       │       │   ├── bagit-transfer-pilot-v1.json
  │       │       │   ├── corpus-v1.json
  │       │       │   ├── format-identification-fido-v109.json
  │       │       │   └── swhid-pilot-v1.json
  │       │       ├── retirement-r9
  │       │       │   └── retirement-r9.json
  │       │       └── standards-r8
  │       │           └── migration-r8.json
  │       ├── config
  │       │   └── archivematica-preservation-r10.compose.yml
  │       ├── docs
  │       │   ├── creative-preservation-archivematica-r6.md
  │       │   ├── creative-preservation-external-composition-r1.md
  │       │   ├── creative-preservation-operations-r7.md
  │       │   ├── creative-preservation-pilot-r1.md
  │       │   └── creative-preservation-standards-migration-r8.md
  │       ├── planning
  │       │   └── lego-plan-r1.json
  │       ├── scripts
  │       │   ├── fixity_consumer_contract.py
  │       │   ├── test_verify_source.py
  │       │   └── verify_source.py
  │       ├── systemd
  │       │   ├── ordivon-preservation-fixity-r7.service
  │       │   └── ordivon-preservation-fixity-r7.timer
  │       ├── README.md
  │       └── SOURCE_BOUNDARY.json
  ├── catalogs
  │   ├── authorities
  │   │   ├── evidence
  │   │   │   └── acceptance
  │   │   │       ├── authority-catalog-seed-closure-20260914.json
  │   │   │       └── enterprise-operating-model-r1-dogfood-20260914.json
  │   │   ├── observations
  │   │   │   ├── acm-sigsoft-benchmarking
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── acm-sigsoft-data-science
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── acm-sigsoft-general
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── acm-sigsoft-replication
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── agent-skills-spec
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── ansi-niso-z39.104-2022-credit
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── apache-arrow-format-1.5
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── apache-beam-programming-model
  │   │   │   │   └── 2026-09-20.json
  │   │   │   ├── apache-iceberg-1.11.0
  │   │   │   │   └── 2026-09-20.json
  │   │   │   ├── apache-iceberg-spec-v3
  │   │   │   │   └── 2026-09-20.json
  │   │   │   ├── apache-parquet-format-2.13.0
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── apalache-0.58.3
  │   │   │   │   └── 2026-09-22.json
  │   │   │   ├── archimate-3.2
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── archivematica-1.18.0
  │   │   │   │   └── 2026-09-20.json
  │   │   │   ├── artefactual-fixity-0.8.0
  │   │   │   │   └── 2026-09-20.json
  │   │   │   ├── asyncapi-3.1.0
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── bitol-odcs-3.2.0
  │   │   │   │   └── 2026-09-20.json
  │   │   │   ├── bitol-odps-1.1.0
  │   │   │   │   └── 2026-09-20.json
  │   │   │   ├── c2pa-2.4
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── cloudevents-1.0.2
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── commons-ip-2.11.3
  │   │   │   │   └── 2026-09-20.json
  │   │   │   ├── coretrustseal-requirements-2026-2028
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── cpmi-iosco-pfmi-2012
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── crossref-metadata-deposit-schema-5.5.0
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── csl-1.0.2
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── cyclonedx-1.7
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── datacite-metadata-schema-4.7
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── debezium-stable-cdc
  │   │   │   │   └── 2026-09-20.json
  │   │   │   ├── dpc-ram-3
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── e-ark-csip-2.2.0
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── e-ark-sip-2.2.0
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── eark-csip-2.2.0
  │   │   │   │   └── 2026-09-20.json
  │   │   │   ├── eark-sip-2.2.0
  │   │   │   │   └── 2026-09-20.json
  │   │   │   ├── emse-submission-guidelines
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── erpnext-budget-provider
  │   │   │   │   └── 2026-09-19.json
  │   │   │   ├── erpnext-crm-provider
  │   │   │   │   └── 2026-09-19.json
  │   │   │   ├── fair-principles
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── fix-4.4-errata-20030618
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── frappe-crm-provider
  │   │   │   │   └── 2026-09-19.json
  │   │   │   ├── frappe-helpdesk-provider
  │   │   │   │   └── 2026-09-19.json
  │   │   │   ├── frappe-hr-payroll-provider
  │   │   │   │   └── 2026-09-19.json
  │   │   │   ├── games-user-research-practice
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── godot-provider
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── google-analytics-traffic-source
  │   │   │   │   └── 2026-09-19.json
  │   │   │   ├── google-search-essentials
  │   │   │   │   └── 2026-09-19.json
  │   │   │   ├── gsn-3
  │   │   │   │   └── 2026-09-22.json
  │   │   │   ├── iab-privacy-standards
  │   │   │   │   └── 2026-09-19.json
  │   │   │   ├── icc-esomar-code-2025
  │   │   │   │   └── 2026-09-19.json
  │   │   │   ├── icc-marketing-code-2024
  │   │   │   │   └── 2026-09-19.json
  │   │   │   ├── in-toto-1.0
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── iptc-photo-metadata-2025.1
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── iso-10002-2018
  │   │   │   │   ├── 2026-09-14.json
  │   │   │   │   └── 2026-09-19.json
  │   │   │   ├── iso-10004-2018
  │   │   │   │   ├── 2026-09-14.json
  │   │   │   │   └── 2026-09-19.json
  │   │   │   ├── iso-10005-2018
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── iso-10006-2017
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── iso-14289-2-2024
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── iso-14721-2025
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── iso-15489-1-2016
  │   │   │   │   └── 2026-09-20.json
  │   │   │   ├── iso-17442-1-2020
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── iso-19005-4-2020
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── iso-19011-2026
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── iso-20022-1-2026
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── iso-20104-2015
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── iso-20252-2026
  │   │   │   │   └── 2026-09-19.json
  │   │   │   ├── iso-20400-2017
  │   │   │   │   └── 2026-09-19.json
  │   │   │   ├── iso-20652-2006
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── iso-20671-1-2021
  │   │   │   │   └── 2026-09-19.json
  │   │   │   ├── iso-21502-2020
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── iso-22301-2019-amd1-2024
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── iso-28500-2017
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── iso-30401-2018-amd1-2022-amd2-2024
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── iso-30405-2023
  │   │   │   │   └── 2026-09-19.json
  │   │   │   ├── iso-31000-2018
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── iso-32000-2-2020
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── iso-37301-2021
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── iso-37500-2014
  │   │   │   │   └── 2026-09-19.json
  │   │   │   ├── iso-56001-2024
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── iso-8000-115-2024
  │   │   │   │   └── 2026-09-20.json
  │   │   │   ├── iso-9001-2015-amd1-2024
  │   │   │   │   ├── 2026-09-14.json
  │   │   │   │   └── 2026-09-19.json
  │   │   │   ├── iso-9001-2026
  │   │   │   │   ├── 2026-09-14.json
  │   │   │   │   └── 2026-09-19.json
  │   │   │   ├── iso-9004-2018
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── iso-9241-11-2018
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── iso-9241-210-2019
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── iso-iec-11179-3-2023
  │   │   │   │   └── 2026-09-20.json
  │   │   │   ├── iso-iec-11179-3-amd1-2026
  │   │   │   │   └── 2026-09-20.json
  │   │   │   ├── iso-iec-12113-2022
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── iso-iec-20000-1-2018-amd1-2024
  │   │   │   │   ├── 2026-09-14.json
  │   │   │   │   └── 2026-09-19.json
  │   │   │   ├── iso-iec-25010-2023
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── iso-iec-27001-2022-amd1-2024
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── iso-iec-29500-1-2016
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── iso-iec-42001-2023
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── iso-iec-5259-2-2024
  │   │   │   │   └── 2026-09-20.json
  │   │   │   ├── iso-iec-ieee-12207-2026
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── iso-iec-ieee-15288-2023
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── iso-iec-ieee-29148-2018
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── iso-integrated-management-systems-guide-2026
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── json-schema-draft-2020-12
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── lean-startup-principles
  │   │   │   │   └── 2026-09-19.json
  │   │   │   ├── mcp-spec-2026-07-28
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── mets-2
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── mrc-outcomes-data-quality-2022
  │   │   │   │   └── 2026-09-19.json
  │   │   │   ├── ndsa-levels-digital-preservation-2.1
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── nist-ai-rmf-1.0
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── nist-csf-2.0
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── nist-oscal-1.1.3
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── nist-privacy-framework-1.0
  │   │   │   │   └── 2026-09-20.json
  │   │   │   ├── nist-sp-800-218-ssdf-1.1
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── nuxmv-2.2.0
  │   │   │   │   └── 2026-09-22.json
  │   │   │   ├── oasis-opendocument-1.3
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── oasis-sarif-2.1.0
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── oci-distribution-spec-1.1.1
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── oci-image-spec-1.1.1
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── oci-runtime-spec-1.3.0
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── ocra-1.1.2
  │   │   │   │   └── 2026-09-22.json
  │   │   │   ├── ocra-2.1.0
  │   │   │   │   └── 2026-09-22.json
  │   │   │   ├── ogc-geopackage-1.4.0
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── omg-bpmn-2.0.2
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── omg-cmmn-1.1
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── omg-dmn-1.5
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── omg-reqif-1.2
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── omg-sacm-2.3
  │   │   │   │   └── 2026-09-22.json
  │   │   │   ├── openapi-3.2.0
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── openid-connect-core-1.0-errata2
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── openlineage-spec
  │   │   │   │   ├── 2026-09-14.json
  │   │   │   │   └── 2026-11-06.json
  │   │   │   ├── opentelemetry-genai-semconv
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── opentelemetry-spec-1.60.0
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── orcid-id-structure
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── otlp-1.11.0
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── owasp-asvs-5.0.0
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── pacti-0.3.1
  │   │   │   │   └── 2026-09-22.json
  │   │   │   ├── premis-3.0
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── prisma-2020
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── pronom-registry
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── qudt-units-3.5.1
  │   │   │   │   └── 2026-09-20.json
  │   │   │   ├── rfc-1034
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── rfc-1035
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── rfc-6749
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── rfc-7858
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── rfc-8310
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── rfc-8414
  │   │   │   │   └── 2026-09-20.json
  │   │   │   ├── rfc-8484
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── rfc-8493-bagit-1.0
  │   │   │   │   └── 2026-09-20.json
  │   │   │   ├── rfc-8707
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── rfc-9000
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── rfc-9110
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── rfc-9113
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── rfc-9114
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── rfc-9700
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── rfc-9728
  │   │   │   │   └── 2026-09-20.json
  │   │   │   ├── rfc-9846
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── ro-crate-1.3
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── roger-martin-strategy-choice-cascade
  │   │   │   │   └── 2026-09-19.json
  │   │   │   ├── ror-schema-2.1
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── samr-registration-materials-2026
  │   │   │   │   └── 2026-09-19.json
  │   │   │   ├── sdmx-3.1
  │   │   │   │   └── 2026-09-20.json
  │   │   │   ├── sdmx-cl-obs-status-2.3
  │   │   │   │   └── 2026-09-20.json
  │   │   │   ├── slsa-1.2
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── spdx-3.0
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── springer-research-data-policy
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── strategyzer-business-model-canvas
  │   │   │   │   └── 2026-09-19.json
  │   │   │   ├── strategyzer-value-proposition-canvas
  │   │   │   │   └── 2026-09-19.json
  │   │   │   ├── stripe-saas-pricing-packaging
  │   │   │   │   └── 2026-09-19.json
  │   │   │   ├── swhid-scheme-v1
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── tla-tools-1.7.4
  │   │   │   │   └── 2026-09-22.json
  │   │   │   ├── togaf-standard-10th-edition
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── ucum-spec
  │   │   │   │   └── 2026-09-20.json
  │   │   │   ├── w3c-dcat-3-2024
  │   │   │   │   └── 2026-09-20.json
  │   │   │   ├── w3c-odrl-2.2-2018
  │   │   │   │   └── 2026-09-20.json
  │   │   │   ├── w3c-png-3-2025
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── w3c-prov-o-2013
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── wcag-2.2
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── worldcc-contract-management-standard-4e
  │   │   │   │   └── 2026-09-19.json
  │   │   │   ├── xbox-accessibility-guidelines-3.2
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── xbrl-2.1
  │   │   │   │   └── 2026-09-14.json
  │   │   │   ├── yc-essential-startup-advice
  │   │   │   │   └── 2026-09-19.json
  │   │   │   └── yc-how-to-sell-2018
  │   │   │       └── 2026-09-19.json
  │   │   ├── planning
  │   │   │   └── lego-plan-r1.json
  │   │   ├── records
  │   │   │   ├── acm-sigsoft
  │   │   │   │   ├── acm-sigsoft-benchmarking.json
  │   │   │   │   ├── acm-sigsoft-data-science.json
  │   │   │   │   ├── acm-sigsoft-general.json
  │   │   │   │   └── acm-sigsoft-replication.json
  │   │   │   ├── agent-skills
  │   │   │   │   └── agent-skills-spec.json
  │   │   │   ├── apache-arrow
  │   │   │   │   └── apache-arrow-format-1.5.json
  │   │   │   ├── apache-beam
  │   │   │   │   └── apache-beam-programming-model.json
  │   │   │   ├── apache-iceberg
  │   │   │   │   ├── apache-iceberg-1.11.0.json
  │   │   │   │   └── apache-iceberg-spec-v3.json
  │   │   │   ├── apache-parquet
  │   │   │   │   └── apache-parquet-format-2.13.0.json
  │   │   │   ├── apalache-mc
  │   │   │   │   └── apalache-0.58.3.json
  │   │   │   ├── artefactual
  │   │   │   │   ├── archivematica-1.18.0.json
  │   │   │   │   └── artefactual-fixity-0.8.0.json
  │   │   │   ├── asyncapi
  │   │   │   │   └── asyncapi-3.1.0.json
  │   │   │   ├── bitol
  │   │   │   │   ├── bitol-odcs-3.2.0.json
  │   │   │   │   └── bitol-odps-1.1.0.json
  │   │   │   ├── c2pa
  │   │   │   │   └── c2pa-2.4.json
  │   │   │   ├── citation-style-language
  │   │   │   │   └── csl-1.0.2.json
  │   │   │   ├── cncf-cloudevents
  │   │   │   │   └── cloudevents-1.0.2.json
  │   │   │   ├── commons-ip
  │   │   │   │   └── commons-ip-2.11.3.json
  │   │   │   ├── coretrustseal
  │   │   │   │   └── coretrustseal-requirements-2026-2028.json
  │   │   │   ├── cpmi-iosco
  │   │   │   │   └── cpmi-iosco-pfmi-2012.json
  │   │   │   ├── crossref
  │   │   │   │   └── crossref-metadata-deposit-schema-5.5.0.json
  │   │   │   ├── datacite
  │   │   │   │   └── datacite-metadata-schema-4.7.json
  │   │   │   ├── debezium
  │   │   │   │   └── debezium-stable-cdc.json
  │   │   │   ├── digital-preservation-coalition
  │   │   │   │   └── dpc-ram-3.json
  │   │   │   ├── dilcis
  │   │   │   │   ├── eark-csip-2.2.0.json
  │   │   │   │   └── eark-sip-2.2.0.json
  │   │   │   ├── dilcis-board
  │   │   │   │   ├── e-ark-csip-2.2.0.json
  │   │   │   │   └── e-ark-sip-2.2.0.json
  │   │   │   ├── fbk
  │   │   │   │   ├── nuxmv-2.2.0.json
  │   │   │   │   ├── ocra-1.1.2.json
  │   │   │   │   └── ocra-2.1.0.json
  │   │   │   ├── fix-trading
  │   │   │   │   └── fix-4.4-errata-20030618.json
  │   │   │   ├── frappe
  │   │   │   │   ├── erpnext-budget-provider.json
  │   │   │   │   ├── erpnext-crm-provider.json
  │   │   │   │   ├── frappe-crm-provider.json
  │   │   │   │   ├── frappe-helpdesk-provider.json
  │   │   │   │   └── frappe-hr-payroll-provider.json
  │   │   │   ├── games-user-research
  │   │   │   │   └── games-user-research-practice.json
  │   │   │   ├── go-fair
  │   │   │   │   └── fair-principles.json
  │   │   │   ├── godot-engine
  │   │   │   │   └── godot-provider.json
  │   │   │   ├── google
  │   │   │   │   ├── google-analytics-traffic-source.json
  │   │   │   │   └── google-search-essentials.json
  │   │   │   ├── iab
  │   │   │   │   └── iab-privacy-standards.json
  │   │   │   ├── icc
  │   │   │   │   ├── icc-esomar-code-2025.json
  │   │   │   │   └── icc-marketing-code-2024.json
  │   │   │   ├── ietf
  │   │   │   │   ├── rfc-1034.json
  │   │   │   │   ├── rfc-1035.json
  │   │   │   │   ├── rfc-6749.json
  │   │   │   │   ├── rfc-7858.json
  │   │   │   │   ├── rfc-8310.json
  │   │   │   │   ├── rfc-8414.json
  │   │   │   │   ├── rfc-8484.json
  │   │   │   │   ├── rfc-8493-bagit-1.0.json
  │   │   │   │   ├── rfc-8707.json
  │   │   │   │   ├── rfc-9000.json
  │   │   │   │   ├── rfc-9110.json
  │   │   │   │   ├── rfc-9113.json
  │   │   │   │   ├── rfc-9114.json
  │   │   │   │   ├── rfc-9700.json
  │   │   │   │   ├── rfc-9728.json
  │   │   │   │   └── rfc-9846.json
  │   │   │   ├── in-toto
  │   │   │   │   └── in-toto-1.0.json
  │   │   │   ├── iptc
  │   │   │   │   └── iptc-photo-metadata-2025.1.json
  │   │   │   ├── iso
  │   │   │   │   ├── iso-10002-2018.json
  │   │   │   │   ├── iso-10004-2018.json
  │   │   │   │   ├── iso-10005-2018.json
  │   │   │   │   ├── iso-10006-2017.json
  │   │   │   │   ├── iso-14289-2-2024.json
  │   │   │   │   ├── iso-14721-2025.json
  │   │   │   │   ├── iso-15489-1-2016.json
  │   │   │   │   ├── iso-17442-1-2020.json
  │   │   │   │   ├── iso-19005-4-2020.json
  │   │   │   │   ├── iso-19011-2026.json
  │   │   │   │   ├── iso-20022-1-2026.json
  │   │   │   │   ├── iso-20104-2015.json
  │   │   │   │   ├── iso-20252-2026.json
  │   │   │   │   ├── iso-20400-2017.json
  │   │   │   │   ├── iso-20652-2006.json
  │   │   │   │   ├── iso-20671-1-2021.json
  │   │   │   │   ├── iso-21502-2020.json
  │   │   │   │   ├── iso-22301-2019-amd1-2024.json
  │   │   │   │   ├── iso-28500-2017.json
  │   │   │   │   ├── iso-30401-2018-amd1-2022-amd2-2024.json
  │   │   │   │   ├── iso-30405-2023.json
  │   │   │   │   ├── iso-31000-2018.json
  │   │   │   │   ├── iso-32000-2-2020.json
  │   │   │   │   ├── iso-37301-2021.json
  │   │   │   │   ├── iso-37500-2014.json
  │   │   │   │   ├── iso-56001-2024.json
  │   │   │   │   ├── iso-8000-115-2024.json
  │   │   │   │   ├── iso-9001-2015-amd1-2024.json
  │   │   │   │   ├── iso-9001-2026.json
  │   │   │   │   ├── iso-9004-2018.json
  │   │   │   │   ├── iso-9241-11-2018.json
  │   │   │   │   ├── iso-9241-210-2019.json
  │   │   │   │   └── iso-integrated-management-systems-guide-2026.json
  │   │   │   ├── iso-iec
  │   │   │   │   ├── iso-iec-11179-3-2023.json
  │   │   │   │   ├── iso-iec-11179-3-amd1-2026.json
  │   │   │   │   ├── iso-iec-12113-2022.json
  │   │   │   │   ├── iso-iec-20000-1-2018-amd1-2024.json
  │   │   │   │   ├── iso-iec-25010-2023.json
  │   │   │   │   ├── iso-iec-27001-2022-amd1-2024.json
  │   │   │   │   ├── iso-iec-29500-1-2016.json
  │   │   │   │   ├── iso-iec-42001-2023.json
  │   │   │   │   └── iso-iec-5259-2-2024.json
  │   │   │   ├── iso-iec-ieee
  │   │   │   │   ├── iso-iec-ieee-12207-2026.json
  │   │   │   │   ├── iso-iec-ieee-15288-2023.json
  │   │   │   │   └── iso-iec-ieee-29148-2018.json
  │   │   │   ├── json-schema
  │   │   │   │   └── json-schema-draft-2020-12.json
  │   │   │   ├── lean-startup
  │   │   │   │   └── lean-startup-principles.json
  │   │   │   ├── linux-foundation
  │   │   │   │   └── spdx-3.0.json
  │   │   │   ├── loc-premis
  │   │   │   │   └── premis-3.0.json
  │   │   │   ├── mets-editorial-board
  │   │   │   │   └── mets-2.json
  │   │   │   ├── microsoft-xbox
  │   │   │   │   └── xbox-accessibility-guidelines-3.2.json
  │   │   │   ├── model-context-protocol
  │   │   │   │   └── mcp-spec-2026-07-28.json
  │   │   │   ├── mrc
  │   │   │   │   └── mrc-outcomes-data-quality-2022.json
  │   │   │   ├── ndsa
  │   │   │   │   └── ndsa-levels-digital-preservation-2.1.json
  │   │   │   ├── niso
  │   │   │   │   └── ansi-niso-z39.104-2022-credit.json
  │   │   │   ├── nist
  │   │   │   │   ├── nist-ai-rmf-1.0.json
  │   │   │   │   ├── nist-csf-2.0.json
  │   │   │   │   ├── nist-oscal-1.1.3.json
  │   │   │   │   ├── nist-privacy-framework-1.0.json
  │   │   │   │   └── nist-sp-800-218-ssdf-1.1.json
  │   │   │   ├── oasis
  │   │   │   │   ├── oasis-opendocument-1.3.json
  │   │   │   │   └── oasis-sarif-2.1.0.json
  │   │   │   ├── oci
  │   │   │   │   ├── oci-distribution-spec-1.1.1.json
  │   │   │   │   ├── oci-image-spec-1.1.1.json
  │   │   │   │   └── oci-runtime-spec-1.3.0.json
  │   │   │   ├── ogc
  │   │   │   │   └── ogc-geopackage-1.4.0.json
  │   │   │   ├── omg
  │   │   │   │   ├── omg-bpmn-2.0.2.json
  │   │   │   │   ├── omg-cmmn-1.1.json
  │   │   │   │   ├── omg-dmn-1.5.json
  │   │   │   │   ├── omg-reqif-1.2.json
  │   │   │   │   └── omg-sacm-2.3.json
  │   │   │   ├── openapi-initiative
  │   │   │   │   └── openapi-3.2.0.json
  │   │   │   ├── openid-foundation
  │   │   │   │   └── openid-connect-core-1.0-errata2.json
  │   │   │   ├── openlineage
  │   │   │   │   └── openlineage-spec.json
  │   │   │   ├── opentelemetry
  │   │   │   │   ├── opentelemetry-genai-semconv.json
  │   │   │   │   ├── opentelemetry-spec-1.60.0.json
  │   │   │   │   └── otlp-1.11.0.json
  │   │   │   ├── orcid
  │   │   │   │   └── orcid-id-structure.json
  │   │   │   ├── owasp
  │   │   │   │   └── owasp-asvs-5.0.0.json
  │   │   │   ├── owasp-ecma
  │   │   │   │   └── cyclonedx-1.7.json
  │   │   │   ├── pacti
  │   │   │   │   └── pacti-0.3.1.json
  │   │   │   ├── prisma
  │   │   │   │   └── prisma-2020.json
  │   │   │   ├── qudt
  │   │   │   │   └── qudt-units-3.5.1.json
  │   │   │   ├── research-object
  │   │   │   │   └── ro-crate-1.3.json
  │   │   │   ├── roger-l-martin
  │   │   │   │   └── roger-martin-strategy-choice-cascade.json
  │   │   │   ├── ror
  │   │   │   │   └── ror-schema-2.1.json
  │   │   │   ├── samr
  │   │   │   │   └── samr-registration-materials-2026.json
  │   │   │   ├── scsc
  │   │   │   │   └── gsn-3.json
  │   │   │   ├── sdmx
  │   │   │   │   ├── sdmx-3.1.json
  │   │   │   │   └── sdmx-cl-obs-status-2.3.json
  │   │   │   ├── slsa
  │   │   │   │   └── slsa-1.2.json
  │   │   │   ├── software-heritage
  │   │   │   │   └── swhid-scheme-v1.json
  │   │   │   ├── springer-nature
  │   │   │   │   ├── emse-submission-guidelines.json
  │   │   │   │   └── springer-research-data-policy.json
  │   │   │   ├── strategyzer
  │   │   │   │   ├── strategyzer-business-model-canvas.json
  │   │   │   │   └── strategyzer-value-proposition-canvas.json
  │   │   │   ├── stripe
  │   │   │   │   └── stripe-saas-pricing-packaging.json
  │   │   │   ├── the-open-group
  │   │   │   │   ├── archimate-3.2.json
  │   │   │   │   └── togaf-standard-10th-edition.json
  │   │   │   ├── tlaplus
  │   │   │   │   └── tla-tools-1.7.4.json
  │   │   │   ├── ucum
  │   │   │   │   └── ucum-spec.json
  │   │   │   ├── uk-national-archives
  │   │   │   │   └── pronom-registry.json
  │   │   │   ├── w3c
  │   │   │   │   ├── w3c-dcat-3-2024.json
  │   │   │   │   ├── w3c-odrl-2.2-2018.json
  │   │   │   │   ├── w3c-png-3-2025.json
  │   │   │   │   ├── w3c-prov-o-2013.json
  │   │   │   │   └── wcag-2.2.json
  │   │   │   ├── worldcc
  │   │   │   │   └── worldcc-contract-management-standard-4e.json
  │   │   │   ├── xbrl-international
  │   │   │   │   └── xbrl-2.1.json
  │   │   │   └── y-combinator
  │   │   │       ├── yc-essential-startup-advice.json
  │   │   │       └── yc-how-to-sell-2018.json
  │   │   ├── schemas
  │   │   │   ├── external-authority-index-v1.schema.json
  │   │   │   ├── external-authority-observation-v1.schema.json
  │   │   │   └── external-authority-record-v1.schema.json
  │   │   ├── scripts
  │   │   │   ├── authority_catalog.py
  │   │   │   ├── authority_catalog_search.py
  │   │   │   ├── authority_catalog_sources.py
  │   │   │   ├── check_authority_catalog_r1.py
  │   │   │   └── check_historical_registration.py
  │   │   ├── tests
  │   │   │   └── test_authority_catalog.py
  │   │   ├── venues
  │   │   │   └── fse-2027-research-r1.json
  │   │   ├── .gitignore
  │   │   ├── mise.toml
  │   │   ├── pyproject.toml
  │   │   ├── README.md
  │   │   └── uv.lock
  │   ├── capabilities
  │   │   ├── artifact
  │   │   │   └── README.md
  │   │   ├── docs
  │   │   │   ├── EXTERNAL_CAPABILITY_EVALUATION_R1.md
  │   │   │   └── HUMAN_EXTERNAL_LEGO_REVIEW_R1.md
  │   │   ├── ele
  │   │   │   ├── README.md
  │   │   │   ├── relations.py
  │   │   │   ├── schema.sql
  │   │   │   └── studies.py
  │   │   ├── evidence
  │   │   │   ├── github-radar
  │   │   │   │   └── 2026-11-06.json
  │   │   │   ├── capability-packages-r1-20260913.md
  │   │   │   ├── cross-owner-source-observations-20261106.json
  │   │   │   ├── worktrunk-candidate-20261106.json
  │   │   │   └── worktrunk-repo-owner-consumer-shadow-20261106.json
  │   │   ├── packages
  │   │   │   ├── artifact.md
  │   │   │   ├── data-analytics.md
  │   │   │   ├── distribution.md
  │   │   │   ├── engineering.md
  │   │   │   ├── game.md
  │   │   │   ├── INDEX.md
  │   │   │   ├── media.md
  │   │   │   ├── network.md
  │   │   │   ├── operations.md
  │   │   │   ├── preservation.md
  │   │   │   ├── README.md
  │   │   │   ├── research.md
  │   │   │   └── security.md
  │   │   ├── profiles
  │   │   │   └── web-interaction-r1.json
  │   │   ├── providers
  │   │   │   ├── artifact-v2.md
  │   │   │   ├── browser-use.md
  │   │   │   ├── check-jsonschema.md
  │   │   │   ├── codex.md
  │   │   │   ├── comfyui.md
  │   │   │   ├── commons-ip.md
  │   │   │   ├── dagster.md
  │   │   │   ├── dify.md
  │   │   │   ├── distribution-v2.md
  │   │   │   ├── enduro.md
  │   │   │   ├── firecrawl.md
  │   │   │   ├── flowable.md
  │   │   │   ├── graphify.md
  │   │   │   ├── haystack.md
  │   │   │   ├── langfuse.md
  │   │   │   ├── langgraph.md
  │   │   │   ├── litellm.md
  │   │   │   ├── llamaindex.md
  │   │   │   ├── markitdown.md
  │   │   │   ├── mcp.md
  │   │   │   ├── microsoft-agent-framework.md
  │   │   │   ├── n8n.md
  │   │   │   ├── network-v2.md
  │   │   │   ├── openinference.md
  │   │   │   ├── opentelemetry.md
  │   │   │   ├── phoenix.md
  │   │   │   ├── plane.md
  │   │   │   ├── playwright-cli.md
  │   │   │   ├── qdrant.md
  │   │   │   ├── reasoning-waist.md
  │   │   │   ├── runtime.md
  │   │   │   ├── security-v2.md
  │   │   │   ├── strictdoc.md
  │   │   │   ├── temporal.md
  │   │   │   ├── workstation-v2.md
  │   │   │   └── worktrunk.md
  │   │   ├── routing
  │   │   │   ├── web_interaction_route.py
  │   │   │   └── web_provider_census.py
  │   │   ├── schemas
  │   │   │   └── external-capability-candidate-r1.schema.json
  │   │   ├── scripts
  │   │   │   ├── check_external_candidate_references.py
  │   │   │   ├── compare_worktrunk_owner_consumer.py
  │   │   │   ├── github_radar_incremental.py
  │   │   │   └── verify_reasoning_providers.py
  │   │   ├── tests
  │   │   │   ├── test_ele_pg_studies.py
  │   │   │   ├── test_external_capability_evaluation.py
  │   │   │   ├── test_web_interaction_route.py
  │   │   │   └── test_web_provider_routing_skill.py
  │   │   ├── AGENTS.md
  │   │   ├── authority-map-r1.md
  │   │   ├── README.md
  │   │   └── RESEARCH_CAPABILITY_PACKAGE_R1.md
  │   ├── data-products
  │   │   └── experimental-episode-corpus-r1
  │   │       ├── acceptance.json
  │   │       ├── artifact-dataset-contract.json
  │   │       ├── governance-policy.odrl.jsonld
  │   │       ├── odcs.json
  │   │       └── odps.json
  │   └── knowledge
  │       ├── evidence
  │       │   ├── acceptance
  │       │   │   ├── agent-architecture-lego-catalog-r1.json
  │       │   │   └── agent-service-control-stability-r1.json
  │       │   ├── agent-campaigns
  │       │   │   ├── agent-common-structure-destroyer-r1-C01.md
  │       │   │   └── prompt-corpus-common-structure-r1-wave1-recovered.md
  │       │   └── analysis
  │       │       └── agent-service-control-stability-r1.json
  │       ├── graphs
  │       │   ├── agent-architecture-lego-catalog-r1.json
  │       │   ├── ai-miracle-material-lego-case-r1.json
  │       │   ├── browser-security-detector-coverage-r6.json
  │       │   ├── browser-security-detector-coverage-r9.json
  │       │   ├── cloudflare-provider-security-boundary-r1.json
  │       │   ├── ordivon-agent-birth-r1.json
  │       │   ├── ordivon-agent-service-control-stability-r1.json
  │       │   └── zcode-workspace-snapshot-security-lego-r1.json
  │       ├── lessons
  │       │   ├── agent-architecture-lego-catalog-r1.md
  │       │   ├── agent-birth-provider-boundary-r1.md
  │       │   ├── agent-product-common-structure-r1-wave3-partial.md
  │       │   ├── agent-product-common-structure-r1.md
  │       │   ├── agent-security-cross-domain-destroyer-r1.md
  │       │   ├── agent-security-cross-system-destroyer-r1.md
  │       │   ├── agent-security-lego-r1.md
  │       │   ├── agent-service-regime-card-r1.md
  │       │   ├── agent-skills-kernel.md
  │       │   ├── ai-miracle-material-lego-case-r1.md
  │       │   ├── authority-mature-substrate-decomposition-r1.md
  │       │   ├── aws-agentcore-agent-service-kernel-r1.md
  │       │   ├── browser-automation-dynamic-defense-r1.md
  │       │   ├── browser-use-agent-browser-kernel.md
  │       │   ├── browserless-source-deep-dive-r1.md
  │       │   ├── camoufox-source-deep-dive-r1.md
  │       │   ├── cloudflare-provider-security-boundary-r1.md
  │       │   ├── cloudflare-provider-security-exp-r1.md
  │       │   ├── cloudflare-provider-security-exp-r2.md
  │       │   ├── cloudflare-provider-security-exp-r5.md
  │       │   ├── cloudflare-provider-security-exp-r9.md
  │       │   ├── composition-science-foundations-r1.md
  │       │   ├── dagster-asset-orchestration-kernel.md
  │       │   ├── dify-ai-application-platform-kernel.md
  │       │   ├── firecrawl-web-context-kernel.md
  │       │   ├── flaresolverr-source-deep-dive-r1.md
  │       │   ├── langfuse-phoenix-ai-engineering-platform-kernel.md
  │       │   ├── langgraph-agent-state-machine-kernel.md
  │       │   ├── lego-question-compiler-outcome-pressure-r1.md
  │       │   ├── lego-self-analysis-wave1-r1.md
  │       │   ├── lego-theory-foundations-r1.md
  │       │   ├── lego-wave2-prospective-validation-r1.md
  │       │   ├── lego-wave23-self-audit-r1.md
  │       │   ├── lego-wave3-prospective-validation-r1.md
  │       │   ├── litellm-model-gateway-kernel.md
  │       │   ├── llamaindex-haystack-context-retrieval-kernel.md
  │       │   ├── markitdown-document-normalization-kernel.md
  │       │   ├── mcp-interoperability-kernel.md
  │       │   ├── microsoft-activation-scripts-avoidance-study.md
  │       │   ├── microsoft-activation-scripts-deep-architecture-study.md
  │       │   ├── microsoft-foundry-agent-service-kernel-r1.md
  │       │   ├── n8n-dsh-node-composition-r1.md
  │       │   ├── n8n-integration-kernel.md
  │       │   ├── oh-my-pi-adaptive-edit-abi-kernel.md
  │       │   ├── oh-my-pi-child-run-agent-hub-kernel.md
  │       │   ├── oh-my-pi-harness-mechanism-map.md
  │       │   ├── ordivon-agent-birth-lego-r1.md
  │       │   ├── ordivon-agent-service-control-stability-r1.md
  │       │   ├── otel-openinference-observability-kernel.md
  │       │   ├── patchright-source-deep-dive-r1.md
  │       │   ├── poker-ai-lego-question-compiler-pilot-r1.md
  │       │   ├── qdrant-vector-search-kernel.md
  │       │   ├── rebrowser-patches-source-deep-dive-r1.md
  │       │   ├── seleniumbase-source-deep-dive-r1.md
  │       │   ├── spec-kit-engineering-kernel.md
  │       │   ├── superpowers-engineering-discipline-kernel.md
  │       │   ├── system-prompts-corpus-deep-architecture-study.md
  │       │   ├── temporal-durable-execution-kernel.md
  │       │   ├── worktrunk-workspace-native-git-r1.md
  │       │   └── zcode-workspace-snapshot-security-lego-r1.md
  │       └── README.md
  ├── docs
  │   ├── architecture
  │   │   ├── evidence
  │   │   │   ├── CONVERGENCE_OBSERVATION_DATASET_R1.json
  │   │   │   ├── CONVERGENCE_OWNER_COST_F2EC_R1.json
  │   │   │   ├── CONVERGENCE_QUEUE_TELEMETRY_BASELINE_R1.json
  │   │   │   ├── FORMAL_LEGO_ISSUE_CENSUS_20261024_R1.json
  │   │   │   ├── FORMAL_LEGO_ISSUE_CENSUS_20261024_R2.json
  │   │   │   ├── FORMAL_LEGO_ISSUE_CENSUS_20261025_R1.json
  │   │   │   ├── FORMAL_LEGO_ISSUE_CENSUS_20261101_R1.json
  │   │   │   ├── FORMAL_LEGO_ISSUE_CENSUS_20261101_R2.json
  │   │   │   ├── FORMAL_LEGO_ISSUE_CENSUS_20261107_R1.json
  │   │   │   ├── lego-theory-wave2-prospective-r1.json
  │   │   │   ├── lego-theory-wave3-prospective-r1.json
  │   │   │   ├── ORDIVON_PHASE1_NAME_SEEDS_20261027_R4.json
  │   │   │   ├── PHASE1_LINUX_UNIT_DRIFT_FACETS_20261027_R1.json
  │   │   │   ├── PHASE1_R8_148_NODES_UPSTREAM_PARITY_20261028.json
  │   │   │   ├── PHASE1_SOURCE_INSTALLED_BOUNDARIES_20261027_R1.json
  │   │   │   └── PHASE1_WHOLE_SYSTEM_NEGATIVE_SPACE_20261028_R1.json
  │   │   ├── policies
  │   │   │   ├── CONSUMPTION_BOUNDARY_R1.md
  │   │   │   ├── external-ownership-boundary.json
  │   │   │   ├── EXTERNAL_OWNERSHIP_BOUNDARY.md
  │   │   │   └── README.md
  │   │   ├── schemas
  │   │   │   ├── convergence-ci-economic-annotation-v1.schema.json
  │   │   │   ├── convergence-ci-observation-v1.schema.json
  │   │   │   ├── convergence-owner-cost-episode-v1.schema.json
  │   │   │   ├── convergence-pressure-assessment-v1.schema.json
  │   │   │   └── convergence-queue-observation-v1.schema.json
  │   │   ├── agent-native-measurement-improvement-loop-r1.json
  │   │   ├── agent-plugin-adoption-r1.md
  │   │   ├── AGENT_CONCEPTS_FORMAL_LEGO_RESEARCH_20261024.md
  │   │   ├── AGENT_CONTRACT_EXECUTION_SPEC_R1.md
  │   │   ├── AGENT_OUTCOME_CONSTRAINT_EXECUTION_SPEC_R1.md
  │   │   ├── AGENT_OUTCOME_REALIZATION_R21_SPEC_20261109.md
  │   │   ├── AGENT_PLUGIN_BOUNDARY_R2.md
  │   │   ├── AGENT_PLUGIN_CORE_R3.md
  │   │   ├── AGENT_PLUGIN_R4_ACCEPTANCE_20260921.md
  │   │   ├── architecture-convergence-a01r2.json
  │   │   ├── ARCHITECTURE_CONVERGENCE_A01R2.md
  │   │   ├── AUTHORITY_SEMANTIC_EXPRESSION_R1.md
  │   │   ├── c03-skill-bridge-consumer-census-r1.json
  │   │   ├── C03_SKILL_BRIDGE_CONSUMER_CENSUS_R1.md
  │   │   ├── CAPABILITY_PACKAGES_R1.md
  │   │   ├── classification.md
  │   │   ├── COMMERCIAL_STRATEGY_CURRENT_FACTS_R1.md
  │   │   ├── COMPOSITION_SCIENCE_R1.md
  │   │   ├── convergence-queue-lego-r1.json
  │   │   ├── COUNTEREXAMPLE_GUIDED_REPRESENTATION_R1.md
  │   │   ├── CROSS_DOMAIN_VERIFICATION_R3.md
  │   │   ├── CURRENT_ARCHITECTURE.md
  │   │   ├── DATA_DURABLE_PRESERVATION_R1.md
  │   │   ├── DATA_LIFECYCLE_CENSUS_R1.md
  │   │   ├── DATA_PRODUCT_CONSUMPTION_FEEDBACK_R1.md
  │   │   ├── DATA_PRODUCTS_FEDERATION_R1.md
  │   │   ├── DECISIONS.md
  │   │   ├── deployed-architecture-r1.json
  │   │   ├── e01-e02-trace-identity-acceptance-20260921.json
  │   │   ├── e01-trace-context-contract-r1.json
  │   │   ├── e02-authenticated-principal-boundary-r2.json
  │   │   ├── ENTERPRISE_OPERATING_MODEL_R1.md
  │   │   ├── evidence-boundary-census-r1.json
  │   │   ├── EVIDENCE_BOUNDARY_CENSUS_R1.md
  │   │   ├── experimental-episode-r1.md
  │   │   ├── EXTERNAL_INNOVATION_THEORY_CENSUS_R1.md
  │   │   ├── gateway-single-agent-northbound-acceptance-20260926.json
  │   │   ├── gateway-swf-northbound-acceptance-20260924.json
  │   │   ├── GATEWAY_B02_CAPABILITY_PROJECTION_ACCEPTANCE_20260921.md
  │   │   ├── GATEWAY_CAPABILITY_AUTHZ_CONTRACT_R1.md
  │   │   ├── GATEWAY_HOST_NORTHBOUND_ACCEPTANCE_20260922.md
  │   │   ├── intent-field-census-r1.json
  │   │   ├── LEARNING_DATA_OWNERSHIP_CENSUS_R1.md
  │   │   ├── LEGO_THEORY_WAVE2_R1.md
  │   │   ├── LEGO_THEORY_WAVE3_R1.md
  │   │   ├── ordivon-composition-architecture-lego-r1.json
  │   │   ├── ORDIVON_COMPOSITION_ARCHITECTURE_EXECUTION_PLAN_R1.md
  │   │   ├── ORDIVON_COMPOSITION_ARCHITECTURE_R1.md
  │   │   ├── OWNER_DEPENDENCY_BOUNDARY_R1.md
  │   │   ├── OWNER_MODULARITY_STRUCTURE_LIFECYCLE_PROGRAM_R1.md
  │   │   ├── persistent-trace-backend-acceptance-20260921.json
  │   │   ├── research-study-authority-r1.json
  │   │   ├── RESEARCH_PUBLICATION_CLOSURE_R1.md
  │   │   ├── RESEARCH_PUBLICATION_PERCEPTUAL_CONFORMANCE_R2.md
  │   │   ├── RESEARCH_STUDY_AUTHORITY_R1.md
  │   │   ├── SKILLS.md
  │   │   ├── STANDARD_NATIVE_ENTERPRISE_ENVIRONMENT_R1.md
  │   │   ├── STANDARD_NATIVE_ENTERPRISE_ENVIRONMENT_R2.md
  │   │   ├── structure-r2-transition-r1.json
  │   │   ├── STRUCTURE_R2.md
  │   │   └── TESTING_UPSTREAM_ADOPTION_R1.md
  │   ├── migration
  │   │   ├── acceptance
  │   │   │   └── HARNESS_SECURITY_OWNER_CONSUMER_CUTOVER_ACCEPTANCE_20260921.md
  │   │   └── retirement
  │   │       ├── business-operations-erpnext-r1.md
  │   │       ├── codex-harness-mcp-retirement.md
  │   │       ├── commercial-marketing-externalization-r1.md
  │   │       ├── commercial-practice-externalization.md
  │   │       ├── commercial-strategy-debt-externalization-r1.md
  │   │       ├── harness-standalone-policy.json
  │   │       ├── host-v2-standalone-policy.json
  │   │       ├── media-standalone-policy.json
  │   │       ├── network-v2-standalone-policy.json
  │   │       ├── next-standalone-policy.json
  │   │       ├── runtime-standalone-policy.json
  │   │       ├── workstation-lab-policy.json
  │   │       └── workstation-v2-standalone-policy.json
  │   └── start
  │       ├── agent-first-run.md
  │       ├── human-first-run.md
  │       ├── README.md
  │       └── tasks.md
  ├── domains
  │   ├── capital
  │   │   ├── artifacts
  │   │   │   └── .gitkeep
  │   │   ├── config
  │   │   │   ├── accounting_substrate.json
  │   │   │   ├── binance_usdm_equity_perp_provider.json
  │   │   │   ├── candidate_tool_surface_registry.json
  │   │   │   ├── capability_dependencies.json
  │   │   │   ├── capital_domain_taxonomy.json
  │   │   │   ├── clock_quality_gate.json
  │   │   │   ├── crypto_data_adapters.json
  │   │   │   ├── demo_execution_policy.json
  │   │   │   ├── execution_feasibility.json
  │   │   │   ├── execution_policy.json
  │   │   │   ├── external_candidate_funnel.json
  │   │   │   ├── external_owner_census.json
  │   │   │   ├── fix_order_semantics.json
  │   │   │   ├── historical_validation_data.json
  │   │   │   ├── language_baseline.json
  │   │   │   ├── lean_runtime.json
  │   │   │   ├── legacy_replay_surface_registry.json
  │   │   │   ├── live_test_account_policy.json
  │   │   │   ├── network_v2_public_data.json
  │   │   │   ├── nonlive_credential_provisioning.json
  │   │   │   ├── nonlive_effect_authority.json
  │   │   │   ├── okx_live_provider.json
  │   │   │   ├── portfolio_risk_budget.json
  │   │   │   ├── private_reality_policy.json
  │   │   │   ├── prospective_validation.json
  │   │   │   ├── protocol_identity_migration_v2.json
  │   │   │   ├── quantitative_component_inventory.json
  │   │   │   └── shadow_precommit.json
  │   │   ├── contracts
  │   │   │   ├── legacy_protocol_v1
  │   │   │   │   ├── external-boundary-v1.json
  │   │   │   │   ├── external-write-policy-input-v1.json
  │   │   │   │   ├── nonlive-effect-admission-v1.json
  │   │   │   │   └── portfolio-risk-budget-v1.schema.json
  │   │   │   ├── external-boundary-v2.json
  │   │   │   ├── external-write-policy-input-v2.json
  │   │   │   ├── nonlive-effect-admission-v2.json
  │   │   │   ├── parquet-materialization-readback-v1.json
  │   │   │   ├── portfolio-risk-budget-v2.schema.json
  │   │   │   ├── production-authorization.json
  │   │   │   ├── README.md
  │   │   │   └── websocket-client-mechanics-v1.json
  │   │   ├── data-products
  │   │   │   └── crypto-public-shadow-r2
  │   │   │       ├── acceptance.json
  │   │   │       ├── governance-policy.odrl.jsonld
  │   │   │       ├── odcs.json
  │   │   │       └── odps.json
  │   │   ├── destroyer
  │   │   │   └── false-green-corpus-v0.json
  │   │   ├── docs
  │   │   │   ├── ALGEBRAIC_FINANCE_POLICY_R1.md
  │   │   │   ├── ARCHITECTURE.md
  │   │   │   ├── COMPOSITION_FIRST_2026-09-14.md
  │   │   │   ├── CRYPTO_FIX44_PROJECTION_R4_2026-09-14.md
  │   │   │   ├── FINANCE_DIRECTORY_OWNER_AUDIT_R1.md
  │   │   │   ├── FINANCE_HUMAN_GUIDE_R1.md
  │   │   │   ├── FINANCE_INVESTMENT_FIRST_R1.md
  │   │   │   ├── FINANCE_INVESTMENT_MODE_R2.md
  │   │   │   ├── FINANCE_PAPER_INVESTMENT_R1.md
  │   │   │   ├── FINANCE_R2_RESEARCH_BOUNDARY.md
  │   │   │   ├── MARKET_SENSORS_R1.md
  │   │   │   ├── MULTISTAGE_FINANCE_R1.md
  │   │   │   ├── OKX_DEMO_EXTERNAL_EXECUTION_R1.md
  │   │   │   ├── ORDIVON_CAPITAL_EXTERNAL_OWNER_CENSUS_R1.md
  │   │   │   ├── PAPER_ETF_EOD_SNAPSHOT_R1.md
  │   │   │   ├── PIT_JOINT_FORECAST_R1.md
  │   │   │   ├── PORTFOLIO_RISK_MONITORING_R1.md
  │   │   │   ├── PORTFOLIO_SCENARIO_ANALYSIS_R1.md
  │   │   │   └── UNIT_R_DCA_LONG_HISTORY_R1.md
  │   │   ├── evidence
  │   │   │   ├── acceptance
  │   │   │   │   ├── binance-sndk-usdm-public-canary-r1.json
  │   │   │   │   ├── dependence-model-monitoring-r1.json
  │   │   │   │   ├── dependence-model-oot-validation-r1.json
  │   │   │   │   ├── market-sensors-sndk-canary-r1.json
  │   │   │   │   ├── model-monitoring-lineage-r1.json
  │   │   │   │   ├── portfolio-counterfactuals-p5-p6-r1.json
  │   │   │   │   └── portfolio-risk-observatory-p1-p4-r1.json
  │   │   │   ├── data-products
  │   │   │   │   └── crypto-public-shadow-consumption-r1
  │   │   │   │       ├── decision-outcome-feedback.json
  │   │   │   │       ├── openlineage.json
  │   │   │   │       └── receipt.json
  │   │   │   ├── finance-research
  │   │   │   │   └── spy-shy-forward-20261108
  │   │   │   │       ├── current-assessment.json
  │   │   │   │       ├── frozen-plan.json
  │   │   │   │       ├── README.md
  │   │   │   │       ├── research-plan.json
  │   │   │   │       └── retrospective-result.json
  │   │   │   ├── clock-quality-audit-20260914-postrepair.json
  │   │   │   ├── crypto-fix44-projection-r4-20260914.json
  │   │   │   ├── crypto-public-shadow-r1-20260913.json
  │   │   │   ├── crypto-public-shadow-r2-20260914.json
  │   │   │   ├── crypto-public-shadow-r2-20260921.json
  │   │   │   ├── crypto-shadow-mechanics-r1-20260913.json
  │   │   │   ├── crypto-stream-resilience-r3-20260921.json
  │   │   │   ├── crypto-vpn-public-data-qualification-20260913.json
  │   │   │   ├── full-nonlive-effect-closure-20260914.json
  │   │   │   ├── okx-live-provider-binding-20260914.json
  │   │   │   └── wave-b-m5-status-20260913.json
  │   │   ├── examples
  │   │   │   ├── paper_fixed_mix_etf_20261106.json
  │   │   │   ├── passive_benchmark_first_run_r1.json
  │   │   │   ├── portfolio_scenario_brief_r1.json
  │   │   │   ├── r1_witness_parquet_duckdb.py
  │   │   │   └── strategic_contribution_r1.json
  │   │   ├── fixtures
  │   │   │   └── r5_legacy_bounded
  │   │   │       ├── manifest.json
  │   │   │       ├── market-capital-r26-p01-registry-parcel-authority-20260908.json
  │   │   │       ├── market-capital-r27-p21-effect-reconciliation-final-20260908.json
  │   │   │       └── market-capital-r28-p31-effect-authority-v2-final-20260908.json
  │   │   ├── formal
  │   │   │   ├── AccountingReservationR1.smt2
  │   │   │   ├── AlgebraicCapitalR1.smt2
  │   │   │   ├── BrokerLiquidationCashflowR1.smt2
  │   │   │   ├── MarketsCapturePITR1.smt2
  │   │   │   ├── MultistageOneRCashflowR1.smt2
  │   │   │   ├── paper_cash_settlement_r1.smt2
  │   │   │   ├── paper_settlement_source_contract.py
  │   │   │   ├── PaperCloseAmounts.lean
  │   │   │   ├── PortfolioApportionmentGeneral.lean
  │   │   │   ├── PortfolioContributionR1.smt2
  │   │   │   ├── PortfolioPassiveBenchmarkGeneral.lean
  │   │   │   ├── PortfolioPassiveBenchmarkR1.smt2
  │   │   │   ├── README.md
  │   │   │   ├── RiskExposureBound.lean
  │   │   │   ├── RiskExposureBound.md
  │   │   │   ├── UnitRMarginBoundR1.smt2
  │   │   │   └── UnitRRebalanceConservationR1.smt2
  │   │   ├── infra
  │   │   │   ├── systemd
  │   │   │   │   └── ordivon-wsl-host-clock-sync.service
  │   │   │   └── optional-witness-substrate.compose.yaml
  │   │   ├── planning
  │   │   │   └── lego-plan-r1.json
  │   │   ├── schema
  │   │   │   ├── legacy_protocol_v1
  │   │   │   │   └── private-reality-snapshot-v1.schema.json
  │   │   │   ├── private-reality-snapshot-v2.schema.json
  │   │   │   └── quantitative_component_inventory.schema.json
  │   │   ├── scripts
  │   │   │   ├── capture-binance-usdm-private-r1
  │   │   │   ├── capture-binance-usdm-public-r1
  │   │   │   ├── capture-crypto-public-rest
  │   │   │   ├── check-binance-usdm-equity-perp-preflight
  │   │   │   ├── check-binance-usdm-private-readonly-preflight
  │   │   │   ├── check-capabilities
  │   │   │   ├── check-clock-quality-gate
  │   │   │   ├── check-crypto-data-adapter-policy
  │   │   │   ├── check-demo-execution-preflight
  │   │   │   ├── check-execution-feasibility
  │   │   │   ├── check-execution-policy
  │   │   │   ├── check-language-baseline
  │   │   │   ├── check-live-test-account-policy
  │   │   │   ├── check-network-v2-public-data
  │   │   │   ├── check-nonlive-credential-provisioning
  │   │   │   ├── check-nonlive-effect-authority
  │   │   │   ├── check-okx-live-provider-binding
  │   │   │   ├── check-private-reality-credential-bindings
  │   │   │   ├── check-private-reality-readonly-preflight
  │   │   │   ├── check-provider-registration-handoff
  │   │   │   ├── check-quantitative-component-inventory
  │   │   │   ├── consume_crypto_public_shadow_product_r1.py
  │   │   │   ├── finance_lego.py
  │   │   │   ├── install-nonlive-credential
  │   │   │   ├── persist-model-monitoring-r1
  │   │   │   ├── portfolio_scenario_brief.py
  │   │   │   ├── reconcile-underlying-reopen-r1
  │   │   │   ├── run-canonical-tests
  │   │   │   ├── run-capability-python
  │   │   │   ├── run-capability-rust
  │   │   │   ├── run-capital-trading-fullpath-closure
  │   │   │   ├── run-crypto-fix-projection-r4
  │   │   │   ├── run-crypto-public-shadow-r1
  │   │   │   ├── run-crypto-public-shadow-r2
  │   │   │   ├── run-crypto-public-streaming-r2-candidate
  │   │   │   ├── run-crypto-stream-resilience-r3
  │   │   │   ├── run-crypto-stream-resilience-r3-candidate
  │   │   │   ├── run-crypto-stream-resilience-r3-session
  │   │   │   ├── run-finance-lego
  │   │   │   ├── run-nonlive-capital-effect-matrix
  │   │   │   ├── run-okx-demo-execution
  │   │   │   ├── run-okx-factor-observatory-r1
  │   │   │   ├── run-okx-instrument-sensors-r1
  │   │   │   ├── run-paper-etf-replay-r1
  │   │   │   ├── run-paper-etf-vintage-compare-r1
  │   │   │   ├── run-parquet-duckdb-owner-requalification-r17
  │   │   │   ├── run-portfolio-scenario-brief
  │   │   │   ├── run-strategic-contribution-brief
  │   │   │   ├── run-websockets-owner-requalification-r17
  │   │   │   └── strategic_contribution_brief.py
  │   │   ├── src
  │   │   │   └── ordivon_capital
  │   │   │       ├── accounting
  │   │   │       │   ├── __init__.py
  │   │   │       │   ├── durable.py
  │   │   │       │   ├── paper_close.py
  │   │   │       │   ├── postgres_ledger.py
  │   │   │       │   ├── postgres_paper_close.py
  │   │   │       │   └── substrate.py
  │   │   │       ├── governance
  │   │   │       │   ├── __init__.py
  │   │   │       │   └── policy_decision.py
  │   │   │       ├── markets
  │   │   │       │   ├── __init__.py
  │   │   │       │   ├── binance_usdm_public_capture.py
  │   │   │       │   ├── binance_usdm_reference.py
  │   │   │       │   ├── crypto_public_shadow.py
  │   │   │       │   ├── crypto_public_streaming.py
  │   │   │       │   ├── crypto_stream_health.py
  │   │   │       │   ├── crypto_stream_resilience.py
  │   │   │       │   ├── etf_eod_snapshot.py
  │   │   │       │   ├── historical_close_snapshot.py
  │   │   │       │   ├── market_sensors.py
  │   │   │       │   ├── okx_sensor_capture.py
  │   │   │       │   └── websocket_proxy_lifecycle.py
  │   │   │       ├── portfolio
  │   │   │       │   ├── __init__.py
  │   │   │       │   ├── algebraic_policy.py
  │   │   │       │   ├── information_tree.py
  │   │   │       │   ├── multistage_policy.py
  │   │   │       │   ├── paper_close_performance.py
  │   │   │       │   ├── paper_investment.py
  │   │   │       │   ├── paper_vintage.py
  │   │   │       │   ├── passive_benchmark.py
  │   │   │       │   ├── portfolio_counterfactuals.py
  │   │   │       │   └── strategic_contribution.py
  │   │   │       ├── research
  │   │   │       │   ├── __init__.py
  │   │   │       │   ├── experiment_protocol.py
  │   │   │       │   ├── independent_policy_replay.py
  │   │   │       │   ├── investment_candidate.py
  │   │   │       │   ├── model_monitoring.py
  │   │   │       │   ├── monitoring_persistence.py
  │   │   │       │   ├── monitoring_persistence_cli.py
  │   │   │       │   ├── okx_factor_observer.py
  │   │   │       │   ├── pit_joint_forecast.py
  │   │   │       │   ├── prospective_validation.py
  │   │   │       │   ├── quantitative_inventory_validation.py
  │   │   │       │   ├── standards_inventory.py
  │   │   │       │   └── unit_r_dca.py
  │   │   │       ├── risk
  │   │   │       │   ├── __init__.py
  │   │   │       │   ├── broker_margin.py
  │   │   │       │   ├── dependence_analysis.py
  │   │   │       │   ├── paper_close_risk.py
  │   │   │       │   ├── portfolio_risk.py
  │   │   │       │   ├── risk_budget_validation.py
  │   │   │       │   ├── risk_values.py
  │   │   │       │   ├── tail_report.py
  │   │   │       │   └── tail_risk.py
  │   │   │       ├── trading
  │   │   │       │   ├── __init__.py
  │   │   │       │   ├── binance_usdm_private_capture.py
  │   │   │       │   ├── binance_usdm_provider.py
  │   │   │       │   ├── execution_feasibility.py
  │   │   │       │   ├── execution_reconciliation.py
  │   │   │       │   ├── fix44_projection.py
  │   │   │       │   ├── okx_demo_execution.py
  │   │   │       │   ├── okx_official_cli.py
  │   │   │       │   ├── okx_readonly_client.py
  │   │   │       │   ├── paper_fill_calendar.py
  │   │   │       │   ├── postgres_demo_intent.py
  │   │   │       │   └── private_reality.py
  │   │   │       └── __init__.py
  │   │   ├── tests
  │   │   │   ├── test_accounting_durable.py
  │   │   │   ├── test_accounting_smoke_optimizer_contract.py
  │   │   │   ├── test_accounting_substrate.py
  │   │   │   ├── test_accounting_substrate_type_authority.py
  │   │   │   ├── test_algebraic_policy.py
  │   │   │   ├── test_binance_usdm_private_capture.py
  │   │   │   ├── test_binance_usdm_provider.py
  │   │   │   ├── test_broker_margin_evidence.py
  │   │   │   ├── test_candidate_tool_surface_isolation.py
  │   │   │   ├── test_capability_current_postgres.py
  │   │   │   ├── test_capital_domain_taxonomy.py
  │   │   │   ├── test_clock_quality_gate.py
  │   │   │   ├── test_crypto_data_adapters.py
  │   │   │   ├── test_crypto_execution_lane.py
  │   │   │   ├── test_crypto_fix44_projection.py
  │   │   │   ├── test_crypto_public_shadow.py
  │   │   │   ├── test_crypto_public_streaming.py
  │   │   │   ├── test_crypto_shadow_mechanics.py
  │   │   │   ├── test_crypto_stream_health.py
  │   │   │   ├── test_crypto_stream_resilience_policy.py
  │   │   │   ├── test_crypto_stream_resilience_runner.py
  │   │   │   ├── test_crypto_streaming_runner_policy.py
  │   │   │   ├── test_current_runtime_admission.py
  │   │   │   ├── test_current_source_pointer_integrity.py
  │   │   │   ├── test_data_product_consumption_crypto_public_shadow.py
  │   │   │   ├── test_data_product_crypto_public_shadow.py
  │   │   │   ├── test_demo_execution_preflight.py
  │   │   │   ├── test_duckdb_provenance_identity.py
  │   │   │   ├── test_etf_eod_snapshot.py
  │   │   │   ├── test_execution_feasibility.py
  │   │   │   ├── test_execution_policy.py
  │   │   │   ├── test_execution_reconciliation.py
  │   │   │   ├── test_experiment_protocol.py
  │   │   │   ├── test_external_owner_census.py
  │   │   │   ├── test_factor_lego_consumer_contract.py
  │   │   │   ├── test_finance_agent_role_composition.py
  │   │   │   ├── test_finance_lego_cli.py
  │   │   │   ├── test_finance_real_etf_research_case.py
  │   │   │   ├── test_finance_research_composition.py
  │   │   │   ├── test_fix44_projection.py
  │   │   │   ├── test_independent_policy_replay.py
  │   │   │   ├── test_intermediate_obligations.py
  │   │   │   ├── test_investment_candidate.py
  │   │   │   ├── test_investment_candidate_source_replay.py
  │   │   │   ├── test_jsonschema_owner_requalification.py
  │   │   │   ├── test_legacy_replay_surface_isolation.py
  │   │   │   ├── test_live_test_account_policy.py
  │   │   │   ├── test_live_test_admission.py
  │   │   │   ├── test_live_test_canary_policy.py
  │   │   │   ├── test_market_sensors.py
  │   │   │   ├── test_model_monitoring.py
  │   │   │   ├── test_monitoring_persistence.py
  │   │   │   ├── test_multistage_policy.py
  │   │   │   ├── test_nautilus_candidate.py
  │   │   │   ├── test_network_v2_public_data_binding.py
  │   │   │   ├── test_nonlive_credential_installer.py
  │   │   │   ├── test_nonlive_credential_provisioning.py
  │   │   │   ├── test_nonlive_effect_authority.py
  │   │   │   ├── test_nonlive_effect_qualification.py
  │   │   │   ├── test_nonlive_policy_optimized_contract.py
  │   │   │   ├── test_observability_legacy_retirement.py
  │   │   │   ├── test_okx_demo_execution.py
  │   │   │   ├── test_okx_factor_observer.py
  │   │   │   ├── test_okx_live_provider_binding.py
  │   │   │   ├── test_okx_official_cli.py
  │   │   │   ├── test_okx_readonly_client.py
  │   │   │   ├── test_okx_sensor_capture.py
  │   │   │   ├── test_paper_close.py
  │   │   │   ├── test_paper_close_performance.py
  │   │   │   ├── test_paper_close_risk.py
  │   │   │   ├── test_paper_fill_calendar.py
  │   │   │   ├── test_paper_head_readback.py
  │   │   │   ├── test_paper_investment.py
  │   │   │   ├── test_paper_vintage_comparison.py
  │   │   │   ├── test_parquet_duckdb_owner_requalification.py
  │   │   │   ├── test_passive_benchmark.py
  │   │   │   ├── test_pit_etf_eod_composition.py
  │   │   │   ├── test_pit_joint_forecast.py
  │   │   │   ├── test_portfolio_counterfactuals.py
  │   │   │   ├── test_portfolio_risk.py
  │   │   │   ├── test_portfolio_scenario_brief_consumer.py
  │   │   │   ├── test_postgres_accounting_traces.py
  │   │   │   ├── test_postgres_demo_intent.py
  │   │   │   ├── test_postgres_ledger.py
  │   │   │   ├── test_private_reality_bindings.py
  │   │   │   ├── test_private_reality_normalization.py
  │   │   │   ├── test_private_reality_policy.py
  │   │   │   ├── test_prospective_validation.py
  │   │   │   ├── test_protocol_identity_v2.py
  │   │   │   ├── test_r21_capital_source_responsibilities.py
  │   │   │   ├── test_r5_legacy_differential.py
  │   │   │   ├── test_standalone_source_retirement.py
  │   │   │   ├── test_standards_inventory.py
  │   │   │   ├── test_strategic_contribution.py
  │   │   │   ├── test_terminal_liabilities.py
  │   │   │   ├── test_unit_r_dca.py
  │   │   │   ├── test_verification_boundary.py
  │   │   │   ├── test_wave_b_contract.py
  │   │   │   ├── test_websocket_proxy_lifecycle.py
  │   │   │   └── test_websockets_owner_requalification.py
  │   │   ├── tools
  │   │   │   ├── jsonschema_4_26_0
  │   │   │   │   ├── check-candidate
  │   │   │   │   ├── differential_r18.py
  │   │   │   │   ├── qualification-r18.json
  │   │   │   │   └── run-differential-r18
  │   │   │   ├── legacy_replay
  │   │   │   │   ├── lean_wave_b
  │   │   │   │   │   ├── algorithm
  │   │   │   │   │   │   ├── MarketCapitalValidationAlgorithm.cs
  │   │   │   │   │   │   ├── MarketCapitalValidationAlgorithm.csproj
  │   │   │   │   │   │   └── packages.lock.json
  │   │   │   │   │   ├── check-lean-runtime
  │   │   │   │   │   ├── fetch-nasdaq-wave-b-m3
  │   │   │   │   │   ├── prepare-lean-validation-data
  │   │   │   │   │   ├── probe-prospective-validation-wave-b-m5
  │   │   │   │   │   ├── run-lean-wave-b-m1
  │   │   │   │   │   ├── run-lean-wave-b-m2
  │   │   │   │   │   ├── run-lean-wave-b-m3
  │   │   │   │   │   ├── run-lean-wave-b-m4
  │   │   │   │   │   └── run-shadow-precommit-wave-b-m6
  │   │   │   │   └── README.md
  │   │   │   ├── nautilus_rc4
  │   │   │   │   ├── config
  │   │   │   │   │   ├── crypto_execution_lane.json
  │   │   │   │   │   ├── crypto_shadow_mechanics.json
  │   │   │   │   │   └── nautilus_candidate.json
  │   │   │   │   ├── check-candidate
  │   │   │   │   ├── check-crypto-execution-lane
  │   │   │   │   ├── check-demo-execution-configs
  │   │   │   │   ├── check-okx-read-surface
  │   │   │   │   ├── crypto_lane.py
  │   │   │   │   ├── crypto_shadow_mechanics.py
  │   │   │   │   ├── nautilus_qualification.py
  │   │   │   │   ├── nonlive_effect_matrix.py
  │   │   │   │   ├── nonlive_effect_qualification.py
  │   │   │   │   ├── okx_live_config_probe.py
  │   │   │   │   ├── run-crypto-shadow-mechanics-r1
  │   │   │   │   ├── run-m6-differential
  │   │   │   │   └── run-nonlive-effect-matrix
  │   │   │   ├── okx_official_cli
  │   │   │   │   ├── .gitignore
  │   │   │   │   ├── package.json
  │   │   │   │   └── pnpm-lock.yaml
  │   │   │   ├── opa_1_20_2
  │   │   │   │   ├── market_controls.rego
  │   │   │   │   └── README.md
  │   │   │   ├── qualification
  │   │   │   │   ├── parquet_duckdb_owner_r17.py
  │   │   │   │   └── websockets_owner_r17.py
  │   │   │   ├── quickfixn_1_14_1
  │   │   │   │   ├── fix44-projector
  │   │   │   │   │   ├── MarketCapital.Fix44Projector.csproj
  │   │   │   │   │   ├── packages.lock.json
  │   │   │   │   │   └── Program.cs
  │   │   │   │   └── README.md
  │   │   │   ├── tigerbeetle_0_17_9
  │   │   │   │   ├── ordivon_capital
  │   │   │   │   │   ├── accounting
  │   │   │   │   │   │   ├── __init__.py
  │   │   │   │   │   │   ├── tigerbeetle_durable.py
  │   │   │   │   │   │   └── tigerbeetle_substrate.py
  │   │   │   │   │   └── __init__.py
  │   │   │   │   ├── replay
  │   │   │   │   │   ├── run-tigerbeetle-capital-substrate-smoke-r1
  │   │   │   │   │   ├── run-tigerbeetle-durable-restart-smoke-r32
  │   │   │   │   │   └── run-tigerbeetle-reservation-resolution-smoke-r31
  │   │   │   │   └── tigerbeetle_capital_substrate.json
  │   │   │   └── okx_live_provider_probe.py
  │   │   ├── wave_b
  │   │   │   └── fixtures
  │   │   │       └── wave_a_target_portfolio.json
  │   │   ├── .gitignore
  │   │   ├── .python-version
  │   │   ├── mise.toml
  │   │   ├── pyproject.toml
  │   │   ├── README.md
  │   │   ├── rust-toolchain.toml
  │   │   └── uv.lock
  │   └── game
  │       ├── .ordivon
  │       │   └── project.yaml
  │       ├── docs
  │       │   ├── agent-execution-contract-spec.md
  │       │   ├── agent-execution-implementation-plan.md
  │       │   ├── authority.md
  │       │   ├── factory-pipeline.md
  │       │   ├── room-encounter-playtest-template.csv
  │       │   └── room-encounter-playtest.md
  │       ├── examples
  │       │   ├── beacon-relay
  │       │   │   ├── art
  │       │   │   │   ├── enemyFlyingAlt_1.png
  │       │   │   │   ├── enemyFlyingAlt_1.png.import
  │       │   │   │   ├── enemyFlyingAlt_2.png
  │       │   │   │   ├── enemyFlyingAlt_2.png.import
  │       │   │   │   ├── enemySwimming_1.png
  │       │   │   │   ├── enemySwimming_1.png.import
  │       │   │   │   ├── enemySwimming_2.png
  │       │   │   │   ├── enemySwimming_2.png.import
  │       │   │   │   ├── enemyWalking_1.png
  │       │   │   │   ├── enemyWalking_1.png.import
  │       │   │   │   ├── enemyWalking_2.png
  │       │   │   │   ├── enemyWalking_2.png.import
  │       │   │   │   ├── gameover.wav
  │       │   │   │   ├── gameover.wav.import
  │       │   │   │   ├── House In a Forest Loop.ogg
  │       │   │   │   ├── House In a Forest Loop.ogg.import
  │       │   │   │   ├── playerGrey_up1.png
  │       │   │   │   ├── playerGrey_up1.png.import
  │       │   │   │   ├── playerGrey_up2.png
  │       │   │   │   ├── playerGrey_up2.png.import
  │       │   │   │   ├── playerGrey_walk1.png
  │       │   │   │   ├── playerGrey_walk1.png.import
  │       │   │   │   ├── playerGrey_walk2.png
  │       │   │   │   └── playerGrey_walk2.png.import
  │       │   │   ├── fonts
  │       │   │   │   ├── FONTLOG.txt
  │       │   │   │   ├── LICENSE.txt
  │       │   │   │   ├── Xolonium-Regular.ttf
  │       │   │   │   └── Xolonium-Regular.ttf.import
  │       │   │   ├── screenshots
  │       │   │   │   ├── .gdignore
  │       │   │   │   └── gameplay.png
  │       │   │   ├── .gitignore
  │       │   │   ├── acceptance.gd
  │       │   │   ├── acceptance.gd.uid
  │       │   │   ├── capture.gd
  │       │   │   ├── capture.gd.uid
  │       │   │   ├── CREDITS.txt
  │       │   │   ├── export_presets.cfg
  │       │   │   ├── hud.gd
  │       │   │   ├── hud.gd.uid
  │       │   │   ├── hud.tscn
  │       │   │   ├── icon.webp
  │       │   │   ├── icon.webp.import
  │       │   │   ├── LICENSE
  │       │   │   ├── main.gd
  │       │   │   ├── main.gd.uid
  │       │   │   ├── main.tscn
  │       │   │   ├── mob.gd
  │       │   │   ├── mob.gd.uid
  │       │   │   ├── mob.tscn
  │       │   │   ├── player.gd
  │       │   │   ├── player.gd.uid
  │       │   │   ├── player.tscn
  │       │   │   ├── project.godot
  │       │   │   ├── README.md
  │       │   │   ├── relay_plan.gd
  │       │   │   ├── relay_plan.gd.uid
  │       │   │   ├── relay_plan.tres
  │       │   │   ├── relay_sites.gd
  │       │   │   └── relay_sites.gd.uid
  │       │   ├── kenney-visual-composition
  │       │   │   ├── assets
  │       │   │   │   └── kenney
  │       │   │   │       ├── player_blue_stand.png
  │       │   │   │       ├── player_blue_stand.png.import
  │       │   │   │       ├── player_green_stand.png
  │       │   │   │       └── player_green_stand.png.import
  │       │   │   ├── .gitignore
  │       │   │   ├── acceptance.gd
  │       │   │   ├── acceptance.gd.uid
  │       │   │   ├── alternate_avatar.tscn
  │       │   │   ├── main.tscn
  │       │   │   ├── project.godot
  │       │   │   └── README.md
  │       │   ├── native-composition
  │       │   │   ├── assets
  │       │   │   │   ├── kenney-ui-art
  │       │   │   │   │   └── button_rectangle_depth_border.png
  │       │   │   │   └── kenney-ui-audio
  │       │   │   │       ├── click1.wav
  │       │   │   │       ├── click2.wav
  │       │   │   │       ├── LICENSE.txt
  │       │   │   │       └── README.md
  │       │   │   ├── configs
  │       │   │   │   ├── base.tres
  │       │   │   │   └── player_variant.tres
  │       │   │   ├── assert.gd
  │       │   │   ├── assert_audio.gd
  │       │   │   ├── composition_root.gd
  │       │   │   ├── grid_config.gd
  │       │   │   ├── grid_rules.gd
  │       │   │   ├── grid_state_view.gd
  │       │   │   ├── grid_state_view.tscn
  │       │   │   ├── grid_state_view_variant.tscn
  │       │   │   ├── main.tscn
  │       │   │   ├── movement_audio_feedback.gd
  │       │   │   ├── project.godot
  │       │   │   └── README.md
  │       │   ├── orbit-collector
  │       │   │   ├── src
  │       │   │   │   ├── gameplay.rs
  │       │   │   │   ├── main.rs
  │       │   │   │   └── rules.rs
  │       │   │   ├── Cargo.lock
  │       │   │   ├── Cargo.toml
  │       │   │   └── README.md
  │       │   └── room-encounter
  │       │       ├── addons
  │       │       │   └── dialogue_manager
  │       │       │       ├── assets
  │       │       │       │   ├── cue.svg
  │       │       │       │   ├── cue.svg.import
  │       │       │       │   ├── icon.svg
  │       │       │       │   ├── icon.svg.import
  │       │       │       │   ├── logo.svg
  │       │       │       │   ├── logo.svg.import
  │       │       │       │   ├── region.svg
  │       │       │       │   ├── region.svg.import
  │       │       │       │   ├── resource.svg
  │       │       │       │   ├── resource.svg.import
  │       │       │       │   ├── update.svg
  │       │       │       │   └── update.svg.import
  │       │       │       ├── compiler
  │       │       │       │   ├── compilation.gd
  │       │       │       │   ├── compilation.gd.uid
  │       │       │       │   ├── compiled_line.gd
  │       │       │       │   ├── compiled_line.gd.uid
  │       │       │       │   ├── compiler.gd
  │       │       │       │   ├── compiler.gd.uid
  │       │       │       │   ├── compiler_regex.gd
  │       │       │       │   ├── compiler_regex.gd.uid
  │       │       │       │   ├── compiler_result.gd
  │       │       │       │   ├── compiler_result.gd.uid
  │       │       │       │   ├── expression_parser.gd
  │       │       │       │   ├── expression_parser.gd.uid
  │       │       │       │   ├── resolved_goto_data.gd
  │       │       │       │   ├── resolved_goto_data.gd.uid
  │       │       │       │   ├── resolved_line_data.gd
  │       │       │       │   ├── resolved_line_data.gd.uid
  │       │       │       │   ├── resolved_tag_data.gd
  │       │       │       │   ├── resolved_tag_data.gd.uid
  │       │       │       │   ├── tree_line.gd
  │       │       │       │   └── tree_line.gd.uid
  │       │       │       ├── components
  │       │       │       │   ├── cue_editor_property
  │       │       │       │   │   ├── editor_property.gd
  │       │       │       │   │   ├── editor_property.gd.uid
  │       │       │       │   │   ├── editor_property_control.gd
  │       │       │       │   │   ├── editor_property_control.gd.uid
  │       │       │       │   │   └── editor_property_control.tscn
  │       │       │       │   ├── dialogue_editor_property
  │       │       │       │   │   ├── editor_property.gd
  │       │       │       │   │   ├── editor_property.gd.uid
  │       │       │       │   │   ├── editor_property_control.gd
  │       │       │       │   │   ├── editor_property_control.gd.uid
  │       │       │       │   │   ├── editor_property_control.tscn
  │       │       │       │   │   ├── resource_button.gd
  │       │       │       │   │   ├── resource_button.gd.uid
  │       │       │       │   │   └── resource_button.tscn
  │       │       │       │   ├── blank_slate.gd
  │       │       │       │   ├── blank_slate.gd.uid
  │       │       │       │   ├── blank_slate.tscn
  │       │       │       │   ├── code_edit.gd
  │       │       │       │   ├── code_edit.gd.uid
  │       │       │       │   ├── code_edit.tscn
  │       │       │       │   ├── code_edit_syntax_highlighter.gd
  │       │       │       │   ├── code_edit_syntax_highlighter.gd.uid
  │       │       │       │   ├── cue_list.gd
  │       │       │       │   ├── cue_list.gd.uid
  │       │       │       │   ├── cue_list.tscn
  │       │       │       │   ├── download_update_panel.gd
  │       │       │       │   ├── download_update_panel.gd.uid
  │       │       │       │   ├── download_update_panel.tscn
  │       │       │       │   ├── errors_panel.gd
  │       │       │       │   ├── errors_panel.gd.uid
  │       │       │       │   ├── errors_panel.tscn
  │       │       │       │   ├── export_to_csv_dialog.gd
  │       │       │       │   ├── export_to_csv_dialog.gd.uid
  │       │       │       │   ├── export_to_csv_dialog.tscn
  │       │       │       │   ├── files_list.gd
  │       │       │       │   ├── files_list.gd.uid
  │       │       │       │   ├── files_list.tscn
  │       │       │       │   ├── preview_generator.gd
  │       │       │       │   ├── preview_generator.gd.uid
  │       │       │       │   ├── search_and_replace.gd
  │       │       │       │   ├── search_and_replace.gd.uid
  │       │       │       │   ├── search_and_replace.tscn
  │       │       │       │   ├── update_button.gd
  │       │       │       │   ├── update_button.gd.uid
  │       │       │       │   └── update_button.tscn
  │       │       │       ├── example_balloon
  │       │       │       │   ├── example_balloon.gd
  │       │       │       │   ├── example_balloon.gd.uid
  │       │       │       │   ├── example_balloon.tscn
  │       │       │       │   ├── ExampleBalloon.cs
  │       │       │       │   ├── ExampleBalloon.cs.uid
  │       │       │       │   ├── ExampleBalloon.tscn
  │       │       │       │   ├── small_example_balloon.tscn
  │       │       │       │   └── SmallExampleBalloon.tscn
  │       │       │       ├── l10n
  │       │       │       │   ├── en.po
  │       │       │       │   ├── es.po
  │       │       │       │   ├── translations.pot
  │       │       │       │   ├── uk.po
  │       │       │       │   ├── zh.po
  │       │       │       │   └── zh_TW.po
  │       │       │       ├── nodes
  │       │       │       │   ├── actionable
  │       │       │       │   │   ├── dialogue_actionable_2d.gd
  │       │       │       │   │   ├── dialogue_actionable_2d.gd.uid
  │       │       │       │   │   ├── dialogue_actionable_2d.svg
  │       │       │       │   │   ├── dialogue_actionable_2d.svg.import
  │       │       │       │   │   ├── dialogue_actionable_3d.gd
  │       │       │       │   │   ├── dialogue_actionable_3d.gd.uid
  │       │       │       │   │   ├── dialogue_actionable_3d.svg
  │       │       │       │   │   ├── dialogue_actionable_3d.svg.import
  │       │       │       │   │   ├── DialogueActionable2D.cs
  │       │       │       │   │   ├── DialogueActionable2D.cs.uid
  │       │       │       │   │   ├── DialogueActionable3D.cs
  │       │       │       │   │   └── DialogueActionable3D.cs.uid
  │       │       │       │   ├── context
  │       │       │       │   │   ├── dialogue_state_context.gd
  │       │       │       │   │   ├── dialogue_state_context.gd.uid
  │       │       │       │   │   ├── dialogue_state_context.svg
  │       │       │       │   │   ├── dialogue_state_context.svg.import
  │       │       │       │   │   ├── DialogueStateContext.cs
  │       │       │       │   │   └── DialogueStateContext.cs.uid
  │       │       │       │   ├── dialogue_label
  │       │       │       │   │   ├── dialogue_label.gd
  │       │       │       │   │   ├── dialogue_label.gd.uid
  │       │       │       │   │   ├── dialogue_label.svg
  │       │       │       │   │   ├── dialogue_label.svg.import
  │       │       │       │   │   ├── dialogue_label.tscn
  │       │       │       │   │   ├── DialogueLabel.cs
  │       │       │       │   │   ├── DialogueLabel.cs.uid
  │       │       │       │   │   └── DialogueLabel.tscn
  │       │       │       │   ├── marker
  │       │       │       │   │   ├── dialogue_marker_2d.gd
  │       │       │       │   │   ├── dialogue_marker_2d.gd.uid
  │       │       │       │   │   ├── dialogue_marker_2d.svg
  │       │       │       │   │   ├── dialogue_marker_2d.svg.import
  │       │       │       │   │   ├── dialogue_marker_3d.gd
  │       │       │       │   │   ├── dialogue_marker_3d.gd.uid
  │       │       │       │   │   ├── dialogue_marker_3d.svg
  │       │       │       │   │   ├── dialogue_marker_3d.svg.import
  │       │       │       │   │   ├── DialogueMarker2D.cs
  │       │       │       │   │   ├── DialogueMarker2D.cs.uid
  │       │       │       │   │   ├── DialogueMarker3D.cs
  │       │       │       │   │   └── DialogueMarker3D.cs.uid
  │       │       │       │   └── responses_menu
  │       │       │       │       ├── dialogue_responses_menu.gd
  │       │       │       │       ├── dialogue_responses_menu.gd.uid
  │       │       │       │       ├── dialogue_responses_menu.svg
  │       │       │       │       ├── dialogue_responses_menu.svg.import
  │       │       │       │       ├── DialogueResponsesMenu.cs
  │       │       │       │       └── DialogueResponsesMenu.cs.uid
  │       │       │       ├── utilities
  │       │       │       │   ├── builtins.gd
  │       │       │       │   ├── builtins.gd.uid
  │       │       │       │   ├── dialogue_cache.gd
  │       │       │       │   ├── dialogue_cache.gd.uid
  │       │       │       │   ├── error.gd
  │       │       │       │   ├── error.gd.uid
  │       │       │       │   ├── theme_values.gd
  │       │       │       │   ├── theme_values.gd.uid
  │       │       │       │   ├── translations.gd
  │       │       │       │   ├── translations.gd.uid
  │       │       │       │   ├── waiter.gd
  │       │       │       │   └── waiter.gd.uid
  │       │       │       ├── views
  │       │       │       │   ├── debugger_view.gd
  │       │       │       │   ├── debugger_view.gd.uid
  │       │       │       │   ├── debugger_view.tscn
  │       │       │       │   ├── find_in_dialogue_view.gd
  │       │       │       │   ├── find_in_dialogue_view.gd.uid
  │       │       │       │   ├── find_in_dialogue_view.tscn
  │       │       │       │   ├── find_in_dialogue_view_result_template.tscn
  │       │       │       │   ├── main_view.gd
  │       │       │       │   ├── main_view.gd.uid
  │       │       │       │   └── main_view.tscn
  │       │       │       ├── constants.gd
  │       │       │       ├── constants.gd.uid
  │       │       │       ├── debugger_plugin.gd
  │       │       │       ├── debugger_plugin.gd.uid
  │       │       │       ├── dialogue_line.gd
  │       │       │       ├── dialogue_line.gd.uid
  │       │       │       ├── dialogue_manager.gd
  │       │       │       ├── dialogue_manager.gd.uid
  │       │       │       ├── dialogue_processor.gd
  │       │       │       ├── dialogue_processor.gd.uid
  │       │       │       ├── dialogue_resource.gd
  │       │       │       ├── dialogue_resource.gd.uid
  │       │       │       ├── dialogue_response.gd
  │       │       │       ├── dialogue_response.gd.uid
  │       │       │       ├── DialogueManager.cs
  │       │       │       ├── DialogueManager.cs.uid
  │       │       │       ├── editor_translation_parser_plugin.gd
  │       │       │       ├── editor_translation_parser_plugin.gd.uid
  │       │       │       ├── export_plugin.gd
  │       │       │       ├── export_plugin.gd.uid
  │       │       │       ├── import_plugin.gd
  │       │       │       ├── import_plugin.gd.uid
  │       │       │       ├── inspector_plugin.gd
  │       │       │       ├── inspector_plugin.gd.uid
  │       │       │       ├── LICENSE
  │       │       │       ├── plugin.cfg
  │       │       │       ├── plugin.cfg.uid
  │       │       │       ├── plugin.gd
  │       │       │       ├── plugin.gd.uid
  │       │       │       ├── settings.gd
  │       │       │       ├── settings.gd.uid
  │       │       │       ├── test_scene.gd
  │       │       │       ├── test_scene.gd.uid
  │       │       │       └── test_scene.tscn
  │       │       ├── assets
  │       │       │   ├── click1.wav
  │       │       │   ├── click1.wav.import
  │       │       │   ├── click2.wav
  │       │       │   ├── click2.wav.import
  │       │       │   ├── LICENSE.txt
  │       │       │   └── README.md
  │       │       ├── configs
  │       │       │   ├── default.tres
  │       │       │   ├── tactical_trial.tres
  │       │       │   └── variant.tres
  │       │       ├── narrative
  │       │       │   ├── acceptance.gd
  │       │       │   ├── acceptance.gd.uid
  │       │       │   ├── encounter_dialogue.gd
  │       │       │   ├── encounter_dialogue.gd.uid
  │       │       │   ├── encounter_dialogue.tscn
  │       │       │   ├── gate.dialogue
  │       │       │   ├── gate.dialogue.import
  │       │       │   ├── gate_state.gd
  │       │       │   └── gate_state.gd.uid
  │       │       ├── .gitignore
  │       │       ├── agent_episode.gd
  │       │       ├── agent_episode.gd.uid
  │       │       ├── agent_episode_acceptance.py
  │       │       ├── assert.gd
  │       │       ├── assert.gd.uid
  │       │       ├── assert_process_restart.gd
  │       │       ├── assert_process_restart.gd.uid
  │       │       ├── encounter_audio_feedback.gd
  │       │       ├── encounter_audio_feedback.gd.uid
  │       │       ├── encounter_root.gd
  │       │       ├── encounter_root.gd.uid
  │       │       ├── encounter_rules.gd
  │       │       ├── encounter_rules.gd.uid
  │       │       ├── encounter_save_slot.gd
  │       │       ├── encounter_save_slot.gd.uid
  │       │       ├── encounter_tuning.gd
  │       │       ├── encounter_tuning.gd.uid
  │       │       ├── encounter_view.gd
  │       │       ├── encounter_view.gd.uid
  │       │       ├── encounter_view.tscn
  │       │       ├── encounter_view_variant.tscn
  │       │       ├── export_presets.cfg
  │       │       ├── main.tscn
  │       │       ├── native_scene_acceptance.py
  │       │       ├── project.godot
  │       │       ├── README.md
  │       │       ├── room_theme.tres
  │       │       ├── visual_capture.gd
  │       │       └── visual_capture.gd.uid
  │       ├── formal
  │       │   ├── README.md
  │       │   ├── verify_orbit_rules.py
  │       │   └── verify_room_arithmetic.py
  │       ├── knowledge
  │       │   ├── game_counterexample_synthesis_r1.json
  │       │   ├── game_design_counterexample_memory_r1.json
  │       │   ├── game_external_knowledge_base_r1.json
  │       │   ├── game_external_skill_watchlist_r1.json
  │       │   ├── game_mechanism_experience_library_r1.json
  │       │   ├── game_mechanism_relationship_spec_r1.json
  │       │   └── game_teardown_queue_r1.json
  │       ├── planning
  │       │   └── lego-plan-r1.json
  │       ├── research
  │       │   └── autonomous-interest-r7
  │       │       ├── build_manifest_reference.py
  │       │       ├── evaluator_reference.py
  │       │       ├── protocol_selftest.py
  │       │       ├── renderer_reference.py
  │       │       ├── selection_reference.py
  │       │       ├── selftest_model.json
  │       │       └── study_runner_reference.py
  │       ├── scripts
  │       │   ├── cli-argument.ts
  │       │   ├── counterexample-synthesis-query.ts
  │       │   ├── design-counterexample-query.ts
  │       │   ├── external-knowledge-query.ts
  │       │   ├── mechanism-experience-query.ts
  │       │   ├── mechanism-relationship-query.ts
  │       │   ├── package_orbit_linux.sh
  │       │   └── test_orbit_package_contract.py
  │       ├── src
  │       │   ├── counterexample-projection.ts
  │       │   ├── knowledge-file.ts
  │       │   ├── mechanism-relationship-graph.ts
  │       │   └── query-input.ts
  │       ├── test
  │       │   ├── game-cli-argument.test.ts
  │       │   ├── game-counterexample-projection.test.ts
  │       │   ├── game-design-counterexample-memory.test.ts
  │       │   ├── game-external-knowledge-base.test.ts
  │       │   ├── game-external-knowledge-query.test.ts
  │       │   ├── game-lego-catalog.test.ts
  │       │   ├── game-mechanism-experience-library.test.ts
  │       │   ├── game-mechanism-relationship-graph.test.ts
  │       │   └── game-query-input.test.ts
  │       ├── .gitignore
  │       ├── AGENTS.md
  │       ├── LICENSE
  │       ├── mise.toml
  │       ├── package.json
  │       ├── pnpm-lock.yaml
  │       ├── README.md
  │       └── tsconfig.json
  ├── extensions
  │   ├── chatgpt-skills-mcp
  │   │   ├── config
  │   │   │   ├── skills-mcp-requirements.txt
  │   │   │   └── skills-mcp.example.json
  │   │   ├── docs
  │   │   │   ├── chatgpt-skills-mcp-registration.md
  │   │   │   ├── SKILL_MCP_STANDARDS_ALIGNMENT.md
  │   │   │   └── skills-standards-alignment.md
  │   │   ├── planning
  │   │   │   └── lego-plan-r1.json
  │   │   ├── plugins
  │   │   │   └── ordivon-skills-bridge
  │   │   │       ├── mcp.json
  │   │   │       └── plugin.json
  │   │   ├── scripts
  │   │   │   ├── cloudflare_skill_route.py
  │   │   │   ├── skills_mcp.py
  │   │   │   └── skills_mcp_consumer_readiness.py
  │   │   ├── src
  │   │   │   └── ordivon_skills
  │   │   │       ├── __init__.py
  │   │   │       ├── catalog.py
  │   │   │       ├── config.py
  │   │   │       ├── eligibility.py
  │   │   │       ├── http_auth.py
  │   │   │       ├── model.py
  │   │   │       ├── parser.py
  │   │   │       ├── scanner.py
  │   │   │       └── sep2640.py
  │   │   ├── systemd
  │   │   │   └── ordivon-skills-mcp.service
  │   │   ├── tests
  │   │   │   ├── fixtures
  │   │   │   │   └── agent-plugins-1.0.0
  │   │   │   │       ├── mcp.schema.json
  │   │   │   │       ├── plugin.schema.json
  │   │   │   │       └── PROVENANCE.json
  │   │   │   ├── test_agent_plugins_conformance.py
  │   │   │   ├── test_method_router_skill.py
  │   │   │   ├── test_native_thinking_skill_discovery.py
  │   │   │   ├── test_owner_boundary.py
  │   │   │   ├── test_recursive_lego_math_discovery.py
  │   │   │   ├── test_skill_catalog_r2.py
  │   │   │   ├── test_skills_mcp_oauth.py
  │   │   │   ├── test_skills_mcp_r2.py
  │   │   │   ├── test_skills_mcp_r3.py
  │   │   │   ├── test_skills_sep2640.py
  │   │   │   ├── test_source_config_single_valued_r21.py
  │   │   │   ├── test_source_enabled_boolean_r21.py
  │   │   │   ├── test_source_scope_policy_r21.py
  │   │   │   ├── test_task_space_obligation_handoff.py
  │   │   │   ├── test_task_space_reentry.py
  │   │   │   └── test_task_space_reentry_adversarial_r1.py
  │   │   ├── .python-version
  │   │   ├── mise.toml
  │   │   ├── pyproject.toml
  │   │   ├── README.md
  │   │   └── uv.lock
  │   └── ordivon-control-plane
  │       ├── mcp.json
  │       └── plugin.json
  ├── packages
  │   ├── composition
  │   │   ├── docs
  │   │   │   ├── COGNITIVE_CIRCUIT_R1.md
  │   │   │   ├── FINANCE_CONTRACTUAL_EXECUTION_SPEC_R1.md
  │   │   │   ├── IDENTITY_TOKEN_GRAMMAR_20261031.md
  │   │   │   ├── INTERFACE_CONTRACT_EVOLUTION_R2.md
  │   │   │   ├── META_IMPROVEMENT_MEASUREMENT_R1.md
  │   │   │   ├── SUCCESSOR_CONTRACT_R1.md
  │   │   │   └── VERIFICATION_OBLIGATION_R1.md
  │   │   ├── formal
  │   │   │   ├── EffectReplayFence.cfg
  │   │   │   ├── EffectReplayFence.ReconciliationIsUnreachable.cfg
  │   │   │   ├── EffectReplayFence.TerminalCommittedWithoutEffectIsUnreachable.cfg
  │   │   │   ├── EffectReplayFence.tla
  │   │   │   ├── EffectReplayFence.UnindexedUncertaintyIsUnreachable.cfg
  │   │   │   ├── Lego21OwnerBoundary.cfg
  │   │   │   ├── Lego21OwnerBoundary.direct-egress.cfg
  │   │   │   ├── Lego21OwnerBoundary.direct-local.cfg
  │   │   │   ├── Lego21OwnerBoundary.foreign-evidence-probe.cfg
  │   │   │   ├── Lego21OwnerBoundary.foreign-receipt-probe.cfg
  │   │   │   ├── Lego21OwnerBoundary.harness-local.cfg
  │   │   │   ├── Lego21OwnerBoundary.readiness-probe.cfg
  │   │   │   ├── Lego21OwnerBoundary.receipt-probe.cfg
  │   │   │   ├── Lego21OwnerBoundary.sourcecut-probe.cfg
  │   │   │   ├── Lego21OwnerBoundary.tla
  │   │   │   └── README.md
  │   │   ├── planning
  │   │   │   └── lego-plan-r1.json
  │   │   ├── policies
  │   │   │   └── research-adopted-r1
  │   │   │       ├── data.json
  │   │   │       ├── policy.rego
  │   │   │       ├── policy_test.rego
  │   │   │       └── README.md
  │   │   ├── profiles
  │   │   │   └── admission
  │   │   │       ├── admission-interactive-circuit-r1.json
  │   │   │       └── admission-workload-circuit-r1.json
  │   │   ├── scripts
  │   │   │   ├── check_standard_native_enterprise_r2.py
  │   │   │   ├── pacti_timeout_model.py
  │   │   │   ├── pacti_timeout_obligation_r1.py
  │   │   │   └── verify_effect_replay_formal.sh
  │   │   ├── src
  │   │   │   └── ordivon_composition
  │   │   │       ├── evidence
  │   │   │       │   └── standard-native-enterprise-r2-dogfood-20260914.json
  │   │   │       ├── schemas
  │   │   │       │   ├── cognitive-circuit-manifest-v1.schema.json
  │   │   │       │   ├── composition-gate-result-v1.schema.json
  │   │   │       │   ├── cross-domain-verification-r3-binding.schema.json
  │   │   │       │   ├── experimental-episode-binding-r1.schema.json
  │   │   │       │   ├── interface-compatibility-result-v1.schema.json
  │   │   │       │   ├── interface-contract-expectation-v1.schema.json
  │   │   │       │   ├── interface-contract-observation-v1.schema.json
  │   │   │       │   ├── standard-native-profile-projection-v1.schema.json
  │   │   │       │   ├── successor-contract-v1.schema.json
  │   │   │       │   ├── successor-gate-result-v1.schema.json
  │   │   │       │   ├── verification-obligation-set-v1.schema.json
  │   │   │       │   ├── verifier-binding-set-v1.schema.json
  │   │   │       │   └── verifier-resolution-v1.schema.json
  │   │   │       ├── __init__.py
  │   │   │       ├── cognitive_circuit_r1.py
  │   │   │       ├── cross_domain_binding_r3.py
  │   │   │       ├── effect_reconciliation_r1.py
  │   │   │       ├── interface_contract_r2.py
  │   │   │       ├── research_artifact_gate_r3.py
  │   │   │       ├── successor_contract_r1.py
  │   │   │       ├── verification_impact.py
  │   │   │       ├── verification_obligation_r1.py
  │   │   │       └── web_security_gate_r3.py
  │   │   ├── tests
  │   │   │   ├── fixtures
  │   │   │   │   ├── pacti
  │   │   │   │   │   ├── pacti-timeout-obligation-r2.json
  │   │   │   │   │   └── pacti-timeout-obligation-spec-r2.json
  │   │   │   │   ├── cross-domain-verification-r3-bindings.json
  │   │   │   │   └── gateway-client-interface-contract-r2-dogfood.json
  │   │   │   ├── test_admission_fabric_r1.py
  │   │   │   ├── test_cognitive_circuit_r1.py
  │   │   │   ├── test_cross_domain_verification_r3.py
  │   │   │   ├── test_effect_reconciliation_r1.py
  │   │   │   ├── test_finance_contractual_execution_consumer.py
  │   │   │   ├── test_finance_research_frozen_consumer.py
  │   │   │   ├── test_gate_evidence_reference_law.py
  │   │   │   ├── test_graph_operator_properties.py
  │   │   │   ├── test_identity_token_grammar.py
  │   │   │   ├── test_interface_contract_core.py
  │   │   │   ├── test_interface_contract_r2.py
  │   │   │   ├── test_native_formal_model_gate.py
  │   │   │   ├── test_nonfinite_source_numeric_r21.py
  │   │   │   ├── test_owner_python_binding.py
  │   │   │   ├── test_pacti_timeout_obligation_r1.py
  │   │   │   ├── test_research_adopted_policy.py
  │   │   │   ├── test_source_json_uniqueness.py
  │   │   │   ├── test_successor_contract_r1.py
  │   │   │   └── test_verification_obligation_r1.py
  │   │   ├── AGENTS.md
  │   │   ├── mise.toml
  │   │   ├── pyproject.toml
  │   │   ├── README.md
  │   │   └── uv.lock
  │   └── data
  │       ├── docs
  │       │   ├── AGENT.md
  │       │   ├── FORMAL_VERIFICATION.md
  │       │   ├── HUMAN.md
  │       │   └── LEGO_CENSUS.md
  │       ├── formal
  │       │   ├── DataMultiVersion.lean
  │       │   ├── DataProduct.lean
  │       │   └── DataPublication.lean
  │       ├── scripts
  │       │   ├── inspect_federation.py
  │       │   └── project_owned_products.py
  │       ├── src
  │       │   └── ordivon_data
  │       │       ├── __init__.py
  │       │       ├── catalog.py
  │       │       ├── local_evidence.py
  │       │       ├── odps_projection.py
  │       │       └── verification.py
  │       ├── tests
  │       │   ├── test_catalog.py
  │       │   └── test_odps_projection.py
  │       ├── AGENTS.md
  │       ├── mise.toml
  │       └── README.md
  ├── platform
  │   ├── network
  │   │   ├── .github
  │   │   │   └── actionlint.yaml
  │   │   ├── acceptance
  │   │   │   ├── connectivity
  │   │   │   │   ├── direct-chain.sh
  │   │   │   │   └── family-fallback.sh
  │   │   │   ├── dns
  │   │   │   │   └── upstream-resilience.sh
  │   │   │   ├── egress
  │   │   │   │   ├── finance-lane-witness.py
  │   │   │   │   ├── finance-public-data.py
  │   │   │   │   └── live-carrier-witness.py
  │   │   │   ├── fault
  │   │   │   │   └── l4-toxiproxy.sh
  │   │   │   ├── full-ip
  │   │   │   │   └── tun-quic.sh
  │   │   │   ├── lifecycle
  │   │   │   │   ├── cold-start.sh
  │   │   │   │   └── process-recovery.sh
  │   │   │   ├── observability
  │   │   │   │   ├── blackbox-prometheus.sh
  │   │   │   │   ├── live-prometheus-ready.sh
  │   │   │   │   └── prometheus-singbox-sample.sh
  │   │   │   ├── protocol
  │   │   │   │   └── divergence.sh
  │   │   │   ├── topology
  │   │   │   │   └── netns.sh
  │   │   │   └── README.md
  │   │   ├── capabilities
  │   │   │   ├── failover
  │   │   │   │   ├── acceptance
  │   │   │   │   │   └── priority-failover-smoke.sh
  │   │   │   │   └── Taskfile.yml
  │   │   │   ├── wireguard
  │   │   │   │   ├── acceptance
  │   │   │   │   │   └── userspace-lifecycle.sh
  │   │   │   │   ├── external
  │   │   │   │   │   └── wireguard-go.lock
  │   │   │   │   └── Taskfile.yml
  │   │   │   └── README.md
  │   │   ├── config
  │   │   │   ├── blackbox
  │   │   │   │   └── blackbox.yml
  │   │   │   ├── prometheus
  │   │   │   │   ├── consumers
  │   │   │   │   │   ├── claude.yml
  │   │   │   │   │   ├── codex.yml
  │   │   │   │   │   ├── finance.yml
  │   │   │   │   │   ├── model-provider.yml
  │   │   │   │   │   └── supply-chain.yml
  │   │   │   │   ├── consumer.rules.yml
  │   │   │   │   └── prometheus.yml
  │   │   │   ├── sing-box
  │   │   │   │   └── direct.json
  │   │   │   └── sysctl
  │   │   │       └── 90-network-v2-forwarding.conf
  │   │   ├── consumers
  │   │   │   ├── browserless
  │   │   │   │   ├── acceptance
  │   │   │   │   │   ├── production-path.sh
  │   │   │   │   │   └── serial-browserless.sh
  │   │   │   │   ├── config
  │   │   │   │   │   └── provider-carrier.json
  │   │   │   │   ├── systemd
  │   │   │   │   │   ├── network-v2-browserless-dns.service
  │   │   │   │   │   ├── network-v2-browserless-legacy-provider.target
  │   │   │   │   │   ├── network-v2-browserless-provider-carrier.service
  │   │   │   │   │   └── network-v2-browserless-wireguard.service
  │   │   │   │   ├── production-cutover.sh
  │   │   │   │   ├── provider-switch.sh
  │   │   │   │   ├── README.md
  │   │   │   │   └── Taskfile.yml
  │   │   │   ├── chat-ingress
  │   │   │   │   ├── config
  │   │   │   │   │   ├── egress.json
  │   │   │   │   │   └── sing-box.json
  │   │   │   │   ├── systemd
  │   │   │   │   │   ├── network-v2-chat-ingress-proxy.service
  │   │   │   │   │   ├── network-v2-chat-ingress-relay.service
  │   │   │   │   │   └── network-v2-chat-ingress.target
  │   │   │   │   ├── ready.sh
  │   │   │   │   └── Taskfile.yml
  │   │   │   ├── claude
  │   │   │   │   ├── config
  │   │   │   │   │   ├── authority.json
  │   │   │   │   │   └── sing-box.json
  │   │   │   │   ├── systemd
  │   │   │   │   │   ├── network-v2-claude-client-bridge.service
  │   │   │   │   │   ├── network-v2-claude-client-netns.service
  │   │   │   │   │   ├── network-v2-claude-client.target
  │   │   │   │   │   ├── network-v2-claude-proxy.service
  │   │   │   │   │   ├── network-v2-claude-relay.service
  │   │   │   │   │   └── network-v2-claude.target
  │   │   │   │   ├── README.md
  │   │   │   │   ├── ready.sh
  │   │   │   │   └── Taskfile.yml
  │   │   │   ├── codex
  │   │   │   │   ├── config
  │   │   │   │   │   └── sing-box.json
  │   │   │   │   ├── systemd
  │   │   │   │   │   ├── network-v2-codex-proxy.service
  │   │   │   │   │   ├── network-v2-codex-relay.service
  │   │   │   │   │   └── network-v2-codex.target
  │   │   │   │   ├── PACKAGE_TOKEN_EVIDENCE.md
  │   │   │   │   ├── PROGRAM_COVERAGE.md
  │   │   │   │   ├── README.md
  │   │   │   │   ├── ready.sh
  │   │   │   │   ├── Taskfile.yml
  │   │   │   │   ├── windows_exit_differential.py
  │   │   │   │   ├── windows_package_program_coverage.py
  │   │   │   │   ├── windows_package_token_evidence.py
  │   │   │   │   ├── windows_process_egress.py
  │   │   │   │   └── windows_wfp_evidence.py
  │   │   │   ├── developer-egress
  │   │   │   │   ├── github_release_mise.py
  │   │   │   │   ├── profile.sh
  │   │   │   │   └── README.md
  │   │   │   ├── discord
  │   │   │   │   ├── config
  │   │   │   │   │   ├── authority.json
  │   │   │   │   │   └── egress.json
  │   │   │   │   ├── systemd
  │   │   │   │   │   ├── network-v2-discord-egress.service
  │   │   │   │   │   └── network-v2-discord.target
  │   │   │   │   ├── README.md
  │   │   │   │   ├── ready.sh
  │   │   │   │   └── Taskfile.yml
  │   │   │   ├── finance
  │   │   │   │   ├── config
  │   │   │   │   │   ├── binance-spot-public-rest-authority.json
  │   │   │   │   │   ├── binance-spot-public-ws-authority.json
  │   │   │   │   │   ├── binance-usdm-rest-authority.json
  │   │   │   │   │   ├── binance-usdm-ws-authority.json
  │   │   │   │   │   ├── binance-wallet-rest-authority.json
  │   │   │   │   │   ├── egress.json
  │   │   │   │   │   ├── fred-public-csv-authority.json
  │   │   │   │   │   ├── okx-rest-authority.json
  │   │   │   │   │   ├── okx-ws-authority.json
  │   │   │   │   │   └── us-treasury-rest-authority.json
  │   │   │   │   ├── systemd
  │   │   │   │   │   ├── network-v2-finance-egress.service
  │   │   │   │   │   └── network-v2-finance.target
  │   │   │   │   ├── README.md
  │   │   │   │   ├── ready.sh
  │   │   │   │   └── Taskfile.yml
  │   │   │   ├── mobile-tailnet-exit
  │   │   │   │   ├── systemd
  │   │   │   │   │   └── network-v2-mobile-tailnet-exit.service
  │   │   │   │   ├── README.md
  │   │   │   │   ├── ready.py
  │   │   │   │   ├── run.sh
  │   │   │   │   └── Taskfile.yml
  │   │   │   ├── model-provider
  │   │   │   │   ├── config
  │   │   │   │   │   ├── authority.json
  │   │   │   │   │   └── egress.json
  │   │   │   │   ├── systemd
  │   │   │   │   │   ├── network-v2-model-provider-egress.service
  │   │   │   │   │   └── network-v2-model-provider.target
  │   │   │   │   ├── README.md
  │   │   │   │   ├── ready.sh
  │   │   │   │   └── Taskfile.yml
  │   │   │   ├── supply-chain
  │   │   │   │   ├── acceptance
  │   │   │   │   │   └── docker-rebind-smoke.sh
  │   │   │   │   ├── config
  │   │   │   │   │   ├── authority.json
  │   │   │   │   │   └── egress.json
  │   │   │   │   ├── systemd
  │   │   │   │   │   ├── docker.service.d
  │   │   │   │   │   │   └── ordivon-network-v2-supply-chain-proxy.conf
  │   │   │   │   │   ├── network-v2-supply-chain-egress.service
  │   │   │   │   │   └── network-v2-supply-chain.target
  │   │   │   │   ├── README.md
  │   │   │   │   ├── ready.sh
  │   │   │   │   └── Taskfile.yml
  │   │   │   ├── windows-real-chrome
  │   │   │   │   ├── config
  │   │   │   │   │   ├── authority.json
  │   │   │   │   │   └── sing-box.json
  │   │   │   │   ├── systemd
  │   │   │   │   │   ├── network-v2-windows-real-chrome-proxy.service
  │   │   │   │   │   ├── network-v2-windows-real-chrome-relay.service
  │   │   │   │   │   └── network-v2-windows-real-chrome.target
  │   │   │   │   ├── README.md
  │   │   │   │   ├── ready.sh
  │   │   │   │   └── Taskfile.yml
  │   │   │   ├── x-reality
  │   │   │   │   ├── config
  │   │   │   │   │   ├── authority.json
  │   │   │   │   │   └── egress.json
  │   │   │   │   ├── systemd
  │   │   │   │   │   ├── network-v2-x-reality-egress.service
  │   │   │   │   │   └── network-v2-x-reality.target
  │   │   │   │   ├── README.md
  │   │   │   │   ├── ready.sh
  │   │   │   │   └── Taskfile.yml
  │   │   │   └── README.md
  │   │   ├── docs
  │   │   │   ├── ACCEPTANCE_MATRIX.md
  │   │   │   ├── AGENT_GUIDE.md
  │   │   │   ├── ARCHITECTURE.md
  │   │   │   ├── DECISION_MATRIX.md
  │   │   │   └── HUMAN_GUIDE.md
  │   │   ├── evidence
  │   │   │   ├── capability-matrix.json
  │   │   │   ├── current-capabilities.json
  │   │   │   └── reference-linux-20260912.json
  │   │   ├── formal
  │   │   │   ├── fixtures
  │   │   │   │   └── control-plane-source-bindings.json
  │   │   │   ├── control_plane_independence.py
  │   │   │   ├── core_convergence_refinement.py
  │   │   │   ├── dns_cache_state.py
  │   │   │   ├── egress_policy_refinement.py
  │   │   │   └── shared_egress_alias_refinement.py
  │   │   ├── planning
  │   │   │   ├── execution-program-r1.md
  │   │   │   └── lego-plan-r1.json
  │   │   ├── providers
  │   │   │   ├── gluetun
  │   │   │   │   ├── config
  │   │   │   │   │   └── carrier-adapter.json
  │   │   │   │   ├── quadlet
  │   │   │   │   │   ├── network-v2-gluetun-owned.container
  │   │   │   │   │   └── network-v2-gluetun-owned.network
  │   │   │   │   ├── systemd
  │   │   │   │   │   ├── network-v2-gluetun-owned-adapter.service
  │   │   │   │   │   ├── network-v2-gluetun-owned-reconcile.service
  │   │   │   │   │   ├── network-v2-gluetun-owned-reconcile.timer
  │   │   │   │   │   └── network-v2-gluetun-owned.target
  │   │   │   │   ├── identity-exclusive.sh
  │   │   │   │   ├── native_profile.py
  │   │   │   │   ├── README.md
  │   │   │   │   └── Taskfile.yml
  │   │   │   ├── surfshark
  │   │   │   │   ├── acceptance
  │   │   │   │   │   └── carrier-smoke.sh
  │   │   │   │   ├── config
  │   │   │   │   │   └── carrier.json
  │   │   │   │   ├── external
  │   │   │   │   │   └── gluetun-servers.lock
  │   │   │   │   ├── README.md
  │   │   │   │   └── Taskfile.yml
  │   │   │   ├── zte-u30pro
  │   │   │   │   ├── observe.py
  │   │   │   │   ├── README.md
  │   │   │   │   └── Taskfile.yml
  │   │   │   └── README.md
  │   │   ├── reference
  │   │   │   └── linux
  │   │   │       ├── containerlab
  │   │   │       │   └── reference.clab.yml
  │   │   │       ├── workflows
  │   │   │       │   └── network-reference-linux.yml
  │   │   │       ├── containerlab-smoke.sh
  │   │   │       ├── netem-smoke.sh
  │   │   │       ├── preflight.sh
  │   │   │       ├── README.md
  │   │   │       ├── Taskfile.yml
  │   │   │       ├── wireguard-kernel-smoke.sh
  │   │   │       └── wireguard-userspace-smoke.sh
  │   │   ├── scripts
  │   │   │   ├── capability-report.py
  │   │   │   └── monitoring-sourcecut-preflight.py
  │   │   ├── substrates
  │   │   │   └── shared-egress
  │   │   │       ├── systemd
  │   │   │       │   ├── network-v2-browserless-forward.service
  │   │   │       │   ├── network-v2-browserless-netns.service
  │   │   │       │   └── network-v2-browserless.target
  │   │   │       ├── carrier-ready.sh
  │   │   │       ├── forward.py
  │   │   │       ├── netns.py
  │   │   │       ├── README.md
  │   │   │       └── Taskfile.yml
  │   │   ├── systemd
  │   │   │   ├── network-v2-blackbox.service
  │   │   │   ├── network-v2-dnsproxy.service
  │   │   │   ├── network-v2-prometheus.service
  │   │   │   ├── network-v2-r0.target
  │   │   │   └── network-v2-singbox.service
  │   │   ├── tests
  │   │   │   ├── test_blackbox_ip_family_contract.py
  │   │   │   ├── test_blackbox_scrape_budget_contract.py
  │   │   │   ├── test_browserless_serial_restoration_contract.py
  │   │   │   ├── test_capability_report_contract.py
  │   │   │   ├── test_chat_ingress_consumer.py
  │   │   │   ├── test_claude_egress_readiness_consumer.py
  │   │   │   ├── test_claude_loaded_policy_cdc.py
  │   │   │   ├── test_codex_cdn_ready_effects.py
  │   │   │   ├── test_codex_mobile_tailnet_sourcecut.py
  │   │   │   ├── test_codex_windows_exit_differential.py
  │   │   │   ├── test_codex_windows_package_program_coverage.py
  │   │   │   ├── test_codex_windows_package_token_evidence.py
  │   │   │   ├── test_codex_windows_process_egress.py
  │   │   │   ├── test_codex_windows_wfp_evidence.py
  │   │   │   ├── test_developer_egress_profile.py
  │   │   │   ├── test_egress_routing_behavior.py
  │   │   │   ├── test_existing_lego_declaration_closure.py
  │   │   │   ├── test_finance_public_data_business.py
  │   │   │   ├── test_finance_readiness_deadline_cegar.py
  │   │   │   ├── test_github_release_mise.py
  │   │   │   ├── test_gluetun_native_provider.py
  │   │   │   ├── test_gluetun_owned_reconcile_contract.py
  │   │   │   ├── test_live_carrier_observer_continuity.py
  │   │   │   ├── test_monitoring_precommit.py
  │   │   │   ├── test_prometheus_singbox_witness.py
  │   │   │   ├── test_readiness_shared_budget.py
  │   │   │   ├── test_shared_forward_lifecycle.py
  │   │   │   ├── test_shared_netns_lifecycle.py
  │   │   │   ├── test_shared_provider_carrier.py
  │   │   │   ├── test_supply_chain_consumer.py
  │   │   │   ├── test_x_reality_consumer.py
  │   │   │   └── test_zte_u30pro_observer.py
  │   │   ├── .gitignore
  │   │   ├── AGENTS.md
  │   │   ├── mise.toml
  │   │   ├── README.md
  │   │   ├── STACK.md
  │   │   └── Taskfile.yml
  │   ├── security
  │   │   ├── .clusterfuzzlite
  │   │   │   ├── build.sh
  │   │   │   ├── Dockerfile
  │   │   │   └── project.yaml
  │   │   ├── artifacts
  │   │   │   └── .gitkeep
  │   │   ├── contracts
  │   │   │   ├── agent-admission-v1
  │   │   │   │   ├── evaluate.py
  │   │   │   │   └── README.md
  │   │   │   └── agent-request-verifier-v1
  │   │   │       ├── evidence
  │   │   │       │   └── CNF-EXTENSION-INTEROP-R1.json
  │   │   │       ├── patches
  │   │   │       │   └── oauth4webapi@3.8.8.patch
  │   │   │       ├── src
  │   │   │       │   └── index.ts
  │   │   │       ├── test
  │   │   │       │   └── cnf-extension-interop.test.ts
  │   │   │       ├── .gitignore
  │   │   │       ├── package.json
  │   │   │       ├── pnpm-lock.yaml
  │   │   │       ├── pnpm-workspace.yaml
  │   │   │       ├── README.md
  │   │   │       ├── RFC7800-KEYCLOAK-INTEROP-ACCEPTANCE-R1.md
  │   │   │       └── tsconfig.json
  │   │   ├── docs
  │   │   │   ├── ATTESTATION-MODEL.md
  │   │   │   ├── BROWSER-SECURITY-WITNESS-R1.md
  │   │   │   ├── CONSEQUENCE-VERIFICATION-DIFFERENTIAL.md
  │   │   │   ├── CYCLONEDX-VEX-ACCEPTANCE-R1.md
  │   │   │   ├── DIFFERENTIAL-R1.md
  │   │   │   ├── REMEDIATION-REVERIFY-ACCEPTANCE-R1.md
  │   │   │   ├── SCOPE-PROFILES.md
  │   │   │   ├── SCORECARD-ACCEPTANCE-R1.md
  │   │   │   ├── security-owner-guide.md
  │   │   │   ├── SIGNED-VSA.md
  │   │   │   ├── STANDARDS-BASELINE.md
  │   │   │   ├── TECHNOLOGY-SELECTION-R2.md
  │   │   │   ├── THREAT-MODEL-ACCEPTANCE-R1.md
  │   │   │   ├── VM-PROVIDER-DISPLACEMENT-R1.md
  │   │   │   └── ZAP-ACTIVE-SCAN-ACCEPTANCE-R1.md
  │   │   ├── fixtures
  │   │   │   ├── agent-admission
  │   │   │   │   └── v0-allow.json
  │   │   │   ├── browser-security
  │   │   │   │   ├── harness-r2-live-lkg-carrier11-bundle.json
  │   │   │   │   ├── harness-r2-live-lkg-carrier11-manifest.json
  │   │   │   │   ├── harness-r2-live-lkg-carrier12-bundle.json
  │   │   │   │   ├── harness-r2-live-lkg-carrier12-manifest.json
  │   │   │   │   ├── harness-r2-live-lkg-carrier13-bundle.json
  │   │   │   │   ├── harness-r2-live-lkg-carrier13-manifest.json
  │   │   │   │   ├── harness-r2-live-lkg-pool-index.json
  │   │   │   │   ├── r2-reference-bundle.json
  │   │   │   │   └── r2-reference-manifest.json
  │   │   │   ├── clean
  │   │   │   │   ├── app.py
  │   │   │   │   └── requirements.txt
  │   │   │   └── zap_reflected_xss_server.py
  │   │   ├── formal
  │   │   │   ├── AgentApprovalBinding.lean
  │   │   │   ├── ConsequenceEvidence.lean
  │   │   │   └── EffectAuthorityBinding.lean
  │   │   ├── fuzz
  │   │   │   └── replay_binding_fuzzer.py
  │   │   ├── labs
  │   │   │   └── agent-admission-rs
  │   │   │       ├── evidence
  │   │   │       │   ├── AGENT-ADMISSION-E2E-R1.json
  │   │   │       │   └── AGENT-ADMISSION-WEBAUTHN-E2E-R1.json
  │   │   │       ├── keycloak
  │   │   │       │   └── realm-agent-admission-lab.json
  │   │   │       ├── patches
  │   │   │       │   └── oauth4webapi@3.8.8.patch
  │   │   │       ├── src
  │   │   │       │   ├── app.ts
  │   │   │       │   ├── bootstrap-grant.ts
  │   │   │       │   ├── e2e-client.ts
  │   │   │       │   ├── errors.ts
  │   │   │       │   ├── grant-store.ts
  │   │   │       │   ├── model.ts
  │   │   │       │   ├── oauth-verifier.ts
  │   │   │       │   ├── opa.ts
  │   │   │       │   ├── principal-store.ts
  │   │   │       │   ├── server.ts
  │   │   │       │   ├── webauthn-e2e.ts
  │   │   │       │   ├── webauthn-router.ts
  │   │   │       │   └── webauthn-service.ts
  │   │   │       ├── test
  │   │   │       │   ├── app.test.ts
  │   │   │       │   ├── compat.test.ts
  │   │   │       │   └── webauthn-state.test.ts
  │   │   │       ├── .gitignore
  │   │   │       ├── e2e.sh
  │   │   │       ├── KEYCLOAK-OAUTH4WEBAPI-COMPAT.md
  │   │   │       ├── package.json
  │   │   │       ├── pnpm-lock.yaml
  │   │   │       ├── pnpm-workspace.yaml
  │   │   │       ├── README.md
  │   │   │       ├── tsconfig.json
  │   │   │       └── webauthn-e2e.sh
  │   │   ├── planning
  │   │   │   └── lego-plan-r1.json
  │   │   ├── policies
  │   │   │   ├── admission.rego
  │   │   │   ├── admission_test.rego
  │   │   │   ├── agent_admission.rego
  │   │   │   ├── agent_admission_effect_integration_test.rego
  │   │   │   ├── agent_admission_test.rego
  │   │   │   ├── consequence_verification.rego
  │   │   │   ├── consequence_verification_test.rego
  │   │   │   ├── effect_admission.rego
  │   │   │   └── effect_admission_test.rego
  │   │   ├── profiles
  │   │   │   ├── product
  │   │   │   │   └── gitleaks.toml
  │   │   │   └── zap
  │   │   │       └── local-authorized-r1.yaml
  │   │   ├── providers
  │   │   │   └── packer
  │   │   │       ├── plugins.pkr.hcl
  │   │   │       └── validation.pkr.hcl
  │   │   ├── schemas
  │   │   │   ├── agent-admission-input-v0.schema.json
  │   │   │   └── owasp-threat-model-v1.0.2.schema.json
  │   │   ├── scripts
  │   │   │   ├── assemble_gate_input.py
  │   │   │   ├── build_browser_security_witness.py
  │   │   │   ├── compare_browser_security_bundles.py
  │   │   │   ├── compare_browser_security_pool.py
  │   │   │   ├── compare_browser_security_witnesses.py
  │   │   │   ├── differential_consequence_verification.py
  │   │   │   ├── emit_attestations.py
  │   │   │   ├── promote_browser_security_pool_lkg.py
  │   │   │   ├── scan_product.sh
  │   │   │   ├── sign_vsa_cosign.sh
  │   │   │   ├── smoke_libvirt_lifecycle.sh
  │   │   │   ├── smoke_libvirt_tpm.sh
  │   │   │   ├── smoke_scorecard_public.sh
  │   │   │   ├── smoke_zap_authorized_local.sh
  │   │   │   ├── validate_cyclonedx_vex.py
  │   │   │   ├── validate_packer_qemu.sh
  │   │   │   ├── validate_scorecard_result.py
  │   │   │   ├── validate_threat_model_binding.py
  │   │   │   ├── validate_tmbom.sh
  │   │   │   ├── verify_build_provenance.py
  │   │   │   ├── verify_remediation_delta.py
  │   │   │   ├── verify_vsa_bundle.py
  │   │   │   └── verify_vsa_cosign.sh
  │   │   ├── src
  │   │   │   └── ordivon_security_v2
  │   │   │       ├── __init__.py
  │   │   │       ├── admission.py
  │   │   │       ├── attestations.py
  │   │   │       ├── browser_security_comparison.py
  │   │   │       ├── browser_security_observation.py
  │   │   │       ├── browser_security_pool.py
  │   │   │       ├── browser_security_witness.py
  │   │   │       ├── evidence.py
  │   │   │       ├── provenance.py
  │   │   │       ├── remediation.py
  │   │   │       ├── scorecard.py
  │   │   │       ├── signed_vsa.py
  │   │   │       ├── threat_model.py
  │   │   │       └── vex.py
  │   │   ├── tests
  │   │   │   ├── fixtures
  │   │   │   │   └── signed-vsa-r2
  │   │   │   │       ├── subject.carrier
  │   │   │   │       ├── trust-policy.json
  │   │   │   │       ├── verification-summary.vsa.intoto.json
  │   │   │   │       ├── verifier.pub
  │   │   │   │       └── vsa.sigstore.json
  │   │   │   ├── test_admission.py
  │   │   │   ├── test_agent_admission_contract.py
  │   │   │   ├── test_agent_admission_schema_boundary.py
  │   │   │   ├── test_attestations.py
  │   │   │   ├── test_browser_security.py
  │   │   │   ├── test_browser_security_collector.py
  │   │   │   ├── test_browser_security_lkg_reseal.py
  │   │   │   ├── test_browser_security_observation_validity.py
  │   │   │   ├── test_browser_security_pool.py
  │   │   │   ├── test_evidence.py
  │   │   │   ├── test_opa_container_gate.py
  │   │   │   ├── test_owner_uv_lock_freshness.py
  │   │   │   ├── test_provenance.py
  │   │   │   ├── test_remediation.py
  │   │   │   ├── test_scorecard.py
  │   │   │   ├── test_signed_vsa.py
  │   │   │   ├── test_threat_model.py
  │   │   │   ├── test_tmbom_pinned_schema.py
  │   │   │   └── test_vex.py
  │   │   ├── threat-models
  │   │   │   └── security-v2-r1.json
  │   │   ├── .gitignore
  │   │   ├── .python-version
  │   │   ├── mise.toml
  │   │   ├── pyproject.toml
  │   │   ├── README.md
  │   │   └── uv.lock
  │   └── workstation
  │       ├── ansible
  │       │   ├── bootstrap.yml
  │       │   ├── game-production-tools.yml
  │       │   ├── host-substrate.yml
  │       │   ├── inventory.ini
  │       │   ├── jev-fastpath-provider.yml
  │       │   ├── n8n.yml
  │       │   ├── observability-grafana.yml
  │       │   ├── observability-logs.yml
  │       │   ├── observability-metrics.yml
  │       │   ├── observability-traces.yml
  │       │   ├── postgresql-backup.yml
  │       │   ├── ppt-master-provider.yml
  │       │   ├── retire-wsl-cloudflare-canary.yml
  │       │   ├── retire-wsl-windows-runtime-provider.yml
  │       │   ├── temporal-production.yml
  │       │   ├── workstation-node-carriers.yml
  │       │   ├── workstation-retire-legacy-launchers.yml
  │       │   ├── workstation-service-profiles.yml
  │       │   ├── workstation-tool-bindings.yml
  │       │   └── workstation-windows-jev-fastpath-provider.yml
  │       ├── contracts
  │       │   ├── asyncapi
  │       │   │   ├── distribution-admission-data.schema.json
  │       │   │   ├── distribution-integration-result-data.schema.json
  │       │   │   └── integration-events.asyncapi.yaml
  │       │   ├── cloudevents
  │       │   │   └── ordivon-event.schema.json
  │       │   ├── outbox
  │       │   │   └── postgresql-outbox.sql.example
  │       │   └── README.md
  │       ├── docs
  │       │   ├── ARCHITECTURE.md
  │       │   ├── CANONICAL_PATH_CUTOVER_R6.md
  │       │   ├── CLOUDFLARE_PROVIDER_MAINTENANCE.md
  │       │   ├── D_DRIVE_OFFLINE_MAINTENANCE_R3.md
  │       │   ├── HOST_HISTORICAL_PROJECTION_R3.md
  │       │   ├── JEV_FASTPATH_PROVIDER.md
  │       │   ├── MIGRATION_R1.md
  │       │   ├── N8N_DISTRIBUTION_ADAPTER_SMOKE.md
  │       │   ├── N8N_INTEGRATION_SMOKE.md
  │       │   ├── N8N_SERVICE.md
  │       │   ├── PPT_MASTER_PROVIDER.md
  │       │   ├── STANDARDS_FIRST_COMPOSITION.md
  │       │   ├── TEMPORAL_PRODUCTION_GREEN.md
  │       │   ├── UPDATE_DISCOVERY_R2.md
  │       │   ├── WINDOWS_CLOUDFLARED_RUNTIME_INGRESS.md
  │       │   └── WORKSTATION_CONTRACT_FIRST_EXECUTION_SPEC_R1.md
  │       ├── evidence
  │       │   ├── host-v1-final-pg-archive-20260913.json
  │       │   └── host-v1-parquet-duckdb-r3-20260913.json
  │       ├── grafana
  │       │   ├── grafana.env
  │       │   └── ordivon-grafana.container
  │       ├── host
  │       │   ├── coredump.conf.d-20-ordivon-agent-node.conf
  │       │   ├── system.conf.d-20-ordivon-agent-limits.conf
  │       │   └── user.conf.d-20-ordivon-agent-limits.conf
  │       ├── inventory
  │       │   ├── queries
  │       │   │   ├── npm_packages.sql
  │       │   │   ├── os_version.sql
  │       │   │   ├── python_packages.sql
  │       │   │   ├── running_executables.sql
  │       │   │   ├── system_identity.sql
  │       │   │   └── uptime.sql
  │       │   ├── snapshots
  │       │   │   └── 2026-09-14-machine-tools.json
  │       │   ├── current-substrate.md
  │       │   ├── probe_executables.ps1
  │       │   ├── probe_executables.py
  │       │   ├── README.md
  │       │   └── sources.json
  │       ├── manifests
  │       │   └── external-stack-v1.json
  │       ├── n8n
  │       │   ├── workflows
  │       │   │   ├── ordivon-distribution-adapter-smoke-v1.json
  │       │   │   └── ordivon-integration-smoke-v1.json
  │       │   ├── n8n.env
  │       │   ├── ordivon-n8n-runners.container
  │       │   ├── ordivon-n8n.container
  │       │   └── ordivon-n8n.pod
  │       ├── observability
  │       │   ├── gatus
  │       │   │   ├── config.yaml
  │       │   │   └── ordivon-gatus.service
  │       │   ├── grafana-datasources.yaml
  │       │   ├── loki.yaml
  │       │   ├── netdata-v2.conf
  │       │   ├── node-exporter.conf
  │       │   ├── prometheus.conf
  │       │   ├── prometheus.yml
  │       │   ├── README.md
  │       │   ├── tempo.yaml
  │       │   ├── vector-systemd.conf
  │       │   └── vector.yaml
  │       ├── policy
  │       │   └── README.md
  │       ├── postgresql
  │       │   ├── ordivon-postgresql-backup.service
  │       │   ├── ordivon-postgresql-backup.timer
  │       │   ├── pgbackrest.conf
  │       │   └── postgresql-pgdata.conf
  │       ├── providers
  │       │   └── cloudflare
  │       │       ├── config
  │       │       │   └── edge-policy.json
  │       │       ├── deploy
  │       │       │   └── systemd
  │       │       │       ├── ordivon-edge-gc.service
  │       │       │       └── ordivon-edge-gc.timer
  │       │       ├── docs
  │       │       │   ├── operations.md
  │       │       │   ├── release.md
  │       │       │   ├── reliability.md
  │       │       │   └── security.md
  │       │       ├── scripts
  │       │       │   ├── check-operations
  │       │       │   ├── check-policy-config.py
  │       │       │   ├── configure-r2-lifecycle
  │       │       │   ├── configure_r2_lifecycle.py
  │       │       │   ├── emit-contract-fixtures.ts
  │       │       │   ├── install-edge-client
  │       │       │   ├── install-edge-operations
  │       │       │   ├── ordivon_cloudflare_tofu_handoff.py
  │       │       │   ├── ordivon_edge_client.py
  │       │       │   ├── ordivon_edge_gc.py
  │       │       │   ├── ordivon_edge_release.py
  │       │       │   ├── tsconfig.contracts.json
  │       │       │   └── wrangler-dry-run.mjs
  │       │       ├── src
  │       │       │   ├── artifacts.ts
  │       │       │   ├── auth.ts
  │       │       │   ├── body.ts
  │       │       │   ├── browser-manifest.ts
  │       │       │   ├── browser-policy.ts
  │       │       │   ├── browser-run.ts
  │       │       │   ├── cleanup.ts
  │       │       │   ├── contracts.ts
  │       │       │   ├── errors.ts
  │       │       │   ├── execution.ts
  │       │       │   ├── external-fetch.ts
  │       │       │   ├── fetch-policy.ts
  │       │       │   ├── http.ts
  │       │       │   ├── idempotency.ts
  │       │       │   ├── index.ts
  │       │       │   ├── observability.ts
  │       │       │   ├── policy.ts
  │       │       │   ├── receipts.ts
  │       │       │   └── version.ts
  │       │       ├── test
  │       │       │   ├── client_test.py
  │       │       │   ├── contracts.test.ts
  │       │       │   ├── gc_test.py
  │       │       │   ├── handoff_tofu_test.py
  │       │       │   ├── helpers.ts
  │       │       │   ├── lifecycle_test.py
  │       │       │   ├── release_controller_test.py
  │       │       │   ├── transactions.test.ts
  │       │       │   └── worker.test.ts
  │       │       ├── .gitignore
  │       │       ├── AGENTS.md
  │       │       ├── LICENSE
  │       │       ├── MIGRATION_PROVENANCE.md
  │       │       ├── package.json
  │       │       ├── pnpm-lock.yaml
  │       │       ├── pnpm-workspace.yaml
  │       │       ├── README.md
  │       │       ├── tsconfig.json
  │       │       └── wrangler.jsonc
  │       ├── scripts
  │       │   ├── accept-n8n-distribution-adapter-smoke.sh
  │       │   ├── converge-n8n-distribution-adapter-smoke.sh
  │       │   ├── converge-n8n-integration-smoke.sh
  │       │   ├── deploy-gatus
  │       │   ├── host_historical_projection.py
  │       │   ├── invoke-n8n-distribution-adapter-smoke.py
  │       │   ├── invoke-n8n-integration-smoke.py
  │       │   ├── temporal-n8n-integration-smoke.py
  │       │   ├── temporal_green_smoke.py
  │       │   ├── temporal_nexus_smoke.py
  │       │   ├── temporal_pgbackrest_restore_smoke.sh
  │       │   ├── test-integration-contracts.py
  │       │   └── verify-n8n-rootless.sh
  │       ├── systemd
  │       │   ├── service-profiles
  │       │   │   ├── loki.service.d
  │       │   │   │   └── 20-ordivon-observability-heavy.conf
  │       │   │   ├── netdata.service.d
  │       │   │   │   └── 20-ordivon-observability-heavy.conf
  │       │   │   └── vector.service.d
  │       │   │       └── 20-ordivon-observability-heavy.conf
  │       │   ├── ordivon-observability-heavy.target
  │       │   ├── ordivon-update-discovery.service
  │       │   └── ordivon-update-discovery.timer
  │       ├── tempo
  │       │   └── ordivon-tempo.container
  │       ├── temporal
  │       │   ├── production.yaml
  │       │   └── temporal.service.j2
  │       ├── tests
  │       │   ├── test_codex_cli_pnpm_contract.py
  │       │   ├── test_d_drive_compact_r3.py
  │       │   ├── test_distribution_adapter_source_binding.py
  │       │   ├── test_equipment_binding_compat.py
  │       │   ├── test_executable_probe.py
  │       │   ├── test_gateway_mcp_tofu.py
  │       │   ├── test_gatus_deployment.py
  │       │   ├── test_host_historical_projection.py
  │       │   ├── test_host_substrate_authority.py
  │       │   ├── test_jev_consumer_secret_materializer.py
  │       │   ├── test_jev_fastpath_provider.py
  │       │   ├── test_machine_inventory_contract.py
  │       │   ├── test_node_manifest_unique_keys.py
  │       │   ├── test_observability_prometheus.py
  │       │   ├── test_observability_traces.py
  │       │   ├── test_playwright_cli_binding.py
  │       │   ├── test_provider_authority_validation.py
  │       │   ├── test_provider_linux_observers.py
  │       │   ├── test_provider_windows_wsl.py
  │       │   ├── test_provider_windows_wsl_service.py
  │       │   ├── test_runtime_provider_retirement.py
  │       │   ├── test_service_profiles.py
  │       │   ├── test_temporal_pgbackrest_restore_smoke.py
  │       │   ├── test_temporal_restore_scratch_safety.py
  │       │   ├── test_temporal_restore_stop_failure.py
  │       │   ├── test_temporal_sdk_ops_contract.py
  │       │   ├── test_tofu_agent_birth_handoff.py
  │       │   ├── test_tool_binding_projection.py
  │       │   ├── test_update_candidate_report.py
  │       │   ├── test_windows_cloudflared_runtime_ingress.py
  │       │   ├── test_windows_jev_fastpath_provider.py
  │       │   ├── test_windows_update_discovery_contract.py
  │       │   ├── test_windows_user_git_bundle_consumer.py
  │       │   ├── test_windows_workspace_environment_doctor.py
  │       │   ├── test_workstation_agent_automation_carrier.py
  │       │   ├── test_workstation_consequences.py
  │       │   ├── test_workstation_input_authority_ingress.py
  │       │   ├── test_workstation_tool_binding.py
  │       │   ├── test_wsl_cloudflare_canary_retirement.py
  │       │   └── test_wsl_sparse_guest_health.py
  │       ├── tofu
  │       │   ├── agent-birth-handoff
  │       │   │   ├── .gitignore
  │       │   │   ├── .terraform.lock.hcl
  │       │   │   ├── main.tf
  │       │   │   ├── outputs.tf
  │       │   │   ├── README.md
  │       │   │   ├── tofurc
  │       │   │   ├── variables.tf
  │       │   │   └── versions.tf
  │       │   └── README.md
  │       ├── tools
  │       │   └── update_candidate_report.py
  │       ├── windows
  │       │   ├── install_update_discovery.ps1
  │       │   ├── update_candidate_report.ps1
  │       │   ├── user_git_bundle_checkout.ps1
  │       │   └── workspace_environment_doctor.ps1
  │       ├── workstation
  │       │   ├── nix
  │       │   │   ├── codex-cli
  │       │   │   │   ├── package.json
  │       │   │   │   ├── pnpm-lock.yaml
  │       │   │   │   ├── pnpm-workspace.yaml
  │       │   │   │   └── README.md
  │       │   │   ├── nix
  │       │   │   │   └── home.nix
  │       │   │   ├── flake.lock
  │       │   │   └── flake.nix
  │       │   ├── providers
  │       │   │   ├── acceptance
  │       │   │   │   ├── authority-validation-r1.json
  │       │   │   │   ├── windows-wsl-observer-r1.json
  │       │   │   │   └── windows-wsl-service-control-r1.json
  │       │   │   ├── authority_validation
  │       │   │   │   ├── AuthorityValidationProvider.ps1
  │       │   │   │   └── materialize.py
  │       │   │   ├── d_drive_compact
  │       │   │   │   ├── d_drive_compact_gate_r3.py
  │       │   │   │   ├── DDriveCompactAuthorizeR4.ps1
  │       │   │   │   ├── DDriveCompactRunR3.ps1
  │       │   │   │   ├── DDriveOfflineCompactR3.ps1
  │       │   │   │   └── materialize.py
  │       │   │   ├── windows_wsl
  │       │   │   │   ├── materialize.py
  │       │   │   │   └── WindowsWslProvider.ps1
  │       │   │   ├── windows_wsl_service
  │       │   │   │   ├── materialize.py
  │       │   │   │   └── WindowsWslServiceControlProvider.ps1
  │       │   │   ├── linux_service_observer.py
  │       │   │   ├── README.md
  │       │   │   ├── runtime_control_provider.py
  │       │   │   └── wsl_sparse_guest_health.py
  │       │   ├── windows
  │       │   │   ├── cloudflared-runtime.dsc.yaml
  │       │   │   ├── jev-fastpath-provider.toml
  │       │   │   ├── jev_fastpath_provider.py
  │       │   │   ├── materialize-cloudflared-runtime-token.ps1
  │       │   │   ├── materialize-jev-consumer-secrets.ps1
  │       │   │   ├── materialize_jev_consumer_secrets.py
  │       │   │   └── workstation.dsc.yaml
  │       │   ├── agent_automation_carrier.py
  │       │   ├── equipment_binding.py
  │       │   ├── input_authority_contract.py
  │       │   ├── input_authority_ingress.py
  │       │   ├── playwright_cli_binding.py
  │       │   ├── README.md
  │       │   ├── software.toml
  │       │   └── tool_binding.py
  │       ├── .gitignore
  │       ├── .python-version
  │       ├── mise.toml
  │       ├── pyproject.toml
  │       ├── README.md
  │       └── uv.lock
  ├── profiles
  │   ├── domains
  │   │   ├── game
  │   │   │   ├── game-autonomous-interest-model-r7.schema.json
  │   │   │   ├── game-autonomous-interest-protocol-r7.json
  │   │   │   ├── GAME_AUTONOMOUS_INTEREST_PROTOCOL_R7.md
  │   │   │   └── README.md
  │   │   └── README.md
  │   └── research
  │       ├── mechanical-components
  │       │   └── research-mechanical-component-r1.schema.json
  │       ├── publication
  │       │   ├── carrier-attestation-r1.schema.json
  │       │   ├── finding-r1.schema.json
  │       │   ├── observer-report-r1.schema.json
  │       │   ├── observer-task-envelope-r1.schema.json
  │       │   ├── perceptual-conformance-r1.json
  │       │   ├── perceptual-conformance-r1.schema.json
  │       │   ├── publication-closure-r1.json
  │       │   └── publication-closure-r2.json
  │       └── tool-qualification
  │           ├── examples
  │           │   └── worktrunk-workspace-r1.json
  │           ├── tool-qualification-packet-r1.schema.json
  │           └── TOOL_QUALIFICATION_R1.md
  ├── services
  │   ├── gateway
  │   │   ├── formal
  │   │   │   ├── evidence
  │   │   │   │   ├── GatewayOwnerObservationR1-20261108.json
  │   │   │   │   ├── GatewayOwnerRPCPhase-20261108.json
  │   │   │   │   ├── GatewayRoutingR1-20261107.json
  │   │   │   │   └── GatewayVerification-20261108.json
  │   │   │   ├── check_owner_status_contract.py
  │   │   │   ├── check_routing_conformance.py
  │   │   │   ├── GatewayCapabilityAuthzR1.cfg
  │   │   │   ├── GatewayCapabilityAuthzR1.reachability.cfg
  │   │   │   ├── GatewayCapabilityAuthzR1.tla
  │   │   │   ├── GatewayCapabilityAuthzR1.unsafe.cfg
  │   │   │   ├── GatewayOwnerObservationR1.cfg
  │   │   │   ├── GatewayOwnerObservationR1.reachability.cfg
  │   │   │   ├── GatewayOwnerObservationR1.tla
  │   │   │   ├── GatewayOwnerObservationR1.unsafe.cfg
  │   │   │   ├── GatewayRoutingR1.cfg
  │   │   │   ├── GatewayRoutingR1.reachability.cfg
  │   │   │   ├── GatewayRoutingR1.tla
  │   │   │   └── GatewayRoutingR1.unsafe.cfg
  │   │   ├── packaging
  │   │   │   ├── windows
  │   │   │   │   ├── activate_service.ps1
  │   │   │   │   ├── install_release.ps1
  │   │   │   │   ├── materialize_credentials.ps1
  │   │   │   │   ├── materialize_service.ps1
  │   │   │   │   ├── probe_candidate.py
  │   │   │   │   ├── protect_candidate_acl.ps1
  │   │   │   │   └── verify_release.py
  │   │   │   ├── enable_local_service_identity.sh
  │   │   │   ├── enable_trace_export.sh
  │   │   │   ├── enable_windows_service_identity.sh
  │   │   │   ├── install_release.sh
  │   │   │   └── verify_tool_surface.py
  │   │   ├── planning
  │   │   │   ├── GATEWAY_WINDOWS_CANDIDATE_CARRIER_EVIDENCE_R1.json
  │   │   │   ├── GATEWAY_WINDOWS_R2_CRASH_HOST_READBACK_EVIDENCE.json
  │   │   │   ├── GATEWAY_WINDOWS_RELEASE_EVIDENCE_R1.json
  │   │   │   ├── GATEWAY_WINDOWS_SERVICE_CARRIER_EVIDENCE_R1.json
  │   │   │   ├── GATEWAY_WINDOWS_TOOLCHAIN_EVIDENCE_R1.json
  │   │   │   ├── lego-plan-r1.json
  │   │   │   └── lego-plan-windows-carrier-r2.json
  │   │   ├── src
  │   │   │   └── ordivon_gateway
  │   │   │       ├── __init__.py
  │   │   │       ├── access_auth.py
  │   │   │       ├── audit.py
  │   │   │       ├── authzen_authorizer.py
  │   │   │       ├── capability_authz.py
  │   │   │       ├── capability_catalog.py
  │   │   │       ├── capability_projection.py
  │   │   │       ├── contracts.py
  │   │   │       ├── execution_commands.py
  │   │   │       ├── execution_coordinator.py
  │   │   │       ├── execution_observations.py
  │   │   │       ├── execution_refs.py
  │   │   │       ├── host_attention_tools.py
  │   │   │       ├── host_social_tools.py
  │   │   │       ├── host_tool_contracts.py
  │   │   │       ├── host_tools.py
  │   │   │       ├── host_work_tools.py
  │   │   │       ├── http_ingress_guard.py
  │   │   │       ├── mcp_server.py
  │   │   │       ├── owner_protocol.py
  │   │   │       ├── research_resolution.py
  │   │   │       ├── research_routes.py
  │   │   │       ├── routing.py
  │   │   │       ├── service.py
  │   │   │       ├── upstream.py
  │   │   │       └── upstream_identity.py
  │   │   ├── systemd
  │   │   │   ├── ordivon-gateway.service.d
  │   │   │   │   ├── 10-local-service-identity.example.conf
  │   │   │   │   ├── 20-public-access.example.conf
  │   │   │   │   ├── 30-windows-service-identity.example.conf
  │   │   │   │   ├── 35-skills-owner.example.conf
  │   │   │   │   └── 40-otel-traces.example.conf
  │   │   │   └── ordivon-gateway.service
  │   │   ├── tests
  │   │   │   ├── test_access_auth.py
  │   │   │   ├── test_audit.py
  │   │   │   ├── test_authzen_authorizer.py
  │   │   │   ├── test_capability_authz_middleware.py
  │   │   │   ├── test_capability_projection.py
  │   │   │   ├── test_capability_readiness_state.py
  │   │   │   ├── test_execution_principal_request_namespace.py
  │   │   │   ├── test_gateway_service.py
  │   │   │   ├── test_host_byte_budget_tool_contract.py
  │   │   │   ├── test_http_ingress_coverage.py
  │   │   │   ├── test_latest_runtime_release_carrier.py
  │   │   │   ├── test_linux_pg_business_sdk_bridge.py
  │   │   │   ├── test_live_epoch5_runtime_currentness.py
  │   │   │   ├── test_live_streamable_http_ingress.py
  │   │   │   ├── test_owner_http_pool.py
  │   │   │   ├── test_owner_mcp_protocol_mode.py
  │   │   │   ├── test_pg_real_runtime_owner.py
  │   │   │   ├── test_projection_concurrency.py
  │   │   │   ├── test_research_capability_resolution.py
  │   │   │   ├── test_search_observation_isolation.py
  │   │   │   ├── test_skills_owner_optin.py
  │   │   │   ├── test_systemd_contract.py
  │   │   │   ├── test_tool_surface_release_contract.py
  │   │   │   ├── test_upstream_identity.py
  │   │   │   ├── test_windows_acl_preflight.py
  │   │   │   ├── test_windows_activation_contract.py
  │   │   │   ├── test_windows_credential_contract.py
  │   │   │   ├── test_windows_local_identity.py
  │   │   │   ├── test_windows_release_contract.py
  │   │   │   ├── test_windows_runtime_typed_status_read.py
  │   │   │   └── test_windows_service_contract.py
  │   │   ├── .python-version
  │   │   ├── AGENTS.md
  │   │   ├── enforcement-surface.json
  │   │   ├── mcp-surface.json
  │   │   ├── pyproject.toml
  │   │   ├── README.md
  │   │   └── uv.lock
  │   ├── harness
  │   │   ├── .github
  │   │   │   ├── ISSUE_TEMPLATE
  │   │   │   │   ├── bug_report.yml
  │   │   │   │   ├── config.yml
  │   │   │   │   └── feature_request.yml
  │   │   │   ├── workflows
  │   │   │   │   └── release-acceptance.yml
  │   │   │   ├── actionlint.yaml
  │   │   │   └── pull_request_template.md
  │   │   ├── .ordivon
  │   │   │   ├── project.yaml
  │   │   │   ├── publication.yaml
  │   │   │   └── rights.yaml
  │   │   ├── config
  │   │   │   ├── agent-automation-mcp-requirements.txt
  │   │   │   ├── agent-automation-temporal-requirements.txt
  │   │   │   ├── agent-automation.toml
  │   │   │   ├── browser-benchmark-suite.json
  │   │   │   ├── browser-capability-routes.json
  │   │   │   ├── browser-decision-corpus-r1.json
  │   │   │   ├── browserless-playwright-requirements.txt
  │   │   │   ├── harness-otel-event-sink-requirements.txt
  │   │   │   ├── mind2web-browser-decision-corpus-no-context-r1.json
  │   │   │   ├── mind2web-browser-decision-corpus-r1.json
  │   │   │   └── system1-decision-corpus-r1.json
  │   │   ├── containers
  │   │   │   └── ordivon-browserless@.container
  │   │   ├── docs
  │   │   │   ├── superpowers
  │   │   │   │   └── plans
  │   │   │   │       └── 2026-09-19-durable-human-handoff-standards-replacement.md
  │   │   │   ├── ADAPTIVE_EDIT_GATEWAY_R2.md
  │   │   │   ├── AM-DSH-EVOLUTION-CHALLENGER.md
  │   │   │   ├── AM2-LOOP-BOUNDARY-FALSIFIERS.md
  │   │   │   ├── AM5-GENERATED-MORPHOLOGY-CANDIDATE.md
  │   │   │   ├── AM8-LIVE-MORPHING-GATE.md
  │   │   │   ├── authority.md
  │   │   │   ├── BROWSER-SECURITY-WITNESS-SOURCE-R1.md
  │   │   │   ├── BROWSER_AX_GENERALIZATION_R1.md
  │   │   │   ├── BROWSER_BENCHMARK_CONTRACT_S2.md
  │   │   │   ├── BROWSER_BENCHMARK_PROSPECTIVE_S5.md
  │   │   │   ├── BROWSER_BENCHMARK_RUNNER_S3.md
  │   │   │   ├── BROWSER_BENCHMARK_RUNTIME_HANDOFF_S4.md
  │   │   │   ├── BROWSER_CAPABILITY_ROUTER_R1.md
  │   │   │   ├── BROWSER_DECISION_ARCHITECTURE_R1.md
  │   │   │   ├── BROWSER_DECISION_PROVIDER_DUEL_R1.md
  │   │   │   ├── BROWSER_READINESS_OPS_R6.md
  │   │   │   ├── CANONICAL_COMPATIBILITY.md
  │   │   │   ├── COMPATIBILITY.md
  │   │   │   ├── DAP_PROVIDER_PORT_R8.md
  │   │   │   ├── DATA_AND_PRIVACY.md
  │   │   │   ├── DELIBERATION-BEFORE-TOOLS-H0.md
  │   │   │   ├── DELIBERATION-COMPOSITION-H1.md
  │   │   │   ├── DELIBERATION-LIFECYCLE-H2.md
  │   │   │   ├── DOMAIN-TOOL-BRIDGE-P0.md
  │   │   │   ├── EVIDENCE_CURRENTNESS.md
  │   │   │   ├── harness-boundary-h5-decision.md
  │   │   │   ├── LAYA_ARCHITECTURE_DUEL_R1.md
  │   │   │   ├── LSP_PROVIDER_PORT_R7.md
  │   │   │   ├── LSP_WORKSPACE_EDIT_R7.md
  │   │   │   ├── OPERATIONS.md
  │   │   │   ├── ordivon-harness-v0.md
  │   │   │   ├── ORDIVON_HARNESS_E1_E2_DESIGN.md
  │   │   │   ├── ORDIVON_HARNESS_OH1_OH5_CLOSEOUT.md
  │   │   │   ├── P0-CAPABILITY-COMPOSITION-CLOSEOUT.md
  │   │   │   ├── P0-INDEPENDENT-PERSISTENCE.md
  │   │   │   ├── PROVIDER-BOUNDARY-DIAGNOSIS-R1.md
  │   │   │   ├── QUICKSTART.md
  │   │   │   ├── RELEASES.md
  │   │   │   ├── STATUS.md
  │   │   │   ├── SYSTEM1_DECISION_BENCHMARK_R1.md
  │   │   │   └── VERIFICATION.md
  │   │   ├── evals
  │   │   │   ├── fixtures
  │   │   │   │   └── capability-environment-owner-dogfood-20260827.json
  │   │   │   ├── fresh_agent_ab
  │   │   │   │   ├── audit-v2-currentness.json
  │   │   │   │   ├── CLOSEOUT-v1-v2.md
  │   │   │   │   ├── corpus-v1.json
  │   │   │   │   ├── corpus-v2-currentness.json
  │   │   │   │   ├── corrected-metrics-v1.json
  │   │   │   │   ├── POSTHOC-AUDIT-v1.md
  │   │   │   │   ├── PREREGISTRATION-v1.md
  │   │   │   │   ├── PREREGISTRATION-v2-currentness.md
  │   │   │   │   ├── result-v1.json
  │   │   │   │   ├── result-v2-currentness.json
  │   │   │   │   ├── run_live_v1.py
  │   │   │   │   ├── run_live_v2_currentness.py
  │   │   │   │   ├── summary-v1.json
  │   │   │   │   └── summary-v2-currentness.json
  │   │   │   ├── harness-document-retirement-004
  │   │   │   │   ├── fixture
  │   │   │   │   │   ├── docs
  │   │   │   │   │   │   ├── MIGRATION-R1.md
  │   │   │   │   │   │   ├── OLD-PHASE.md
  │   │   │   │   │   │   └── OPERATOR.md
  │   │   │   │   │   ├── evidence
  │   │   │   │   │   │   └── consumed-fixture.json
  │   │   │   │   │   └── README.md
  │   │   │   │   ├── README.md
  │   │   │   │   ├── task.json
  │   │   │   │   └── verifier.py
  │   │   │   ├── harness-edit-addressing-002
  │   │   │   │   ├── evidence
  │   │   │   │   │   └── r2-task-qa.json
  │   │   │   │   ├── known-invalid
  │   │   │   │   │   └── both-enabled.py
  │   │   │   │   ├── oracle
  │   │   │   │   │   └── feature_flags.py
  │   │   │   │   ├── verifier
  │   │   │   │   │   └── test_outcome.py
  │   │   │   │   ├── qa.py
  │   │   │   │   ├── README.md
  │   │   │   │   └── task.json
  │   │   │   ├── harness-edit-multiregion-003
  │   │   │   │   ├── evidence
  │   │   │   │   │   └── r2-task-qa.json
  │   │   │   │   ├── known-invalid
  │   │   │   │   │   ├── collateral.py
  │   │   │   │   │   ├── retry-only.py
  │   │   │   │   │   └── timeout-only.py
  │   │   │   │   ├── oracle
  │   │   │   │   │   └── pipeline.py
  │   │   │   │   ├── verifier
  │   │   │   │   │   └── test_outcome.py
  │   │   │   │   ├── qa.py
  │   │   │   │   ├── README.md
  │   │   │   │   └── task.json
  │   │   │   ├── harness-repository-repair-001
  │   │   │   │   ├── evidence
  │   │   │   │   │   └── r2-task-qa.json
  │   │   │   │   ├── known-invalid
  │   │   │   │   │   ├── floor-only.py
  │   │   │   │   │   └── visible-suite-overfit.py
  │   │   │   │   ├── oracle
  │   │   │   │   │   └── allocation.py
  │   │   │   │   ├── verifier
  │   │   │   │   │   └── test_outcome.py
  │   │   │   │   ├── qa.py
  │   │   │   │   ├── README.md
  │   │   │   │   └── task.json
  │   │   │   └── capability_environment_owner_dogfood.py
  │   │   ├── evidence
  │   │   │   ├── browser-security
  │   │   │   │   ├── agent-birth-provider-boundary-r1-20260918.json
  │   │   │   │   ├── browserless-canary-control-r1-20260918.json
  │   │   │   │   ├── browserless-canary-known-different-r1-20260918.json
  │   │   │   │   ├── cloudflare-provider-security-exp-r1-20260917.json
  │   │   │   │   ├── cloudflare-provider-security-exp-r2-20260918.json
  │   │   │   │   ├── cloudflare-provider-security-exp-r3-20260918.json
  │   │   │   │   ├── cloudflare-provider-security-exp-r3-geometry-ablation-20260918.json
  │   │   │   │   ├── cloudflare-provider-security-exp-r3-repeatability-20260918.json
  │   │   │   │   ├── cloudflare-provider-security-exp-r3-run2-20260918.json
  │   │   │   │   ├── cloudflare-provider-security-exp-r4-cf07-analysis-20260918.json
  │   │   │   │   ├── cloudflare-provider-security-exp-r4-cf07-metadata-20260918.json
  │   │   │   │   ├── cloudflare-provider-security-exp-r4-cf07-outcome-anchor-20260918.json
  │   │   │   │   ├── cloudflare-provider-security-exp-r5-controlled-run1-20260918.json
  │   │   │   │   ├── cloudflare-provider-security-exp-r5-controlled-run2-20260918.json
  │   │   │   │   ├── cloudflare-provider-security-exp-r5-repeatability-20260918.json
  │   │   │   │   ├── cloudflare-provider-security-exp-r6-cf07-prospective-telemetry-20260918.json
  │   │   │   │   ├── cloudflare-provider-security-exp-r7-controlled-run1-20260918.json
  │   │   │   │   ├── cloudflare-provider-security-exp-r7-controlled-run2-20260918.json
  │   │   │   │   ├── cloudflare-provider-security-exp-r7-repeatability-20260918.json
  │   │   │   │   ├── cloudflare-provider-security-exp-r8-fresh-service-run1-20260918.json
  │   │   │   │   ├── cloudflare-provider-security-exp-r8-fresh-service-run2-20260918.json
  │   │   │   │   ├── cloudflare-provider-security-exp-r8-repeatability-20260918.json
  │   │   │   │   ├── cloudflare-provider-security-exp-r9-repeatability-20260918.json
  │   │   │   │   ├── cloudflare-provider-security-exp-r9-window-placement-run1-20260918.json
  │   │   │   │   ├── cloudflare-provider-security-exp-r9-window-placement-run2-20260918.json
  │   │   │   │   └── pool-runner-r1-acceptance-20260918.json
  │   │   │   ├── system1-decision
  │   │   │   │   ├── mind2web-census-r1
  │   │   │   │   │   ├── test_domain__test_domain_0.json.json
  │   │   │   │   │   ├── test_domain__test_domain_1.json.json
  │   │   │   │   │   ├── test_domain__test_domain_2.json.json
  │   │   │   │   │   ├── test_domain__test_domain_3.json.json
  │   │   │   │   │   ├── test_domain__test_domain_4.json.json
  │   │   │   │   │   ├── test_domain__test_domain_5.json.json
  │   │   │   │   │   ├── test_domain__test_domain_6.json.json
  │   │   │   │   │   ├── test_domain__test_domain_7.json.json
  │   │   │   │   │   ├── test_domain__test_domain_8.json.json
  │   │   │   │   │   ├── test_domain__test_domain_9.json.json
  │   │   │   │   │   ├── test_task__test_task_0.json.json
  │   │   │   │   │   ├── test_task__test_task_1.json.json
  │   │   │   │   │   ├── test_task__test_task_2.json.json
  │   │   │   │   │   ├── test_website__test_website_0.json.json
  │   │   │   │   │   └── test_website__test_website_1.json.json
  │   │   │   │   ├── browser-decision-crossencoder-r1-20260921.json
  │   │   │   │   ├── browser-decision-jev-blocked-r1-20260921.json
  │   │   │   │   └── browser-decision-laya-r1-20260921.json
  │   │   │   ├── adaptive-edit-r2-live-ab-deepseek-flash-20260914.json
  │   │   │   ├── adaptive-edit-r2-live-ab-deepseek-flash-addressing-20260914.json
  │   │   │   ├── adaptive-edit-r2-live-ab-deepseek-flash-multiregion-20260914.json
  │   │   │   ├── codex-app-h3-live-64ab44b-20260731.json
  │   │   │   ├── dap-r8-gdb-launch-20260914.json
  │   │   │   ├── dap-r8-runtime-owned-attach-20260914.json
  │   │   │   ├── harness-agent-first-mandate-6daeee4.json
  │   │   │   ├── harness-agent-plugin-h1-acceptance-20260922.json
  │   │   │   ├── harness-agent-plugin-h2-durable-gateway-effects-20260922.json
  │   │   │   ├── harness-agent-plugin-h2b-cooperative-cancellation-20260922.json
  │   │   │   ├── harness-c3-agent-first-api-be7200a.json
  │   │   │   ├── harness-campaign3-rich-effect-owner-v1-capture.json
  │   │   │   ├── harness-campaign3-rich-effect-owner-v1-result.json
  │   │   │   ├── harness-campaign5-provider-route-preservation-v1-result.json
  │   │   │   ├── harness-capability-environment-v1.json
  │   │   │   ├── harness-conclusion-correction-separation-9e47ee6.json
  │   │   │   ├── harness-current-affordance-compact-v2.json
  │   │   │   ├── harness-current-no-tool-conclusion-control-repair-v1.json
  │   │   │   ├── harness-deepseek-mixed-turn-6124cd2.json
  │   │   │   ├── harness-first-interface-owner-bridges-v2.json
  │   │   │   ├── harness-first-interface-owner-bridges-v3.json
  │   │   │   ├── harness-first-interface-owner-bridges-v4.json
  │   │   │   ├── harness-first-interface-owner-bridges-v5.json
  │   │   │   ├── harness-first-interface-owner-composition-atlas-v1.json
  │   │   │   ├── harness-global-secondary-deepseek-51825aa.json
  │   │   │   ├── harness-global-secondary-replan-a38f4cf.json
  │   │   │   ├── harness-h0-deliberation-authority-9576039.json
  │   │   │   ├── harness-h1-deliberation-composition-89a7fa1.json
  │   │   │   ├── harness-h1-independent-cli-e9612fa.json
  │   │   │   ├── harness-h2-deliberation-lifecycle-28d3a28.json
  │   │   │   ├── harness-h2-deliberation-lifecycle-64f58c7.json
  │   │   │   ├── harness-h2-deliberation-lifecycle-6c0defb.json
  │   │   │   ├── harness-h2-deliberation-lifecycle-8100879.json
  │   │   │   ├── harness-h2-deliberation-lifecycle-89fc499.json
  │   │   │   ├── harness-h2-deliberation-lifecycle-ae02d6b.json
  │   │   │   ├── harness-h2-runtime-r2-live-d50f609-20260731.json
  │   │   │   ├── harness-h3-independent-product-1577610.json
  │   │   │   ├── harness-h4-stress-ce7e861.json
  │   │   │   ├── harness-ha5-structured-completion-d7d5417.json
  │   │   │   ├── harness-i0-source-integration-0ec4f1b.json
  │   │   │   ├── harness-no-progress-conclusion-ownership-8170e65.json
  │   │   │   ├── harness-no-vpn-tool-continuity-49a3882.json
  │   │   │   ├── harness-pc11-working-view-ea38f34.json
  │   │   │   ├── harness-pc110-caller-cognition-ingress-b640f2d.json
  │   │   │   ├── harness-pc111-interaction-durable-promotion-9e6f7dd.json
  │   │   │   ├── harness-pc112-durable-cognition-supersession-425373c.json
  │   │   │   ├── harness-pc12a-privacy-authority-a8a6a2f.json
  │   │   │   ├── harness-pc12b-multiturn-working-view-fd13fab.json
  │   │   │   ├── harness-pc13-agent-owned-working-set-fa23bfc.json
  │   │   │   ├── harness-pc14-discovery-selection-55cfe64.json
  │   │   │   ├── harness-pc15-epistemic-control-9e65feb.json
  │   │   │   ├── harness-pc16-cross-process-tool-exchange-253f792.json
  │   │   │   ├── harness-pc17-durable-knowledge-promotion-5a0530a.json
  │   │   │   ├── harness-pc18-historical-cognition-recall-fceb781.json
  │   │   │   ├── harness-pc19-cognition-transition-progress-8b0f025.json
  │   │   │   ├── harness-post-skills-extraction-python-3.14.7-20260921.json
  │   │   │   ├── harness-python-3.14.7-upgrade-20260921.json
  │   │   │   ├── harness-r0-cognition-product-composition-debb576.json
  │   │   │   ├── harness-r1-single-capability-truth-716cc4b.json
  │   │   │   ├── harness-r2-proven-kernel-extraction-a983c1a.json
  │   │   │   ├── harness-r2-three-kernel-lineage-badae55.json
  │   │   │   ├── harness-r3-static-composition-admission-4e9d4b9.json
  │   │   │   ├── harness-r3-supported-agent-surface-fe6fc1a.json
  │   │   │   ├── harness-replacement-h5-live-76420e4-20260731.json
  │   │   │   ├── harness-rsi-p0-agent-owned-multi-attempt-ae02d6b.json
  │   │   │   ├── harness-rsi-p1-live-multi-attempt-6c0defb.json
  │   │   │   ├── harness-rsi-p2-self-modification-5360130.json
  │   │   │   ├── harness-rsi-p3-recursive-improvement-aea4ec1.json
  │   │   │   ├── harness-rsi-p4-capability-composition-9032d0f.json
  │   │   │   ├── harness-rsi-p5-final-acceptance-89fc499.json
  │   │   │   ├── harness-rsi-p5-high-information-discovery-999d753.json
  │   │   │   ├── harness-source-reconciliation-structured-observation-v1.json
  │   │   │   ├── harness-unreachable-abandonment-retirement-v1.json
  │   │   │   ├── hermes-acp-h4-live-3d9a559-20260731.json
  │   │   │   ├── hho-p0-fault-matrix-50cb9b5.json
  │   │   │   ├── hho-p0-local-host-compat-73f7150.json
  │   │   │   ├── hho-p0-production-preflight-43d7820.json
  │   │   │   ├── hho-p0-release-h2-f7e03aa.json
  │   │   │   ├── hho-p0-scale-1000x100-50cb9b5.json
  │   │   │   ├── hho-p0-scale-1000x100-73f7150.json
  │   │   │   ├── hho-p0-scale-1000x100-f7e03aa.json
  │   │   │   ├── index.json
  │   │   │   ├── lsp-r7-clangd-runtime-patch-20260914.json
  │   │   │   ├── lsp-r7-lifecycle-faults-20260914.json
  │   │   │   ├── lsp-r7-lsp-client-lifecycle-20260914.json
  │   │   │   ├── lsp-r7-taplo-runtime-patch-20260914.json
  │   │   │   ├── observation-exporter-e3cb34b.json
  │   │   │   ├── ordivon-harness-oh3-deepseek-live-20260801.json
  │   │   │   ├── ordivon-harness-oh4-deepseek-live-20260801.json
  │   │   │   ├── ordivon-harness-oh5-recovery-live-20260801.json
  │   │   │   ├── repository-repair-conclusion-gate-b23d5fa.json
  │   │   │   ├── repository-repair-edit-runtime-bridge-dd50136.json
  │   │   │   ├── repository-repair-edit-runtime-bridge-e625671.json
  │   │   │   ├── repository-repair-runtime-bridge-7664240.json
  │   │   │   └── ts11-tool-surface-ablation.json
  │   │   ├── fixtures
  │   │   │   ├── harness-edit-addressing-repeated-v1
  │   │   │   │   ├── feature_flags.py
  │   │   │   │   ├── SPEC.md
  │   │   │   │   └── test_feature_flags.py
  │   │   │   ├── harness-edit-multiregion-v1
  │   │   │   │   ├── pipeline.py
  │   │   │   │   ├── SPEC.md
  │   │   │   │   └── test_pipeline.py
  │   │   │   └── harness-replacement-repository-repair-v1
  │   │   │       ├── artifacts
  │   │   │       │   └── .gitkeep
  │   │   │       ├── allocation.py
  │   │   │       ├── SPEC.md
  │   │   │       └── test_allocation.py
  │   │   ├── formal
  │   │   │   ├── ConversationBindingCutoverR1.admission-probe.cfg
  │   │   │   ├── ConversationBindingCutoverR1.cfg
  │   │   │   ├── ConversationBindingCutoverR1.growth-probe.cfg
  │   │   │   ├── ConversationBindingCutoverR1.interrupted-probe.cfg
  │   │   │   ├── ConversationBindingCutoverR1.tla
  │   │   │   ├── ProviderClaimR1.ack-probe.cfg
  │   │   │   ├── ProviderClaimR1.cfg
  │   │   │   ├── ProviderClaimR1.delivery-probe.cfg
  │   │   │   ├── ProviderClaimR1.expiry-probe.cfg
  │   │   │   ├── ProviderClaimR1.privacy-fresh-probe.cfg
  │   │   │   ├── ProviderClaimR1.privacy-redacted-probe.cfg
  │   │   │   ├── ProviderClaimR1.tla
  │   │   │   └── README.md
  │   │   ├── planning
  │   │   │   ├── browser-capability-router-r1.json
  │   │   │   ├── HARNESS_AGENT_TASK_REFINEMENT_SPEC_R1.md
  │   │   │   ├── human-handoff-lego-r1.json
  │   │   │   └── lego-plan-r1.json
  │   │   ├── research
  │   │   │   ├── authority
  │   │   │   │   ├── publications
  │   │   │   │   │   └── 7fa847df5d74a23380b3fa830cf7996382bbdc3f0c29533015588c2b780ab333.json
  │   │   │   │   └── CURRENT.json
  │   │   │   ├── experiments
  │   │   │   │   ├── browser-security-r3
  │   │   │   │   │   └── neutral_differential.py
  │   │   │   │   ├── browser-security-r4
  │   │   │   │   │   └── cf07_metadata_snapshot.py
  │   │   │   │   ├── browser-security-r5
  │   │   │   │   │   └── container_direct_differential.py
  │   │   │   │   ├── browser-security-r7
  │   │   │   │   │   └── launcher_default_ablation.py
  │   │   │   │   ├── browser-security-r8
  │   │   │   │   │   └── fresh_service_attribution.py
  │   │   │   │   ├── browser-security-r9
  │   │   │   │   │   └── window_placement_attribution.py
  │   │   │   │   ├── browser_ax_projection_v1.py
  │   │   │   │   ├── browser_decision_duel_analysis_r1.py
  │   │   │   │   ├── browser_decision_provider_eval_r1.py
  │   │   │   │   ├── build_browser_decision_corpus_r1.py
  │   │   │   │   ├── campaign3_rich_effect_owner_v1.py
  │   │   │   │   ├── campaign4_rebuttal_direct_v1.py
  │   │   │   │   ├── campaign5_provider_route_preservation_v1.py
  │   │   │   │   ├── claim_standing_e5_v2.py
  │   │   │   │   ├── for_direct_federation_v1.py
  │   │   │   │   ├── harness_temporal_needs_input_pilot.py
  │   │   │   │   └── harness_temporal_needs_input_segment.py
  │   │   │   ├── fixtures
  │   │   │   │   ├── browser_ax_cross_origin_child.html
  │   │   │   │   ├── browser_ax_generalization_r1.html
  │   │   │   │   └── research-fresh-agent-corpus-r1.json
  │   │   │   ├── 00-OWNER-BOUNDARY.md
  │   │   │   ├── 05-PROJECT-CONSTITUTION-V1.md
  │   │   │   ├── 10-FOUNDATION-FAMILIES.md
  │   │   │   ├── 100-CAMPAIGN3-OPERATIONAL-EFFECT-STANDING-CHARTER-V1.md
  │   │   │   ├── 101-CAMPAIGN3-ROUND1-CONCEPTUAL-DESTRUCTIVE-RECONSTRUCTION.md
  │   │   │   ├── 102-CAMPAIGN3-ROUND2-ENGINEERING-DOGFOOD-CONTRACT.md
  │   │   │   ├── 103-CAMPAIGN3-ROUND2-ENGINEERING-DOGFOOD-RESULT.md
  │   │   │   ├── 104-CAMPAIGN3-ROUND3-BOUNDARY-AUDIT-AND-CLOSEOUT.md
  │   │   │   ├── 106-CAMPAIGN4-OPERATIONAL-ACCOUNTABILITY-CHARTER-V1.md
  │   │   │   ├── 107-CAMPAIGN4-ROUND1-CONCEPTUAL-DESTRUCTIVE-RECONSTRUCTION.md
  │   │   │   ├── 108-CAMPAIGN4-ROUND2-ENGINEERING-DOGFOOD-CONTRACT.md
  │   │   │   ├── 109-CAMPAIGN4-ROUND2-ENGINEERING-DOGFOOD-RESULT.md
  │   │   │   ├── 110-CAMPAIGN4-ROUND3-BOUNDARY-AUDIT-AND-CLOSEOUT.md
  │   │   │   ├── 112-CAMPAIGN5-BOUNDARY-RECONFIGURATION-CHARTER-V1.md
  │   │   │   ├── 113-CAMPAIGN5-ROUND1-CONCEPTUAL-DESTRUCTIVE-RECONSTRUCTION.md
  │   │   │   ├── 114-CAMPAIGN5-ROUND2-ENGINEERING-DOGFOOD-CONTRACT.md
  │   │   │   ├── 115-CAMPAIGN5-ROUND2-ENGINEERING-DOGFOOD-RESULT.md
  │   │   │   ├── 116-CAMPAIGN5-ROUND3-BOUNDARY-AUDIT-AND-CLOSEOUT.md
  │   │   │   ├── 118-CAMPAIGN6-FEDERATED-OPERATIONAL-IDENTITY-CHARTER-V1.md
  │   │   │   ├── 119-CAMPAIGN6-ROUND1-CONCEPTUAL-DESTRUCTIVE-RECONSTRUCTION.md
  │   │   │   ├── 120-CAMPAIGN6-ROUND2-ADJACENT-ENGINEERING-DOGFOOD-CONTRACT.md
  │   │   │   ├── 121-CAMPAIGN6-ROUND2-ADJACENT-ENGINEERING-DOGFOOD-RESULT.md
  │   │   │   ├── 122-CAMPAIGN6-ROUND3-BOUNDARY-AUDIT-AND-CLOSEOUT.md
  │   │   │   ├── 124-FOR-DIRECT-DOGFOOD-V1-EXPERIMENT-CONTRACT.md
  │   │   │   ├── 125-FOR-DIRECT-DOGFOOD-V1-RESULT-AND-CLOSEOUT.md
  │   │   │   ├── 127-OPERATIONAL-CLAIM-STANDING-V0-CHARTER.md
  │   │   │   ├── 128-OPERATIONAL-CLAIM-STANDING-V0-DESTRUCTIVE-ANALYSIS.md
  │   │   │   ├── 129-OPERATIONAL-CLAIM-STANDING-V0-REFERENCE-CONTRACT.md
  │   │   │   ├── 130-OPERATIONAL-CLAIM-STANDING-V0-BOUNDARY-AUDIT-AND-CLOSEOUT.md
  │   │   │   ├── 132-CLAIM-STANDING-MINIMAL-MATERIALIZATION-V1-ACCEPTANCE-CONTRACT.md
  │   │   │   ├── 133-CLAIM-STANDING-MINIMAL-MATERIALIZATION-V1-E5V2-RESULT-AND-CLOSEOUT.md
  │   │   │   ├── 135-CAMPAIGN4-COUNTEREVIDENCE-REBUTTAL-DIRECT-DOGFOOD-V1-CONTRACT.md
  │   │   │   ├── 136-CAMPAIGN4-COUNTEREVIDENCE-REBUTTAL-DIRECT-DOGFOOD-V1-RESULT-AND-CLOSEOUT.md
  │   │   │   ├── 137-TYPED-FRONTIER-TOURNAMENT-V2.md
  │   │   │   ├── 138-CAMPAIGN3-REAL-RICH-EFFECT-OWNER-DOGFOOD-V1-CONTRACT.md
  │   │   │   ├── 139-CAMPAIGN3-REAL-RICH-EFFECT-OWNER-DOGFOOD-V1-RESULT-AND-CLOSEOUT.md
  │   │   │   ├── 140-POST-RICH-EFFECT-TYPED-FRONTIER-TOURNAMENT-V1.md
  │   │   │   ├── 141-CAMPAIGN5-PROVIDER-ROUTE-PRESERVATION-DIRECT-DOGFOOD-V1-CONTRACT.md
  │   │   │   ├── 142-CAMPAIGN5-PROVIDER-ROUTE-PRESERVATION-DIRECT-DOGFOOD-V1-RESULT-AND-CLOSEOUT.md
  │   │   │   ├── 143-POST-PROVIDER-ROUTE-TYPED-FRONTIER-TOURNAMENT-V1.md
  │   │   │   ├── 144-CURRENT-NO-TOOL-CONCLUSION-CONTROL-REGRESSION-REPAIR-V1-CONTRACT.md
  │   │   │   ├── 145-CURRENT-NO-TOOL-CONCLUSION-CONTROL-REGRESSION-REPAIR-V1-RESULT-AND-CLOSEOUT.md
  │   │   │   ├── 146-POST-NO-TOOL-REPAIR-TYPED-FRONTIER-TOURNAMENT-V1.md
  │   │   │   ├── 147-EVIDENCE-INDEX-TYPED-INGESTION-CURRENTNESS-REPAIR-V1-CONTRACT.md
  │   │   │   ├── 148-EVIDENCE-INDEX-TYPED-INGESTION-CURRENTNESS-REPAIR-V1-RESULT-AND-CLOSEOUT.md
  │   │   │   ├── 149-POST-EVIDENCE-REPAIR-TYPED-FRONTIER-TOURNAMENT-V1.md
  │   │   │   ├── 15-RESEARCH-PROGRAMME-MAP-V1.md
  │   │   │   ├── 150-WHEEL-PUBLIC-API-CONTRACT-CURRENTNESS-REPAIR-V1-CONTRACT.md
  │   │   │   ├── 151-WHEEL-PUBLIC-API-CONTRACT-CURRENTNESS-REPAIR-V1-RESULT-AND-CLOSEOUT.md
  │   │   │   ├── 152-POST-WHEEL-REPAIR-TYPED-FRONTIER-TOURNAMENT-V1.md
  │   │   │   ├── 153-FRESH-AGENT-CAPABILITY-CURRENTNESS-ABLATION-V1-V2-RESULT-AND-CLOSEOUT.md
  │   │   │   ├── 153-PROVIDER-FIRST-HTTPX-TRANSPORT-CURRENT-REVALIDATION-V1-RESULT-AND-CLOSEOUT.md
  │   │   │   ├── 154-POST-HTTPX-EVIDENCE-CURRENTNESS-REPAIR-V1-CONTRACT.md
  │   │   │   ├── 155-POST-HTTPX-EVIDENCE-CURRENTNESS-REPAIR-V1-RESULT-AND-CLOSEOUT.md
  │   │   │   ├── 156-POST-BATCH-SEARCH-EVIDENCE-CURRENTNESS-REPAIR-V1-CONTRACT.md
  │   │   │   ├── 157-POST-BATCH-SEARCH-EVIDENCE-CURRENTNESS-REPAIR-V1-RESULT-AND-CLOSEOUT.md
  │   │   │   ├── 20-OPERATIONAL-SPINE.md
  │   │   │   ├── 30-DERIVED-LAWS.md
  │   │   │   ├── 40-CROSS-OWNER-BRIDGES.md
  │   │   │   ├── 50-ENGINEERING-CONSUMPTION-MAP.md
  │   │   │   ├── 60-HAF-REGISTRY-AND-PROVENANCE.md
  │   │   │   ├── 70-HISTORY-NEGATIVE-RESULTS-AND-REPAIRS.md
  │   │   │   ├── 80-OPEN-FRONTIER-AND-REOPEN.md
  │   │   │   ├── 85-FRONTIER-AUDIT-V1.md
  │   │   │   ├── 88-CAMPAIGN1-OPERATIONAL-IDENTITY-UNDER-FAILURE-CHARTER-V1.md
  │   │   │   ├── 89-CAMPAIGN1-ROUND1-CONCEPTUAL-DESTRUCTIVE-RECONSTRUCTION.md
  │   │   │   ├── 90-CAMPAIGN1-ROUND2-ENGINEERING-DOGFOOD-CONTRACT.md
  │   │   │   ├── 91-CAMPAIGN1-ROUND2-ENGINEERING-DOGFOOD-RESULT.md
  │   │   │   ├── 92-CAMPAIGN1-ROUND3-BOUNDARY-AUDIT-AND-CLOSEOUT.md
  │   │   │   ├── 94-CAMPAIGN2-OPERATIONAL-CONTEXT-EQUIVALENCE-CHARTER-V1.md
  │   │   │   ├── 95-CAMPAIGN2-ROUND1-CONCEPTUAL-DESTRUCTIVE-RECONSTRUCTION.md
  │   │   │   ├── 96-CAMPAIGN2-ROUND2-ENGINEERING-DOGFOOD-CONTRACT.md
  │   │   │   ├── 97-CAMPAIGN2-ROUND2-ENGINEERING-DOGFOOD-RESULT.md
  │   │   │   ├── 98-CAMPAIGN2-ROUND3-BOUNDARY-AUDIT-AND-CLOSEOUT.md
  │   │   │   └── README.md
  │   │   ├── schemas
  │   │   │   └── agent-automation
  │   │   │       └── campaign-spec-v2.schema.json
  │   │   ├── scripts
  │   │   │   ├── acceptance_h0_deliberation_authority.py
  │   │   │   ├── agent_automation_browserless.py
  │   │   │   ├── agent_automation_browserless_effects.py
  │   │   │   ├── agent_automation_ledger_reconcile.py
  │   │   │   ├── agent_automation_mcp.py
  │   │   │   ├── agent_automation_mcp_deploy.py
  │   │   │   ├── agent_automation_registry.py
  │   │   │   ├── agent_automation_release.py
  │   │   │   ├── browser_benchmark_contract.py
  │   │   │   ├── browser_benchmark_prospective.py
  │   │   │   ├── browser_benchmark_route_adapter.py
  │   │   │   ├── browser_benchmark_runner.py
  │   │   │   ├── browser_benchmark_runtime_handoff.py
  │   │   │   ├── browser_capability_router.py
  │   │   │   ├── browser_security_browserless_canary.py
  │   │   │   ├── browser_security_pool_runner.py
  │   │   │   ├── browser_security_witness_source.py
  │   │   │   ├── browser_use_browserless.py
  │   │   │   ├── browserless_display_auth.py
  │   │   │   ├── browserless_human_handoff.py
  │   │   │   ├── browserless_human_interaction.py
  │   │   │   ├── browserless_idle_reaper.py
  │   │   │   ├── browserless_image_promotion.py
  │   │   │   ├── browserless_materialization_target.py
  │   │   │   ├── browserless_podman_deploy.py
  │   │   │   ├── browserless_substrate.py
  │   │   │   ├── campaign_materialization.py
  │   │   │   ├── cft_human_materialization.py
  │   │   │   ├── cft_human_session.py
  │   │   │   ├── cft_human_session_auth.py
  │   │   │   ├── cft_human_session_deploy.py
  │   │   │   ├── chatgpt_conversation_discovery.py
  │   │   │   ├── chatgpt_provider_gate.py
  │   │   │   ├── chatgpt_provider_resource.py
  │   │   │   ├── check_adaptive_edit_r2_benchmark.py
  │   │   │   ├── check_codex_app_h3_receipt.py
  │   │   │   ├── check_dependencies.py
  │   │   │   ├── check_docs.py
  │   │   │   ├── check_evidence.py
  │   │   │   ├── check_harness_replacement_h5_receipt.py
  │   │   │   ├── check_harness_without_host.py
  │   │   │   ├── check_hermes_acp_h4_receipt.py
  │   │   │   ├── check_repository_repair_edit_runtime_receipt.py
  │   │   │   ├── check_runtime_search_profile.py
  │   │   │   ├── check_wheel.py
  │   │   │   ├── configure_deepseek_api.py
  │   │   │   ├── conversation_binding_contract.py
  │   │   │   ├── conversation_relay_carrier.py
  │   │   │   ├── demo_deterministic_run.py
  │   │   │   ├── finance_current_state_application.py
  │   │   │   ├── finance_readonly_observation.py
  │   │   │   ├── harness_otel_event_sink.py
  │   │   │   ├── harness_p0_scale_acceptance.py
  │   │   │   ├── harness_replacement_h5_support.py
  │   │   │   ├── jev_active_user_launcher.ps1
  │   │   │   ├── jev_fastpath_adapter.py
  │   │   │   ├── local-acceptance
  │   │   │   ├── materialization_reconciliation_archive.py
  │   │   │   ├── mind2web_crossencoder_benchmark.py
  │   │   │   ├── mind2web_external_corpus.py
  │   │   │   ├── mind2web_laya_benchmark.py
  │   │   │   ├── mind2web_shard_census.py
  │   │   │   ├── owner-environment
  │   │   │   ├── playwright_browserless_binding_reconcile.py
  │   │   │   ├── playwright_browserless_chatgpt_submit.py
  │   │   │   ├── playwright_browserless_conversation_output.py
  │   │   │   ├── playwright_browserless_human_resume.py
  │   │   │   ├── playwright_browserless_provider_preflight.py
  │   │   │   ├── playwright_browserless_turn_once.py
  │   │   │   ├── playwright_cft_chatgpt_resume.py
  │   │   │   ├── postgres_conversation_binding.py
  │   │   │   ├── postgres_turn_effects.py
  │   │   │   ├── postgres_wake_turn_map.py
  │   │   │   ├── provider_boundary_diagnosis.py
  │   │   │   ├── run_adaptive_edit_r2_live_ab.py
  │   │   │   ├── sqlite_conversation_binding.py
  │   │   │   ├── sqlite_conversation_materializer.py
  │   │   │   ├── sqlite_wake_turn_map.py
  │   │   │   ├── standard_identifiers.py
  │   │   │   ├── system1_decision_benchmark.py
  │   │   │   ├── temporal_agent_automation.py
  │   │   │   ├── temporal_agent_automation_deploy.py
  │   │   │   ├── temporal_agent_automation_launch.py
  │   │   │   ├── temporal_agent_automation_worker.py
  │   │   │   ├── wake_turn_contract.py
  │   │   │   ├── windows_user_browser_chatgpt.ps1
  │   │   │   └── windows_user_browser_materialization_target.py
  │   │   ├── src
  │   │   │   ├── anc_canonical
  │   │   │   │   ├── __init__.py
  │   │   │   │   └── canonical.py
  │   │   │   └── ordivon_harness
  │   │   │       ├── ordivon
  │   │   │       │   ├── __init__.py
  │   │   │       │   ├── adaptive_edit_bridge.py
  │   │   │       │   ├── agent_bridge.py
  │   │   │       │   ├── cognition_admission.py
  │   │   │       │   ├── continuity_guards.py
  │   │   │       │   ├── continuity_records.py
  │   │   │       │   ├── control.py
  │   │   │       │   ├── deepseek.py
  │   │   │       │   ├── deepseek_protocol.py
  │   │   │       │   ├── events.py
  │   │   │       │   ├── loop.py
  │   │   │       │   ├── model.py
  │   │   │       │   ├── provider_lifecycle.py
  │   │   │       │   ├── provider_state_guards.py
  │   │   │       │   ├── run_continuity.py
  │   │   │       │   ├── run_contract.py
  │   │   │       │   ├── run_recovery.py
  │   │   │       │   ├── run_store_port.py
  │   │   │       │   ├── runtime_bridge.py
  │   │   │       │   ├── runtime_lowering.py
  │   │   │       │   ├── tool_bridge.py
  │   │   │       │   ├── tool_errors.py
  │   │   │       │   ├── turn_projection.py
  │   │   │       │   └── working_set_queries.py
  │   │   │       ├── __init__.py
  │   │   │       ├── adaptive_edit.py
  │   │   │       ├── agent_plugin.py
  │   │   │       ├── agent_run.py
  │   │   │       ├── agent_tool_observation.py
  │   │   │       ├── api.py
  │   │   │       ├── cli.py
  │   │   │       ├── completion.py
  │   │   │       ├── core_contracts.py
  │   │   │       ├── dap_provider_port.py
  │   │   │       ├── domain_tools.py
  │   │   │       ├── execution_binding.py
  │   │   │       ├── gateway_execution_port.py
  │   │   │       ├── independent_cli.py
  │   │   │       ├── independent_result.py
  │   │   │       ├── lsp_provider_port.py
  │   │   │       ├── lsp_workspace_edit.py
  │   │   │       ├── mcp_http_client.py
  │   │   │       ├── object_store.py
  │   │   │       ├── plugin_gateway_effect.py
  │   │   │       ├── plugin_mcp.py
  │   │   │       ├── postgres_store.py
  │   │   │       ├── protocol.py
  │   │   │       ├── run_state.py
  │   │   │       ├── runtime_port.py
  │   │   │       ├── sqlite_store.py
  │   │   │       ├── standalone.py
  │   │   │       ├── store.py
  │   │   │       ├── store_errors.py
  │   │   │       ├── structured_result_conformance.py
  │   │   │       ├── tool_program.py
  │   │   │       ├── tool_program_contract.py
  │   │   │       ├── tool_program_recovery.py
  │   │   │       ├── user_browser_gateway.py
  │   │   │       ├── version.py
  │   │   │       └── working_view.py
  │   │   ├── systemd
  │   │   │   ├── ordivon-agent-automation-mcp.service
  │   │   │   ├── ordivon-agent-temporal-worker.service
  │   │   │   ├── ordivon-browser-agent.target
  │   │   │   ├── ordivon-browserless-display@.service
  │   │   │   ├── ordivon-browserless-human-vnc@.service
  │   │   │   ├── ordivon-browserless-human-web@.service
  │   │   │   ├── ordivon-browserless-idle-reaper.service
  │   │   │   ├── ordivon-browserless-idle-reaper.timer
  │   │   │   ├── ordivon-browserless-operator-proxy@.service
  │   │   │   ├── ordivon-cft-human-browser@.service
  │   │   │   ├── ordivon-cft-human-display@.service
  │   │   │   ├── ordivon-cft-human-session@.target
  │   │   │   ├── ordivon-cft-human-vnc@.service
  │   │   │   └── ordivon-cft-human-web@.service
  │   │   ├── tests
  │   │   │   ├── fixtures
  │   │   │   │   ├── engineering_incident_browserless_20260909.json
  │   │   │   │   └── provider-call-v3-s0-frozen.json
  │   │   │   ├── conftest.py
  │   │   │   ├── pg_test_support.py
  │   │   │   ├── test_adaptive_edit.py
  │   │   │   ├── test_adaptive_edit_bridge.py
  │   │   │   ├── test_adaptive_edit_r2_benchmark.py
  │   │   │   ├── test_adaptive_edit_r2_live_ab_runner.py
  │   │   │   ├── test_agent_automation_browserless.py
  │   │   │   ├── test_agent_automation_browserless_effects.py
  │   │   │   ├── test_agent_automation_jcs_standard.py
  │   │   │   ├── test_agent_automation_ledger_reconcile.py
  │   │   │   ├── test_agent_automation_mcp.py
  │   │   │   ├── test_agent_automation_mcp_deploy.py
  │   │   │   ├── test_agent_automation_occurrence_retirement.py
  │   │   │   ├── test_agent_automation_otel_resource_identity.py
  │   │   │   ├── test_agent_automation_reconcile_surface.py
  │   │   │   ├── test_agent_automation_registry.py
  │   │   │   ├── test_agent_automation_release.py
  │   │   │   ├── test_agent_automation_release_monorepo.py
  │   │   │   ├── test_agent_automation_turn_receipt_jcs.py
  │   │   │   ├── test_agent_automation_write_authority.py
  │   │   │   ├── test_agent_plugin_composition.py
  │   │   │   ├── test_agent_plugin_harness_run.py
  │   │   │   ├── test_browser_ax_projection_v1.py
  │   │   │   ├── test_browser_benchmark_contract.py
  │   │   │   ├── test_browser_benchmark_prospective.py
  │   │   │   ├── test_browser_benchmark_route_adapter.py
  │   │   │   ├── test_browser_benchmark_runner.py
  │   │   │   ├── test_browser_benchmark_runtime_handoff.py
  │   │   │   ├── test_browser_capability_router.py
  │   │   │   ├── test_browser_decision_corpus_r1.py
  │   │   │   ├── test_browser_decision_duel_analysis_r1.py
  │   │   │   ├── test_browser_security_browserless_canary.py
  │   │   │   ├── test_browser_security_cf07_metadata_r4.py
  │   │   │   ├── test_browser_security_pool_runner.py
  │   │   │   ├── test_browser_security_r5.py
  │   │   │   ├── test_browser_security_r7.py
  │   │   │   ├── test_browser_security_r8.py
  │   │   │   ├── test_browser_security_r9.py
  │   │   │   ├── test_browser_security_witness_source.py
  │   │   │   ├── test_browser_use_browserless.py
  │   │   │   ├── test_browserless_conversation_output_contract.py
  │   │   │   ├── test_browserless_display_auth.py
  │   │   │   ├── test_browserless_human_interaction.py
  │   │   │   ├── test_browserless_idle_reaper.py
  │   │   │   ├── test_browserless_image_promotion.py
  │   │   │   ├── test_browserless_materialization_target.py
  │   │   │   ├── test_browserless_pg_required_consumer.py
  │   │   │   ├── test_browserless_podman_deploy.py
  │   │   │   ├── test_browserless_post_send_route.py
  │   │   │   ├── test_browserless_postgres_wake_selection.py
  │   │   │   ├── test_browserless_provider_preflight.py
  │   │   │   ├── test_browserless_sqlite_connection_lifetime.py
  │   │   │   ├── test_browserless_submit_clean_surface.py
  │   │   │   ├── test_browserless_submit_no_human_session.py
  │   │   │   ├── test_browserless_substrate.py
  │   │   │   ├── test_campaign_census_freshness.py
  │   │   │   ├── test_cft_human_session.py
  │   │   │   ├── test_cft_human_session_deploy.py
  │   │   │   ├── test_cft_human_session_durable.py
  │   │   │   ├── test_chatgpt_conversation_discovery.py
  │   │   │   ├── test_cli_currentness.py
  │   │   │   ├── test_codex_app_h3_receipt.py
  │   │   │   ├── test_conclusion_correction_separation.py
  │   │   │   ├── test_configure_deepseek_api.py
  │   │   │   ├── test_conversation_adopt.py
  │   │   │   ├── test_conversation_affinity.py
  │   │   │   ├── test_conversation_binding_pg_selection.py
  │   │   │   ├── test_conversation_continue_first.py
  │   │   │   ├── test_conversation_continue_transport.py
  │   │   │   ├── test_current_no_tool_conclusion_control_regression.py
  │   │   │   ├── test_dap_provider_port.py
  │   │   │   ├── test_deepseek_httpx_transport.py
  │   │   │   ├── test_deepseek_loopback_proxy.py
  │   │   │   ├── test_deepseek_mixed_turn.py
  │   │   │   ├── test_deepseek_terminal_state_contract.py
  │   │   │   ├── test_domain_tool_bridge.py
  │   │   │   ├── test_durable_human_control_api.py
  │   │   │   ├── test_durable_human_materialization.py
  │   │   │   ├── test_durable_human_temporal_wait.py
  │   │   │   ├── test_eval_harness_document_retirement_004.py
  │   │   │   ├── test_eval_harness_edit_addressing_002.py
  │   │   │   ├── test_eval_harness_edit_multiregion_003.py
  │   │   │   ├── test_eval_harness_repository_repair_001.py
  │   │   │   ├── test_evidence_index_typed_ingestion.py
  │   │   │   ├── test_finance_current_state_application.py
  │   │   │   ├── test_finance_owner_uv_selection_contract.py
  │   │   │   ├── test_finance_readonly_observation.py
  │   │   │   ├── test_gateway_execution_port.py
  │   │   │   ├── test_h0_deliberation_authority.py
  │   │   │   ├── test_harness_otel_event_sink.py
  │   │   │   ├── test_harness_replacement_h5.py
  │   │   │   ├── test_harness_replacement_h5_receipt.py
  │   │   │   ├── test_hermes_acp_h4_receipt.py
  │   │   │   ├── test_independent_proposal_claim_binding.py
  │   │   │   ├── test_independent_receipt_type_refinement.py
  │   │   │   ├── test_jev_fastpath_adapter.py
  │   │   │   ├── test_lsp_provider_port.py
  │   │   │   ├── test_lsp_workspace_edit.py
  │   │   │   ├── test_materialization_reconciliation_archive.py
  │   │   │   ├── test_mcp_http_client.py
  │   │   │   ├── test_mcp_python315_release_contract.py
  │   │   │   ├── test_observation_gate_and_port.py
  │   │   │   ├── test_owner_environment_doctor_contract.py
  │   │   │   ├── test_p0_composition_projection.py
  │   │   │   ├── test_p0_continuity_records.py
  │   │   │   ├── test_p0_core_contracts.py
  │   │   │   ├── test_p0_core_package_boundary.py
  │   │   │   ├── test_p0_execution_binding.py
  │   │   │   ├── test_p0_run_store_port.py
  │   │   │   ├── test_p0_scale_acceptance.py
  │   │   │   ├── test_p0_sqlite_agent_loop.py
  │   │   │   ├── test_p0_sqlite_provider_store.py
  │   │   │   ├── test_p0_sqlite_runtime_bridge.py
  │   │   │   ├── test_p0_sqlite_store.py
  │   │   │   ├── test_p0_sqlite_tool_store.py
  │   │   │   ├── test_p0_standalone_runner.py
  │   │   │   ├── test_p1_procedural_capital.py
  │   │   │   ├── test_p2_tool_program.py
  │   │   │   ├── test_p2_tool_program_provider_loop.py
  │   │   │   ├── test_p2_tool_program_recovery.py
  │   │   │   ├── test_pc110_caller_cognition_ingress.py
  │   │   │   ├── test_pc111_interaction_durable_promotion.py
  │   │   │   ├── test_pc112_durable_cognition_supersession.py
  │   │   │   ├── test_pc12_privacy_authority.py
  │   │   │   ├── test_pc12b_multiturn_projection.py
  │   │   │   ├── test_pc13_agent_owned_working_set.py
  │   │   │   ├── test_pc14_candidate_discovery_overlay.py
  │   │   │   ├── test_pc15_epistemic_control.py
  │   │   │   ├── test_pc16_cross_process_tool_exchange.py
  │   │   │   ├── test_pc17_durable_knowledge_promotion.py
  │   │   │   ├── test_pc18_historical_cognition_recall.py
  │   │   │   ├── test_pc19_cognition_transition_progress.py
  │   │   │   ├── test_pc1_working_view.py
  │   │   │   ├── test_pg_binding_cutover_formal_gate.py
  │   │   │   ├── test_plugin_gateway_effect.py
  │   │   │   ├── test_postgres_cli.py
  │   │   │   ├── test_postgres_conversation_binding.py
  │   │   │   ├── test_postgres_harness_store.py
  │   │   │   ├── test_postgres_turn_effects.py
  │   │   │   ├── test_postgres_wake_turn_map.py
  │   │   │   ├── test_provider_boundary_diagnosis.py
  │   │   │   ├── test_provider_call_protocol.py
  │   │   │   ├── test_provider_claim_formal_gate.py
  │   │   │   ├── test_provider_effect_policy_convergence.py
  │   │   │   ├── test_provider_recovery_signal_fence_p1.py
  │   │   │   ├── test_public_api.py
  │   │   │   ├── test_r0_cognition_product_composition.py
  │   │   │   ├── test_r1_single_capability_truth.py
  │   │   │   ├── test_r2_cognition_admission_kernel.py
  │   │   │   ├── test_r2_provider_lifecycle_port.py
  │   │   │   ├── test_r2_turn_projection_kernel.py
  │   │   │   ├── test_r3_supported_agent_run.py
  │   │   │   ├── test_repository_boundary.py
  │   │   │   ├── test_repository_repair_edit_runtime_receipt.py
  │   │   │   ├── test_research_fresh_agent_corpus_r1.py
  │   │   │   ├── test_research_owner_publication.py
  │   │   │   ├── test_runtime_python_compatibility_currentness.py
  │   │   │   ├── test_runtime_task_cursor_refinement_cegar.py
  │   │   │   ├── test_search_workspace_batch.py
  │   │   │   ├── test_security_owner_locator.py
  │   │   │   ├── test_sqlite_connection_context_law.py
  │   │   │   ├── test_sqlite_conversation_binding.py
  │   │   │   ├── test_sqlite_materializer_transaction_guard.py
  │   │   │   ├── test_sqlite_wake_turn_map.py
  │   │   │   ├── test_structured_completion.py
  │   │   │   ├── test_structured_no_progress_completion.py
  │   │   │   ├── test_structured_result_carrier.py
  │   │   │   ├── test_structured_result_conformance.py
  │   │   │   ├── test_system1_decision_benchmark.py
  │   │   │   ├── test_temporal_agent_automation_contract.py
  │   │   │   ├── test_temporal_agent_automation_deploy.py
  │   │   │   ├── test_temporal_latest_runtime_contract.py
  │   │   │   ├── test_tool_observation_evidence_seal.py
  │   │   │   ├── test_trace_type_refinement.py
  │   │   │   ├── test_turn_evidence_transition.py
  │   │   │   ├── test_user_browser_gateway_controller.py
  │   │   │   ├── test_user_browser_gateway_receipt_ambiguity.py
  │   │   │   ├── test_wheel_public_api_contract.py
  │   │   │   ├── test_wheel_python_baseline.py
  │   │   │   └── test_windows_user_browser_materialization_target.py
  │   │   ├── .gitignore
  │   │   ├── .python-version
  │   │   ├── ARCHITECTURE.md
  │   │   ├── CHANGELOG.md
  │   │   ├── CONTRIBUTING.md
  │   │   ├── LICENSE
  │   │   ├── mise.toml
  │   │   ├── pyproject.toml
  │   │   ├── README.md
  │   │   ├── SECURITY.md
  │   │   └── uv.lock
  │   ├── host
  │   │   ├── docs
  │   │   │   ├── HOST_OWNER_GUIDE.md
  │   │   │   ├── HOST_R21_AGENT_EXECUTION_PLAN.md
  │   │   │   ├── HOST_R21_AGENT_EXECUTION_SPEC.md
  │   │   │   ├── SOCIAL_WORK_FABRIC_R1.md
  │   │   │   ├── SOCIAL_WORK_FABRIC_R2_IMPLEMENTATION.md
  │   │   │   └── SOCIAL_WORK_FABRIC_R2_SPEC.md
  │   │   ├── formal
  │   │   │   ├── HostUnicodeGram.lean
  │   │   │   ├── HostWorkDAG.lean
  │   │   │   └── work_graph_dag.py
  │   │   ├── migrations
  │   │   │   ├── versions
  │   │   │   │   ├── 0001_host_v2_core.py
  │   │   │   │   ├── 0002_concurrent_idempotency_claim.py
  │   │   │   │   ├── 0003_product_surfaces.py
  │   │   │   │   ├── 0004_r6_cleanup.py
  │   │   │   │   ├── 0005_explicit_board_task_route.py
  │   │   │   │   ├── 0006_social_work_fabric_work_graph.py
  │   │   │   │   ├── 0007_social_work_fabric_social_graph.py
  │   │   │   │   ├── 0008_social_work_fabric_attention.py
  │   │   │   │   ├── 0009_retire_legacy_task_board.py
  │   │   │   │   ├── 0010_social_work_fabric_r2.py
  │   │   │   │   ├── 0011_retire_external_news.py
  │   │   │   │   ├── 0012_message_literal_trigram.py
  │   │   │   │   └── 0013_unicode_substring_gin.py
  │   │   │   ├── env.py
  │   │   │   └── script.py.mako
  │   │   ├── packaging
  │   │   │   ├── systemd
  │   │   │   │   ├── host-v2.env.example
  │   │   │   │   └── ordivon-host-v2.service
  │   │   │   ├── install_release.sh
  │   │   │   └── verify_tool_surface.py
  │   │   ├── planning
  │   │   │   ├── host-friction-observatory-r1.json
  │   │   │   ├── lego-plan-r1.json
  │   │   │   ├── lego-plan-r3.json
  │   │   │   └── social-work-fabric-r1.json
  │   │   ├── src
  │   │   │   └── ordivon_host_v2
  │   │   │       ├── __init__.py
  │   │   │       ├── attention_projections.py
  │   │   │       ├── attention_sql.py
  │   │   │       ├── attention_store.py
  │   │   │       ├── canonical_json.py
  │   │   │       ├── collaboration_inputs.py
  │   │   │       ├── collection_pagination.py
  │   │   │       ├── command_receipts.py
  │   │   │       ├── contracts.py
  │   │   │       ├── coordination_inputs.py
  │   │   │       ├── coordination_intent_commands.py
  │   │   │       ├── errors.py
  │   │   │       ├── mcp_attention_tools.py
  │   │   │       ├── mcp_domain_errors.py
  │   │   │       ├── mcp_server.py
  │   │   │       ├── mcp_social_tools.py
  │   │   │       ├── mcp_tool_registration.py
  │   │   │       ├── mcp_work_tools.py
  │   │   │       ├── native_pool_observability.py
  │   │   │       ├── postgres_bounds.py
  │   │   │       ├── postgres_connections.py
  │   │   │       ├── py.typed
  │   │   │       ├── service.py
  │   │   │       ├── social_contracts.py
  │   │   │       ├── social_errors.py
  │   │   │       ├── social_message_commands.py
  │   │   │       ├── social_message_queries.py
  │   │   │       ├── social_read_queries.py
  │   │   │       ├── social_space_commands.py
  │   │   │       ├── social_space_queries.py
  │   │   │       ├── social_store.py
  │   │   │       ├── social_topic_commands.py
  │   │   │       ├── social_topic_queries.py
  │   │   │       ├── work_inputs.py
  │   │   │       ├── work_queries.py
  │   │   │       ├── work_relation_commands.py
  │   │   │       └── work_store.py
  │   │   ├── tests
  │   │   │   ├── conftest.py
  │   │   │   ├── test_attention_query_boundary.py
  │   │   │   ├── test_attention_single_snapshot_postgres.py
  │   │   │   ├── test_canonical_json_property.py
  │   │   │   ├── test_clean_room.py
  │   │   │   ├── test_contract_policy.py
  │   │   │   ├── test_host_db_preflight_contract.py
  │   │   │   ├── test_host_focused_default.py
  │   │   │   ├── test_host_history_doctor_postgres.py
  │   │   │   ├── test_host_queue_qualification.py
  │   │   │   ├── test_mcp_domain_errors.py
  │   │   │   ├── test_mcp_native_pool_stats.py
  │   │   │   ├── test_mcp_surface.py
  │   │   │   ├── test_mcp_surface_identity.py
  │   │   │   ├── test_message_get_contract.py
  │   │   │   ├── test_native_pool_postgres.py
  │   │   │   ├── test_release_packaging.py
  │   │   │   ├── test_schema_diagnostic.py
  │   │   │   ├── test_social_creation_linearizability.py
  │   │   │   ├── test_social_message_digest_postgres.py
  │   │   │   ├── test_social_message_read_integrity.py
  │   │   │   ├── test_social_query_boundary.py
  │   │   │   ├── test_social_store_exact_integer_contract.py
  │   │   │   ├── test_social_timestamp_strict_bigint.py
  │   │   │   ├── test_social_work_fabric_architecture.py
  │   │   │   ├── test_social_work_fabric_attention.py
  │   │   │   ├── test_social_work_fabric_postgres.py
  │   │   │   ├── test_social_work_fabric_retirement.py
  │   │   │   ├── test_social_work_fabric_social_graph.py
  │   │   │   ├── test_social_work_fabric_social_store.py
  │   │   │   ├── test_social_work_fabric_society.py
  │   │   │   ├── test_social_work_fabric_work_graph.py
  │   │   │   ├── test_systemd_liveness_contract.py
  │   │   │   ├── test_tool_surface_release_contract.py
  │   │   │   ├── test_topic_state_lifecycle_postgres.py
  │   │   │   ├── test_work_query_boundary.py
  │   │   │   ├── test_work_relation_three_node_oracle.py
  │   │   │   └── test_work_snapshot_read_refinement.py
  │   │   ├── tools
  │   │   │   └── host_queue_verify.sh
  │   │   ├── .gitignore
  │   │   ├── .python-version
  │   │   ├── AGENTS.md
  │   │   ├── alembic.ini
  │   │   ├── mcp-surface.json
  │   │   ├── mise.toml
  │   │   ├── pyproject.toml
  │   │   ├── README.md
  │   │   └── uv.lock
  │   └── runtime
  │       ├── .config
  │       │   └── nextest.toml
  │       ├── .github
  │       │   ├── ISSUE_TEMPLATE
  │       │   │   ├── bug_report.yml
  │       │   │   ├── config.yml
  │       │   │   └── feature_request.yml
  │       │   ├── workflows
  │       │   │   └── release-acceptance.yml
  │       │   ├── actionlint.yaml
  │       │   ├── CODEOWNERS
  │       │   └── pull_request_template.md
  │       ├── .ordivon
  │       │   ├── project.yaml
  │       │   ├── publication.yaml
  │       │   └── rights.yaml
  │       ├── crates
  │       │   ├── ordivon-runtime-core
  │       │   │   ├── migrations
  │       │   │   │   └── runtime
  │       │   │   │       ├── 0001_runtime.sql
  │       │   │   │       ├── 0002_orphan_recovery.sql
  │       │   │   │       ├── 0003_terminal_repair.sql
  │       │   │   │       ├── 0004_orphan_reclaim.sql
  │       │   │   │       ├── 0005_condition_retirement.sql
  │       │   │   │       └── 0006_workspace_patch_retirement.sql
  │       │   │   ├── sql
  │       │   │   │   └── pg_fresh_epoch.sql
  │       │   │   ├── src
  │       │   │   │   ├── bin
  │       │   │   │   │   ├── ordivon-runtime-doctor.rs
  │       │   │   │   │   ├── ordivon-runtime-inspect.rs
  │       │   │   │   │   ├── ordivon-runtime-job-fixture.rs
  │       │   │   │   │   ├── ordivon-runtime-repair.rs
  │       │   │   │   │   ├── ordivon-runtime-runner.rs
  │       │   │   │   │   └── ordivon-runtime-windows-deploy.rs
  │       │   │   │   ├── runtime
  │       │   │   │   │   ├── engine
  │       │   │   │   │   │   ├── admission.rs
  │       │   │   │   │   │   ├── admission_validation.rs
  │       │   │   │   │   │   ├── artifact_projection.rs
  │       │   │   │   │   │   ├── construction.rs
  │       │   │   │   │   │   ├── execution.rs
  │       │   │   │   │   │   ├── execution_environment.rs
  │       │   │   │   │   │   ├── execution_preparation.rs
  │       │   │   │   │   │   ├── input_bindings.rs
  │       │   │   │   │   │   ├── job_activity_evidence.rs
  │       │   │   │   │   │   ├── job_control.rs
  │       │   │   │   │   │   ├── launch_identity.rs
  │       │   │   │   │   │   ├── observation_projection.rs
  │       │   │   │   │   │   ├── orphan_recovery.rs
  │       │   │   │   │   │   ├── output.rs
  │       │   │   │   │   │   ├── prepared_binding_recovery.rs
  │       │   │   │   │   │   ├── provider_commitments.rs
  │       │   │   │   │   │   ├── reconciliation.rs
  │       │   │   │   │   │   ├── release.rs
  │       │   │   │   │   │   ├── terminal_commit.rs
  │       │   │   │   │   │   ├── terminal_evidence.rs
  │       │   │   │   │   │   ├── workspace.rs
  │       │   │   │   │   │   └── workspace_evidence.rs
  │       │   │   │   │   ├── error
  │       │   │   │   │   │   ├── sqlite.rs
  │       │   │   │   │   │   └── universal.rs
  │       │   │   │   │   ├── inspection
  │       │   │   │   │   │   ├── operator
  │       │   │   │   │   │   │   └── archive.rs
  │       │   │   │   │   │   ├── job.rs
  │       │   │   │   │   │   ├── operator.rs
  │       │   │   │   │   │   └── summary_query_tests.rs
  │       │   │   │   │   ├── pg_runtime
  │       │   │   │   │   │   ├── artifact.rs
  │       │   │   │   │   │   ├── job.rs
  │       │   │   │   │   │   ├── native_stop.rs
  │       │   │   │   │   │   ├── node_query.rs
  │       │   │   │   │   │   ├── reconciliation.rs
  │       │   │   │   │   │   ├── release.rs
  │       │   │   │   │   │   ├── scheduling.rs
  │       │   │   │   │   │   └── workspace.rs
  │       │   │   │   │   ├── platform
  │       │   │   │   │   │   ├── linux.rs
  │       │   │   │   │   │   └── mod.rs
  │       │   │   │   │   ├── registry
  │       │   │   │   │   │   ├── admission.rs
  │       │   │   │   │   │   ├── lifecycle.rs
  │       │   │   │   │   │   ├── query.rs
  │       │   │   │   │   │   ├── reconciliation.rs
  │       │   │   │   │   │   ├── recovery.rs
  │       │   │   │   │   │   └── storage.rs
  │       │   │   │   │   ├── artifact_release_state.rs
  │       │   │   │   │   ├── attempt_supervisor_owner_storage.sql
  │       │   │   │   │   ├── authority_contract.rs
  │       │   │   │   │   ├── control_primitives.rs
  │       │   │   │   │   ├── doctor.rs
  │       │   │   │   │   ├── engine.rs
  │       │   │   │   │   ├── error.rs
  │       │   │   │   │   ├── evidence.rs
  │       │   │   │   │   ├── execution_provider.rs
  │       │   │   │   │   ├── execution_provider_storage.sql
  │       │   │   │   │   ├── host_dependency.rs
  │       │   │   │   │   ├── host_dependency_storage.sql
  │       │   │   │   │   ├── inspection.rs
  │       │   │   │   │   ├── integration_tests.rs
  │       │   │   │   │   ├── job_attempt_state.rs
  │       │   │   │   │   ├── lifecycle_locks.rs
  │       │   │   │   │   ├── mod.rs
  │       │   │   │   │   ├── operation_circuit.rs
  │       │   │   │   │   ├── pg_runtime.rs
  │       │   │   │   │   ├── registry.rs
  │       │   │   │   │   ├── registry_storage.rs
  │       │   │   │   │   ├── repair.rs
  │       │   │   │   │   ├── reservation_state.rs
  │       │   │   │   │   ├── runtime_release_storage.sql
  │       │   │   │   │   ├── supervisor.rs
  │       │   │   │   │   ├── tests.rs
  │       │   │   │   │   ├── types.rs
  │       │   │   │   │   ├── windows.rs
  │       │   │   │   │   ├── windows_broker.rs
  │       │   │   │   │   └── workspace_state.rs
  │       │   │   │   ├── universal
  │       │   │   │   │   ├── workspace
  │       │   │   │   │   │   ├── changes.rs
  │       │   │   │   │   │   ├── close_recovery.rs
  │       │   │   │   │   │   ├── file_io.rs
  │       │   │   │   │   │   ├── paths_git.rs
  │       │   │   │   │   │   ├── records.rs
  │       │   │   │   │   │   └── source_state.rs
  │       │   │   │   │   ├── config.rs
  │       │   │   │   │   ├── error.rs
  │       │   │   │   │   ├── fsutil.rs
  │       │   │   │   │   ├── mod.rs
  │       │   │   │   │   ├── mutation.rs
  │       │   │   │   │   ├── projection.rs
  │       │   │   │   │   ├── resource_receipt.rs
  │       │   │   │   │   ├── runner.rs
  │       │   │   │   │   ├── tests.rs
  │       │   │   │   │   ├── types.rs
  │       │   │   │   │   └── workspace.rs
  │       │   │   │   ├── lib.rs
  │       │   │   │   ├── pg_admission.rs
  │       │   │   │   ├── pg_dispatch.rs
  │       │   │   │   ├── pg_readback.rs
  │       │   │   │   ├── resource_fit.rs
  │       │   │   │   ├── resource_scheduling.rs
  │       │   │   │   └── windows_security.rs
  │       │   │   ├── tests
  │       │   │   │   ├── platform_owner_boundary.rs
  │       │   │   │   ├── sqlite_unsigned_contract.rs
  │       │   │   │   └── systemd_supervisor.rs
  │       │   │   └── Cargo.toml
  │       │   └── ordivon-runtime-mcp
  │       │       ├── src
  │       │       │   ├── server
  │       │       │   │   ├── tests
  │       │       │   │   │   ├── projection_contract.rs
  │       │       │   │   │   ├── stage_trace.rs
  │       │       │   │   │   └── tool_catalog.rs
  │       │       │   │   ├── contract.rs
  │       │       │   │   ├── execution_binding.rs
  │       │       │   │   ├── handler.rs
  │       │       │   │   ├── input_ingress.rs
  │       │       │   │   ├── mod.rs
  │       │       │   │   ├── pg_output_contract.rs
  │       │       │   │   ├── pg_server.rs
  │       │       │   │   ├── server_state.rs
  │       │       │   │   ├── tests.rs
  │       │       │   │   ├── tool_error.rs
  │       │       │   │   ├── tools.rs
  │       │       │   │   └── tracing.rs
  │       │       │   ├── access_auth.rs
  │       │       │   ├── lib.rs
  │       │       │   ├── main.rs
  │       │       │   ├── pg_auth.rs
  │       │       │   ├── pg_main.rs
  │       │       │   ├── trace.rs
  │       │       │   └── windows_service.rs
  │       │       ├── tests
  │       │       │   └── pg_vertical.rs
  │       │       └── Cargo.toml
  │       ├── docs
  │       │   ├── audits
  │       │   │   ├── 2026-11-07-runtime-owner-audit.md
  │       │   │   └── 2026-11-08-runtime-modernization-brainstorm.md
  │       │   ├── evidence
  │       │   │   └── windows-r6c-c3-pass-20260920.json
  │       │   ├── guides
  │       │   │   ├── agent-runtime.md
  │       │   │   ├── operator-runtime.md
  │       │   │   └── runtime-legos.md
  │       │   ├── reference
  │       │   │   └── tools.md
  │       │   ├── agent-ux.md
  │       │   ├── authority.md
  │       │   ├── compatibility.md
  │       │   ├── data-and-privacy.md
  │       │   ├── effect-comparison.md
  │       │   ├── effect-kernel.md
  │       │   ├── NATIVE_RUNTIME_NODES_R1.md
  │       │   ├── operations.md
  │       │   ├── quickstart.md
  │       │   ├── recovery.md
  │       │   ├── releases.md
  │       │   ├── runtime-decomposition-history.md
  │       │   ├── runtime.md
  │       │   ├── RUNTIME_WINDOWS_R6C_ACCEPTANCE_R1.md
  │       │   ├── STANDARDS_FIRST_W2_BOUNDARY_R1.md
  │       │   └── status.md
  │       ├── evidence
  │       │   └── harness-h2-runtime-r2-live-d50f609-20260731.json
  │       ├── examples
  │       │   └── runtime-demo
  │       │       ├── inspect_policy.py
  │       │       ├── policy.py
  │       │       ├── report.py
  │       │       └── test_policy.py
  │       ├── formal
  │       │   ├── README.md
  │       │   ├── RuntimeDispatchR1.cfg
  │       │   ├── RuntimeDispatchR1.foreign-result-probe.cfg
  │       │   ├── RuntimeDispatchR1.tla
  │       │   ├── RuntimeDispatchR1.trace-r1.acceptance.json
  │       │   ├── RuntimeDispatchR1.trace-r1.json
  │       │   ├── RuntimePgCutoverR1.cfg
  │       │   ├── RuntimePgCutoverR1.tla
  │       │   ├── RuntimeResourceQueueR1.cfg
  │       │   ├── RuntimeResourceQueueR1.tla
  │       │   ├── RuntimeWindowsFirstPgR1.cfg
  │       │   ├── RuntimeWindowsFirstPgR1.tla
  │       │   ├── toolchain.lock.json
  │       │   ├── WorkspaceConsumerCloseR1.cfg
  │       │   ├── WorkspaceConsumerCloseR1.liveness.cfg
  │       │   ├── WorkspaceConsumerCloseR1.r2-candidate.cfg
  │       │   ├── WorkspaceConsumerCloseR1.reachability.cfg
  │       │   └── WorkspaceConsumerCloseR1.tla
  │       ├── packaging
  │       │   ├── systemd
  │       │   │   ├── tmpfiles.d
  │       │   │   │   └── ordivon.conf
  │       │   │   ├── ordivon-runtime-lifecycle.service
  │       │   │   ├── ordivon-runtime-lifecycle.timer
  │       │   │   ├── ordivon-runtime-storage-pressure.service
  │       │   │   ├── ordivon-runtime-storage-pressure.timer
  │       │   │   ├── ordivon-runtime.env.example
  │       │   │   ├── ordivon-runtime.service
  │       │   │   ├── ordivon-storage-pressure-control.json
  │       │   │   └── ordivon-workspace-retention.json
  │       │   └── windows
  │       │       ├── materialize-ordivon-runtime-service.ps1
  │       │       └── ordivon-runtime.env.example
  │       ├── planning
  │       │   ├── EXECUTION_FABRIC_R1_ROADMAP.md
  │       │   ├── invariants-r1.json
  │       │   ├── lego-plan-r1.json
  │       │   ├── state-responsibility-census-r1.json
  │       │   ├── test-taxonomy-r1.json
  │       │   ├── tool-necessity-audit-r1.json
  │       │   ├── WINDOWS_AUTHORITY_FACTORIZATION_EXECUTION_PLAN_R1.md
  │       │   ├── WINDOWS_AUTHORITY_FACTORIZATION_LEGO_R1.json
  │       │   ├── WORKSPACE_CONSUMER_LIFECYCLE_R21_EXECUTION_PLAN.md
  │       │   └── WORKSPACE_CONSUMER_LIFECYCLE_R21_SPEC.md
  │       ├── platform
  │       │   └── windows
  │       │       ├── Ordivon.WindowsJobFixture.cs
  │       │       ├── Ordivon.WindowsJobLauncher.cs
  │       │       └── Ordivon.WindowsPrivilegedBroker.cs
  │       ├── research
  │       │   ├── authority
  │       │   │   ├── publications
  │       │   │   │   ├── 227cc7e253de5fa10be7cbecdfd2e7d84724b507c4a0504836fc63996ac53497.json
  │       │   │   │   ├── 350d042df3c01399cf9314c6954f0c3f4c45bdeb660aa275556e098a77ec62eb.json
  │       │   │   │   ├── 9c67d1b4094ce85a2465579430bb1a941f1923457087fb74cde0642d7b9a51b3.json
  │       │   │   │   ├── a39e5ec16ed955bc02b1e11db6f120f5f812e093324a6a3171d368f710a8665b.json
  │       │   │   │   ├── e06cac5f69942068fabe80dc5da22fc1fb566d3004ce4951df545534fda289d9.json
  │       │   │   │   └── e2eb5a6d46c50390ec4b666cd6faba5528ff42b2c9e1bfb75cb45b6c0c4177ed.json
  │       │   │   └── CURRENT.json
  │       │   ├── core
  │       │   │   ├── DERIVED-RUNTIME-CORE-LAWS.md
  │       │   │   ├── ENGINEERING-CONSUMPTION.md
  │       │   │   ├── FOUNDATION-FAMILIES.md
  │       │   │   ├── HISTORICAL-EF27.md
  │       │   │   ├── OWNER-BRIDGES.md
  │       │   │   ├── README.md
  │       │   │   ├── REGISTRY-PROVENANCE.md
  │       │   │   ├── RUNTIME-ARCHITECTURE.md
  │       │   │   ├── SATURATION-NEGATIVE-EVIDENCE.md
  │       │   │   └── SBF-OWNER-ROLE-MAP.md
  │       │   ├── engineering
  │       │   │   ├── RUNTIME-FOUNDATIONS-V1-ENGINEERING-CONSUMPTION-CLOSEOUT.md
  │       │   │   ├── RUNTIME-FOUNDATIONS-V1-ENGINEERING-CONSUMPTION-R2-CONSUMERS.md
  │       │   │   ├── RUNTIME-FOUNDATIONS-V1-ENGINEERING-CONSUMPTION-R3-INTEGRATION.md
  │       │   │   └── RUNTIME-FOUNDATIONS-V1-ENGINEERING-CONSUMPTION.md
  │       │   ├── foundations
  │       │   │   ├── README.md
  │       │   │   ├── RF0-CLOSEOUT.json
  │       │   │   ├── RF0-CONTINUATION.md
  │       │   │   ├── RF0-RUNTIME-PHENOMENON-SPACE.md
  │       │   │   ├── RF0-SOURCES.md
  │       │   │   ├── RF1-CLOSEOUT.json
  │       │   │   ├── RF1-CONTINUATION.md
  │       │   │   ├── RF1-SOURCES.md
  │       │   │   ├── RF1-STATE-CHANGE-EVENT-BEHAVIOR-DYNAMICS.md
  │       │   │   ├── RF10-CLOSEOUT.json
  │       │   │   ├── RF10-CONTINUATION.md
  │       │   │   ├── RF10-FAILURE-RECOVERY-RETRY-IDEMPOTENCY-EXACTLY-ONCE.md
  │       │   │   ├── RF10-SOURCES.md
  │       │   │   ├── RF11-CLOSEOUT.json
  │       │   │   ├── RF11-CONTINUATION.md
  │       │   │   ├── RF11-OBSERVATION-EVIDENCE-PROOF-TRUTH-SURFACES.md
  │       │   │   ├── RF11-SOURCES.md
  │       │   │   ├── RF12-CLOSEOUT.json
  │       │   │   ├── RF12-COMPOSITION-TRANSACTIONS-CROSS-OPERATION-ATOMICITY.md
  │       │   │   ├── RF12-CONTINUATION.md
  │       │   │   ├── RF12-SOURCES.md
  │       │   │   ├── RF13-CLOSEOUT.json
  │       │   │   ├── RF13-CONTINUATION.md
  │       │   │   ├── RF13-ISOLATION-CONTAINMENT-TRUST.md
  │       │   │   ├── RF13-SOURCES.md
  │       │   │   ├── RF14-CLOSEOUT.json
  │       │   │   ├── RF14-CONTINUATION.md
  │       │   │   ├── RF14-DETERMINISM-NONDETERMINISM-AGENT-ACTION.md
  │       │   │   ├── RF14-SOURCES.md
  │       │   │   ├── RF15-CLOSEOUT.json
  │       │   │   ├── RF15-CONTINUATION.md
  │       │   │   ├── RF15-EXTERNAL-WORLD-OPEN-SYSTEM-EFFECTS.md
  │       │   │   ├── RF15-SOURCES.md
  │       │   │   ├── RF16-CLOSEOUT.json
  │       │   │   ├── RF16-CONTINUATION.md
  │       │   │   ├── RF16-CROSS-DOMAIN-FALSIFICATION-RUNTIME-FOUNDATIONS-V1.md
  │       │   │   ├── RF16-SOURCES.md
  │       │   │   ├── RF2-ACTION-INTENT-PROPOSAL-COMMAND-OPERATION.md
  │       │   │   ├── RF2-CLOSEOUT.json
  │       │   │   ├── RF2-CONTINUATION.md
  │       │   │   ├── RF2-SOURCES.md
  │       │   │   ├── RF3-CLOSEOUT.json
  │       │   │   ├── RF3-CONTINUATION.md
  │       │   │   ├── RF3-EXECUTION-REALIZATION-EFFECT-CONSEQUENCE.md
  │       │   │   ├── RF3-SOURCES.md
  │       │   │   ├── RF4-CLOSEOUT.json
  │       │   │   ├── RF4-CONTINUATION.md
  │       │   │   ├── RF4-IDENTITY-SAMENESS-REPLAY-HISTORY.md
  │       │   │   ├── RF4-SOURCES.md
  │       │   │   ├── RF5-CLOSEOUT.json
  │       │   │   ├── RF5-CONTINUATION.md
  │       │   │   ├── RF5-SOURCES.md
  │       │   │   ├── RF5-TIME-ORDERING-CONCURRENCY-CAUSALITY.md
  │       │   │   ├── RF6-AUTHORITY-CAPABILITY-PERMISSION-CONTROL.md
  │       │   │   ├── RF6-CLOSEOUT.json
  │       │   │   ├── RF6-CONTINUATION.md
  │       │   │   ├── RF6-SOURCES.md
  │       │   │   ├── RF7-BOUNDARY-ENVIRONMENT-CONTEXT-DEPENDENCY.md
  │       │   │   ├── RF7-CLOSEOUT.json
  │       │   │   ├── RF7-CONTINUATION.md
  │       │   │   ├── RF7-SOURCES.md
  │       │   │   ├── RF8-CLOSEOUT.json
  │       │   │   ├── RF8-CONTINUATION.md
  │       │   │   ├── RF8-RESOURCE-CAPACITY-CONSTRAINT-SCARCITY.md
  │       │   │   ├── RF8-SOURCES.md
  │       │   │   ├── RF9-CLOSEOUT.json
  │       │   │   ├── RF9-CONTINUATION.md
  │       │   │   ├── RF9-SCHEDULING-COORDINATION-ADMISSION-BACKPRESSURE.md
  │       │   │   ├── RF9-SOURCES.md
  │       │   │   ├── RUNTIME-FOUNDATIONS-RF0-RF16-CLOSEOUT.md
  │       │   │   └── RUNTIME-FOUNDATIONS-V1.md
  │       │   ├── programme
  │       │   │   ├── consumption
  │       │   │   │   ├── C1-STANDING-CURRENTNESS-RECOVERY.md
  │       │   │   │   ├── C10-CROSS-FAMILY-SATURATION-AUDIT.md
  │       │   │   │   ├── C2-CONSEQUENTIAL-RETRY-REGROUNDING.md
  │       │   │   │   ├── C3-FRESH-EXECUTION-SUPPORT-REUSE.md
  │       │   │   │   ├── C4-CROSS-OWNER-STANDING-CURRENTNESS.md
  │       │   │   │   ├── C5-EVIDENCE-CLAIM-SCOPE.md
  │       │   │   │   ├── C6-LOCAL-GLOBAL-PUBLICATION-COMPOSITION.md
  │       │   │   │   ├── C7-IDENTITY-LINEAGE-CAUSAL-ATTRIBUTION.md
  │       │   │   │   ├── C8-BINDING-AUTHORITY-REALIZATION-ORTHOGONALITY.md
  │       │   │   │   └── C9-LIFECYCLE-RETENTION-RECLAIMABILITY.md
  │       │   │   ├── evidence
  │       │   │   │   ├── C1-STANDING-CURRENTNESS-RECOVERY.json
  │       │   │   │   ├── C10-CROSS-FAMILY-SATURATION-AUDIT.json
  │       │   │   │   ├── C2-CONSEQUENTIAL-RETRY-REGROUNDING.json
  │       │   │   │   ├── C3-FRESH-EXECUTION-SUPPORT-REUSE.json
  │       │   │   │   ├── C4-CROSS-OWNER-STANDING-CURRENTNESS.json
  │       │   │   │   ├── C5-EVIDENCE-CLAIM-SCOPE.json
  │       │   │   │   ├── C6-LOCAL-GLOBAL-PUBLICATION-COMPOSITION.json
  │       │   │   │   ├── C7-IDENTITY-LINEAGE-CAUSAL-ATTRIBUTION.json
  │       │   │   │   ├── C8-BINDING-AUTHORITY-REALIZATION-ORTHOGONALITY.json
  │       │   │   │   └── C9-LIFECYCLE-RETENTION-RECLAIMABILITY.json
  │       │   │   ├── tools
  │       │   │   │   ├── claim_scope_probe.py
  │       │   │   │   ├── composite_saturation_probe.py
  │       │   │   │   ├── currentness_probe.py
  │       │   │   │   ├── lifecycle_retention_probe.py
  │       │   │   │   ├── lineage_causation_probe.py
  │       │   │   │   ├── orthogonality_probe.py
  │       │   │   │   ├── publication_pipeline_probe.py
  │       │   │   │   ├── retry_admissibility_probe.py
  │       │   │   │   ├── support_reuse_probe.py
  │       │   │   │   └── typed_currentness_probe.py
  │       │   │   ├── CONSTITUTION.md
  │       │   │   ├── DOGFOOD-AND-CASE-STUDIES.md
  │       │   │   ├── EMERGING-RESEARCH.md
  │       │   │   ├── ENGINEERING-CONSUMPTION.md
  │       │   │   ├── FALSIFIER-LIBRARY.md
  │       │   │   ├── PROGRAMME-SATURATION-CLOSEOUT.md
  │       │   │   ├── README.md
  │       │   │   ├── REOPEN-CONDITIONS.md
  │       │   │   └── THEORY-CORE.md
  │       │   └── README.md
  │       ├── scripts
  │       │   ├── tests
  │       │   │   ├── pg_recovery_pitr_probe.py
  │       │   │   ├── test_agent_ux_report.py
  │       │   │   ├── test_archive.py
  │       │   │   ├── test_cache.py
  │       │   │   ├── test_cache_root_singlepass.py
  │       │   │   ├── test_cache_singlewalk_consumer.py
  │       │   │   ├── test_cache_vanishing_entry.py
  │       │   │   ├── test_capacity_acceptance.py
  │       │   │   ├── test_demo_runtime_flow.py
  │       │   │   ├── test_deploy_reclaim.py
  │       │   │   ├── test_dirty_checkpoint.py
  │       │   │   ├── test_focused_verification_contract.py
  │       │   │   ├── test_formal_trace.py
  │       │   │   ├── test_host_h2_r2_receipt.py
  │       │   │   ├── test_lifecycle.py
  │       │   │   ├── test_mcp_e2e.py
  │       │   │   ├── test_mcp_e2e_reconciliation.py
  │       │   │   ├── test_mcp_probe.py
  │       │   │   ├── test_operational_scripts.py
  │       │   │   ├── test_owner_python_pin.py
  │       │   │   ├── test_pg_consumer_source_bound_formal.py
  │       │   │   ├── test_pg_disposable_physical.py
  │       │   │   ├── test_pg_operator_release.py
  │       │   │   ├── test_pg_physical_verification_contract.py
  │       │   │   ├── test_pg_retention_census.py
  │       │   │   ├── test_pg_workspace_reclaim.py
  │       │   │   ├── test_postgres_registry_currentness.py
  │       │   │   ├── test_postgres_registry_stage.py
  │       │   │   ├── test_pressure_control.py
  │       │   │   ├── test_reference_model_shards.py
  │       │   │   ├── test_release_receipt_semantics_r1.py
  │       │   │   ├── test_resource_workload_profile.py
  │       │   │   ├── test_status.py
  │       │   │   └── test_tla_formal_external_jar.py
  │       │   ├── agent_ux_report.py
  │       │   ├── backup.py
  │       │   ├── check_docs.py
  │       │   ├── check_host_h2_r2_receipt.py
  │       │   ├── check_runtime_standard_native_r3.py
  │       │   ├── demo_runtime_flow.py
  │       │   ├── local-acceptance
  │       │   ├── mcp_e2e.py
  │       │   ├── mcp_probe.py
  │       │   ├── ordivon-runtime-archive
  │       │   ├── ordivon-runtime-cache
  │       │   ├── ordivon-runtime-capacity-acceptance
  │       │   ├── ordivon-runtime-deploy
  │       │   ├── ordivon-runtime-lifecycle
  │       │   ├── ordivon-runtime-pg-operator
  │       │   ├── ordivon-runtime-pg-reclaim
  │       │   ├── ordivon-runtime-pressure-control
  │       │   ├── ordivon-runtime-reclaim
  │       │   ├── ordivon-runtime-status
  │       │   ├── ordivon_runtime_pg_operator.py
  │       │   ├── owner-environment
  │       │   ├── pg_disposable_physical.py
  │       │   ├── pg_retention_census.py
  │       │   ├── postgres_registry_currentness.py
  │       │   ├── postgres_registry_stage.py
  │       │   ├── resource_workload_profile.py
  │       │   ├── restore.py
  │       │   ├── snapshot_fds.py
  │       │   ├── tla-formal
  │       │   ├── verify_formal_trace.py
  │       │   ├── verify_reference_model_shards.py
  │       │   ├── windows-job-launcher-acceptance.py
  │       │   └── windows-native-runtime-r6c-acceptance.ps1
  │       ├── sql
  │       │   └── pg_resource_scheduler_v1.sql
  │       ├── standards
  │       │   ├── runtime_standard_native_r3.sdoc
  │       │   ├── runtime_standard_native_r3.toml
  │       │   └── runtime_standard_native_r3_report.json
  │       ├── tests
  │       │   ├── test_systemd_liveness_contract.py
  │       │   ├── test_windows_launcher_effective_cwd_identity_contract.py
  │       │   ├── test_windows_launcher_error_evidence.py
  │       │   ├── test_windows_launcher_verbatim_path_bridge.py
  │       │   ├── test_windows_native_runtime_r6c_acceptance.py
  │       │   ├── test_windows_privileged_broker_contract.py
  │       │   └── test_windows_runtime_service_materializer.py
  │       ├── .editorconfig
  │       ├── .gitattributes
  │       ├── .gitignore
  │       ├── .gitleaks.toml
  │       ├── .gitleaksignore
  │       ├── .python-version
  │       ├── AGENTS.md
  │       ├── Cargo.lock
  │       ├── Cargo.toml
  │       ├── CHANGELOG.md
  │       ├── CONTRIBUTING.md
  │       ├── deny.toml
  │       ├── LICENSE
  │       ├── mise.toml
  │       ├── pyproject.toml
  │       ├── README.md
  │       ├── requirements-runtime-pg-operator.in
  │       ├── requirements-runtime-pg-operator.lock.txt
  │       ├── requirements-tooling.lock.txt
  │       ├── requirements-tooling.txt
  │       ├── rust-toolchain.toml
  │       └── SECURITY.md
  ├── studies
  │   ├── data-lifecycle
  │   │   ├── evidence
  │   │   │   ├── data-products-r1
  │   │   │   │   ├── acceptance.json
  │   │   │   │   ├── federated-catalog.dcat.jsonld
  │   │   │   │   └── product-provenance.prov.jsonld
  │   │   │   ├── data-products-r2
  │   │   │   │   ├── acceptance.json
  │   │   │   │   ├── federated-catalog.dcat.jsonld
  │   │   │   │   └── product-provenance.prov.jsonld
  │   │   │   ├── experimental-episode-rw5
  │   │   │   │   ├── acceptance.json
  │   │   │   │   ├── observability.json
  │   │   │   │   └── standard-validation.json
  │   │   │   ├── github-pilot-r1
  │   │   │   │   ├── analysis
  │   │   │   │   │   ├── analysis-summary.json
  │   │   │   │   │   ├── crossref-country-metadata-rates.csv
  │   │   │   │   │   └── se4all-yearly-country-means.csv
  │   │   │   │   ├── catalog
  │   │   │   │   │   └── catalog.dcat.jsonld
  │   │   │   │   ├── contracts
  │   │   │   │   │   ├── crossref-member-participation.odcs.json
  │   │   │   │   │   ├── crossref-metadata-coverage.odcs.json
  │   │   │   │   │   └── se4all-energy.odcs.json
  │   │   │   │   ├── lineage
  │   │   │   │   │   ├── crossref-transform.openlineage.json
  │   │   │   │   │   └── se4all-transform.openlineage.json
  │   │   │   │   ├── semantics
  │   │   │   │   │   └── external-semantic-profile.json
  │   │   │   │   ├── source
  │   │   │   │   │   ├── acquisition-policy.json
  │   │   │   │   │   ├── repository.txt
  │   │   │   │   │   ├── standards.json
  │   │   │   │   │   └── tidytuesday-main.sha
  │   │   │   │   ├── standards
  │   │   │   │   │   ├── odcs-json-schema-v3.2.0.json
  │   │   │   │   │   └── OpenLineage-2.0.2.json
  │   │   │   │   ├── .gitignore
  │   │   │   │   ├── manifest.json
  │   │   │   │   └── quality-report.json
  │   │   │   ├── preservation-r1
  │   │   │   │   ├── acceptance.json
  │   │   │   │   └── ndsa-2.1-assessment.json
  │   │   │   └── temporal-evolution-r1
  │   │   │       ├── source
  │   │   │       │   └── external-temporal-reference-profile.json
  │   │   │       ├── .gitignore
  │   │   │       ├── activation-decision.json
  │   │   │       ├── bounded-replay-conformance.json
  │   │   │       ├── manifest.json
  │   │   │       ├── reference-identity-report.json
  │   │   │       ├── revision-ledger.json
  │   │   │       └── schema-evolution-conformance.json
  │   │   ├── tests
  │   │   │   ├── test_data_lifecycle_semantics.py
  │   │   │   ├── test_data_preservation_evidence.py
  │   │   │   ├── test_data_product_consumption_feedback.py
  │   │   │   ├── test_data_product_federation.py
  │   │   │   ├── test_data_product_governance.py
  │   │   │   └── test_data_temporal_evolution.py
  │   │   ├── data-lifecycle-census-r1.json
  │   │   ├── data-lifecycle-census-r2.json
  │   │   ├── data-lifecycle-census-r3.json
  │   │   ├── data-lifecycle-census-r4.json
  │   │   ├── data-lifecycle-census-r5.json
  │   │   └── data-lifecycle-census-r6.json
  │   └── experimental-episodes
  │       ├── episode-store
  │       │   ├── migrations
  │       │   │   ├── versions
  │       │   │   │   └── 0001_episode_projection.py
  │       │   │   └── env.py
  │       │   ├── sql
  │       │   │   └── runtime_r5c_export.sql
  │       │   ├── src
  │       │   │   └── ordivon_experimental_episode_store
  │       │   │       ├── __init__.py
  │       │   │       ├── aip_readback.py
  │       │   │       ├── analysis.py
  │       │   │       ├── ingest.py
  │       │   │       ├── r5c_backfill.py
  │       │   │       └── r5c_projection.py
  │       │   ├── tests
  │       │   │   ├── test_aip_readback.py
  │       │   │   ├── test_analysis_contract.py
  │       │   │   ├── test_committed_ingest_readback.py
  │       │   │   ├── test_data_product_contract.py
  │       │   │   ├── test_ingest_contract.py
  │       │   │   └── test_r5c_projection.py
  │       │   ├── alembic.ini
  │       │   ├── mise.toml
  │       │   ├── pyproject.toml
  │       │   ├── README.md
  │       │   └── uv.lock
  │       ├── evidence
  │       │   ├── acceptance
  │       │   │   └── experimental-episode-rw5-bindings.json
  │       │   ├── analysis
  │       │   │   └── experimental-system-analysis-r1.json
  │       │   ├── corpus-r1
  │       │   │   └── manifest.json
  │       │   └── data-products
  │       │       └── experimental-episode-analysis-r1
  │       │           ├── artifact-index-verification.json
  │       │           ├── openlineage.json
  │       │           ├── provenance.prov.jsonld
  │       │           └── receipt.json
  │       └── experiments
  │           └── evidence-consumer-pilot-r1
  │               ├── deliver_research.py
  │               ├── delivery-20261109.json
  │               ├── pilot.py
  │               ├── README.md
  │               ├── result-20261108.json
  │               ├── RESULTS.md
  │               ├── task-outcomes-20261109.json
  │               ├── task_outcome_pilot.py
  │               ├── TASK_OUTCOME_RESULTS_20261109.md
  │               ├── test_deliver_research.py
  │               ├── test_pilot.py
  │               └── test_task_outcome_pilot.py
  ├── tests
  │   ├── catalogs
  │   │   └── test_research_tool_and_mechanical_component_contracts.py
  │   └── fixtures
  │       └── research
  │           └── publication-carrier-paper3-dogfood-r1.json
  ├── tools
  │   ├── formal
  │   │   ├── mise.toml
  │   │   ├── Proof.als
  │   │   ├── Proof.dfy
  │   │   ├── Proof.qnt
  │   │   ├── Proof.rs
  │   │   ├── ProofKani.rs
  │   │   ├── README.md
  │   │   ├── RecursiveLegoRefinement.lean
  │   │   ├── RecursiveLegoVariationFrame.lean
  │   │   └── verify.py
  │   └── repo
  │       ├── agent_plugin
  │       │   ├── materialize.py
  │       │   ├── source.py
  │       │   └── test_materialize.py
  │       ├── migration
  │       │   ├── check-primary-main.sh
  │       │   ├── check-publication-main.sh
  │       │   ├── integrate-main.sh
  │       │   ├── test-check-publication-main.sh
  │       │   └── test-integrate-main.sh
  │       ├── planning
  │       │   └── lego-plan-r1.json
  │       ├── affected_owners.py
  │       ├── bash-5.3.20.sha256
  │       ├── check_architecture_docs.py
  │       ├── check_archived_source_boundary.py
  │       ├── check_composition_architecture.py
  │       ├── check_github_governance.py
  │       ├── check_owner_boundaries.py
  │       ├── check_sql_dialects.py
  │       ├── check_structure_r2.py
  │       ├── check_tracked_secrets.sh
  │       ├── ci_owner_shards.py
  │       ├── ci_telemetry.py
  │       ├── convergence_plan.py
  │       ├── convergence_pressure.py
  │       ├── dependency_contracts.toml
  │       ├── exhaustive_coverage.py
  │       ├── install_latest_stable_bash.sh
  │       ├── install_sql_verifiers.sh
  │       ├── install_verified_cargo_deny.py
  │       ├── owners.toml
  │       ├── queue_telemetry.py
  │       ├── source_content_facets.py
  │       ├── source_history_legos.py
  │       ├── test-check-archived-source-boundary.sh
  │       ├── test_affected_owners.py
  │       ├── test_architecture_docs.py
  │       ├── test_ci_owner_shards.py
  │       ├── test_composition_architecture.py
  │       ├── test_convergence_plan.py
  │       ├── test_convergence_pressure.py
  │       ├── test_dependency_update_ownership.py
  │       ├── test_exhaustive_coverage.py
  │       ├── test_formal_source_contract.py
  │       ├── test_github_governance.py
  │       ├── test_install_verified_cargo_deny.py
  │       ├── test_issue_owner_registration.py
  │       ├── test_lego_graph_laws.py
  │       ├── test_owner_boundaries.py
  │       ├── test_postgres_owner_migration_issue.py
  │       ├── test_source_content_facets.py
  │       ├── test_source_history_legos.py
  │       ├── test_sql_dialects.py
  │       ├── test_structure_r2.py
  │       ├── test_tracked_secrets.py
  │       ├── test_workspace_ready.py
  │       └── workspace-ready
  ├── .gitignore
  ├── .gitleaksignore
  ├── AGENTS.md
  ├── CONTRIBUTING.md
  ├── LICENSE
  ├── mise.toml
  ├── README.md
  ├── renovate.json
  └── SECURITY.md
```

## Evidence limits

The full nested tree is mechanically complete. Runtime-installed files, dynamically loaded modules, deployment references, external service/consumer contracts and content equivalence were not inferred from physical path presence. See `AUDIT_REPORT.md` for bounded deep review by module and `REFACTOR_PLAN.md` for selected maintenance actions.


## Per-file immutable-source ledger — cross-Agent reuse, not a second registry

A separate, machine-readable `FILE_LEDGER.tsv.gz` from independent peer PR #2032/source `139b1ad36de3a60a5987f6a40512909fa8011906` has been **reused verbatim** under this canonical audit location rather than independently reinvented. SHA-256 compressed bytes:

`1274eac9f9c8571854b77b950f025863e1f91a94fa32074358b20be932873d9e`.

It has **5,003 TSV rows** (one header plus one row for each of the **5,002 pinned original source files**); columns include `path`, `git_blob_sha`, `bytes`, `mode`, `owner_or_region`, `extension` and `semantic_review`. All `semantic_review` entries say `NOT_YET_DETERMINED_BY_MACHINE`, correctly refusing to promote file enumeration to human/Agent semantic acceptance.

Independent inspection compared every ledger path, Git blob OID, file mode and byte count against the original pinned source content in this exact Git checkout: **0 mismatches**; the current audit branch also contains additional documents not in the source ledger and they are intentionally excluded. This ledger is a dated source witness, not a writable Owner registry, an installed manifest or a certificate that dynamic consumers are absent.
