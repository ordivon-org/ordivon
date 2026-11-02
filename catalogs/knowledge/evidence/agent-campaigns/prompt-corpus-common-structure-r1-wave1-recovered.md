# Prompt/Tool Corpus Common Structure R1 — Recovered Wave-1 Evidence

Status: **PARTIAL_RECOVERY / 8 SUBSTANTIVE REPORTS RECOVERED / 2 NOT RETRIEVED**
Campaign: `campaign:github-prompt-corpus-common-structure-20260914-r1`
Recovered: 2026-09-14

## Evidence boundary

The production Agent Automation birth ledger proves all ten occurrences were bound to exact provider conversations. The Browserless DOM output collector later failed because ChatGPT Web redirected exact conversation navigation to the home surface under a `Too many requests` condition; therefore DOM capture is not used as report authority here.

Eight substantive prior assistant reports/checkpoints were independently recoverable from ChatGPT conversation history. They are summarized below as secondary campaign evidence. Two reports (`A02`, `A05`) were not recovered and are explicitly left missing rather than reconstructed from guesswork.

This file does **not** claim that recovered summaries are byte-identical to the original full reports.

---

## A01 — Claude / Claude Code

Standing: **RECOVERED_SUBSTANTIVE_REPORT**

Observed conclusions:

- canonical tool registry;
- reason → act → observe loop;
- independent subagent contexts;
- structured task state;
- lazy capability/context loading;
- prompt policy separated from host-enforced permissions, hooks, sandbox and worktree isolation;
- verification includes Tool-result feedback, LSP, PostToolUse lint/check injection, Stop-hook continuation and plugin eval;
- distinctive mechanisms include typed agent principals, context-isolating delegation, lifecycle hook bus, temporary Skill authority, composite plugins and subagent versus peer-agent-team topologies.

Commonality candidates proposed by A01:

- tool registry;
- observe/act loop;
- delegation;
- policy/effect separation;
- lifecycle interception;
- isolation;
- persistent soft context;
- verification;
- extensibility;
- model routing.

Provenance standing:

- current official docs: high confidence;
- official GitHub: medium-high;
- historical corpus snapshots: medium;
- undocumented/leaked sources: excluded or low confidence.

---

## A02 — Cursor + VS Code/Copilot + Augment-style IDE Agents

Standing: **NOT_RETRIEVED**

The exact A02 substantive report was not recovered. Do not infer its conclusions from neighboring reports.

Related IDE-product evidence does appear independently in B04, including VS Code Manual/Assisted/Allow-all modes, Cursor Run Modes/allowlists/classifier/sandbox separation and Augment Agent/Auto/Quick Ask permission modes, but that evidence remains attributed to B04 rather than silently promoted to A02.

---

## A03 — Devin + Replit + Manus-style autonomous/cloud Agents

Standing: **RECOVERED_SUBSTANTIVE_REPORT**

Core conclusion:

> These systems are stateful execution systems, not merely repository editors.

Observed architecture:

- durable task/session state;
- owned VM/sandbox/project substrate;
- scoped credentials/effect interfaces;
- observation/evaluation loop;
- canonical commit/release boundary.

Authority/effect surface spans:

- shell;
- browser/desktop;
- deployment;
- databases;
- secrets;
- external SaaS;
- communications.

Product-specific evidence:

- Devin: VM snapshots, session secrets, RBAC, reproducible VM lineage;
- Replit: isolated background-task copies, checkpoints, connectors/RBAC, Apply-to-main, speculative parallel branches and cross-code/database/agent checkpoints;
- Manus: explicit running/waiting/stopped/error lifecycle, typed confirmations for email/terminal/calendar/deployment/browser/secrets, explicit sandbox-versus-provider effect boundaries.

Commonality candidates:

- durable task/session;
- owned execution environment;
- credential broker;
- long-running asynchronous progress;
- canonical commit/release gate;
- reusable procedural context;
- machine-readable telemetry;
- verification feedback;
- human takeover;
- model specialization.

---

## A04 — v0 + Lovable + Same + Bolt app-building Agents

Standing: **RECOVERED_SUBSTANTIVE_REPORT**

Provenance rule:

- prompt corpus used as secondary discovery only;
- vendor docs/open-source implementation preferred.

Core product loop:

```text
intent
→ context
→ mutation
→ preview
→ observation
→ publication
```

Observed mechanisms:

- project-centric state rather than a single repository-edit turn;
- design context is first-class;
- publication/deployment is a real effect boundary;
- common effect classes include inspect/edit files, dependency/runtime operations, preview, browser feedback, database/integration effects, VCS and deployment.

Distinctive examples:

- v0: per-chat isolated Vercel Sandbox, project-scoped shared state, Git branch/commit/PR flow, Ask/Auto/Full permission differences;
- Bolt: streamed `boltArtifact` / `boltAction` style execution over WebContainer;
- Same: historical versioning plus screenshot/lint/runtime-error feedback;
- Lovable: semantic tools, project Knowledge/Skills/testing/integration surfaces.

This family strongly supports preview/render feedback as a verification surface and treats deploy/publish separately from editing.

---

## A05 — canonical/open-source Codex CLI + Gemini CLI + Cline + RooCode baseline

Standing: **NOT_RETRIEVED**

The exact A05 substantive report was not recovered. A prior user follow-up confirms the report was considered strong and explicitly asked it to tighten the boundary between canonical observed facts and inferred cross-product abstractions, and to scope `common` / `unique` labels to the studied family rather than industry-wide.

Do not reconstruct the missing report from that follow-up alone.

---

## B01 — Tool Surface Taxonomy

Standing: **RECOVERED_SUBSTANTIVE_REPORT**

Central conclusion:

> Semantic effect classes are more stable across products than tool names.

High-confidence common candidates:

- typed action → observation;
- read/search separated from mutation;
- shell/general execution;
- structured file mutation;
- iterative feedback;
- authority mediation;
- extensible external Tool bus.

Minimal practical software-Agent waist proposed by B01:

```text
local observe
+ structured mutate
+ general execute
+ returned observation
```

MCP is treated as a **secondary extensibility waist**, not a universal mandatory core.

Extensions rather than universal primitives:

- web retrieval/browser;
- plan/task state;
- subagents;
- dynamic discovery;
- mode-scoped capabilities;
- rollback/checkpoints.

Low-universality/product-specific surfaces:

- persistent memory;
- database/deploy;
- image/artifact publishing;
- scheduled tasks;
- teams;
- specialized routing.

Counterevidence:

- CodeAct-like systems compress many typed tools into code/execution;
- some memory/checkpoints are Harness-managed rather than model-visible Tools;
- corpus selection and static-snapshot bias.

Confidence:

- effect taxonomy: high;
- minimal practical waist for software Agents: high;
- generalization across all Agent classes: medium;
- MCP as a useful candidate extensibility waist: high, but not universal.

---

## B02 — Prompt / Context / State Compilation

Standing: **RECOVERED_SUBSTANTIVE_REPORT**

Central conclusion:

> Mature Agents are better modeled as a typed context compiler than as one giant system prompt.

Candidate compilation model:

```text
effective_context
= compile(
    model,
    policy,
    mode,
    tools,
    scoped_instructions,
    skills,
    explicit_state,
    history,
    memory,
    budget
  )
```

Observed/common mechanisms:

- static base/model policy separated from dynamic tools, project rules, Skills, memory, modes, runtime state and history;
- hierarchical scope and precedence;
- scoped/lazy loading and progressive disclosure;
- token/byte budgets;
- provenance and cache-aware assembly;
- model-family-specific compilation;
- runtime capability manifest drives available Tools;
- transcript/event history separated from explicit current world state;
- compaction/condensation should preserve canonical current state rather than blindly replay raw transcript.

Host code naturally owns:

- permissions;
- hooks;
- selection/scoping;
- budgeting;
- deduplication;
- compaction;
- lifecycle.

Prompt/prose naturally owns semantic guidance, not enforcement.

Distinctive examples cited:

- Codex typed differential `WorldState` and canonical reinjection after compaction;
- Claude placement taxonomy;
- Cursor sidecar memory;
- OpenHands condenser;
- Aider repository map.

Counterevidence:

- coding-Agent/open-source selection bias;
- documentation may describe intended rather than exact runtime behavior;
- moving-main/version drift;
- Aider demonstrates a simpler viable architecture;
- memory and compaction implementations differ substantially.

---

## B03 — Control Loop + Verification

Standing: **RECOVERED_SUBSTANTIVE_REPORT**

Common control loop:

```text
assemble context
→ model inference
→ proposed effect
→ policy / approval
→ execute
→ structured observation
→ state update
→ continue or complete
```

Explicit runtime state may contain:

- plan/todo state;
- mode;
- approval standing;
- session/task state.

Verification examples:

- Codex: tests/checks plus Tool observations;
- Gemini: validated plan paths/content, telemetry, hooks and rewind;
- Cline: Tool-result feedback, retry limits, completion semantics, hooks and checkpoints;
- Roo: `attempt_completion`, todo/task operations, checkpoints and retrieval evidence.

Common candidates:

- Tool registry;
- separate authority layer;
- plan/read-only control state where needed;
- session state;
- observation-driven continuation;
- recovery;
- model routing;
- verification hooks.

Distinctive variants:

- Gemini JIT / validated-plan approval;
- Cline source-sensitive Plan → Act and plugin registry;
- Roo delegation / semantic retrieval;
- Codex capability-parametric runtime / automatic approval reviewer.

Counterevidence:

- open-source/coding-Agent selection bias;
- Cline/Roo lineage dependence;
- host/version variance;
- hooks and multi-Agent behavior continue to evolve.

---

## B04 — Authority / Permissions / Safety

Standing: **RECOVERED_SUBSTANTIVE_REPORT**

Central conclusion:

> Authority must be layered outside Prompt text.

Common layered structure:

```text
model-visible capability selection
→ authorization / approval policy
→ environmental confinement
→ provider / effect validation
→ audit / observation
```

Strong distinctions:

- Tool visibility != permission;
- permission != sandbox/isolation;
- Prompt rule != enforcement;
- model intent cannot grant itself credentials/network/filesystem authority.

Examples:

- VS Code: Manual / Assisted / Allow-all modes;
- Cursor: local Run Modes, allowlists/classifier/sandbox protections, separate cloud VMs;
- Augment: Agent pauses for terminal/external actions, Auto executes, Quick Ask is read-only.

Secrets and external effects remain policy-mediated.

Verification is an act → observe → repair loop using terminal/task/test/browser results, diagnostics, SCM/diffs, checkpoints and human review where applicable.

Observability may include logs, prompts, Tool payloads, errors, token and subagent traces, but observability is not itself authority.

---

## B05 — Provenance / Selection Bias / False-Commonality Falsifier

Standing: **RECOVERED_SUBSTANTIVE_REPORT**

Corpus verdict:

- mixed-provenance discovery index;
- not ground truth;
- per-artifact provenance should be graded P0–P4;
- version, extraction and selection bias must remain explicit.

Common skeleton candidates surviving its red-team pass:

- runtime-assembled context;
- typed action surface;
- action → execution → observation;
- layered context;
- externalized authority;
- execution substrate;
- verification.

Candidate universals explicitly falsified or rejected:

- one Tool per turn;
- mandatory human approval;
- immutable static Prompt;
- universal JSON function calling.

B05 therefore supports a compact structural kernel while rejecting implementation-shape universals.

---

# Recovery coverage

```text
A01  RECOVERED
A02  NOT_RETRIEVED
A03  RECOVERED
A04  RECOVERED
A05  NOT_RETRIEVED
B01  RECOVERED
B02  RECOVERED
B03  RECOVERED
B04  RECOVERED
B05  RECOVERED
```

Recovered substantive reports: **8 / 10**.

The missing A02/A05 reports remain gaps. They do not block promotion of a common primitive when the pre-registered threshold is independently satisfied by at least two recovered product-family reports, at least one recovered mechanism report, and the B05 falsifier.
