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

For cross-provider routing, use `docs/CAPABILITY_AUTHORITY_MAP_R1.md`. It maps primitives to their natural authorities, mature provider candidates, activation triggers, do-not-build boundaries and verification boundaries. It is a catalog/routing view, not a permanent dependency topology.

For web/browser/desktop interaction specifically, `capabilities/profiles/web-interaction-r1.json` is the machine-readable thin-first routing profile and `scripts/web_interaction_route.py` overlays current local/caller-bound availability. Natural-language task interpretation remains Agent/caller-owned; the resolver never treats provider documentation as availability truth. The reusable Agent procedure lives at `.agents/skills/web-provider-routing/SKILL.md`.


## Provider currentness

Provider records are routing knowledge, not a live provider registry. A dated statement that a CLI, image, service, model, installer, or local binding was observed does not remain current merely because the Markdown file remains.

At task time, prefer the provider's natural currentness source:

- CLI/package identity: provider-native `--version` or the repository's locked dependency resolution;
- container/image identity: container runtime image inspection and digest;
- installed release/binding: the release manager or owner-native binding/profile command;
- remote service: its authenticated health/version/capability surface when such a query is semantically valid;
- external standard/provider version knowledge: append-only records under `authorities/observations/` where appropriate.

If no trustworthy current probe exists, treat the local availability statement as a dated observation and revalidate before relying on it. Do not create a durable Ordivon ProviderStatus database merely to centralize facts already owned by package managers, container runtimes, services, or other natural providers.
