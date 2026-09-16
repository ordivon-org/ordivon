# External-first Agent capability packaging

Date: 2026-09-16
Status: **ADOPT UPSTREAM / REMOVE PRIVATE PACKAGING SEMANTICS**

## Decision

Ordivon will use the published external standards for portable Agent capability packaging instead of creating a private Domain Capability Pack, Skill registry, or cross-Harness plugin format.

Canonical upstream ownership:

- **Agent Plugins 1.0** owns the portable package boundary: root `plugin.json`, optional `skills/`, optional `mcp.json`, and reverse-domain client extensions.
- **Agent Skills** owns reusable procedural Skill content and `SKILL.md` semantics.
- **MCP** owns Agent-facing capability/context interoperability.
- Client/provider-native systems own installation, authentication, permissions, registries, execution and domain truth unless an upstream standard explicitly owns them.

Ordivon continues to own only state and semantics that are genuinely local to Ordivon, especially Runtime physical execution evidence and Host continuity/collaboration.

## Local asset disposition

| Local asset / mechanism | Disposition | Upstream owner / target | Action |
| --- | --- | --- | --- |
| `.agents/skills/*/SKILL.md` | **ADOPT-UPSTREAM / KEEP CONTENT** | Agent Skills | Keep as canonical project-level procedural content. Do not wrap in a private Skill format. |
| Agent Skill progressive disclosure | **REPLACE-UPSTREAM** | Agent Skills client guidance | Let capable clients discover/activate Skills natively. |
| Project/user Skill scope | **REPLACE-UPSTREAM** | Agent Skills client guidance | Use project/user scope and `.agents/skills` convention rather than Ordivon scope ontology. |
| Project-over-user Skill collision rule | **REPLACE-UPSTREAM** | Agent Skills client guidance | Use the standard client convention; only require deterministic same-scope behavior. |
| Legacy `.codex-plugin`, `~/.codex/skills`, `~/.hermes/skills` scanning | **TEMP-BRIDGE** | Agent Plugins / Agent Skills client-native installation | Retain only while migrating installed legacy assets; do not make these roots part of a new Ordivon standard. |
| Custom cross-source namespace generation | **RETIRE** | Agent Plugins package identity + client discovery | Do not create permanent `repo/plugin/source` namespace semantics. |
| `skills.list/search/resolve/read` MCP service | **TEMP-BRIDGE** | Direct Agent Plugin / Agent Skill client support | Keep loopback-only only for clients that cannot directly consume local standard assets. Retire when direct client loading is available. |
| `skill://...` custom resource projection | **TEMP-BRIDGE** | Client-native Skill activation/file access | Not a canonical Skill URI standard. Remove with the bridge. |
| Skill catalog snapshot/CAS as generic platform feature | **DO NOT EXPAND** | Plugin/package versions + client-native state | Keep only if a concrete local security/continuity requirement survives direct standard adoption. |
| Custom persistent Skill trust DB/scanner | **DO NOT ASSUME** | Client trust/permissions/sandboxing | Agent Plugins deliberately leaves trust policy to clients. Prefer client/project trust and allowlisting before building a new trust subsystem. |
| Quarantining untrusted project instructions | **KEEP PRINCIPLE, MINIMIZE MECHANISM** | Client-local trust policy | Never let an untrusted repository silently inject instructions. Implementation should be the thinnest client-local gate available. |
| Model-visible blocked/quarantined metadata | **RETIRE** | Client diagnostics/UI | Filter unavailable/denied Skills out of the model catalog; do not expose hostile descriptions merely for diagnostics. |
| Skill semantic search / learned-Skill Workshop / private marketplace | **RETIRE / DEFER UPSTREAM** | Client/plugin ecosystem | Do not build while upstream ecosystems own discovery and distribution. |
| Private Domain Capability Pack schema/resolver/snapshot | **RETIRED** | Agent Plugins + Skills + MCP + provider-native semantics | No implementation. |
| Runtime MCP semantics | **KEEP ORDIVON OWNER; PACKAGE STANDARDLY** | MCP + Agent Plugins `mcp.json` | Runtime remains physical Job/Attempt/Artifact authority; expose/connect it using standard MCP configuration. |
| Host MCP semantics | **KEEP ORDIVON OWNER; PACKAGE STANDARDLY** | MCP + Agent Plugins `mcp.json` | Host remains continuity/collaboration authority; expose/connect it using standard MCP configuration. |
| Artifact / Research / Game / Market Capital implementations | **KEEP DOMAIN OWNER** | Their native standards/providers | Do not turn domains into plugin ontologies. Package only reusable Skills and MCP connection surfaces when useful. |
| `capabilities/packages/*.md` | **KEEP AS HUMAN KNOWLEDGE** | N/A | Treat as local routing/knowledge documents, not machine package schemas. |
| Private MCP registry | **DO NOT BUILD** | Official MCP Registry / client config | Use upstream registry when public distribution is appropriate; private authenticated endpoints may remain client-configured. |

## First standards-native package

`plugins/ordivon-control-plane/` is a direct Agent Plugins 1.0 package. It contains no Ordivon-specific manifest schema and no copied implementation code:

```text
plugins/ordivon-control-plane/
├── plugin.json
└── mcp.json
```

`mcp.json` declares the existing Streamable HTTP MCP endpoints:

- `https://mcp.ordivon.com/mcp` — Ordivon Runtime;
- `https://host-mcp.ordivon.com/mcp` — Ordivon Host.

Both endpoints are currently protected and return an OAuth/Cloudflare authentication challenge without a valid client token. Agent Plugins 1.0 deliberately keeps authentication client-managed, so the package contains no credentials, OAuth metadata, secret references, or custom auth extension.

## Skills packaging rule

Do **not** create a second source copy of existing `.agents/skills` merely to satisfy the Agent Plugins `skills/` fixed directory.

Current rule:

1. keep repository Skills canonically under `.agents/skills` for direct cross-client project discovery;
2. when a distributable Agent Plugin containing those Skills is actually required, materialize `skills/` in the release artifact from the canonical Skill directories;
3. do not add Ordivon metadata to `SKILL.md` beyond fields allowed by the Agent Skills format;
4. do not make release-artifact duplication into a second source of truth.

This keeps direct repository use simple while preserving standards-native distribution.

The release path is now executable through the stdlib-only `scripts/materialize_agent_plugin.py`. It treats `plugins/ordivon-control-plane/` as the portable package skeleton and `.agents/skills/` as the only Skill source, rejects symlinks/non-regular package input and overwrites, writes the generated `skills/` tree only to a caller-selected release directory, and writes its digest receipt outside the portable package.

Example:

```bash
python3 scripts/materialize_agent_plugin.py \
  --output /tmp/ordivon-control-plane-release \
  --receipt /tmp/ordivon-control-plane-release.receipt.json
hermes plugins validate /tmp/ordivon-control-plane-release
hermes plugins doctor --ci /tmp/ordivon-control-plane-release
```

The materializer intentionally does **not** implement another Agent Skills YAML/schema parser. Agent Skills semantics remain upstream-owned; the generated package is validated by standard/native consumers. A real three-Skill materialization is byte-stable across repeated builds and passes Hermes portable-manifest validation plus runtime Plugin Doctor without an Ordivon plugin loader.

## Skill MCP R2 re-scope

The current Skill MCP implementation is no longer the target architecture. It becomes a **temporary compatibility bridge**.

Allowed bridge responsibilities are only those required by a client gap, for example:

- make already-standard Agent Skills available to a remote client that cannot read the local filesystem;
- enforce a minimal local trust/allowlist boundary before instruction content reaches that client;
- translate standard local assets to an MCP read/activation surface when direct Agent Plugin support is unavailable.

The bridge must not become the owner of Skill identity, package format, marketplace, universal precedence, learned-Skill governance, or provider execution authority.

Cloudflare/public promotion of the current bridge remains frozen until there is a demonstrated client requirement that cannot be met by direct Agent Plugins / Agent Skills support.

## No-extension default

Agent Plugins permits reverse-domain client extensions, but Ordivon should start with **none**.

Only add an Ordivon namespace if a concrete client-specific need cannot be represented by the portable core or kept as local runtime/host configuration. The extension must remain ignorable by other clients and must never redefine portable Skill or MCP semantics.

## Adoption order

```text
upstream standard/native client
        ↓
configuration
        ↓
standard Agent Plugin packaging
        ↓
minimal compatibility bridge if a concrete client gap remains
        ↓
Ordivon-specific implementation only for irreducible local authority/state
```

The default answer to a new packaging/discovery feature is therefore **do not implement it in Ordivon** until the corresponding upstream/client-native path has been ruled out for a real use case.
