# Harness Adapter Protocol v0 (HAP-1)

> **v0 / prototype / internal design.** Not a public standard. Not a release.
> Not a live API. Not an MCP server. Not an execution runtime.
> **Status:** OPEN — HAP-1 foundation

## Identity

HAP = **Harness Adapter Protocol.**

HAP is the protocol layer for describing how Ordivon models and governs
external AI/code/runtime harnesses — the surfaces that wrap agents, tools,
CLIs, MCP servers, and worker processes.

HAP does not:
- Execute work by itself.
- Replace agents, MCP servers, CI systems, IDEs, or frameworks.
- Authorize action by mere capability declaration.
- Grant approval because a harness manifest exists.

### Positioning

```
Intelligence proposes.
Governance authorizes.
Orchestration schedules.
Adapter executes.
Execution leaves evidence.
State records truth.
Review supervises.
```

HAP sits at the boundary between **harness** (what wraps and describes an agent/runtime)
and **governance** (what evaluates, authorizes, and reviews). It is adjacent to OGAP but
addresses a distinct concern:

| Protocol | Concern |
|----------|---------|
| **OGAP** | External adapter protocol — governs how external systems make work governable |
| **HAP** | Harness adapter protocol — describes what harnesses can do, what they did, and what evidence they left |

An OGAP-compatible adapter is **governable.**
A HAP-described harness is **describable and auditable.**

Neither compatibility nor description implies authorization.

## Relationship to OGAP

HAP is adjacent to OGAP, not a replacement.

```
OGAP: external system → work claim → evidence → governance decision
HAP:  harness runtime → task shape → capability → execution receipt → evidence
```

OGAP governs the adapter protocol semantics.
HAP describes the harness capability/task/receipt/evidence surface.
Together they provide the full governance loop for agent-driven work.

## Architecture Layers

HAP defines nine boundary concepts between:

| Layer | HAP Object | Concern |
|-------|-----------|---------|
| Model / Intelligence | *(not in HAP scope)* | What the model proposes |
| **Harness** | HarnessAdapterManifest | Identity, family, declared boundaries |
| **Capability** | HarnessCapability | Technical ability (not authorization) |
| **Risk** | HarnessRiskProfile | Risk surface classification |
| Task Request | HarnessTaskRequest | What is being asked |
| Task Plan | HarnessTaskPlan | Proposed execution shape |
| **Boundary** | HarnessBoundaryDeclaration | Allowed/forbidden surfaces |
| Execution | HarnessExecutionReceipt | What was done |
| Evidence | HarnessEvidenceBundle | Proof of what happened |
| Result | HarnessResultSummary | READY/DEGRADED/BLOCKED/etc. |
| Review | HarnessReviewRecord | Human/automated review findings |

## Capability Declaration

HAP capabilities describe technical ability. They do not authorize action.

| Field | Description |
|-------|-------------|
| can_read_files | Can read files from workspace |
| can_write_files | Can write/modify files in workspace |
| can_apply_patch | Can apply targeted file patches |
| can_run_shell | Can execute shell commands |
| can_use_browser | Can interact with browser |
| can_use_mcp | Can connect to MCP servers |
| can_read_credentials | Technical ability to read credential-like material |
| can_call_external_api | Can make outbound API calls |
| supports_streaming_events | Can emit streaming events |
| supports_resume | Can resume from interrupted state |
| supports_structured_output | Can produce structured (JSON/regex) output |
| supports_cost_reporting | Can report token/cost usage |
| supports_worktree_isolation | Can operate in isolated worktree |
| max_context_tokens | Maximum context window size |
| default_timeout_seconds | Default task timeout |

### Critical: can_read_credentials

`can_read_credentials` describes a technical capability only.

It does not:
- Grant credential access
- Imply secret access
- Authorize external calls
- Authorize tool execution
- Grant any permission

**Capability declaration is not authorization.**

## Risk Classification

| risk_level | Description |
|-----------|-------------|
| read_only | No filesystem mutation, no shell, no external calls |
| workspace_write | Can write to workspace files |
| shell | Can execute shell commands |
| external_side_effect | Can make outbound API calls or trigger external state changes |

## Harness Families (non-exhaustive)

HAP-1 defines the protocol framework for describing harnesses. It does not
implement or execute any of them. Example families include:

- **Hermes** — multi-tool AI agent CLI
- **Codex** — OpenAI Codex CLI
- **Claude Code** — Anthropic Claude Code CLI
- **Gemini CLI** — Google Gemini CLI
- **Cursor / Windsurf** — IDE-integrated agent environments
- **MCP server surfaces** — tool-exposing servers
- **Custom workers** — bespoke runtime workers

HAP-1 must not overfit to any single harness.

## Critical Boundaries

| Boundary | Meaning |
|----------|---------|
| Harness capability is not authorization | can_X ≠ may_X |
| Task request is not approval | Asking is not authorization |
| Plan is not execution permission | Planning does not grant execution right |
| Receipt is not approval | Recording what happened is not authorization |
| Evidence is not approval | Proof of work is not authorization |
| READY is not execution authorization | Evidence adequate ≠ action authorized |
| Valid HAP payload does not authorize action | Structure correct ≠ permission granted |
| Compatibility does not authorize action | HAP-described ≠ approved |

## What HAP-1 Does Not Create

HAP-1 is a local documentation + schema/fixture/test foundation only.

- ❌ No live API
- ❌ No SDK
- ❌ No MCP server
- ❌ No SaaS endpoint
- ❌ No package release
- ❌ No public standard
- ❌ No public repo
- ❌ No live adapter transport
- ❌ No broker/API integration
- ❌ No credential access
- ❌ No external tool execution
- ❌ No action authorization
- ❌ Financial/broker/live actions remain NO-GO
- ❌ Phase 8 remains DEFERRED

## External Benchmark Reference

HAP-1 references public frontier-AI governance patterns from OpenAI,
Anthropic, Google DeepMind, NIST, and ISO as external benchmarks for
internal comparison and gap analysis only. This does not imply
certification, compliance, endorsement, partnership, equivalence, or
public-standard status.

## Next Phase

HAP-1 scope is foundation only. HAP-2 (fixture dogfood, transport decision
criteria, harness scenario expansion) requires a separate phase prompt with
Allowed/Forbidden sections.

*Phase: HAP-1 | Risk: R0 | Authority impact: current_truth only*
