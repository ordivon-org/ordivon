# Ordivon responsibility boundaries and Agent naming review

Date: 2026-10-27 (Asia/Shanghai)
Status: RESEARCH_AND_DISCUSSION_COMPLETED / MIGRATION_PROPOSED
Inspected SourceCut: bb50fab9cd3b77595c59fcbeb35cb6c8866f2277

## Decision

Prioritize misleading Agent-visible names and descriptions, then reconcile repository verification boundaries with actual consumer contracts. Do not turn Plugin, Skill, Tool, MCP, CLI and SDK into seven parallel business systems. Do not infer a fixed number of LEGO identities from the 18 registered repository verification partitions.

Recommended first pair: **Gateway Client Plugin** (portable client connection package) and **Gateway Service** (capability projection, routing and protocol adaptation). Keep existing stable public identifiers until consumer and migration evidence supports changing them.

This report records source and standards research plus independent discussion. It implements no rename, deployment, permission change or new registry.

## Exact local evidence

- `tools/repo/owners.toml` declares `truth_role = "repository-mechanics-only-not-domain-authority"` and 18 partitions. Repository verification scope, semantic LEGO, deployment unit and data authority are distinct dimensions.
- `extensions/ordivon-control-plane/plugin.json` calls the package `ordivon-control-plane`, version 0.2.0; its description says portable MCP connection. `mcp.json` declares one Gateway streamable-http endpoint. Two files do not implement a control plane.
- `meta/next/scripts/materialize_agent_plugin.py` and `meta/next/tests/test_agent_plugin_materialization.py` consume this package source. Root `mise.toml`, CODEOWNERS, affected-owner checks and architecture carriers consume its path/name. A directory rename alone would leave real consumers inconsistent.
- `services/gateway/src/ordivon_gateway/routes.py` maps execution to Runtime and continuity to Host. This supports a routing/adaptation boundary rather than a second execution ledger.
- `services/gateway/src/ordivon_gateway/mcp_server.py:285` registers `host.status` and delegates through `social_work_call`; `services/gateway/README.md:46` says that it is not exposed. This source/documentation conflict can misroute an Agent even if every name is improved.
- The same server conditionally mounts external-worker HTTP routes around line 781; README documents `/v1/workers/*` and `/v1/operations/*`. Naming the entire service MCP Gateway would hide an existing optional non-MCP responsibility. Source configuration does not establish production enablement.
- `platform/skills/README.md` already calls this a temporary standard Agent Skills filesystem-to-MCP bridge. Its catalog/scanner/eligibility/binding implementation is narrower than the generic partition label Skills suggests.
- Current Skills discovery and explicit resolution did not expose recursive-lego-calculus in this session. The source file exists and was read. This is a visibility/binding observation, not proof that the Skill is absent.
- Original Skill SHA256: `83099962298977c054076ec8f2d4d6e07f6a3d1e63c7a3c9ffb5a225548030e1`.
- R2.1 formal reference SHA256: `8f445b6df14b15e8bdf8976e6316a0f286253915f1d16c6ae46aa3e9fbed836b`.

## Mature sources and applicable lessons

All sources below were retrieved directly from official documentation on the report date. Provider-specific behaviors must not be promoted into universal standards.

| Source | Relevant fact | Application / limit |
|---|---|---|
| [Kubernetes API](https://kubernetes.io/docs/concepts/overview/kubernetes-api/) | API, discovery and machine-readable schemas support multiple clients | Share operation contracts across CLI/SDK/adapters; do not import Kubernetes infrastructure merely for conceptual uniformity |
| [Kubernetes client libraries](https://kubernetes.io/docs/reference/using-api/client-libraries/) | Client libraries access the same API | A client SDK is different from an implementation/extension SDK |
| [Terraform Core and plugins](https://developer.hashicorp.com/terraform/plugin/how-terraform-works) | Core manages graph/state/plan execution; providers implement service-specific behavior over RPC | Separate irreducible execution semantics from provider adaptation; Core itself is a CLI, so CLI is not universally a thin shell |
| [Terraform Plugin Framework](https://developer.hashicorp.com/terraform/plugin/framework) | Framework handles provider protocol mechanics | Reuse mature extension frameworks; do not rebuild protocol kernels to achieve language uniformity |
| [Envoy Gateway system design](https://gateway.envoyproxy.io/community/design/system-design/) | Control plane configures a distinct proxy data plane | Reserve control-plane terminology for actual configuration/management responsibility; an MCP connection manifest does not satisfy this |
| [Envoy xDS](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/operations/dynamic_configuration) | Static configuration and progressively richer dynamic options coexist | Adopt only needed complexity; Ordivon operation identity/receipts are not ordinary proxy routing |
| [Backstage System Model](https://backstage.io/docs/features/software-catalog/system-model/) | Component, API and Resource are distinct; System/Domain are optional groupings | Useful descriptive facets, not a mandate for extra processes, repositories or permanent classifications |
| [Backstage Catalog](https://backstage.io/docs/features/software-catalog/) | Catalog harvests metadata from source | Reconstruct semantic discovery views; do not move Job/Attempt truth into a second catalog authority |
| [Agent Plugins v1](https://agent-plugins.org/specification) | Portable package specifies Skills and MCP server configurations | Name a package as a client/plugin package; package validity does not prove all components are loaded or usable |
| [Agent Skills](https://agentskills.io/specification) | SKILL.md, optional scripts/references/assets and progressive loading | Keep portable content; retain only necessary local discovery/trust/currentness additions |
| [Claude Code plugins](https://code.claude.com/docs/en/plugins) | Product plugins support additional components such as agents and hooks | Do not confuse product-specific extensions with the portable v1 contract |
| [Claude Code skills](https://code.claude.com/docs/en/skills) | Description participates in selection; scoped names and collisions matter | Put responsibility and when-to-use first; a short name is not a stable identity |
| [Claude Code MCP](https://code.claude.com/docs/en/mcp) | Discovery, deferred tools and description limits affect model visibility | Availability, discovery and current binding are separate facts; avoid burying routing conditions in long descriptions |
| [MCP tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools) | Tool operation/schema and protocol/tool errors are distinct | A successful RPC or accepted submission is insufficient for business completion |
| [Claude Agent SDK](https://code.claude.com/docs/en/agent-sdk/overview) | Agent execution SDK and direct API client SDK serve different roles | Use Client SDK, Agent SDK or Provider SDK as appropriate, rather than one overloaded SDK label |

Skills may contain executable scripts. Their permission declarations are interpreted by the host; some hosts implement temporary preapproval. The portable declaration alone is not cross-host execution authority. This is more accurate than the absolute statement that Skills can never affect permissions.

## Responsibility versus access form

| Dimension | What it describes | Typical Ordivon placement |
|---|---|---|
| Semantic responsibility | Behavior, state, invariants, consumers, replacement contract | Owner-local R2.1 LEGO definitions and native code |
| Callable operation | A bounded action with IO/effects/errors | Tool/API operation |
| Wire protocol | Discovery, message/transport behavior | MCP / HTTP adapters |
| Client/program entry | How a caller invokes behavior | CLI / client SDK |
| Embedded execution framework | A reusable loop or implementation framework | Agent SDK / provider SDK where actually consumed |
| Procedure/knowledge | How and when to select/compose/qualify capabilities | Skill |
| Distribution package | Versioned collection of portable/client-specific components | Plugin |
| Repository verification partition | Paths and native checks | owners.toml |
| Runtime authority | Actual accepted operation, execution and retained state | Existing Runtime/Host/domain services |

These are descriptive dimensions, not a new mandatory schema or registry.

## All 18 registered partitions: proposed treatment

| Current partition | Recommended Agent-visible description/name | Boundary decision |
|---|---|---|
| next | Task representation and cross-domain composition research | First narrow the broad name; trace methods/authority binding/domain experiments internally. Do not treat Next as whole-system owner |
| composition | Composition Library | Preserve generic reusable mechanics; Next has real imports/public dependency |
| control-plugin | Gateway Client Plugin | First rename misleading display/description; evaluate moving the portable package under Gateway integrations after release/consumer inventory. Independent verify scope can remain if useful |
| runtime | Execution Runtime | Preserve Workspace/Job/Attempt execution authority; recurse admission, identity, runner/provider, recovery, artifacts |
| host | Work Continuity and Collaboration Service (Host) | Preserve Work/Social/Attention; avoid generic Host, machine-host or MCP-host interpretation |
| harness | Agent Harness | Preserve bounded model/tool Run semantics; recurse cognition, admission/lowering, completion and effect seams |
| gateway | Gateway Service — capability routing and protocol adapters | Preserve necessary routing/correlation/identity qualification. General proxy/protocol mechanics should reuse mature components; no duplicate downstream ledger |
| skills | Agent Skills Bridge | Preserve only discovered local bridge/trust/currentness responsibilities; standard file semantics remain upstream |
| security | Security Policy and Verification | Keep public policy/verifier contracts; product sessions and domain data remain with consumers |
| workstation | Execution Node Operations | Preserve desired-state/realization, reboot/WSL/service/install/recovery operations; recurse providers, avoid new DNS/Cloudflare owners merely for vendor names |
| network | Network Connectivity and Egress | Preserve path/protocol responsibility; recurse core DNS/proxy/TUN and consumer profiles |
| artifact | Artifact Build, Format Verification and Delivery | Distinguish managed construction/validation from Runtime retained execution output; recurse format/provider/operation only with consumer contracts |
| distribution | Optional Delivery and Effect-Safety Profiles | Keep direct-provider-first scope; avoid universal mandatory distribution/control service |
| media | Media Projection, Authoring and Production | Studio remains an internal authoring capability; recurse assets/provenance/timed text/render/QC without claiming all UI |
| preservation | Preservation Integration and Evidence Profiles | Reuse Archivematica/Fixity/systemd; no new preservation runtime |
| game | Game Knowledge and Assembly | Current source has retrieval and assembly fixture responsibilities, no first-party game product; names must track actual source scope |
| capital | Markets, Execution Safety and Accounting | Recurse market capture, descriptive research/risk, admission, reconciliation, ledger; an independent repo split needs actual lifecycle/consumer evidence |
| web | Web Application | Preserve product browser/agent rails, sessions and durable product replay; consume Security public contracts |

These are proposed display labels, not implemented public API/package identifiers. More specific internal LEGO names do not require new top-level repo owners.

No new top-level repository partition is justified solely by this audit. Independent release, deployment, state lifecycle, contract and consumer evidence could justify one later. Research, Formal and Repo/tooling need explicit cross-system responsibility coverage even where not separate registered owners.

## Concrete Agent effects and falsifiers

| Observed ambiguity | Plausible failure | Change to test |
|---|---|---|
| Control Plane for two-file connection package | Agent looks for scheduling, permissions or execution control inside configuration | Gateway Client Plugin plus first sentence: configures a client's Gateway MCP connection; no server runtime in this package |
| Host | Agent chooses a machine/environment entry for Work persistence, or confuses MCP Host with Ordivon Host | Work Continuity and Collaboration Service; retain the current stable Host identity and qualify its display name by responsibility |
| Next | Agent cannot infer task representation/cross-domain scope | Specific display description and task-routing examples; do not invent a new universal strategy service |
| MCP Gateway versus Gateway MCP Plugin | Similar names obscure client/server direction | Explicit Client Plugin versus Service; keep protocol as a facet |
| Skills versus Skills Bridge | Agent expects installation/execution/marketplace behavior | Describe discovery, exact binding/read, eligibility and currentness; point execution to actual host/runtime |
| Artifact | Agent confuses file byte storage with format construction/validation | Qualify operation and producing service in discovery/receipts |
| SDK | Agent confuses API client with embedded Agent executor | Distinguish Client SDK / Agent SDK / Provider SDK |
| Source/doc conflict about host.status | Agent incorrectly concludes no such endpoint exists | Correct documentation against current registration; separately verify installation |

These are causal hypotheses backed by standards and source discrepancies. Actual reductions in error rate or operation cost remain unmeasured.

## Bounded discovery probes actually performed

Two isolated agents, one per condition, received identical eight routing tasks. Neither used repository/network tools. One saw existing labels; the other descriptive candidates. This is a qualitative probe with different agents and bundled label changes, not a controlled statistical A/B trial or production rollout.

Old labels: connection setup, Host continuity and Next task scope were explicitly low-confidence/UNKNOWN. Descriptive labels made Work continuity and task representation easier to identify, but Gateway MCP Plugin versus MCP Gateway remained ambiguous; some other confidence judgments decreased. Both conditions withheld claims such as Windows support when names alone did not establish them.

The probe falsified the claim that adding MCP and Plugin to names would necessarily resolve routing. It does not establish a quantitative improvement. Revised candidate: Gateway Client Plugin / Gateway Service, paired with concise role descriptions.

A separate independent researcher initially interpreted Host as environment startup/hosting, then retracted it after reading actual schema10 source. This is a concrete discussion example of lexical ambiguity, not an operational incident.

## Independent Space discussion and revisions

Existing Space: `space:ordivon-whole-system-optimization-r1:20261002`
Existing Topic: `topic:ordivon-whole-system-optimization:core-boundaries-r1:20261002`

| Sequence | Message | Contribution |
|---|---|---|
| 20811 | `message:owner-boundaries-naming-research:20261027:opening` | Source-pinned questions and independent challenge request |
| 20813 | `message:owner-boundaries-naming-research:20261027:surfaces-finding` | Surface standards and naming critique; retract generic Host interpretation |
| 20814 | `message:owner-boundaries-naming-research:20261027:upstream-principles` | Counterexamples to CLI-always-thin and file-count-based merging |
| 20815 | `message:owner-boundaries-naming-research:20261027:counterexamples` | Optional HTTP disproves whole-service MCP-only label; naming probe ambiguity |
| 20816 | `message:owner-boundaries-naming-research:20261027:source-audit` | Independent source/consumer audit of remaining owner groups, complementing the surface audit |
| 20817 | `message:owner-boundaries-naming-research:20261027:surfaces-round2` | Accept Client Plugin/Service distinction; withdraw MCP Gateway rename |

Peer replies use independent ActorRefs and reply relations. Host communication records discussion, not source integration or semantic acceptance.

## Migration proposal

1. Build exact old label/name/path → stable identity → intended role/consumer mapping from current sources. Record historical identities without rewriting historical evidence.
2. Change Agent-visible display names and first-sentence descriptions in current discovery/documentation surfaces. A name may be technically valid while still underspecified.
3. Reuse existing owner-native tests for route identity, exact bindings, public imports, package materialization, affected-owner selection and receipts. Add targeted should-select/should-not-select examples through an existing evaluation framework only when implementing the change.
4. Inventory public plugin installation identity, CLI executable names, import names, MCP tool names, authorization subjects, signed receipts and source hashes before changing them. Display-only changes and public identity changes have different compatibility effects.
5. Migrate public names/path/owner IDs in a separate source-relocation change from semantic refactoring. Use existing alias/migration support where available; do not build a universal alias server or install both old/new packages by default.
6. Validate that old/new entrypoints target the same necessary capability, retain effect/permission boundaries and do not duplicate execution. Re-evaluate only evidence whose bound names, bytes, schemas or assumptions actually changed.
7. Retire obsolete aliases after bounded consumer checks and a defined transition; UNKNOWN is not permission to break an external consumer and not a reason for permanent duplication.

Changing a label does not prove behavior equivalent or permission-safe. Formal obligations attach to exact operation/trace/effect contracts and their implementation bridge; metadata and source membership remain narrower evidence.

## Next implementation boundary

First implementation candidate: rename the misleading client package's Agent-visible title/description and align current consumer documentation, with a separately reviewed public package/path migration. Correct the Gateway host.status documentation conflict in the same responsibility area if current source tests confirm it.

Then improve Host, Next and Skills discovery labels/descriptions. Internal recursive decomposition should follow actual contracts, not the desired naming taxonomy. No production DB migration or broad service rewrite is required by this research.

Independent report review corrected a misleading suggestion that current Host identity was legacy, and narrowed the recorded scope of the independent source audit. No behavior or stable identity was changed.
