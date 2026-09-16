# Agent Plugin Boundary R2 — External-First Architecture

Date: 2026-09-16
Status: **PORTABLE CORE FROZEN / PRODUCT ADAPTERS SEPARATE / SKILL OWNERSHIP OPEN**

> Market synthesis follow-up: `docs/AGENT_PLUGIN_CORE_R3.md` is the current cross-vendor core decision. It extends this boundary audit with Claude Code, Vercel, Google, AWS, Agent Plugins 1.1 draft hardening, capability lifecycle, generation binding, context admission, trust classes, and explicit non-goals. R2 remains the detailed ownership decomposition.

## Purpose

This document defines what Ordivon should and should not mean by **Agent Plugin** after reviewing the published Agent Plugins 1.0 specification and contemporary implementations across OpenAI ChatGPT/Codex, VS Code/GitHub Copilot, Cursor, OpenClaw, Kiro, Agent Skills, and MCP 2026-07-28.

The governing principle is simple:

> Agent Plugin is a portable **assembly and distribution boundary**, not a universal capability ontology and not the semantic owner of the capabilities it assembles.

Ordivon therefore adopts the smallest common external contract and leaves richer behavior to the standards or products that already own it.

## External authority snapshot

The following upstream sources were reviewed for this boundary decision:

1. Agent Plugins Specification 1.0.0 — https://agent-plugins.org/specification
2. Agent Plugins overview / governance — https://agent-plugins.org/
3. Agent Plugins compatible clients — https://agent-plugins.org/compatible-clients
4. Agent Skills specification and client implementation guidance — https://agentskills.io/
5. MCP 2026-07-28 release/specification guidance — https://modelcontextprotocol.io/ and https://blog.modelcontextprotocol.io/posts/2026-07-28/
6. MCP Apps extension — https://apps.extensions.modelcontextprotocol.io/
7. MCP Tasks extension — https://tasks.extensions.modelcontextprotocol.io/
8. OpenAI: Plugins in ChatGPT and Codex — https://help.openai.com/en/articles/20001256/
9. OpenAI: Importing and syncing plugin marketplaces from GitHub — https://help.openai.com/en/articles/20001504
10. OpenAI: ChatGPT app templates — https://help.openai.com/en/articles/20001247-chatgpt-app-templates/
11. OpenAI: Developer mode and MCP apps in ChatGPT — https://help.openai.com/en/articles/12584461-developer-mode-and-mcp-apps-in-chatgpt
12. VS Code: Agent plugins — https://code.visualstudio.com/docs/agent-customization/agent-plugins
13. VS Code: Agent customization concepts — https://code.visualstudio.com/docs/agents/concepts/customization
14. GitHub Copilot: About plugins — https://docs.github.com/en/copilot/concepts/agents/about-plugins
15. GitHub Copilot CLI plugin reference — https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference
16. Cursor plugin reference — https://cursor.com/docs/reference/plugins
17. OpenClaw plugin bundles — https://docs.openclaw.ai/plugins/bundles
18. Kiro Powers installation / Agent Plugins support — https://kiro.dev/docs/powers/installation/
19. Anthropic: Agent Skills architecture — https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills

This list is evidence for a 2026-09-16 architecture decision, not a permanent pin. When upstream standards change, re-run the boundary audit instead of extending Ordivon from memory.

---

## 1. What Agent Plugins 1.0 actually standardizes

Agent Plugins 1.0 deliberately defines a small interoperability floor.

Portable package layout:

```text
<plugin-root>/
├── plugin.json              # required portable manifest
├── skills/                  # optional Agent Skills
│   └── <skill>/
│       └── SKILL.md
├── mcp.json                 # optional MCP server declarations
└── <reverse-domain>/        # optional client-specific extension namespace
```

The normative specification defines **exactly two portable component types**:

1. **Agent Skills** discovered from immediate child directories of `skills/` containing `SKILL.md`.
2. **MCP servers** declared in root `mcp.json`.

The standard explicitly keeps commands, hooks, agents, rules, LSP servers and similar capabilities outside the portable v1 core because their formats have not converged sufficiently across clients.

This is not a gap for Ordivon to fill. It is a deliberate standards boundary.

### Consequence for Ordivon

Do not add any private portable component type such as:

```text
agents/
loops/
graphs/
workflows/
runtime/
host/
artifacts/
providers/
capabilities/
policies/
```

and then claim that it is part of the Agent Plugins portable contract.

If a future Agent Plugins version standardizes another component type, adopt it upstream-first at that time.

---

## 2. The five layers that must remain separate

### Layer A — Portable Agent Plugin package

Owner: **Agent Plugins specification**

Purpose: assemble already-standardized portable components into one installable directory.

Allowed portable semantics in v1:

- `plugin.json` identity/metadata/version;
- optional `skills/` discovery;
- optional `mcp.json` server declarations;
- `${PLUGIN_ROOT}` / `${PLUGIN_DATA}` behavior for applicable stdio MCP configuration;
- reverse-domain client extension namespaces as an escape hatch, without portable semantics.

This layer does not own the semantics of Skills or MCP themselves.

### Layer B — Procedural knowledge

Owner: **Agent Skills**

Purpose: reusable instructions, workflow guidance, scripts, references and assets loaded by progressive disclosure.

The canonical semantic unit is the Skill directory and `SKILL.md`, not the Agent Plugin containing it.

A Skill can therefore exist:

- independently at project/user scope;
- inside a product-native skill distribution channel;
- optionally inside an Agent Plugin `skills/` component.

Bundling does not transfer semantic ownership.

### Layer C — Connected capability and context protocol

Owner: **MCP**

Purpose: expose tools, resources, prompts and negotiated protocol extensions from a server to an agent client.

Agent Plugin only says **which MCP servers to connect to**. The actual capability model remains inside MCP.

For MCP 2026-07-28 this includes, among other things:

- `tools/*`;
- `resources/*`;
- `prompts/*`;
- `server/discover`;
- authorization discovery and OAuth resource-server behavior;
- official extensions such as MCP Apps and Tasks when negotiated.

Therefore MCP Apps, MCP Tasks, tools, resources and prompts are **not new Agent Plugin component types**. They are capabilities of the MCP server referenced by `mcp.json`.

### Layer D — Client/product-specific customization and distribution

Owner: **the client/product**

Examples:

- `com.github.copilot/agents/`, commands, rules, hooks and LSP configuration;
- Cursor-native rules, agents, commands, hooks and variables;
- OpenAI Plugin Directory listings, connected apps, app templates, `.app.json`, workspace marketplace import and installation policy;
- OpenClaw native plugins, gateways, channels and provider extensions;
- Kiro Power installation/update behavior;
- client trust, permission, sandbox and UI policy.

These may coexist with an Agent Plugin package, but they are not portable Agent Plugins v1 semantics.

### Layer E — Ordivon domain authority

Owner: **Ordivon domain systems**

Examples:

- Runtime: Workspace / Job / Attempt / Artifact physical execution truth;
- Host: continuity / collaboration / task semantic state;
- Research, Artifact, Media, Game and Market Capital domain semantics;
- orchestration graphs, loops, organization and agent scheduling;
- deployment, recovery and release truth;
- domain-specific policy and evidence.

Agent Plugin may distribute Skills that explain how to use these systems and MCP server declarations that connect to them. It must never become their semantic owner.

---

## 3. Component disposition for Ordivon

| Capability | Portable Agent Plugin v1? | Correct owner | Ordivon disposition |
| --- | --- | --- | --- |
| `plugin.json` metadata | Yes | Agent Plugins | Keep minimal and standards-only |
| Agent Skills | Yes, optional component | Agent Skills | Independent canonical assets; optional composition only |
| MCP server declaration | Yes, optional component | Agent Plugins config + MCP runtime semantics | Core use for Runtime/Host connections |
| MCP tools | No package component | MCP server | Expose from Runtime/Host/domain MCPs |
| MCP resources | No package component | MCP server | Use where resource semantics fit |
| MCP prompts | No package component | MCP server | Use only where user-controlled prompt templates are valuable |
| MCP Apps UI | No package component | MCP Apps extension | Serve through an MCP server if a real UI use case exists |
| MCP Tasks | No package component | MCP Tasks extension | Map long-running operations only where client support and semantics fit |
| Authentication/OAuth | No | MCP/client/provider | Client-managed discovery/authorization; no secrets in plugin package |
| Custom agents/subagents | No portable v1 type | Client/harness | Keep harness-native until an upstream portable standard converges |
| Hooks | No portable v1 type | Client/harness | Client extension only when a concrete client requires it |
| Commands/slash commands | No portable v1 type | Client/harness | Do not add to portable core |
| Rules/instructions | No portable v1 type | Client/harness or Agent Skills where task-scoped | Do not invent Ordivon portable rules format |
| LSP servers | No portable v1 type | Client/editor | Client extension only |
| Graph / loop | No | Orchestration runtime | Keep independent; Plugin may connect or teach usage |
| Multi-agent organization | No | Harness/Host/Runtime | Keep independent |
| Provider adapters | No | Runtime/client | Do not package as portable Agent Plugin semantics |
| Runtime execution state | No | Ordivon Runtime | Never move into plugin state |
| Host continuity state | No | Ordivon Host | Never move into plugin state |
| Credentials/secrets | No | Client/provider secret store | Never embed in plugin files |
| Trust/permissions | No | Client/workspace/provider | Do not build a plugin-owned trust DB |
| Registry/marketplace | No | Product/ecosystem | Use upstream marketplace/directory mechanisms |
| Installation/update/uninstall state | No | Client/product | Observe, do not reimplement |
| Persistent plugin runtime data | Client-managed `PLUGIN_DATA` for stdio use | Client | Do not treat it as domain truth |

---

## 4. What other clients teach us

### VS Code / GitHub Copilot

VS Code and Copilot expose a useful reference architecture:

- portable Agent Plugins layer: Skills + MCP;
- `com.github.copilot` client namespace: agents, commands, rules, hooks, LSP;
- unsupported client namespaces are ignored.

This is exactly the pattern Ordivon should follow when a client-specific feature is unavoidable: **keep the portable core unchanged; isolate the adapter in the client's namespace**.

### Cursor

Cursor supports both Agent Plugins and a richer Cursor-native plugin format. Its native format can include rules, agents, commands, hooks and variables, while the portable Agent Plugins path remains Skills + MCP.

The lesson is not to copy Cursor's extra fields. The lesson is that a mature client can maintain a richer native layer without pretending those fields are cross-client standards.

### OpenClaw

OpenClaw explicitly distinguishes imported Agent Plugin **bundles/content packs** from native OpenClaw plugins. Agent Plugins are mapped into the subset of native capabilities the client supports; native plugins remain a different, more powerful runtime extension mechanism.

That distinction is important for Ordivon: a portable package and an in-process/runtime extension system are different trust and authority classes.

### Kiro

Kiro treats Agent Plugin MCP servers as package-managed connections that activate/deactivate with the installed Power rather than rewriting all of them into the user's global MCP configuration.

This reinforces the ownership rule: installation/runtime projection belongs to the client. The portable package declares; the client decides how to realize it.

### OpenAI ChatGPT / Codex

OpenAI's current **product Plugin** concept is broader than the Agent Plugins portable format. A product Plugin can include Skills, connected Apps and App Templates, while workspace governance controls installation, app authorization and action permissions.

OpenAI workspace marketplace import adds another distribution layer (`.agents/plugins/marketplace.json`, app references, GitHub sync and workspace policies).

These are product-level packaging/distribution mechanisms. They must not be copied into portable `plugin.json` or generalized into an Ordivon private standard.

A direct imported plugin that declares MCP servers can also receive product-specific surface restrictions such as a `Desktop only` label. Referencing an existing OpenAI app is a product adapter decision; it does not change Agent Plugins v1 semantics.

### Anthropic / Agent Skills

Agent Skills originated as a lightweight composable unit for procedural expertise and were later published as an open standard. Skills intentionally complement MCP: a Skill can teach an agent how to perform a workflow that uses external MCP tools.

That reinforces separation rather than ownership:

```text
Skill = how / procedure / reusable expertise
MCP   = what can be reached or done
Plugin = optional assembly of the two
```

---

## 5. MCP is already the extensibility waist below Agent Plugin

Do not create Agent Plugin components for every new MCP capability.

MCP 2026-07-28 already provides a layered extension mechanism and has moved toward a stateless HTTP-oriented core. It supports standard server features and separately negotiated extensions.

### Core / server capabilities

```text
MCP server
├── tools
├── resources
├── prompts
└── server/discover / protocol metadata
```

### Extension examples

```text
MCP server
├── io.modelcontextprotocol/apps
└── io.modelcontextprotocol/tasks
```

For Ordivon:

- Runtime long-running work may eventually project through the MCP Tasks extension when semantics and client support justify it;
- rich interactive artifact/control UI may be exposed through MCP Apps where useful;
- neither should become `tasks/` or `apps/` directories inside the Agent Plugin package unless a future Agent Plugins specification standardizes such component types.

MCP extensions and Agent Plugin client extensions are different mechanisms. Do not conflate them.

---

## 6. OpenAI product Plugin versus Agent Plugins open standard

Use different names internally when necessary to avoid semantic collapse:

### Portable Agent Plugin

Meaning:

```text
Agent Plugins 1.0 directory
plugin.json + optional skills/ + optional mcp.json
```

Authority: agent-plugins.org specification.

### OpenAI Product Plugin

Meaning:

```text
ChatGPT/Codex distributed workflow entry
may include skills + connected apps + app templates + workspace policy
```

Authority: OpenAI product/plugin administration.

### OpenAI App / custom MCP app

Meaning:

```text
ChatGPT connection to external tools/data/actions,
often backed by MCP and its own authorization/workspace policy
```

Authority: OpenAI Apps / MCP integration layer.

These concepts can reference or compose one another, but are not interchangeable.

For Ordivon, the default public architecture should remain:

```text
Portable Agent Plugin
        │
        ├── optional Agent Skills
        │
        └── mcp.json
              │
              ├── Runtime MCP
              └── Host MCP

OpenAI distribution adapter (only when needed)
        │
        ├── workspace/plugin marketplace metadata
        └── existing/custom OpenAI App references
```

Do not put OpenAI app IDs, workspace policy, OAuth secrets or marketplace state into the portable package.

---

## 7. Current Ordivon package verdict

Current canonical package:

```text
plugins/ordivon-control-plane/
├── plugin.json
└── mcp.json
```

with:

```text
ordivon-runtime -> https://mcp.ordivon.com/mcp
ordivon-host    -> https://host-mcp.ordivon.com/mcp
```

is structurally aligned with the external standard and should remain intentionally boring.

### Keep unchanged for now

- no new portable component directories;
- no Ordivon `extensions` namespace;
- no embedded credentials;
- no private plugin registry fields;
- no graph/loop/agent/runtime semantics in the manifest;
- no default Skill bundling until consumer evidence justifies it.

### Optional standard metadata improvements

The root manifest may later add standard metadata such as author, repository, homepage, license and keywords once their canonical values are explicitly owned. These are normal Agent Plugins fields, but there is no reason to invent values merely to make the manifest look fuller.

---

## 8. Skill relationship remains intentionally unresolved

Agent Plugins v1 defines `skills/` as a legal portable component. That answers only one question:

> Can a plugin distribute Agent Skills? **Yes.**

It does not answer:

> Should Ordivon make its Skills semantically subordinate to or always bundled with `ordivon-control-plane`? **No conclusion follows.**

Maintain three valid release models:

### Model A — Independent Skills + MCP-only control-plane Plugin

```text
.agents/skills/*

ordivon-control-plane/
├── plugin.json
└── mcp.json
```

Best when native clients discover project/user Skills independently.

### Model B — Independent canonical Skills + optional Plugin composition

```text
canonical .agents/skills/*
        │
        └── release-time composition
                ↓
ordivon-control-plane/skills/*
```

This is the current policy.

### Model C — Channel-specific default bundle

A specific distribution channel can default to bundled Ordivon Skills if real client evidence shows that it improves installation and invocation without creating versioning or ownership friction.

This would be a release-channel decision, not a redefinition of Agent Skills ownership.

---

## 9. Things Ordivon should explicitly stop trying to turn into Agent Plugin features

The following are outside the portable package and should stay that way unless an upstream standard later converges:

1. Agent Birth and process lifetime.
2. Multi-agent scheduling and organization.
3. A↔B wake loops or orchestration graphs.
4. Runtime Job / Attempt / Artifact state.
5. Host task/board/continuity state.
6. Agent identity and durable ownership.
7. Cross-Harness universal capability discovery.
8. A universal Skill namespace or precedence engine.
9. Trust databases and approval stores.
10. Provider credentials and OAuth state.
11. Deployment/recovery truth.
12. Artifact domain formats.
13. Research protocol semantics.
14. Game/Market Capital domain semantics.
15. Client-specific hooks/commands/agents/rules unless placed in a target client's standard extension namespace for a demonstrated need.

The correct relationship is usually:

```text
Ordivon system owns semantics
        ↓
MCP exposes capability
        ↓
Skill teaches workflow (optional)
        ↓
Agent Plugin packages connection/instructions (optional)
        ↓
client installs and governs
```

not:

```text
Everything -> Agent Plugin -> Ordivon private mega-format
```

---

## 10. Recommended Ordivon architecture

```text
                           DISTRIBUTION / CLIENT LAYER
┌───────────────────────────────────────────────────────────────────────┐
│ OpenAI Plugins / Apps / templates / marketplace                    │
│ Copilot com.github.copilot/*                                       │
│ Cursor-native extensions                                            │
│ OpenClaw / Kiro native installation and policy                      │
└──────────────────────────────────────┬────────────────────────────────┘
                                       │ client-specific adaptation
                                       ▼
                           PORTABLE ASSEMBLY LAYER
┌───────────────────────────────────────────────────────────────────────┐
│ Agent Plugins 1.0                                                    │
│ plugin.json                                                          │
│ ├── [skills/]  optional                                              │
│ └── [mcp.json] optional                                              │
└──────────────────────┬─────────────────────────────┬──────────────────┘
                       │                             │
                       ▼                             ▼
                PROCEDURAL LAYER                PROTOCOL LAYER
┌──────────────────────────────┐   ┌────────────────────────────────────┐
│ Agent Skills                 │   │ MCP 2026-07-28                    │
│ SKILL.md                     │   │ tools/resources/prompts           │
│ scripts/references/assets    │   │ Apps/Tasks extensions             │
└──────────────────────────────┘   │ authorization/discovery            │
                                   └──────────────────┬─────────────────┘
                                                      │
                                                      ▼
                                          ORDIVON AUTHORITY LAYER
                                   ┌────────────────────────────────────┐
                                   │ Runtime / Host                    │
                                   │ Research / Artifact / Game        │
                                   │ Market Capital / Media            │
                                   │ graph / loop / organization       │
                                   └────────────────────────────────────┘
```

This graph should be treated as an ownership diagram, not just a file layout.

---

## 11. Decision rules for future capability requests

When someone asks “Should X be part of Agent Plugin?”, apply these questions in order:

1. **Is X a portable component type in the current Agent Plugins specification?**
   - Yes: use the upstream format.
   - No: continue.

2. **Is X already an MCP capability or official MCP extension?**
   - Yes: expose it behind the MCP server; do not invent a Plugin component.

3. **Is X already an Agent Skills concern?**
   - Yes: keep it in the Skill; bundling remains optional.

4. **Is X client-specific and supported by an official reverse-domain extension namespace?**
   - Yes: use that namespace only when the target client genuinely needs it.

5. **Is X product distribution/governance state?**
   - Keep it in the product/workspace marketplace/app layer.

6. **Is X Ordivon domain state or runtime semantics?**
   - Keep it in the owning Ordivon subsystem and expose only the necessary interface.

7. **None of the above?**
   - Do not create a new portable Ordivon format. Wait for a demonstrated portability need and upstream convergence.

---

## 12. Immediate implementation consequences

### Agent Plugin package

**No feature expansion required.**

The existing `ordivon-control-plane` package is already close to the desired portable minimum.

### Runtime and Host MCP

Continue alignment with MCP 2026-07-28 as the capability waist. New cross-client features should first be evaluated as MCP server features/extensions rather than Agent Plugin fields.

### Skill MCP bridge

Keep as compatibility debt for clients that cannot consume local/native Agent Skills. Do not use the existence of Agent Plugin `skills/` to justify making the bridge permanent.

### OpenAI / ChatGPT distribution

Treat OpenAI workspace/plugin marketplace metadata, app references and custom MCP app configuration as a **separate distribution adapter**. Build it only when the target ChatGPT/Codex deployment path is confirmed.

### Client extensions

Default remains **none**. Add `com.github.copilot`, Cursor-native, OpenAI-specific or other client configuration only for a concrete target and keep it isolated from the portable core.

### Graph / loop / agents

Do not package them into Agent Plugins v1. Continue using the systems that already own their semantics.

---

## 13. Current decision

For Ordivon R2:

```text
Agent Plugin = portable assembly boundary

Portable components:
  1. Agent Skills (optional)
  2. MCP servers (optional)

Everything else:
  - MCP feature/extension,
  - client/product adapter,
  - or Ordivon-owned domain/runtime authority.
```

`ordivon-control-plane` remains **MCP-only by default**.

Skill composition remains **explicit and optional** until native consumer evidence demonstrates a reason to change a particular release channel.

No additional portable Agent Plugin component type will be created locally.

## 14. Revisit triggers

Re-open this decision only when at least one of the following occurs:

- Agent Plugins publishes a new specification version with additional portable component types;
- MCP promotes a new capability/extension that materially changes the Runtime/Host surface;
- OpenAI exposes a stable Agent Plugins import/distribution path whose requirements change the packaging boundary;
- two or more major clients converge on a component format strongly enough that an upstream Agent Plugins proposal is plausible;
- real Ordivon consumer evidence shows that optional Skill composition causes unacceptable install/version/invocation friction.

Until then, minimalism is a feature.
