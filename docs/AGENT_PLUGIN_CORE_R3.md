# Agent Plugin Core R3 — Market Synthesis

Date: 2026-09-16
Status: **CORE FROZEN / TRACK UPSTREAM / NO ORDIVON RICH-PLUGIN FORMAT**

## Purpose

This document records the small set of Agent Plugin principles Ordivon will keep after comparing the current public ecosystems and standards rather than copying any one vendor's implementation.

Reviewed systems and evidence include:

- Agent Plugins Specification 1.0.0 (published) and 1.1.0 (working draft)
- Agent Plugins governance, contribution rules, canonical example, and compatible-client matrix
- OpenAI ChatGPT / Codex Plugins, Apps, App Templates, MCP Apps, workspace distribution and governance
- Anthropic Claude Code Plugins
- GitHub Copilot / VS Code Agent Plugins and client extensions
- Cursor Agent Plugins and Cursor-native Plugins
- OpenClaw compatible bundles and native runtime Plugins
- Kiro Powers and Agent Plugins support
- Vercel Skills / Vercel Plugin ecosystem
- Google Agent Plugins / Data Agent Kit / Gemini CLI extension model
- AWS Agent Toolkit / AWS Agent Plugins

The purpose is not to preserve every vendor feature. The purpose is to identify the interoperability waist and the lifecycle invariants that survive comparison.

---

## 1. Final architecture decision

Ordivon does **not** need a Rich Native Plugin format.

The portable boundary remains:

```text
Agent Plugin
├── plugin.json
├── [skills/]
└── [mcp.json]
```

with:

```text
Agent Skills = reusable procedural knowledge / HOW
MCP          = capability, data, tools, UI/extensions / CAN DO
Agent Plugin = optional portable assembly and distribution boundary
```

Everything richer belongs to a client adapter, an MCP feature/extension, or the owning Ordivon subsystem.

Ordivon MUST NOT create a new portable component type merely because one or more clients expose a similarly named native feature.

---

## 2. Why this is now a strong market conclusion

The published Agent Plugins 1.0 specification standardizes exactly two portable component types: Agent Skills and MCP servers.

The Agent Plugins 1.1 working draft still defines exactly those same two component types. Its current direction strengthens package containment, subprocess/MCP configuration, `${PLUGIN_ROOT}` / `${PLUGIN_DATA}`, remote URL/header safety, version selection, and component failure isolation rather than adding portable agents, hooks, rules, commands, workflows, LSP servers, channels, providers, or runtime plugins.

The standard's contribution rules require a concrete portability problem and implementer support before expanding the portable contract. Technical completeness alone is explicitly not evidence of ecosystem consensus.

This matches the market:

- OpenAI keeps product/workspace Apps, Hooks and governance above the portable core.
- Claude Code exposes a much richer local Plugin, but its extra agents/hooks/workflows/LSP/monitors/channels are client-native.
- GitHub Copilot keeps portable Skills + MCP separate from `com.github.copilot` client extensions.
- Cursor explicitly supports both portable Agent Plugins and a richer Cursor-native Plugin format.
- OpenClaw explicitly separates compatibility bundles from high-trust in-process native runtime Plugins.
- Kiro is moving its earlier Power packaging toward Agent Plugins while keeping steering/hooks/product activation client-owned.
- Vercel participates in the portable standard while its own rich Vercel Plugin separately implements knowledge injection, specialist agents, commands and hooks.
- Google joined Agent Plugins as a Core Maintainer specifically because Agent Skills and MCP were already portable and the duplicated wrapper was the interoperability problem; Google publicly describes the standard as deliberately small in scope.
- AWS Agent Toolkit production Plugins primarily compose curated Agent Skills with an AWS MCP Server, while the same Skills can still be consumed independently.

Conclusion: **the common layer is small by design, not incomplete by accident.**

---

## 3. Core ownership model

```text
                         DISTRIBUTION / CLIENT
┌──────────────────────────────────────────────────────────────────┐
│ ChatGPT / Codex / Claude / Copilot / Cursor / OpenClaw / Kiro  │
│ Install, enable, trust, permissions, UI, marketplace, policy    │
│ Native agents/hooks/rules/commands/LSP/providers when applicable │
└───────────────────────────────┬──────────────────────────────────┘
                                │
                                ▼
                         PORTABLE ASSEMBLY
┌──────────────────────────────────────────────────────────────────┐
│ Agent Plugins                                                   │
│ plugin.json + optional skills/ + optional mcp.json              │
└──────────────────────┬────────────────────────┬──────────────────┘
                       │                        │
                       ▼                        ▼
                 PROCEDURE                 CAPABILITY
┌────────────────────────────┐   ┌─────────────────────────────────┐
│ Agent Skills               │   │ MCP                             │
│ instructions               │   │ tools/resources/prompts        │
│ scripts/references/assets  │   │ authorization + extensions     │
└────────────────────────────┘   │ Apps / Tasks where negotiated   │
                                 └─────────────────┬───────────────┘
                                                   │
                                                   ▼
                                         ORDIVON AUTHORITIES
                                 ┌─────────────────────────────────┐
                                 │ Runtime / Host                 │
                                 │ Research / Artifact / Media    │
                                 │ Game / Market Capital          │
                                 │ graph / loop / organization    │
                                 └─────────────────────────────────┘
```

This is an ownership diagram. Packaging never transfers semantic ownership.

---

## 4. Skill relationship to Agent Plugin

Agent Skills remain independently canonical assets.

A Skill may be:

- consumed directly by a client;
- installed independently;
- discovered at project/user scope;
- optionally composed into an Agent Plugin release.

Bundling does not make Agent Plugin the semantic owner of the Skill.

Current Ordivon policy remains:

```text
canonical .agents/skills/*
        │
        ├── direct/native Skill consumption
        │
        └── optional release composition
                ↓
        Agent Plugin skills/*
```

`ordivon-control-plane` remains MCP-only by default. Skill composition is an explicit release/channel choice.

---

## 5. The lifecycle model Ordivon should retain

The strongest cross-vendor insight is not a larger manifest. It is a clearer **capability lifecycle**.

```text
Source
  ↓
Discover
  ↓
Install
  ↓
Enable
  ↓
Trust / Authorize
  ↓
Relevance selection
  ↓
Activate
  ↓
Bind exact capability generation
  ↓
Execute
  ↓
Stage update candidate
  ↓
Verify / capability-diff / consent where required
  ↓
New work switches to new generation
  ↓
Retire / garbage-collect old generation
```

These are distinct states. They MUST NOT be collapsed into one `installed=true` concept.

### 5.1 Installed is not active

A package may be installed but disabled, unauthorized, irrelevant to the current task, or intentionally omitted from the model context.

Kiro makes task-relevant activation explicit. Vercel likewise budgets and selectively loads Skills rather than injecting everything. Cursor notes that adding more Skills can increase token usage and irrelevant guidance. The general rule is:

> The available capability universe may be large; the active model-visible capability set should be small and task-relevant.

### 5.2 Installed is not authorized

Installing a package MUST NOT imply:

- OAuth completion;
- secret access;
- MCP server trust;
- tool approval;
- hook execution approval;
- provider/domain authorization.

Installation, connection, authorization, tool/action permission and executable-code trust are separate decisions.

### 5.3 Update is not in-place mutation of admitted work

Claude Code and OpenClaw independently demonstrate a mature pattern: already-running work remains bound to the package/plugin generation it admitted, while a successfully prepared new generation is used by later work.

Ordivon should prefer this model for long-lived capability-bearing work:

```text
accepted work → exact capability generation
update arrives → prepare/validate separately
new work       → new generation after admission
old work       → continues on old generation
old generation → retire only when safe
```

Do not build a global watcher that silently changes the semantics of an in-flight Agent.

---

## 6. Package files, mutable data and credentials are three different classes

Keep these separate:

```text
PLUGIN_ROOT / package artifact
    = versioned package content

PLUGIN_DATA / client-managed mutable data
    = caches, generated state, installed dependencies where applicable

Credentials / authorization state
    = client/provider/secret-store owned
```

The Agent Plugins 1.1 working draft reinforces this separation with explicit `PLUGIN_ROOT` / `PLUGIN_DATA` semantics and states that package `env` / HTTP header values are not a portable secret mechanism.

Ordivon MUST NOT embed OAuth tokens, refresh tokens, private credentials or workspace authorization state into portable Plugin files.

---

## 7. Path containment and package integrity are core safety properties

The 1.1 draft formalizes package path containment: files supplied by a Plugin must resolve within the Plugin root, and plugin-relative executable/working-directory paths must remain contained.

Ordivon already uses the same principle in Skill/package handling and should retain it regardless of specification version:

- reject filesystem escape through symlinks/junctions/reparse-point equivalents when reading package-owned paths;
- separate package path safety from subprocess sandbox claims;
- bind release/materialization receipts to exact content;
- never infer safety merely from a path string before filesystem resolution.

Containment is a package integrity property. It is not a claim that a launched process itself is sandboxed.

---

## 8. Failure isolation is part of the portable model

A broken independent component should not destroy valid independent components.

Examples:

- one invalid Skill → skip/report that Skill;
- one invalid or unreachable MCP server → skip/report that server;
- unsupported MCP transport → skip/report that entry;
- independent valid Skills remain usable.

The Agent Plugins 1.1 draft explicitly strengthens these narrow failure boundaries.

Ordivon should preserve the same principle across adapters and capability projections: **fail at the narrowest authoritative boundary, visibly.**

---

## 9. Trust classes must not be flattened

Different things called “Plugin” have radically different authority.

A useful conceptual ordering is:

```text
lower runtime authority

Agent Skill / declarative knowledge
    ↓
portable Agent Plugin package
    ↓
remote MCP capability
    ↓
local stdio MCP process
    ↓
client hook / local executable integration
    ↓
native in-process runtime Plugin
    ↓
agent harness / execution-engine extension

higher runtime authority
```

This is not a universal risk score; it is an authority reminder.

OpenClaw makes the boundary especially explicit: compatible bundles and native in-process Plugins are different trust classes.

Ordivon MUST NOT grant a package broad authority merely because it is installed or because some client ecosystem uses the same word “Plugin” for runtime modules.

---

## 10. Non-interactive operation must fail safe

For unattended Agents, inability to ask a human is **not approval**.

When a required trust/authorization/capability-expansion decision cannot be obtained interactively, the safe default is to deny, skip, or hold the affected capability unless prior durable authority already permits it.

This is particularly important for Ordivon's long-running and unattended execution goals.

---

## 11. Component authorization can be narrower than package installation

A package may be present while selected components are denied or unavailable:

```text
Plugin installed
├── Skill A          allowed
├── Skill B          allowed
├── MCP server X     blocked/unavailable
└── client hook Y    not trusted
```

Do not turn package installation into a transitive authority grant.

Consumer policy should own per-component realization and permissions.

---

## 12. Context admission is a first-class Agent concern

Traditional software Plugins can often remain loaded continuously. Agent capabilities consume model attention and context.

Therefore distinguish:

```text
available capability
installed capability
enabled capability
model-visible capability
currently activated capability
```

Agent Skills progressive disclosure and Kiro/Vercel relevance loading demonstrate the same underlying principle:

> metadata/discovery may be broad; full instructions and tool surfaces should be admitted only when useful.

Ordivon should not respond to a growing capability catalog by injecting every Skill description, tool schema or domain instruction into every Agent.

Any future Ordivon-owned Harness router should operate on explicit metadata and bounded activation, not by inventing another portable Plugin ontology.

---

## 13. Client adapters are projections, never semantic owners

Client-native artifacts may include:

```text
agents/
hooks/
rules/
commands/
workflows/
LSP
steering
monitors
channels
provider plugins
UI templates
```

They are legitimate consumer features but remain client-owned until an upstream portable standard converges.

If Ordivon needs one, generate or maintain a thin adapter for that client.

Examples:

```text
Ordivon semantic authority
        ↓
Copilot agent profile
Cursor rule/subagent
Claude hook/agent
OpenAI product adapter
OpenClaw compatible/native adapter
Kiro steering/hook adapter
```

The projection MUST NOT become the source of truth for Runtime, Host, Agent Birth, graph/loop, Research or any domain state.

---

## 14. Marketplace and registry are not Plugin semantics

Across OpenAI, Claude, Copilot, Cursor, OpenClaw and others, marketplace/catalog systems differ substantially while the underlying Skill/MCP content can remain portable.

Therefore Ordivon will not build a universal Plugin marketplace or private cross-client registry merely to match consumer products.

Distribution metadata, review state, moderation, rollout policy, installation scope and update channels stay outside the portable core.

Use upstream registries/directories when a real publishing need exists.

---

## 15. Compatibility must be measured per feature

“Supports Agent Plugins” is not enough evidence for every detail.

Clients may incrementally implement component types/transports, and real products can differ in placeholder expansion, auth flow, refresh semantics, installation scope or client extensions.

Maintain compatibility evidence at the feature level when Ordivon actually targets a consumer:

```text
client
├── plugin.json/version supported?
├── Skills supported?
├── MCP stdio?
├── MCP Streamable HTTP?
├── OAuth/auth realization?
├── PLUGIN_ROOT / PLUGIN_DATA semantics?
├── Skill refresh semantics?
├── Plugin update semantics?
└── relevant client adapter behavior?
```

Do not change the portable Ordivon package to mimic one client's bug or omission. Prefer client-specific adaptation or wait for upstream conformance fixes.

The official Agent Plugins compatibility page itself only lists capabilities backed by verifiable current implementation evidence; announced/planned support is intentionally insufficient.

---

## 16. Effect truth remains with the semantic owner

A Plugin, Skill, hook, MCP client, native Agent harness or model transcript can report that an action occurred. That report is not automatically authoritative proof of the external effect.

For Ordivon:

```text
model/tool log says success
        ≠
Runtime/Host/domain-owner receipt says committed
```

Only the owning system can establish its domain truth.

This remains true even when a client-native Plugin performs deep runtime integration.

---

## 17. Standard evolution gate

Published upstream standards are authoritative. Working drafts are evidence, not automatically adopted production contracts.

Current state on 2026-09-16:

- Agent Plugins 1.0.0 = published current release;
- Agent Plugins 1.1.0 = working draft;
- both still define exactly two portable component types: Skills and MCP servers.

Ordivon may study and pre-test draft hardening, but MUST NOT silently relabel the canonical package as a newer standard until that version is published and target-client support is established.

For a proposed new portable component, require the same kind of evidence the upstream project requires:

1. concrete cross-client interoperability problem;
2. evidence that the concern belongs in portable packaging rather than client policy/extension or MCP;
3. multiple implementers prepared to adopt it;
4. published upstream semantics or an explicit isolated experiment, not a private Ordivon standard.

---

## 18. What Ordivon explicitly will not build

Unless future upstream standards materially change, do not build:

- `.ordivon-plugin/` rich native Plugin schema;
- portable `agents/`, `hooks/`, `rules/`, `commands/`, `workflows/`, `graphs/`, `loops/`, `providers/`, `channels/`, `runtime/` component types;
- universal cross-Harness Plugin/Skill namespace semantics;
- universal consumer precedence rules;
- universal Plugin marketplace/store;
- Plugin-owned OAuth/secret store;
- Plugin-owned Runtime or Host state;
- live watcher semantics that mutate admitted work in place;
- a central Plugin SDK that makes Ordivon a new all-owning Agent runtime.

The absence of these systems is intentional architecture, not missing implementation.

---

## 19. What Ordivon does keep

### Portable assets

- Agent Skills as independently meaningful standard assets;
- Agent Plugins package for portable assembly/distribution;
- MCP for cross-client tools/context/capabilities.

### Ordivon-owned authorities

- Runtime physical execution truth;
- Host continuity/collaboration truth;
- domain-specific semantics in their owning systems.

### Thin compatibility surfaces

- temporary Skill MCP bridge only where a remote client cannot consume native/local Skills;
- client-specific adapters only when an actual target requires them.

### Lifecycle principles

- exact source/content/version identity;
- install/enable/auth/activation separation;
- bounded context admission;
- generation-bound execution where capability changes can affect semantics;
- staged verified updates rather than destructive in-place mutation;
- narrow failure isolation;
- authority-specific receipts for external effects;
- fail-safe unattended behavior.

---

## 20. Current Ordivon package policy

Canonical portable package stays intentionally small:

```text
plugins/ordivon-control-plane/
├── plugin.json
└── mcp.json
```

Optional Skill composition remains release-time only:

```text
--include-skills
```

No rich client directory is added until a concrete client requirement exists.

No additional portable component type is created locally.

---

## 21. Sources / external evidence snapshot

Primary sources consulted for this synthesis include:

- https://agent-plugins.org/
- https://agent-plugins.org/specification
- https://agent-plugins.org/compatible-clients
- https://github.com/agentplugins/agent-plugins-spec
- https://github.com/agentplugins/agent-plugins-example
- https://developers.openai.com/plugins/
- https://help.openai.com/ (Plugins / Apps / App Templates / marketplace guidance)
- https://code.claude.com/docs/en/plugins-reference
- https://code.visualstudio.com/docs/agent-customization/agent-plugins
- https://docs.github.com/en/copilot/concepts/agents/about-plugins
- https://cursor.com/docs/plugins and related Cursor plugin/security docs
- https://docs.openclaw.ai/plugins and related bundle/SDK/release docs
- https://kiro.dev/docs/powers/ and related MCP/security/hooks docs
- https://vercel.com/plugin and https://github.com/vercel/vercel-plugin
- https://developers.googleblog.com/agent-plugins-package-your-skills-tools-and-more/
- https://docs.cloud.google.com/data-agent-kit/
- https://github.com/google-gemini/gemini-cli/tree/main/docs/extensions
- https://aws.amazon.com/blogs/opensource/aws-supports-agent-plugins-an-open-standard-for-portable-agent-extensions/
- https://docs.aws.amazon.com/agent-toolkit/latest/userguide/plugins.html

This is a dated architecture evidence snapshot. Re-check upstream before changing the portable contract.

---

## 22. Revisit conditions

Re-open the core only when at least one of these is true:

- a new Agent Plugins specification version is published with materially different portable component types;
- a new MCP standard/extension changes the correct protocol boundary;
- at least two major clients converge on a non-portable component and upstream Agent Plugins begins standardizing it;
- concrete Ordivon consumer E2E shows the current portable core cannot express a necessary cross-client capability;
- a security/lifecycle requirement cannot be represented through the current owner boundaries.

Otherwise, keep the core small.
