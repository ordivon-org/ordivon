# Ordivon Phase 1 R5 — Agent-readable source names

Scope: SOURCE OBSERVATION AND CANDIDATE DISPLAY NAMES. Not LEGO decomposition, physical file rename, formal correctness, producer/consumer admission, or approval ownership.

## Typed source naming tuple

`{sourceCut, exactGitPath, mode, blobOid, physicalSourceZone, observedContentForm, displayNameCandidates[], nameEvidenceCut, semanticStanding}`

An Agent-readable display name never replaces the Git source identity. File/source role, functional domain, interface carrier, execution authority, evidence time and actual consumer are independent axes.

## 26 bounded agent display aliases — historical source cut 631c3c8

| Old exact Git directory prefix | Proposed Agent-facing display name | Baseline files |
|---|---|---:|
| `meta/next/authorities/records/` | `external-standard-identity-records` | 176 |
| `meta/next/authorities/observations/` | `external-standard-currentness-observations` | 181 |
| `meta/next/authorities/generated/` | `rebuildable-standard-discovery-index` | 1 |
| `meta/next/evidence/acceptance/` | `historical-acceptance-receipts` | 84 |
| `meta/next/evidence/data-lifecycle/` | `data-lifecycle-historical-observations` | 38 |
| `meta/next/knowledge/lessons/` | `curated-knowledge-lessons` | 83 |
| `meta/next/knowledge/graphs/` | `knowledge-relation-history-graphs` | 31 |
| `services/runtime/research/foundations/` | `runtime-foundational-research` | 71 |
| `services/runtime/research/programme/` | `runtime-research-programme` | 39 |
| `services/runtime/research/core/` | `runtime-architecture-research` | 10 |
| `services/harness/research/` | `agent-run-research-corpus` | 101 |
| `services/harness/evidence/` | `harness-experiment-observation-receipts` | 149 |
| `capabilities/media/research/expression/` | `creative-expression-method-research` | 128 |
| `capabilities/media/research/equipment/` | `creative-equipment-provider-research` | 13 |
| `capabilities/media/productions/` | `creative-production-instances` | 218 |
| `capabilities/artifact/artifact-delivery/shadow-contracts/` | `artifact-shadow-contract-experiments` | 36 |
| `capabilities/artifact/artifact-delivery/shadow-bindings/` | `artifact-shadow-binding-experiments` | 20 |
| `capabilities/artifact/artifact-delivery/consumer-acceptance/` | `artifact-consumer-acceptance-records` | 9 |
| `platform/network/consumers/` | `network-consumer-specific-egress-policy` | 66 |
| `platform/workstation/providers/cloudflare/` | `cloudflare-workstation-provider-source` | 58 |
| `domains/capital/destroyer/` | `capital-false-positive-negative-corpus` | 1 |
| `domains/capital/wave_b/` | `capital-wave-research-fixtures` | 1 |
| `.agents/skills/recursive-lego-calculus/` | `recursive-lego-procedural-method` | 2 |
| `tools/formal/` | `formal-models-and-verifier-toolchain` | 10 |
| `meta/research/` | `main-repo-research-publication-profiles` | 12 |
| `extensions/ordivon-control-plane/` | `declarative-agent-plugin-package` | 2 |

These are source-bound labels only, not semantic proof or permission to move files. Current file counts must be rebuilt from the selected Git SourceCut.

## 12 independently verified false-friend name candidates

Each candidate has one exact Git blob identity and literal marker witness. This proves only the bounded source observation; consumer and installed state remain UNKNOWN.

| Current Git path prefix | Agent display candidate | Misleading interpretation | Source witness path |
|---|---|---|---|
| `meta/next/authorities/records/` | `knowledge.external-standards-and-source-provenance` | identity-authz authority | `meta/next/authorities/records/prisma/prisma-2020.json` |
| `services/runtime/research/` | `execution.runtime-architecture-investigation` | Research study operator | `services/runtime/research/README.md` |
| `services/harness/research/` | `agent.run-mediation-foundation-studies` | scholarly research production | `services/harness/research/00-OWNER-BOUNDARY.md` |
| `platform/network/consumers/finance/` | `network.finance-transport-profile` | capital trading engine | `platform/network/consumers/finance/README.md` |
| `platform/workstation/providers/cloudflare/` | `environment.edge-provider-deployment` | all Workstation inventory | `platform/workstation/providers/cloudflare/README.md` |
| `capabilities/media/research/equipment/` | `media.creative-equipment-evaluation` | academic Research programme | `capabilities/media/research/equipment/README.md` |
| `domains/capital/destroyer/` | `capital.false-positive-evidence-counterexamples` | destructive execution agent | `domains/capital/destroyer/false-green-corpus-v0.json` |
| `domains/capital/wave_b/fixtures/` | `capital.portfolio-validation-fixtures` | production trading strategy | `domains/capital/wave_b/fixtures/wave_a_target_portfolio.json` |
| `services/gateway/src/ordivon_gateway/` | `interfaces.research-capability-routing` | Research study authority | `services/gateway/src/ordivon_gateway/research_routes.py` |
| `extensions/ordivon-control-plane/` | `interfaces.remote-mcp-plugin-package` | independent control-plane execution | `extensions/ordivon-control-plane/plugin.json` |
| `meta/next/domains/game/` | `knowledge.game-method-profile` | game implementation engine | `meta/next/domains/game/README.md` |
| `.agents/skills/recursive-lego-calculus/` | `foundation.lego-semantic-method` | composition implementation or formal verifier | `.agents/skills/recursive-lego-calculus/SKILL.md` |

When a prefix has both a 26-set label and a 12-set more specific candidate, retain BOTH observations. Do not silently declare either the unique semantic identity.

## Mechanical Agent re-discovery

Use an exact resolved SourceCut rather than symbolic HEAD in the scanner. Source navigation is already implemented by existing repository tooling; do not introduce a second source registry.

```bash
cut=$(git rev-parse HEAD)
python3 tools/repo/source_content_facets.py --source-cut "$cut" --summary
python3 tools/repo/exhaustive_coverage.py --source-cut "$cut" --live-cells --summary
```

These tools show current exact source physical paths and content syntax. Names do NOT infer operation, dynamic consumer, formal proof, or installed release. Inverse Agent name resolution is being converged by peers onto the existing exact-cut lookup rather than duplicated.

## Prohibited claims in Phase 1

- Do not rename old paths, Skill names, MCP schemas, API routes, CLI switches, plugin manifests or configuration keys until actual consumers are identified and equivalence is independently established.
- Do not turn JSON kind strings, Markdown headings, package names or declared authority labels into runnable authorization or formal proofs.
- Keep main Git source, Research, Media, Paper, Game, OSS, unversioned data, Windows/Linux services and installed binaries in separate identity universes.
- Unknown and conflicting names stay explicit. There is no misc catch-all that hides an unclassified source.
