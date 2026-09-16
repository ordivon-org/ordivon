# Skill MCP Standards Alignment

Status: standards-first migration slice

## Upstream reference pins (2026-09-16)

- Agent Skills: `agentskills/agentskills@69ef37e9424c0a7ea9dd2293b559e43ec8176379`; immutable tarball SHA-256 `0c9eabbe602095c4f4d771ee55bf74f6bc7e1c770f25d4fe29ce9802981daa20`.
- MCP Skills extension: `modelcontextprotocol/ext-skills@81f55b67fee51515b969c372911e2b28cf217c20`.
- `skills-ref` at the Agent Skills pin is version `0.1.0` and explicitly describes itself as demonstration/reference code. Normative specification text wins if the reference implementation is looser or contradictory.
- Both upstreams were reached through the existing isolated Network v2 WireGuard namespace `nv2-browserless-prod`; the Skills MCP service's default egress authority was not widened.

These pins are audit anchors, not permanent dependency versions. A standards refresh must compare newer normative text and reference tests before changing Ordivon behavior.

## Canonical external standards

Ordivon does not define a new Skill package format. Portable Skill packages conform to the Agent Skills specification and use `SKILL.md` plus ordinary package resources. Product- or Harness-specific fields are adapters/sidecars, not additions to the portable contract.

Ordivon does not define a new remote Skill transport. The canonical MCP surface is the `io.modelcontextprotocol/skills` extension (SEP-2640):

- `skills/list` for bounded discovery,
- `skills/get` for exact Skill retrieval,
- standard MCP `resources/read` for Skill files, and
- optional `resources/directory/read` only when explicitly implemented and advertised.

For MCP 2026-07-28, clients discover the server and extension surface with `server/discover`; the removed legacy initialize/session handshake is not an Ordivon compatibility requirement for the modern endpoint.

## Ordivon-owned responsibilities

The Skill Plane remains responsible for host policy and federation, not portable Skill semantics:

- source discovery/adapters across `.agents/skills`, Codex, Hermes, vendor and plugin roots;
- collision-preserving raw inventory and provenance;
- trust, scanning, quarantine and source-health isolation;
- eligibility observations from explicitly named Harness adapters;
- workspace applicability and visibility policy;
- catalog refresh, revision/digest fences and cache policy;
- search/ranking UX above the standard transport; and
- optional compatibility shims for legacy clients.

`sourceId/name`, `catalogRevision`, `snapshotRevision`, trust state, scanner findings and workspace policy are Ordivon internal/control-plane concepts. They do not redefine Agent Skills identity. A remotely served Skill is identified by its originating MCP server plus its Skill URI.

## Strict standard projection

The SEP-2640 endpoint is fail-closed: a raw/local Skill that does not satisfy the portable Agent Skills contract remains available to the appropriate local Harness adapter but is not advertised as a standards-conforming remote Skill. Ordivon does not silently rewrite third-party frontmatter to make it appear portable.

The standard projection currently enforces the portable frontmatter surface (`name`, `description`, `license`, `compatibility`, `metadata`, experimental `allowed-tools`), parent-directory/name identity, and the SEP-2640 static-resource limits of 512 resources and 16 MiB total. Nested or product-specific metadata remains adapter data unless explicitly projected by a standards-preserving converter.

When available in CI, the upstream Agent Skills reference validator (`skills-ref`) should be used as an independent conformance oracle. It is not a runtime dependency or an Ordivon security authority.

## Product-specific metadata

Follow the mature portable-core + product-sidecar pattern. For example, OpenAI-specific machine configuration belongs under `agents/openai.yaml`, rather than expanding portable `SKILL.md` semantics. The same principle applies to Ordivon: trust, approval, scanner state, Runtime authority and credentials belong in the Ordivon control plane, not in the Skill package.

## Migration policy

The existing model-facing tools `skills.list`, `skills.search`, `skills.resolve` and `skills.read` are a temporary compatibility shim. New remote/ChatGPT integrations must prefer SEP-2640. Do not add new semantic features to the legacy wire unless required for a bounded migration bug.

The old revision-bearing `skill://{sourceId}/{name}/{packageRevision}/...` resource form remains compatibility-only. The standards surface uses stable Skill resource URIs under the MCP server origin; byte freshness is expressed by SEP-2640 resource digests and host-side catalog refresh/fencing.

Project/workspace Skills are not projected on the context-free standards endpoint until workspace identity is bound by the server/connector control plane. Model-supplied filesystem paths are never source-registration or trust authority.

## Deferred optional capabilities

- `resources/directory/read`: not advertised until implemented.
- dialect-to-standard virtual conversion: explicit adapter only, with emitted bytes and manifest digests matching exactly.
- per-agent visibility: only after agent identity is control-plane bound.
- richer search/ranking: host UX, not a replacement for SEP-2640 identity or transport.

## Acceptance gate

A standards-first release must prove:

1. `server/discover` advertises `io.modelcontextprotocol/skills`;
2. `skills/list` returns only standards-conforming visible Skills;
3. `skills/get` can retrieve an exact URI, including eligible explicit-only Skills allowed by host policy;
4. every static resource is listed with SHA-256 digest and size;
5. `resources/read` returns bytes matching the advertised manifest;
6. same-name Skills remain distinct by URI/origin;
7. nonconforming dialect Skills remain visible only through their owning adapter/legacy compatibility path and are never silently normalized; and
8. legacy four-tool clients remain a bounded compatibility concern, not the canonical architecture.
