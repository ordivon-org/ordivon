# Skill MCP Standards Alignment

Status: standards-first temporary-bridge profile

## Upstream audit anchors (2026-09-16)

- Agent Skills audit pin: `agentskills/agentskills@69ef37e9424c0a7ea9dd2293b559e43ec8176379`; recorded immutable tarball SHA-256 `0c9eabbe602095c4f4d771ee55bf74f6bc7e1c770f25d4fe29ce9802981daa20`.
- MCP Skills extension audit pin: `modelcontextprotocol/ext-skills@81f55b67fee51515b969c372911e2b28cf217c20`.
- `skills-ref` is a reference/demonstration implementation and an independent test oracle, not the normative specification or a production runtime dependency.
- The normative Agent Skills specification wins whenever explanatory material, tests, or reference code are looser, stricter, or contradictory.

These pins are audit anchors, not permanent dependency versions. A standards refresh must compare the current normative specification before changing bridge behavior.

## Upstream reference pins (2026-09-16)

- Agent Skills: `agentskills/agentskills@69ef37e9424c0a7ea9dd2293b559e43ec8176379`; immutable tarball SHA-256 `0c9eabbe602095c4f4d771ee55bf74f6bc7e1c770f25d4fe29ce9802981daa20`.
- MCP Skills extension: `modelcontextprotocol/ext-skills@81f55b67fee51515b969c372911e2b28cf217c20`.
- `skills-ref` at the Agent Skills pin is version `0.1.0` and explicitly describes itself as demonstration/reference code. Normative specification text wins if the reference implementation is looser or contradictory.
- Both upstreams were reached through the existing isolated Network v2 WireGuard namespace `nv2-browserless-prod`; the Skills MCP service's default egress authority was not widened.

These pins are audit anchors, not permanent dependency versions. A standards refresh must compare newer normative text and reference tests before changing Ordivon behavior.

## Canonical external standards

Ordivon does not define a new Skill package format. Portable Skill packages conform to Agent Skills and use `SKILL.md` plus ordinary package resources. Product- or Harness-specific fields are adapters/sidecars, not additions to the portable contract.

The current Agent Skills name contract is enforced directly: 1-64 characters, Unicode lowercase alphanumeric characters plus hyphens, no leading/trailing hyphen, no consecutive hyphens, and an exact match to the parent directory name. The specification does not currently grant the bridge authority to normalize names before comparing them. In particular, canonical Unicode/NFKC equivalence is not treated as directory-name equality unless a future normative specification explicitly says so.

Ordivon does not define a new remote Skill transport. The canonical standards projection is the `io.modelcontextprotocol/skills` extension (SEP-2640):

- `skills/list` for bounded discovery,
- `skills/get` for exact Skill retrieval,
- standard MCP `resources/read` for Skill files, and
- optional `resources/directory/read` only when explicitly implemented and advertised.

For MCP 2026-07-28, clients discover the server and extension surface with `server/discover`; removed legacy initialize/session behavior is not reintroduced as an Ordivon protocol.

## Bridge-only Ordivon responsibilities

The running Skill MCP is a temporary filesystem-to-remote-client compatibility bridge. It does not own a universal Skill Plane, registry, namespace, marketplace, learned-Skill lifecycle, or cross-Harness ontology.

While this bridge exists, Ordivon retains only the irreducible local projection boundary:

- operator-configured source/workspace admission rather than model-selected filesystem roots;
- project roots untrusted unless locally admitted;
- path containment and symlink/non-regular-file rejection;
- bounded reads and package/resource limits;
- exact instruction/package/snapshot digest-currentness fences where remote projection needs them;
- suppression of blocked/quarantined Skill descriptions and instructions from model-visible catalogs;
- secret/private-key quarantine before local files can be projected remotely; and
- compatibility adapters for already-installed legacy client roots only while a concrete consumer still needs them.

Prompt-override/shell heuristics remain warnings, not a semantic trust oracle. There is no justification for a persistent Ordivon Skill trust database merely because a temporary remote bridge exists.

When a client directly consumes Agent Skills or an Agent Plugin package and no filesystem-to-network projection remains, bridge-specific trust/path/digest/scanner machinery should be removed for that consumer.

## Strict standards projection

The SEP-2640 endpoint is fail-closed: a raw/local Skill that does not satisfy the portable Agent Skills contract is not advertised as a standards-conforming remote Skill. Ordivon does not silently rewrite third-party frontmatter to make it appear portable.

The standards projection enforces the published frontmatter surface (`name`, `description`, `license`, `compatibility`, `metadata`, experimental `allowed-tools`), exact parent-directory/name identity, and the SEP-2640 static-resource limits of 512 resources and 16 MiB total. Published optional fields are preserved as authored after YAML parsing rather than translated into an Ordivon schema.

Unicode names are URI-percent-encoded per path segment on the compatibility `skill://` projection and round-trip to the original Skill name. URI escaping is transport safety, not Skill identity normalization.

When available in CI, the upstream Agent Skills reference validator (`skills-ref`) may be used as an independent conformance oracle. Agreement with it is useful evidence but cannot create requirements absent from the normative specification.

## Product-specific metadata

Follow the portable-core + product-sidecar pattern. Product-specific machine configuration and Ordivon control-plane state must not expand portable `SKILL.md` semantics. Trust, approval, scanner state, Runtime authority, credentials and OAuth state remain outside the Skill package.

## Migration policy

The model-facing tools `skills.list`, `skills.search`, `skills.resolve` and `skills.read` remain a bounded compatibility surface for clients that cannot consume the standards projection or local Agent Skills directly. New semantic features must not be added to that four-tool wire merely because they are convenient to implement.

The compatibility `skill://` resource form is not a universal Skill URI standard. SEP-2640 resource digests plus local catalog/currentness fences protect the temporary bridge; they must not grow into a permanent Ordivon-wide version/CAS platform.

Project/workspace Skills are not projected from model-supplied filesystem paths. Workspace/source identity is control-plane configuration, never prompt authority.

## Skill and Agent Plugin remain separable

Agent Plugins can bundle an optional `skills/` component, but that packaging capability does not make Agent Plugin the semantic owner of Agent Skills. Ordivon must preserve the ability to:

- consume canonical `.agents/skills` directly;
- expose a remote Skill bridge where a client gap requires it;
- compose selected Skills into an Agent Plugin release explicitly; and
- omit Skills from an Agent Plugin release when MCP-only packaging is sufficient.

The long-term Skill ↔ Agent Plugin default is decided by native-client lifecycle and refresh evidence, not by format convenience.

## Deferred / rejected platform features

- `resources/directory/read`: deferred until a concrete consumer requires and validates it.
- dialect-to-standard virtual conversion: only an explicit standards-preserving adapter with byte/digest evidence; never silent rewriting.
- per-agent visibility: only when agent identity is control-plane bound.
- universal Skill registry/search/marketplace/workshop/watcher: rejected as Ordivon-owned platform scope while upstream/client ecosystems own those concerns.
- persistent trust database or semantic maliciousness classifier: rejected absent a separate irreducible requirement.

## Acceptance gate

A standards-first bridge release must prove:

1. `server/discover` advertises `io.modelcontextprotocol/skills`;
2. `skills/list` returns only standards-conforming visible Skills;
3. `skills/get` can retrieve an exact URI, including eligible explicit-only Skills allowed by local policy;
4. every static resource is listed with SHA-256 digest and size;
5. `resources/read` returns bytes matching the advertised manifest;
6. same-name Skills remain distinct by URI/origin;
7. Unicode lowercase alphanumeric Skill names round-trip through URI encoding;
8. parent-directory/name comparison is exact and does not silently accept NFKC-equivalent-but-different strings;
9. nonconforming dialect Skills are never silently normalized onto the standards surface; and
10. the legacy four-tool surface remains compatibility debt rather than canonical Skill architecture.
