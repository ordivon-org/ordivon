# Capabilities

A capability is independent of the specific tool that provides it.

Capability records should eventually capture only evidence-backed fields such as:

- capability identity and problem classes served;
- **natural semantic authority / object whose lifecycle the capability owns**;
- inputs/outputs;
- preconditions/postconditions;
- side effects and reversibility;
- authority/risk requirements;
- deterministic vs agentic behavior;
- cost/latency/resource characteristics where relevant;
- compatible standards/methods;
- available providers/tools;
- activation trigger / evidence threshold for introducing operational state;
- applicable validators and the boundary beyond which provider success is insufficient.

Existing Runtime, Network, Artifact, Distribution and other systems should be exposed here as replaceable capability providers rather than absorbed as identity-defining Ordivon subsystems.

For cross-provider routing, use `catalogs/capabilities/authority-map-r1.md`. It maps primitives to their natural authorities, mature provider candidates, activation triggers, do-not-build boundaries and verification boundaries. It is a catalog/routing view, not a permanent dependency topology.

For web/browser/desktop interaction specifically, `catalogs/capabilities/profiles/web-interaction-r1.json` is the machine-readable thin-first routing profile and `catalogs/capabilities/routing/web_provider_census.py` observes bounded local provider availability, while `catalogs/capabilities/routing/web_interaction_route.py` combines that observation with task needs and caller-bound availability. Natural-language task interpretation remains Agent/caller-owned; the resolver never treats provider documentation as availability truth. The reusable Agent procedure lives at `.agents/skills/web-provider-routing/SKILL.md`.


## Provider currentness

Provider records are routing knowledge, not a live provider registry. A dated statement that a CLI, image, service, model, installer, or local binding was observed does not remain current merely because the Markdown file remains.

At task time, prefer the provider's natural currentness source:

- CLI/package identity: provider-native `--version` or the repository's locked dependency resolution;
- container/image identity: container runtime image inspection and digest;
- installed release/binding: the release manager or owner-native binding/profile command;
- remote service: its authenticated health/version/capability surface when such a query is semantically valid;
- external standard/provider version knowledge: append-only records under `authorities/observations/` where appropriate.

If no trustworthy current probe exists, treat the local availability statement as a dated observation and revalidate before relying on it. Do not create a durable Ordivon ProviderStatus database merely to centralize facts already owned by package managers, container runtimes, services, or other natural providers.

## External Learning & Evolution (ELE) project studies on PostgreSQL

The existing provider analyses, knowledge decompositions, package studies and
pinned evidence can be imported as a source-bound, searchable PostgreSQL
projection. See [ELE PG study guide](ele/README.md) and
[the native CLI](ele/studies.py). Git source remains the natural Owner's edited
truth until each real consumer has migrated; the PG index is not installed
provider state or an executable/formal LEGO registry.

## External capability evaluation (LEP method)

For a real consumer, see the [Human review guide](docs/HUMAN_EXTERNAL_LEGO_REVIEW_R1.md), [Agent Owner instructions](AGENTS.md), and [architecture/contract](docs/EXTERNAL_CAPABILITY_EVALUATION_R1.md). The reusable Agent Skill is under .agents/skills/external-capability-evaluation/SKILL.md.

Catalog records discovery and evidence, not live provider status, installation, R2.1 admission, or Owner promotion.\r\n\r\n## Tool discovery facets (not another tool registry)

For an Agent requesting a tool, retain these separate observations instead of
flattening them into a single `available=true` classification:

| Question | Existing natural source |
| --- | --- |
| What problem/capability is needed? | This Catalog's capability/authority map, then the domain Owner |
| What procedure should the Agent use? | Relevant project or trusted external Agent Skill |
| Which callable carrier exists? | Live MCP tool definitions, provider-native CLI/API, or `mise tasks ls` |
| Which node/identity can resolve it? | [Workstation inventory](../../platform/workstation/inventory/README.md), probed in the target Runtime context |
| Is the tool currently usable? | Provider-native version/health and execution/readback in that context |
| Is the requested effect accepted? | Natural domain/provider Owner; not the Catalog or a Skill |

Tool facets are **many-to-many**: FFmpeg may satisfy Media, Artifact and Game
consumers without becoming three separate installs or three duplicated registries.
Use the existing [web route profile](profiles/web-interaction-r1.json) and
[web routing Skill](../../.agents/skills/web-provider-routing/SKILL.md)
as the demonstrated on-demand route/probe pattern; other domains retain their
native provider contracts. An unknown or stale observation must not be
silently promoted to a current, callable tool.
