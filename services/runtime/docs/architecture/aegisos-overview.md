# AegisOS Overview

## Positioning

AegisOS is a governance-first AI workflow operating system baseline for constrained real-world work.

It is not a chat product, a prompt bundle, or a finance-specific agent shell. It is a system that organizes:

- intelligence for judgment
- governance for permission and policy
- execution for side effects and receipts
- state for fact and traceable truth
- knowledge for feedback and structured experience
- infrastructure for long-running operation
- experience for supervision and operator control

The working identity can be compressed into one line:

> AegisOS is a governance-first, truth-layered, long-running-capable AI workflow OS baseline with explicit pack and adapter boundaries.

## What It Is

AegisOS currently behaves like a single-agent-first operating base for AI work:

- it keeps a single sovereignty chain for writes and high-consequence transitions
- it allows intelligence to judge without giving intelligence system ownership
- it treats long-running work as runs, checkpoints, handoffs, wake/resume, and fallback, not as one long conversation
- it separates truth, feedback, hint, policy, and experience instead of mixing them into one memory blob
- it exposes supervisor-facing surfaces rather than only rendering model output

In repository terms, the system is now shaped as:

- `Core`
- `Pack`
- `Adapter`
- `Console / Workspace`

## Core Design Philosophy

### 1. AI is not sovereign

Models can judge, summarize, and propose, but they do not own:

- truth definition
- action authorization
- policy interpretation

That is why AegisOS separates:

- Intelligence
- Governance
- Execution
- State
- Knowledge

### 2. Truth must exist separately

Reality is not defined by:

- narration
- report text
- hints
- prompts

Reality is defined by:

- state objects
- request/receipt records
- trace relations
- outcomes
- audit-grade records

### 3. Failure must become structure

A failure is not fixed because the system "remembers" it. A failure is fixed when it becomes one or more of:

- a contract
- deterministic code
- a fallback rule
- a policy refinement
- a test
- a monitoring signal
- a runbook
- a feedback object

### 4. Latent and deterministic work must split

The model should do judgment. Deterministic code should do precision. Execution adapters should own external side effects. Governance should own durable constraints.

### 5. Capability must be reachable and governable

A function merely existing in the repo is not enough. It must be:

- routable
- testable
- registry-visible
- non-duplicative

### 6. Long-running work means pause, handoff, resume

AegisOS does not treat long tasks as infinite thinking. It treats them as structured runtime processes with:

- blocked states
- handoff artifacts
- checkpoint state
- wake reasons
- resume reasons
- fallback paths

### 7. Frontend is a supervisor surface

The user is not only a requester. The user is also:

- a reviewer
- an approver
- a supervisor
- an override source

That is why the frontend is evolving into a command center, execution workspace, and review workbench rather than a single report page.

### 8. Core stays stable, packs stay domain-owned, adapters stay replaceable

The system body must not collapse into:

- finance-specific semantics
- Hermes-specific runtime identity
- UI-local workflow ownership

This is why `packs/finance` and `adapters/runtimes/hermes` exist as explicit boundary layers.

## The Current AegisOS Shape

The system can now be understood as **9 responsibility layers plus 2 cross-cutting boundary layers**.

### Responsibility Layers

1. Experience
2. Capability
3. Orchestration
4. Governance
5. Intelligence
6. Execution
7. State
8. Knowledge
9. Infrastructure

### Boundary Layers

10. Pack
11. Adapter

## Layer-by-Layer Snapshot

### Experience

Experience is no longer just a UI shell. It is becoming a supervisor-facing workspace.

Current anchors:

- homepage command center
- `/analyze` execution workspace
- `/reviews` review workbench
- `WorkspaceProvider`
- `WorkspaceTabs`
- `ConsolePageFrame`
- trust-tier semantics

What this means:

- the UI is object-oriented rather than purely text-oriented
- fact, artifact, hint, and outcome signal are treated differently
- review and trace are work objects, not only display payloads

### Capability

Capability now expresses product actions instead of exposing random services.

Current anchors:

- capability contract split across `domain`, `workflow`, `view`, and `diagnostic`
- analyze capability
- review capability
- recommendation, dashboard, report, validation surfaces

What this means:

- the system is starting to say "what can be done" clearly
- routes and pages are less free to bypass product semantics

### Orchestration

Orchestration is no longer workflow glue. It is runtime order.

Current anchors:

- `ANALYZE_WORKFLOW`
- `TaskRun`
- `WorkflowRun`
- `HandoffArtifact`
- `WakeReason / ResumeReason`
- `CheckpointState`
- `FallbackDecision / FallbackResult`

What this means:

- work can block, degrade, hand off, and resume honestly
- the system is not limited to one-request-one-response semantics

### Governance

Governance is becoming the system's legality and decision layer.

Current anchors:

- `DecisionLanguage`
- `PolicySource`
- `ApprovalRecord`
- `HumanApprovalGate`
- `FeedbackHintConsumer`
- action boundary enforcement

What this means:

- AI does not directly own action legitimacy
- approvals are part of system state, not just UI actions
- hints can influence governance without becoming policy

### Intelligence

Intelligence is now a constrained runtime-facing judgment layer, not just a provider wrapper.

Current anchors:

- `AgentRuntime`
- `MemoryPolicy`
- `HintAwareContextBuilder`
- runtime resolution via adapter-first paths
- Hermes shim reduction

What this means:

- the system can keep model intelligence while reducing provider identity lock-in
- memory injection is governed instead of being an unbounded context dump

### Execution

Execution is evolving into a first-class action system.

Current anchors:

- `ActionRequest`
- `ActionReceipt`
- execution family adapters
- `ExecutionAdapterRegistry`
- `ExecutionProgressRecord`

What this means:

- actions are no longer invisible side effects
- success and failure can be tracked as system objects

### State

State is the truth-bearing graph of the system.

Current anchors:

- `TraceLink`
- `TraceGraph`
- `Outcome`
- `OutcomeGraph`
- `TaskRun`
- `CheckpointState`
- request/receipt state

What this means:

- object lineage is becoming explicit
- state transitions have stronger ownership and traceability

### Knowledge

Knowledge is the structured experience layer, not the truth layer.

Current anchors:

- `FeedbackPacket`
- `FeedbackRecord`
- `RecurringIssueAggregator`
- `CandidateRule`
- hint-aware context paths

What this means:

- the system can accumulate lessons without letting lessons override truth
- feedback can enter future work as advisory structure

### Infrastructure

Infrastructure is becoming the system's operational support layer.

Current anchors:

- `SchedulerService`
- scheduler persistence
- `/api/v1/health`
- `/api/v1/health/history`
- monitoring history
- runbooks

What this means:

- the system is beginning to support long-running, observable operation
- monitoring remains operational signal, not business truth

### Pack

Packs hold domain ownership without taking over core.

Current anchor:

- `packs/finance`

Current finance-owned pieces include:

- policy refs
- tool refs
- analyze defaults and profiles
- frontend analyze surface ownership

What this means:

- finance is becoming a domain pack instead of remaining fused to the system body

### Adapter

Adapters isolate external runtimes and providers from system identity.

Current anchor:

- `adapters/runtimes/hermes`

What this means:

- Hermes can remain important without becoming the system's self-definition
- future runtime replacement is structurally possible

## Core Frozen Primitives

The current system backbone depends on a set of frozen or mostly-frozen primitives:

- `DecisionLanguage`
- `ActionRequest / ActionReceipt`
- `Outcome`
- `FeedbackPacket`
- `TraceLink`
- `Task / Run`
- `AgentRuntime`
- `MemoryPolicy`

These matter because they keep the system from collapsing back into:

- route-local logic
- provider-local identity
- narrative truth
- untracked side effects

## Why This Matters

### Product value

- makes AI work more trustworthy
- makes complex workflows usable by supervisors and reviewers
- compresses AI output into auditable work chains

### Engineering value

- reduces hidden side effects
- gives long-running work a stable runtime model
- allows packs and adapters to evolve without redefining the system body

### Research value

AegisOS now contains credible seeds for work on:

- supervisor-facing AI workspaces
- governance-first agent systems
- truth vs hint separation
- long-running checkpointed agent workflows
- structured feedback and candidate-rule evolution

### Platform value

- core can stay general
- packs can carry domain ownership
- adapters can absorb runtime/provider churn

That is the structural basis for a real operating-system-style AI platform rather than a single-use model product.

## Current Stage Assessment

The most accurate current stage description is:

> AegisOS has crossed out of the ideas phase and into the load-bearing systems phase.

It already has:

- frozen primitives
- a real primary workflow
- governance boundaries
- state-bearing traces
- execution receipts
- knowledge feedback structure
- long-running runtime semantics
- a supervisor-facing console direction
- explicit pack and adapter extraction work

It is not yet:

- a finished platform
- a full flywheel
- a multi-pack ecosystem
- a production-complete AI operating system

But it is already more than a demo. It is now a credible AI workflow OS baseline.

## Compressed Project Statement

> AegisOS is building a new class of AI work system: not one where the model directly rules the product, but one where intelligence works under governance, state, execution, knowledge, and infrastructure constraints to produce work that is runnable, recoverable, auditable, and accumulable.
