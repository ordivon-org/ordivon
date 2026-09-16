# External-first Agent capability packaging

Date: 2026-09-16
Status: **ADOPT UPSTREAM / KEEP SKILL COMPOSITION OPTIONAL**

## Decision

Ordivon will use published external standards for portable Agent capability packaging instead of creating a private Domain Capability Pack, Skill registry, or cross-Harness plugin format.

Canonical upstream ownership:

- **Agent Plugins 1.0** owns one portable package boundary: root `plugin.json`, optional `skills/`, optional `mcp.json`, and reverse-domain client extensions.
- **Agent Skills** owns reusable procedural Skill content and `SKILL.md` semantics independently of whether a Skill is bundled in an Agent Plugin.
- **MCP** owns Agent-facing capability/context interoperability.
- Client/provider-native systems own installation, authentication, permissions, registries, execution and domain truth unless an upstream standard explicitly owns them.

Agent Plugin is therefore a **composition/distribution surface**, not the semantic owner of Skills, Runtime, Host, or domain implementations. Ordivon-owned Skills remain independently meaningful Agent Skills. Whether a release should bundle selected Skills under an Agent Plugin is a consumer-driven packaging decision that must be justified by native-client E2E evidence.

Ordivon continues to own only state and semantics that are genuinely local to Ordivon, especially Runtime physical execution evidence and Host continuity/collaboration.

## Local asset disposition

| Local asset / mechanism | Disposition | Upstream owner / target | Action |
| --- | --- | --- | --- |
| `.agents/skills/*/SKILL.md` | **ADOPT-UPSTREAM / KEEP CONTENT** | Agent Skills | Keep as canonical project-level procedural content. Do not wrap in a private Skill format and do not assume Plugin ownership. |
| Agent Plugin `skills/` component | **OPTIONAL COMPOSITION** | Agent Plugins + Agent Skills | Bundle selected canonical Skills only when a release/consumer requires them. Omission is the default. |
| Agent Skill progressive disclosure | **REPLACE-UPSTREAM** | Agent Skills client guidance | Let capable clients discover/activate Skills natively. |
| Project/user Skill scope | **REPLACE-UPSTREAM** | Agent Skills client guidance | Use project/user scope and `.agents/skills` convention rather than Ordivon scope ontology. |
| Project-over-user Skill collision rule | **REPLACE-UPSTREAM** | Agent Skills client guidance | Use the standard client convention; only require deterministic same-scope behavior. |
| Legacy `.codex-plugin`, `~/.codex/skills`, `~/.hermes/skills` scanning | **TEMP-BRIDGE** | Agent Plugins / Agent Skills client-native installation | Retain only while migrating installed legacy assets; do not make these roots part of a new Ordivon standard. |
| Custom cross-source namespace generation | **RETIRE** | Agent Plugins package identity + client discovery | Do not create permanent `repo/plugin/source` namespace semantics. |
| `skills.list/search/resolve/read` MCP service | **TEMP-BRIDGE** | Direct Agent Skill / Agent Plugin client support | Retain only for clients that cannot directly consume local standard assets. Retire per-consumer when direct loading is available. |
| `skill://...` custom resource projection | **TEMP-BRIDGE** | Client-native Skill activation/file access | Not a canonical Skill URI standard. Remove with the bridge. |
| Skill catalog snapshot/CAS as generic platform feature | **DO NOT EXPAND** | Client/package versions + client-native state | Keep only where the remote bridge requires immutable activation/currentness fences. |
| Custom persistent Skill trust DB/scanner | **DO NOT BUILD** | Client trust/permissions/sandboxing | Direct clients own trust. The bridge retains only narrow filesystem-to-network projection protections. |
| Quarantining untrusted project instructions | **KEEP PRINCIPLE, MINIMIZE MECHANISM** | Client-local trust policy | Never let an untrusted repository silently inject instructions. Use the thinnest client-local/bridge gate available. |
| Model-visible blocked/quarantined metadata | **RETIRE** | Client diagnostics/UI | Filter unavailable/denied Skills out of the model catalog; do not expose hostile descriptions merely for diagnostics. |
| Skill semantic search / learned-Skill Workshop / private marketplace | **RETIRE / DEFER UPSTREAM** | Client/plugin ecosystem | Do not build while upstream ecosystems own discovery and distribution. |
| Private Domain Capability Pack schema/resolver/snapshot | **RETIRED** | Agent Plugins + Skills + MCP + provider-native semantics | No implementation. |
| Runtime MCP semantics | **KEEP ORDIVON OWNER; PACKAGE STANDARDLY** | MCP + optional Agent Plugins `mcp.json` composition | Runtime remains physical Job/Attempt/Artifact authority. |
| Host MCP semantics | **KEEP ORDIVON OWNER; PACKAGE STANDARDLY** | MCP + optional Agent Plugins `mcp.json` composition | Host remains continuity/collaboration authority. |
| Artifact / Research / Game / Market Capital implementations | **KEEP DOMAIN OWNER** | Their native standards/providers | Do not turn domains into plugin ontologies. Package only reusable Skills and MCP connection surfaces when useful. |
| `capabilities/packages/*.md` | **KEEP AS HUMAN KNOWLEDGE** | N/A | Treat as local routing/knowledge documents, not machine package schemas. |
| Private MCP registry | **DO NOT BUILD** | Official MCP Registry / client config | Use upstream registry when public distribution is appropriate; private authenticated endpoints may remain client-configured. |

## First standards-native package

`plugins/ordivon-control-plane/` is a direct Agent Plugins 1.0 package skeleton. It contains no Ordivon-specific manifest schema and no copied implementation code:

```text
plugins/ordivon-control-plane/
├── plugin.json
└── mcp.json
```

`mcp.json` declares the existing Streamable HTTP MCP endpoints:

- `https://mcp.ordivon.com/mcp` — Ordivon Runtime;
- `https://host-mcp.ordivon.com/mcp` — Ordivon Host.

The package contains no credentials, OAuth metadata, secret references, or custom auth extension. Authentication remains client-managed.

## Skill composition rule

Do **not** create a second source copy of existing `.agents/skills` merely to satisfy the optional Agent Plugins `skills/` component.

Current rule:

1. keep repository Skills canonically under `.agents/skills` for direct cross-client project discovery;
2. a normal `ordivon-control-plane` release materializes the Plugin skeleton without Skills;
3. if a concrete consumer/release needs Plugin-bundled Skills, explicitly compose them with `--include-skills` from the canonical Skill directories;
4. do not add Ordivon metadata to `SKILL.md` beyond fields allowed by Agent Skills;
5. do not make release-artifact duplication into a second source of truth;
6. bundling a Skill does not transfer its semantic ownership to Agent Plugin.

The release path is executable through the stdlib-only `scripts/materialize_agent_plugin.py`. It treats `plugins/ordivon-control-plane/` as the portable package skeleton, rejects symlinks/non-regular package input and overwrites, writes only to a caller-selected release directory, and writes its digest receipt outside the portable package.

MCP-only/default release:

```bash
python3 scripts/materialize_agent_plugin.py \
  --output /tmp/ordivon-control-plane-release \
  --receipt /tmp/ordivon-control-plane-release.receipt.json
```

Explicit release composition with current project Skills:

```bash
python3 scripts/materialize_agent_plugin.py \
  --include-skills \
  --output /tmp/ordivon-control-plane-with-skills-release \
  --receipt /tmp/ordivon-control-plane-with-skills-release.receipt.json
```

Both outputs can be checked with native client tooling, for example:

```bash
hermes plugins validate /tmp/ordivon-control-plane-release
hermes plugins doctor --ci /tmp/ordivon-control-plane-release
```

The materializer intentionally does **not** implement another Agent Skills YAML/schema parser. Agent Skills semantics remain upstream-owned; any explicitly bundled Skill component is validated by standard/native consumers. Release receipts record whether Skill composition was `included` or `omitted`.

## Skill MCP R2 re-scope

The current Skill MCP implementation is not the target Skill architecture. It is a **temporary compatibility bridge** for remote/client gaps.

The bridge is currently publicly reachable at `skills-mcp.ordivon.com` behind a dedicated Cloudflare Access Managed OAuth application while the origin remains loopback-bound. Public reachability does not promote the bridge into canonical Skill ownership. It exists only because a remote ChatGPT-style consumer cannot directly read the local filesystem/package state.

Allowed bridge responsibilities are limited to:

- project already-standard Agent Skills to a remote client that cannot read the local filesystem;
- enforce the minimum filesystem-to-network trust/allowlist boundary before instruction content reaches that client;
- preserve path containment, symlink rejection, bounded reads, digest/currentness fences, hidden quarantined content and secret/private-key quarantine;
- translate standard local assets to an MCP read/activation surface where direct Agent Skill or Agent Plugin consumption is unavailable.

The bridge must not become the owner of Skill identity, package format, marketplace, universal precedence, learned-Skill governance, or provider execution authority. It has no justification for a persistent trust database or semantic scanner oracle.

## Skill ↔ Agent Plugin decision gate

Do not decide the long-term composition boundary from format capability alone. Agent Plugins v1 permits Skills as a component, but that only proves that bundling is legal.

Before making Plugin-bundled Skills the Ordivon default, collect consumer evidence for at least:

1. native Agent Skill discovery from `.agents/skills` without Plugin packaging;
2. native Agent Plugin install/enable/upgrade/uninstall lifecycle;
3. bundled Skill discovery/activation from the same Plugin;
4. MCP-only Plugin behavior without bundled Skills;
5. refresh semantics after Skill change and Plugin upgrade/removal;
6. ownership/versioning friction when third-party or user Skills coexist with Ordivon-owned Skills.

The resulting policy may legitimately be one of three forms:

- Skills stay independently distributed and the control-plane Plugin remains MCP-only;
- selected Ordivon-owned Skills are optionally composed into specific Plugin releases;
- native-client evidence shows that bundling should become the default for a well-defined release channel.

No option is preselected.

## No-extension default

Agent Plugins permits reverse-domain client extensions, but Ordivon starts with **none**.

Only add an Ordivon namespace if a concrete client-specific need cannot be represented by the portable core or kept as local Runtime/Host configuration. The extension must remain ignorable by other clients and must never redefine portable Skill or MCP semantics.

## Adoption order

```text
upstream standard / native client
        ↓
independent Agent Skills and MCP surfaces
        ↓
configuration
        ↓
optional Agent Plugin composition for a concrete distribution need
        ↓
minimal compatibility bridge for a demonstrated client gap
        ↓
Ordivon-specific implementation only for irreducible local authority/state
```

The default answer to a new packaging/discovery feature is therefore **do not implement it in Ordivon** until the corresponding upstream/client-native path has been ruled out for a real use case.
