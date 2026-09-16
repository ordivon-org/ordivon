# Skills bridge standards alignment

Status: implementation contract for the temporary Ordivon Skills MCP compatibility bridge.

The bridge does not define a portable Skill or Plugin format. Portable semantics are owned by upstream standards:

- Agent Skills: <https://agentskills.io/specification>
- Agent Skills client implementation guidance: <https://agentskills.io/client-implementation/adding-skills-support>
- Agent Plugins 1.0.0: <https://agent-plugins.org/specification>
- MCP 2026-07-28: <https://modelcontextprotocol.io/specification/2026-07-28>

## Ownership map

| Existing concern | Standing | Authority after alignment |
| --- | --- | --- |
| `SKILL.md` portable format | REPLACE-UPSTREAM | Agent Skills specification |
| YAML parsing | REPLACE-UPSTREAM | YAML 1.2-compatible parser (`PyYAML`), validated against Agent Skills fields |
| author/package conformance | REPLACE-UPSTREAM | strict Agent Skills validation; `skills-ref` is a reference oracle only, not a production dependency |
| runtime ingestion | REPLACE-UPSTREAM | official Agent Skills client guidance: lenient ingestion with diagnostics |
| project/user interop roots | REPLACE-UPSTREAM | `<project>/.agents/skills` and `~/.agents/skills` |
| project-over-user collision rule | REPLACE-UPSTREAM | Agent Skills client implementation convention |
| within-scope collision rule | REPLACE-UPSTREAM | deterministic first/source-order rule; no custom ambiguity protocol |
| model catalog | REPLACE-UPSTREAM | progressive disclosure: effective `name + description` catalog; shadowed duplicates stay out of the model catalog |
| portable plugin package | REPLACE-UPSTREAM | Agent Plugins 1.0.0 `plugin.json`, `skills/`, `mcp.json` |
| MCP transport/wire | REPLACE-UPSTREAM | MCP 2026-07-28 Streamable HTTP via official SDK |
| plugin auth fields | DELETE | Agent Plugins v1 has no portable OAuth/credential-reference field; never embed bearer credentials in `mcp.json` |
| `.codex/skills` scanning | TEMP-BRIDGE | client-specific compatibility source only |
| `.hermes/skills` scanning | TEMP-BRIDGE | client-specific compatibility source only; currently untrusted |
| OpenClaw `metadata.openclaw.requires` | TEMP-BRIDGE | compatibility eligibility adapter only; never portable Agent Skills semantics |
| remote static bearer middleware | TEMP-BRIDGE | retained until the consuming ChatGPT MCP surface is migrated to standard MCP OAuth/OIDC authorization |
| source-qualified `sourceId/name` refs | TEMP-BRIDGE | administrative/exact compatibility addressing; not Agent Skills portable identity |
| Cloudflare tunnel | KEEP-LOCAL | transport needed because this workstation cannot directly connect to OpenAI; not a Skill package semantic |
| project trust gate | KEEP-LOCAL | client-owned security policy explicitly left to clients by Agent Skills/Agent Plugins |
| quarantine/scanner | KEEP-LOCAL | client-owned security policy; never encoded as portable Skill semantics |
| workspaceId-to-path mapping | KEEP-LOCAL | local authority boundary; prevents model-asserted filesystem scope |
| instruction/package/snapshot revision fences | KEEP-LOCAL | local TOCTOU integrity contract for the remote bridge |
| Host/Runtime execution authority | KEEP-LOCAL | outside Plugin/Skill packaging; never delegated to Skill content |

## Discovery contract

Production discovery follows the Agent Skills client guide:

1. Scan `~/.agents/skills` as the interoperable user scope.
2. Scan each pre-registered workspace's `<project>/.agents/skills` as project scope.
3. Gate project Skills on local workspace trust.
4. Project scope wins over user scope.
5. Within one scope, discovery order is deterministic.
6. Model-facing list/search expose one effective winner per Skill name.
7. Client-specific caches are explicitly `compatibilitySources`; they do not redefine the portable format.

`standardDiscovery.user/projects` is a local runtime/testing switch. It is not portable plugin metadata.

## Validation contract

Two distinct validation questions are intentionally separated:

- **Strict conformance**: used for Ordivon-authored/distributed content and conformance tests. It checks the published Agent Skills field set and constraints.
- **Lenient runtime ingestion**: used by the bridge for discovered third-party/client-authored Skills, following the official client guidance. Non-standard fields and cosmetic name issues produce diagnostics; missing descriptions or unparseable YAML still reject the Skill.

Lenient ingestion does not make a private field portable. Diagnostics remain client-local.

## Agent Plugin package

`plugins/ordivon-skills-bridge/` is an Agent Plugins 1.0.0 package containing only:

- `plugin.json`
- `mcp.json`

Its remote MCP entry is `streamable-http` at `https://skills-mcp.ordivon.com/mcp`. No credentials or secret headers are package data. Exact official 1.0.0 JSON Schemas are vendored only as pinned conformance-test fixtures with recorded SHA-256 provenance.

The three Ordivon Next project Skills stay at `.agents/skills`; they are already in the cross-client interoperability location and are not copied into the bridge plugin.

## Authorization boundary

MCP 2026-07-28 continues the protocol's OAuth/OIDC authorization model and hardens issuer validation, credential isolation, scope step-up, and client registration through Client ID Metadata Documents. The current static bearer middleware is therefore a transport compatibility mechanism, not the target standard authorization architecture.

Do not invent a local OAuth server merely to remove this temporary status. Migrate when the chosen identity/authorization provider and ChatGPT consumer flow can satisfy the standard authorization discovery and token-validation contract.
