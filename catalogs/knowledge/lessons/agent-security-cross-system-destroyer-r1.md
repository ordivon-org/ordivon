# Agent Security LEGO — Cross-System Destroyer R1

Date: 2026-09-18
Status: CROSS-SYSTEM PROSPECTIVE VALIDATION R1
Systems: ZCode, OpenAI Codex, Anthropic Claude Code, Cursor, OpenCode, OpenClaw
Parent lens: catalogs/knowledge/lessons/agent-security-lego-r1.md

## 1. Question

Does Agent Security LEGO R1 survive contact with several materially different coding-agent architectures, or was it overfit to the ZCode workspace-snapshot case?

The destroyer test intentionally compares systems with different ownership, runtime, sandbox, network, persistence, and permission models.

The objective is not to rank products. It is to identify:
- security primitives that recur across architectures;
- primitives that are conditional on an execution regime;
- product-specific mechanisms that should not be promoted;
- missing primitives exposed only by cross-system comparison.

## 2. Source and evidence discipline

Priority order:
1. current official product documentation;
2. official source/config schema where available;
3. public reverse-engineering evidence only for the ZCode case.

Observed public sources checked on 2026-09-18:

### OpenAI Codex
- https://developers.openai.com/docs/agent-approvals-security
- https://developers.openai.com/docs/sandboxing
- https://developers.openai.com/docs/environments/cloud-environment
- https://developers.openai.com/docs/cloud/internet-access
- https://github.com/openai/codex/blob/main/codex-rs/core/config.schema.json

### Anthropic Claude Code
- https://code.claude.com/docs/en/security
- https://code.claude.com/docs/en/permissions
- https://code.claude.com/docs/en/settings

### Cursor
- https://prod.cursor.com/docs/agent/security/run-modes
- https://prod.cursor.com/docs/enterprise/privacy-and-data-governance
- https://prod.cursor.com/docs/cloud-agent/security
- https://prod.cursor.com/docs/cloud-agent/security-network
- https://cursor.com/blog/agent-sandboxing

### OpenCode
- https://opencode.ai/docs/permissions
- https://opencode.ai/docs/tools
- https://opencode.ai/docs/providers
- https://opencode.ai/docs/share
- https://dev.opencode.ai/docs/troubleshooting/
- https://dev.opencode.ai/docs/server/

### OpenClaw
- https://docs.openclaw.ai/gateway/security/tool-permissions
- https://docs.openclaw.ai/gateway/sandbox-vs-tool-policy-vs-elevated
- https://docs.openclaw.ai/gateway/sandboxing/workspace-access
- https://docs.openclaw.ai/reference/session-management-compaction/store
- https://docs.openclaw.ai/reference/session-management-compaction/maintenance
- https://docs.openclaw.ai/concepts/memory-provenance
- https://docs.openclaw.ai/releases/2026.8.1/security-and-privacy

ZCode remains the public reverse-engineering case already recorded in:
- catalogs/knowledge/lessons/zcode-workspace-snapshot-security-lego-r1.md
- catalogs/knowledge/graphs/zcode-workspace-snapshot-security-lego-r1.json

No product is treated as globally "secure" or "insecure." Evidence applies to the documented execution regime and version window.

## 3. First destroyer result: PRODUCT is the wrong unit

The strongest cross-system finding is that security posture is not a stable product property.

The correct unit is closer to:

```text
SecurityRegime =
  Product
  × ExecutionLocation
  × PermissionMode
  × SandboxMode
  × NetworkPosture
  × PersistenceMode
  × DelegationMode
  × PolicyBindingTime
```

Examples:
- Codex local workspace-write + network off differs materially from Codex cloud with selected internet access.
- Claude Code Manual differs from auto/bypass modes and from cloud sessions.
- Cursor local Auto-review differs radically from Cursor Cloud Agents.
- OpenClaw sandbox=all/workspaceAccess=none differs radically from sandbox=off + elevated.
- OpenCode default permissive tool posture differs from an explicit ask/deny policy.

Therefore a product-level security label destroys information.

Promotion candidate:
SECURITY_REGIME_IDENTITY.

## 4. Codex decomposition

### Regime C1 — local CLI / IDE, constrained

AS01 Principal / identity authority
- local OS user plus Codex account/config;
- approval reviewer and permission profiles are separate policy authorities.

AS02 Trigger
- prompt/model turn proposes tool or command activity;
- approval/escalation is evaluated at the action boundary.

AS03 Capture / read scope
- sandbox/permission profile determines file access;
- workspace-oriented modes keep writes in workspace;
- protected paths such as .git/.codex receive additional treatment in current documentation/config.

AS04 Derivation
- task context, tool results, diffs, and model-visible projections are derived from local state;
- derivation and model transmission are distinct from arbitrary process network access.

AS05 Local persistence
- config, project trust, approval rules, and local session/runtime state exist;
- this destroyer does not assert one single local retention policy for every Codex surface.

AS06 Egress
- command/process network is off by default in the standard local sandbox;
- network can be granted separately and can be constrained by network proxy/domain policy;
- app/MCP/model-service traffic must not be conflated with shell-process egress.

AS07 Remote persistence
- local execution does not by itself imply a remote workspace copy;
- cloud/model-side data retention is governed by the selected Codex/ChatGPT product surface and data controls, not inferred from shell access.

AS08 Key authority
- no ZCode-like envelope-encryption topology is needed for the local security model.
- KEY_AUTHORITY is therefore conditional, not universal.

AS09 Actuator
- sandbox and approval are explicitly separate controls:
  capability boundary versus consent/escalation boundary.
- named permission profiles add a reusable actuator layer.

AS10 Observation
- execution outputs, approval decisions, and task standing are visible;
- safety monitoring can pause tasks but is not a substitute for sandboxing.

AS11 Retention/delete
- relevant but surface-dependent; local config/session state and remote service state have different owners.

AS12 Disclosure
- current docs explicitly distinguish sandbox, approval, network access, and cloud versus local execution.

Destroyer observation:
Codex strongly supports separation of CAPABILITY BOUNDARY from APPROVAL POLICY. Approval is not itself containment.

### Regime C2 — Codex cloud

Key changes:
- repository is cloned into an OpenAI-managed isolated container;
- setup phase can use internet and secrets;
- agent phase is offline by default unless internet access is enabled;
- environment/container cache introduces remote execution state;
- HTTP/HTTPS egress goes through a proxy in the documented cloud environment.

This proves that "Codex" has multiple authority/persistence regimes and cannot be modeled by one row.

## 5. Claude Code decomposition

### Regime A1 — local Manual mode

AS01
- authenticated Claude Code process + local OS identity + repository/project permission settings.

AS02
- prompt causes tool calls; permission evaluation occurs before controlled actions.

AS03
- read access within working/additional directories is broadly available in Manual mode;
- outside-directory reads prompt through Read/Grep/Glob;
- sandbox denyRead rules can further narrow shell read access when sandboxing is enabled.

AS04
- file/tool outputs become model context;
- WebFetch is isolated into a separate context window, demonstrating explicit derivation/context-boundary design.

AS05
- repository-specific approvals may persist in .claude/settings.local.json;
- file-modification approval can instead be session-scoped.

AS06
- network-capable commands such as curl/wget are not silently equivalent to local reads;
- sandbox network isolation is a stronger boundary than command-text permission alone.

AS07
- ordinary local mode should not be conflated with cloud execution;
- Remote Control stores synchronized session transcript server-side while file execution remains local.

AS08
- not a universal primitive in this regime.

AS09
- fine-grained allow/ask/deny rules;
- permission modes (Manual, acceptEdits, plan, auto, dontAsk, bypassPermissions);
- managed settings can disable high-authority modes.

AS10
- /permissions exposes active rules;
- cloud sessions provide audit logging;
- local side-effect completeness is not claimed by this destroyer.

AS11
- local approvals may persist at repo/session scope;
- cloud VM cleanup and transcript/service retention are separate lifecycle concerns.

AS12
- documentation explicitly warns that Claude only has granted permissions and distinguishes command approval from sandbox/network enforcement.

### Regime A2 — cloud / Remote Control distinction

Claude has at least two remote-looking modes that must not be merged:
- cloud sessions: isolated Anthropic-managed VM, network controls, audit logs, automatic VM cleanup;
- Remote Control: execution/files stay on local machine, session traffic/transcript sync traverses Anthropic service.

Destroyer observation:
EXECUTION LOCATION and TRANSCRIPT LOCATION are independent axes.

Promotion candidate:
EXECUTION_DATA_PLANE_SEPARATION.

## 6. Cursor decomposition

Cursor is the strongest destroyer against any product-level model because local Agent and Cloud Agents have different threat surfaces.

### Regime U1 — local Agent

AS01
- local Cursor session/account plus OS/process authority.

AS02
- prompt/tool calls; current Run Modes decide when actions execute or require additional review.

AS03
- sandboxed shell commands get workspace access while protected paths and external-file operations are separately constrained;
- .cursorignore can hide files from the agent.

AS04
- LLM requests send prompts/code context through Cursor backend;
- codebase indexing is a distinct derivation path: plaintext chunks are used to compute embeddings while embeddings/metadata may persist.

AS05
- local project settings plus index/cache state.

AS06
- local sandbox network is blocked by default and opened through network mode/sandbox.json;
- LLM request traffic is a separate application egress plane from shell-process egress.

AS07
- normal LLM request handling is explicitly distinguished from Cloud Agent code storage;
- embedding/metadata persistence is distinct from raw plaintext persistence.

AS08
- ordinary local mode does not require product-specific key topology in this lens.

AS09
- Run Modes steer execution/approval;
- sandbox.json controls reachable resources;
- these are explicitly different actuators.

AS10
- current UI indicates when commands leave the sandbox;
- organization policy can layer over user/project policy.

AS11
- index/metadata lifecycle is distinct from cloud-agent workspace retention.

AS12
- Cursor documentation explicitly describes two major data flows: LLM requests and Cloud Agents.

### Regime U2 — Cloud Agents

AS01
- GitHub/GitLab app install + per-user account forms a layered repository authorization chain.

AS02
- tasks can be started by web, IDE, CLI, API, Slack, linked issue/PR, schedule, or automation.

AS03
- authorized repository is cloned into a dedicated VM;
- dependencies, configured secrets, and network services can become available.

AS04
- agent derives diffs, tool output, screenshots/videos/logs, conversation state, and environment snapshots.

AS05
- VM runtime state, conversation state, artifacts, and snapshots are distinct persistence classes.

AS06
- agent internet access is enabled by default in current Cloud Agents docs but can be constrained with egress controls.

AS07
- this is explicit remote persistence:
  runtime workspace;
  VM snapshots;
  conversation state;
  secrets/tokens.

AS08
- TLS/AES-256 are documented;
- per-agent keys and optional CMEK/BYOK make key authority explicit.

AS09
- network egress, repo access, secret types, retention policies, and org policy are separate controls.

AS10
- progress/artifacts are streamed and retained; security docs expose lifecycle stages.

AS11
- current docs state materially different retention rules:
  VM snapshots: rolling 90 days inactivity;
  conversation state: indefinite by default, deletable;
  secrets/tokens: until removed;
  Delete Agent API does not delete VM snapshots on demand.

AS12
- the dedicated Cloud Agent security documentation makes persistence classes and deletion asymmetry unusually explicit;
- however, the broader Privacy and Data Governance page summarizes encrypted repository copies as temporary and deleted after the agent completes, while the dedicated Cloud Agent security page separately documents VM snapshots containing cloned code with a rolling 90-day inactivity window.
- treat this as a cross-document disclosure-granularity mismatch requiring object-class clarification, not as proof that either statement is intentionally deceptive.

Destroyer observation:
REMOTE_PERSISTENCE is not one boolean. It is a set of independently retained object classes. Product documentation can also become misleading when one page summarizes only the runtime-workspace class while another documents longer-lived snapshot classes.

Promotion candidate:
PERSISTENCE_CLASS_VECTOR.

## 7. OpenCode decomposition

### Regime O1 — local tool-centric agent

AS01
- local OS/process identity plus model-provider credentials;
- provider credentials are stored locally in auth.json according to current docs.

AS02
- model/tool loop; subagents are explicit actions.

AS03
- read/glob/grep/edit/bash/external_directory are separately permissionable;
- current defaults remain comparatively permissive: most operations allow, while external directory and doom-loop paths ask; .env reads are denied by default in the v1/current permission docs.

AS04
- file/tool results become model context;
- sessions can be summarized;
- explicit share synchronizes complete conversation history to OpenCode servers.

AS05
- session/project/log/auth application data is stored under ~/.local/share/opencode in current docs.

AS06
- provider baseURL is configurable;
- webfetch/websearch/bash network behaviors are distinct tool paths;
- sharing creates another explicit egress path.

AS07
- normal local sessions are locally durable;
- shared sessions become remotely persistent/publicly accessible until unshared;
- model-provider retention is provider-specific.

AS08
- provider credential authority matters; product-specific encryption key topology is not a general requirement for this regime.

AS09
- ordered allow/ask/deny permission rules;
- auto mode converts ask to auto-approve but explicit deny remains enforced;
- current V2 documentation explicitly says a custom subagent uses its own permissions, not a subset of its parent's permissions.

This last point is a direct counterexample to assuming delegation monotonicity.

AS10
- local logs and session storage are inspectable;
- this is not equivalent to a complete data-egress ledger.

AS11
- local sessions can be deleted;
- shared sessions persist until /unshare and docs state related shared data is deleted on unshare;
- provider-side retention remains external.

AS12
- current permission/share docs disclose permissive defaults and public-share semantics.

Destroyer observation:
"Open source/local" does not eliminate egress or persistence. Provider routing and optional share are separate external boundaries.

## 8. OpenClaw decomposition

OpenClaw is the strongest test of authority composition because it exposes several layers independently.

### Regime L1 — sandboxed Gateway agent

AS01
- Gateway/operator/session identity;
- per-agent and per-session authority;
- creator/operator roles can require sandboxing.

AS02
- user turns, hooks, cron/heartbeat, delegated sessions, and agent-to-agent flows can all trigger work.

AS03
- workspaceAccess is explicit:
  none -> private sandbox workspace;
  ro -> agent workspace mounted read-only;
  rw -> workspace mounted read/write.
- additional bind mounts and filesystem roots form separate exposure paths.

AS04
- model context, memory, transcript compaction, derived memory, exports, and plugin/tool outputs are separate derivations.

AS05
- durable session rows, transcript events, memory files, archives, cold storage, and indexes have distinct local owners.

AS06
- provider/model requests, browser/network tools, channel sends, remote workers, plugins/MCP, and elevated execution are distinct effect planes.

AS07
- persistence can be local Gateway state, external channel/provider state, remote worker state, or plugin-owned state; no single retention promise covers them all.

AS08
- secret/credential authority is first-class, but key authority is subsystem-specific.

AS09
- three controls are explicitly separated:
  sandbox = where;
  tool policy = what;
  elevated = escape path.
- session permission modes and organization policy add higher-level actuators.

AS10
- current releases document audit records for session action decisions, plugin/remote actions, routing, approvals, and tool actions.

AS11
- session maintenance has explicit prune/archive/disk/cold-storage semantics;
- memory forget explicitly does not erase original transcripts or every external copy.

AS12
- current docs are explicit about the non-equivalence of sandboxing, tool policy, session visibility, and full tenant isolation.

Destroyer observation:
OpenClaw proves that AUTHORITY is multi-dimensional. Filesystem containment, tool availability, session visibility, elevated execution, and cross-agent reach are independent dimensions.

Promotion candidate:
AUTHORITY_VECTOR rather than one scalar "permission level."

## 9. Cross-system AS01–AS12 matrix

Legend:
- CORE = structurally present in every product/regime sampled;
- CONDITIONAL = first-class only when that feature/regime exists;
- META = analysis contract applied across products rather than a runtime component.

| Primitive | ZCode | Codex | Claude Code | Cursor | OpenCode | OpenClaw | Destroyer standing |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AS01 Identity Authority | yes | yes | yes | yes | yes | yes | CORE |
| AS02 Trigger | yes | yes | yes | yes | yes | yes | CORE |
| AS03 Capture/Read Scope | yes | yes | yes | yes | yes | yes | CORE |
| AS04 Derivation | yes | yes | yes | yes | yes | yes | CORE |
| AS05 Local Persistence | yes | yes | yes | yes | yes | yes | CORE, object classes differ |
| AS06 Egress Path | yes | yes | yes | yes | yes | yes | CORE |
| AS07 Remote Persistence | reported/capable | cloud/service dependent | cloud/remote-control dependent | explicit cloud + index | share/provider dependent | provider/channel/remote dependent | CONDITIONAL BUT FIRST-CLASS |
| AS08 Key Authority | explicit case | subsystem-specific | subsystem-specific | explicit in cloud | subsystem-specific | subsystem-specific | CONDITIONAL |
| AS09 Capability Actuator | mismatch case | explicit | explicit | explicit | explicit | explicit | CORE |
| AS10 Side-effect Observation | weak/forensic in case | partial/explicit | partial/explicit | explicit by regime | logs, partial | strong audit surfaces | CORE REQUIREMENT, completeness varies |
| AS11 Retention/Delete | unresolved | regime-dependent | regime-dependent | explicit classes | local/share/provider split | explicit local + plugin/provider split | CORE |
| AS12 Disclosure Alignment | mismatch test | applicable | applicable | applicable | applicable | applicable | META CORE |

The matrix does not mean every product has the same quality of control. It only tests whether the primitive is needed to describe the architecture.

## 10. New primitives exposed by the destroyer

The original ZCode-derived AS01-AS12 survive, but the comparison reveals four missing dimensions.

### XAS13 — Security Regime Identity

A product name is insufficient.

Record:
- execution location;
- sandbox;
- permission mode;
- network posture;
- persistence mode;
- delegation mode;
- organization-managed constraints.

Without this, comparisons collapse incompatible regimes.

### XAS14 — Policy Binding Time

When does a policy change take effect?

Observed examples across the sample:
- next tool call;
- current session;
- future sessions;
- run admission only;
- nonretroactive for already-running cloud agents;
- persistent repository rule.

A control can be correctly placed but still ineffective for an already-admitted run.

Represent:

```text
policy {
  scope
  binding_event
  effective_from
  expires_at
  retroactive?
}
```

### XAS15 — Authority Delegation / Inheritance

When a parent launches a subagent, worker, cloud run, hook, or automation:
- does child authority equal parent authority?
- is it narrowed?
- independently configured?
- inherited and then clamped?
- capable of escalation?

This matters because "parent was sandboxed" does not prove "child is sandboxed."

### XAS16 — Persistence Class Vector

Replace:

```text
persistent = true/false
```

with independently owned classes:

```text
runtime workspace
conversation transcript
tool output
artifact
snapshot/cache
credential/secret
derived index/embedding
memory
audit record
external-provider copy
backup/archive
```

Each class has its own owner, retention, deletion, encryption, and recovery semantics.

## 11. Cross-system laws

### Law S1 — Security Regime Law

Security posture is a state/configuration of a system, not a brand attribute.

### Law S2 — Approval Is Not Containment

Human/model approval decides whether an action is admitted.
Sandbox/policy determines what the admitted action can actually reach.

Conflating them creates false assurance.

### Law S3 — Egress Plane Separation

At minimum distinguish:
- model/inference egress;
- shell/process egress;
- tool/MCP/plugin egress;
- browser egress;
- telemetry/audit egress;
- snapshot/sync/share egress.

"Network off" is meaningless unless the plane is named.

### Law S4 — Persistence Multiplicity

Remote or local persistence is a vector of object classes, not a single retention number.

### Law S5 — Policy Binding-Time Law

A correct policy applied after admission may not constrain an already-running execution.

### Law S6 — Delegation Monotonicity Must Be Proven

Child/subagent/worker authority should not be assumed to be a subset of parent authority.
The inheritance law must be explicit and testable.

### Law S7 — Derivation Is a Boundary

Embeddings, summaries, snapshots, diffs, screenshots, manifests, indexes, and transcripts can carry sensitive information even when raw source is not retained.

### Law S8 — Deletion Is a Graph Operation

Deleting the visible object is not sufficient.
All persisted/derived descendants require explicit deletion semantics or documented retention.

## 12. Promotion decision

### Stable inside Agent Security LEGO after this destroyer

The following are now supported across the sampled coding-agent domain:

- AS01 Identity Authority
- AS02 Trigger
- AS03 Capture/Read Scope
- AS04 Derivation
- AS05 Local Persistence
- AS06 Egress Path
- AS09 Capability Actuator
- AS10 Side-effect Observation
- AS11 Retention/Delete
- AS12 Disclosure Alignment

AS07 Remote Persistence remains first-class but conditional by regime.
AS08 Key Authority remains conditional by cryptographic/storage design.

New stable Agent Security candidates:
- XAS13 Security Regime Identity
- XAS14 Policy Binding Time
- XAS15 Delegation/Inheritance
- XAS16 Persistence Class Vector

### Shared Ordivon LEGO kernel

NO PROMOTION YET.

Reason:
the destroyer spans multiple products but still one broad domain: coding/agent runtimes.

Shared-kernel promotion should require evidence from unrelated domains such as:
- browser agents;
- email/calendar agents;
- finance agents;
- artifact/media pipelines;
- autonomous game agents;
- enterprise workflow/ERP automation.

This preserves the thin-kernel law.

## 13. Ordivon implications

The cross-system evidence suggests the Security package should eventually be able to produce a machine-readable security-regime record before admitting high-authority agent work:

```text
regime identity
authority vector
trigger set
read/write/derive/network/persist sets
egress planes
policy binding times
delegation law
persistence classes
retention/delete graph
side-effect observation coverage
```

This should remain an Ordivon Security/Runtime policy artifact unless an upstream standard naturally owns the schema.

Agent Plugin remains a distribution/assembly boundary and should not absorb this ontology.

## 14. Next destroyer

The next validation should intentionally leave coding agents.

Recommended targets:
1. browser automation / Agent Birth;
2. connected email/calendar agent;
3. Artifact pipeline with external model/provider calls;
4. Market/finance read-only connector;
5. long-running multi-agent Game workflow.

If the same primitives survive those domains, selected concepts become credible shared LEGO promotion candidates.
