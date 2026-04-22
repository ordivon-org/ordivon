# AegisOS Design Doctrine

## Purpose

This document compresses the operating philosophy of `AegisOS / CAIOS` into a direct mapping:

- philosophy -> design rule
- design rule -> layer/module ownership
- ownership -> implementation discipline

The goal is not to produce a prettier manifesto.

The goal is to make every module an engineering carrier of a system belief.

## Design Thesis

`AegisOS` is not designed as a chat shell, model harness, or finance tool collection.

It is designed as:

**a controlled AI operating system in which intelligence participates in judgment, but governance, execution, state, knowledge, supervision, pack ownership, and adapter ownership remain separate.**

Compressed further:

**judgment goes to intelligence, authorization goes to governance, action goes to execution, reality goes to state, experience goes to knowledge, supervision goes to the workspace, domain ownership goes to packs, and external implementation goes to adapters.**

## Doctrine 1: Intelligence Is Not Sovereignty

### Belief

A model may judge, infer, classify, summarize, and propose.

It may not automatically own:

- truth definition
- action authorization
- policy interpretation
- execution success

### Engineering Consequence

The system must separate:

- intelligence output
- governance decision
- action execution
- factual recording
- experience accumulation

### Modules That Carry This Doctrine

- `DecisionLanguage`
- `PolicySource`
- `HumanApprovalGate`
- `AgentRuntime`
- `ActionRequest / ActionReceipt`

### Wrong Design To Avoid

- model writes state truth directly
- model decides action success by narration
- model promotes hints into policy

## Doctrine 2: Truth Must Exist Separately

### Belief

Reality cannot be defined by:

- chat text
- markdown reports
- narrative summaries
- hints
- audit prose

Reality must come from fact-bearing objects and formal relations.

Compressed:

**State is reality. Knowledge is interpretation.**

### Engineering Consequence

- reports are artifacts, not truth
- hints are guidance, not truth
- trace relations cannot be invented by narrative
- UI must distinguish fact, artifact, outcome signal, hint, missing, and unavailable

### Modules That Carry This Doctrine

- `TraceLink`
- `TraceGraph`
- `Outcome`
- `OutcomeGraph`
- `FeedbackRecord`
- `TrustTier`

### Wrong Design To Avoid

- infer state from markdown
- display hint as completed learning
- treat audit text as source-of-truth state

## Doctrine 3: Failure Must Become Structure

### Belief

A failure is not fixed because the team remembers it.

A failure is fixed when it leaves a durable system asset such as:

- deterministic code
- policy
- contract
- fallback rule
- test
- monitoring signal
- runbook
- recurring issue
- candidate rule

### Engineering Consequence

Every meaningful failure should be able to harden into at least one reusable asset.

### Modules That Carry This Doctrine

- `RecurringIssueAggregator`
- `CandidateRule`
- `FeedbackPacket`
- `FallbackDecision`
- `MonitoringHistory`
- `Runbook`

### Wrong Design To Avoid

- fix only in prompt text
- fix only in PR commentary
- failure without test, invariant, or operations follow-up

## Doctrine 4: Latent and Deterministic Work Must Be Separated

### Belief

Judgment belongs in latent systems.

Precision belongs in deterministic systems.

### Engineering Consequence

- intelligence does judgment
- code does repeatable exact work
- adapters perform external actions
- governance carries long-lived constraint
- context builders only inject what policy allows

### Modules That Carry This Doctrine

- `AgentRuntime`
- `ExecutionAdapterRegistry`
- `HintAwareContextBuilder`
- `MemoryPolicy`

### Wrong Design To Avoid

- model doing exact conversions/scripting the system can do deterministically
- workflow depending on model imagination for precise next-step semantics
- tool availability ignored in favor of model guesswork

## Doctrine 5: Reachability Must Be Verifiable

### Belief

A system ability does not really exist just because code exists somewhere in the repo.

It must also be:

- reachable
- resolvable
- testable
- non-duplicated

### Engineering Consequence

The platform needs registries, route tests, and object endpoints, not dark capabilities.

### Modules That Carry This Doctrine

- `ExecutionAdapterRegistry`
- future `CapabilityRegistry`
- route/integration tests
- detail endpoints such as `GET /recommendations/{id}`

### Wrong Design To Avoid

- unreachable skills
- duplicate route ownership
- workspace opening objects only by scanning list endpoints

## Doctrine 6: Long-Running Means Recoverable

### Belief

The target is not a forever-thinking agent.

The target is a system that can:

- block
- hand off
- wait
- wake
- resume
- degrade honestly

### Engineering Consequence

Long-running behavior must be modeled through formal orchestration/state objects.

### Modules That Carry This Doctrine

- `TaskRun`
- `CheckpointState`
- `HandoffArtifact`
- `WakeReason / ResumeReason`
- `SchedulerService`
- `FallbackResult`

### Wrong Design To Avoid

- `while true` pseudo-agents
- silent retry exhaustion
- UI-only handoff stories without formal references

## Doctrine 7: The Frontend Is a Supervision Surface

### Belief

The user is not only a requester.

The user may also be:

- supervisor
- reviewer
- approver
- override source

### Engineering Consequence

The workspace must support:

- object views
- trace visibility
- outcome visibility
- hint visibility
- honest missing-state communication
- review and approval interaction

### Modules That Carry This Doctrine

- `TrustTier`
- `ReviewConsole`
- `WorkspaceProvider`
- `WorkspaceTabs`
- `ConsolePageFrame`

### Wrong Design To Avoid

- one giant page pretending to be a workspace
- artifact looking like closed-loop truth
- error, empty, and unavailable collapsed into one state

## Doctrine 8: Core Must Stay Stable; Domain and Adapters Must Stay Replaceable

### Belief

The operating system should only generalize stable laws.

That means:

- `core` owns order
- `packs` own domain meaning
- `adapters` own replaceable integrations

### Engineering Consequence

- finance is a pack, not system identity
- Hermes is an adapter, not system identity
- stable primitives stay in core-like ownership
- domain refs/policies/defaults move behind pack facades

### Modules That Carry This Doctrine

- `packs/finance/policy.py`
- `packs/finance/tool_refs.py`
- `packs/finance/analyze_profile.py`
- `adapters/runtimes/hermes/runtime.py`
- `resolve_runtime()`

### Wrong Design To Avoid

- finance nouns reoccupying core
- provider implementation redefining system identity
- adapters mutating system meaning instead of implementing contracts

## Layer Mapping

## 1. Experience

### Carries

- supervision philosophy
- truth vs hint distinction
- object-first visibility

### Expected Modules

- `TrustTier`
- `ReviewConsole`
- `WorkspaceProvider`
- `WorkspaceTabs`
- `TraceDetail`
- `OutcomeDetail`
- `KnowledgeHintSurface`

### Layer Invariant

Experience must not hide complexity by lying about object type or certainty.

## 2. Capability

### Carries

- reachability philosophy
- product action boundary

### Expected Modules

- `analyze capability`
- `review capability`
- `monitoring summary capability`
- future `clarify_intent`
- future `research`

### Layer Invariant

Capabilities describe product-allowed actions, not provider or implementation details.

## 3. Orchestration

### Carries

- recoverable long-running philosophy
- explicit handoff/fallback semantics

### Expected Modules

- `HandoffArtifact`
- `TaskRun`
- `WakeReason / ResumeReason`
- `FallbackDecision`
- `FallbackResult`

### Layer Invariant

Orchestration owns how work continues, pauses, resumes, or degrades.

## 4. Governance

### Carries

- sovereignty philosophy
- control and permission semantics

### Expected Modules

- `DecisionLanguage`
- `PolicySource`
- `ApprovalRecord`
- `HumanApprovalGate`
- `FeedbackHintConsumer`

### Layer Invariant

Intelligence may advise; governance authorizes.

## 5. Intelligence

### Carries

- non-sovereign judgment
- memory under policy
- runtime replaceability

### Expected Modules

- `AgentRuntime`
- `MemoryPolicy`
- `HintAwareContextBuilder`
- task taxonomy
- runtime resolver

### Layer Invariant

Intelligence must not smuggle deterministic work or state truth into latent behavior.

## 6. Execution

### Carries

- action accountability
- request/receipt discipline

### Expected Modules

- `ActionRequest`
- `ActionReceipt`
- `ExecutionAdapterRegistry`
- family adapters
- `ExecutionProgressRecord`

### Layer Invariant

No formal action exists without request/receipt semantics.

## 7. State

### Carries

- truth philosophy
- relation hardening
- outcome as fact

### Expected Modules

- `TraceLink`
- `TraceGraph`
- `Outcome`
- `OutcomeGraph`
- `CheckpointState`

### Layer Invariant

Narrative cannot create state truth.

## 8. Knowledge

### Carries

- structured experience philosophy
- influence without truth takeover

### Expected Modules

- `FeedbackPacket`
- `FeedbackRecord`
- `RecurringIssueAggregator`
- `CandidateRule`

### Layer Invariant

Knowledge may influence future behavior, but may not redefine truth or auto-activate policy.

## 9. Infrastructure

### Carries

- operational survivability
- recoverability
- observability

### Expected Modules

- `SchedulerService`
- scheduler persistence
- monitoring history
- health endpoints
- runbooks

### Layer Invariant

Infrastructure keeps the system alive; it does not own business meaning.

## Module Definition Rule

Every new module should answer these seven questions before implementation:

1. Which doctrine does it carry?
2. Which layer owns it?
3. Is it `Core`, `Pack`, or `Adapter`?
4. Who is the owner?
5. What is it not allowed to do?
6. Which chain does it change?
7. What invariant must stay true?

## Final Compression

**AegisOS modules are not just feature buckets. They are engineering carriers of philosophical constraints about sovereignty, truth, failure, determinism, supervision, and replaceable ownership.**
