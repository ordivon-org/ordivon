# AegisOS Next-Round Execution Plan

## Status

This document is the corrected next-round execution table for the system under its working platform identity:

- external: `AegisOS`
- internal: `CAIOS`

It is based on current repository reality, not on a clean-slate wishlist.

That means:

- modules that are already real are marked as already established
- the next-round focus is on missing load-bearing platform pieces

Phase 0 primitive freeze has now been completed.

That means this document should now be read primarily as the **Phase 1+ execution map**.

## Guiding Rule

The next round is **not** primarily about adding more finance features.

The next round is about:

**filling the remaining load-bearing pieces of the general system substrate.**

Compressed:

**next round is not feature expansion; it is kernel completion.**

## Execution Rule

Every next-round module must answer:

1. is it `Core`, `Pack`, or `Adapter`
2. which chain gap does it close
3. what does it explicitly not do
4. what invariant does it protect
5. can it pollute state truth
6. can it accidentally push finance semantics back into core

## Phase 0: Freeze Core Primitives

This phase is primarily semantic freezing, not large code movement.

### Module 0.1

- Layer: `Cross-layer`
- Module: `DecisionLanguage`
- Why: governance, experience, and execution cannot keep drifting semantically
- Priority: `P0`
- Type: `Core`
- Current Reality:
  - already materially real in current code
  - next need is stricter primitive freeze, not first implementation
- Immediate Action:
  - freeze the formal shape:
    - `execute`
    - `escalate`
    - `reject`
  - standardize:
    - `reason`
    - `source`
    - `evidence`
    - `actor`
    - `scope`
- Done Criteria:
  - analyze main chain and at least one additional surface share the same decision object shape
- Required Test Pack:
  - unit: decision mapping / validation
  - integration: analyze -> governance -> decision object
  - invariant: no governed side-effect without explicit decision

### Module 0.2

- Layer: `Execution / State`
- Module: `ActionRequest / ActionReceipt`
- Why: execution discipline needs a frozen cross-family contract
- Priority: `P0`
- Type: `Core`
- Current Reality:
  - already real across multiple families
  - next need is primitive freeze and platform-neutral contract definition
- Immediate Action:
  - freeze the canonical fields
  - freeze `pending / succeeded / failed` receipt semantics
- Done Criteria:
  - recommendation, review, and validation families all clearly conform to one primitive definition
- Required Test Pack:
  - unit: request / receipt schema validation
  - invariant: no success state without success receipt

### Module 0.3

- Layer: `State`
- Module: `Outcome`
- Why: outcome must be elevated from partial finance-chain usage into a clean primitive
- Priority: `P0`
- Type: `Core`
- Current Reality:
  - outcome is already real
  - next need is explicit primitive freeze and broader relation semantics
- Immediate Action:
  - freeze minimal outcome fields
  - freeze relation semantics independent of finance-only wording
- Done Criteria:
  - recommendation / review / outcome share one explicit primitive model
- Required Test Pack:
  - unit: outcome schema
  - integration: recommendation -> outcome link
  - invariant: no outcome must not be rendered as present

### Module 0.4

- Layer: `Knowledge`
- Module: `FeedbackPacket`
- Why: packet exists, but still needs fully frozen primitive semantics
- Priority: `P0`
- Type: `Core`
- Current Reality:
  - packet already exists and is persisted
  - next need is contract freeze across production / reference / consumption
- Immediate Action:
  - freeze packet fields
  - freeze its semantic status:
    - hint
    - not truth
    - not policy
- Done Criteria:
  - production, trace, governance, and intelligence all use one packet meaning
- Required Test Pack:
  - unit: packet validation
  - invariant: feedback must not override state truth

### Module 0.5

- Layer: `State / Trace`
- Module: `TraceLink`
- Why: trace is real, but the primitive itself still needs stronger formalization
- Priority: `P0`
- Type: `Core`
- Current Reality:
  - trace query path exists
  - next need is explicit relation-type and relation-source freeze
- Immediate Action:
  - define minimum relation types
  - define source precedence:
    - direct persisted link
    - structured fallback
    - not narrative invention
- Done Criteria:
  - recommendation / workflow_run / receipt relations can be expressed through one trace-link primitive
- Required Test Pack:
  - unit: relation builder
  - invariant: no narrative metadata-only truth creation

### Module 0.6

- Layer: `Orchestration / State`
- Module: `Task / Run`
- Why: future wake/resume and long-running work need a shared primitive
- Priority: `P0`
- Type: `Core`
- Current Reality:
  - `WorkflowRun` exists
  - future generalized task/run abstraction is still missing
- Immediate Action:
  - freeze task/run state
  - freeze blocked reason / wake reason / resume semantics
- Done Criteria:
  - workflow run and future task run can be interpreted through one abstraction family
- Required Test Pack:
  - unit: run lifecycle validation
  - integration: run creation / run completion

### Module 0.7

- Layer: `Intelligence`
- Module: `AgentRuntime`
- Why: Hermes must stop feeling like the default system body
- Priority: `P0`
- Type: `Core`
- Current Reality:
  - Hermes integration is real
  - runtime abstraction is still mixed with implementation detail
- Immediate Action:
  - define runtime interface
  - position Hermes as adapter implementation
- Done Criteria:
  - analyze no longer depends on Hermes-specific internal semantics
- Required Test Pack:
  - unit: runtime contract tests
  - integration: Hermes adapter satisfies runtime contract

### Module 0.8

- Layer: `Intelligence / Knowledge`
- Module: `MemoryPolicy`
- Why: without this, knowledge and state will drift into each other
- Priority: `P0`
- Type: `Core`
- Current Reality:
  - hint injection exists
  - memory semantics are not yet frozen as policy
- Immediate Action:
  - separate:
    - transient context
    - persisted memory
    - feedback hints
    - forbidden writes
- Done Criteria:
  - hint injection has an explicit memory-policy boundary
- Required Test Pack:
  - unit: policy resolution
  - invariant: hints and memory must not rewrite canonical truth

## Phase 1: Fill The System Load-Bearing Pieces

This is the primary next-round implementation phase.

## 1. Governance

### Module 1.1

- Layer: `Governance`
- Module: `PolicySource`
- Why: governance rules cannot stay scattered
- Priority: `P0`
- Type: `Core`
- Current Reality:
  - minimal policy source already exists
  - next need is deeper centralization and broader usage
- Immediate Action:
  - deepen `policy_source.py`
  - route more key governance reads through it
- Done Criteria:
  - analyze-critical rules are not scattered across route/service/workflow logic
- Required Test Pack:
  - unit: policy resolution
  - integration: governance reads central policy source
  - invariant: UI / workflow / service do not invent independent policy meaning

### Module 1.2

- Layer: `Governance`
- Module: `FeedbackHintConsumer`
- Why: governance must read feedback without promoting it to policy
- Priority: `P0`
- Type: `Core`
- Current Reality:
  - this is already partially real
  - next need is formal primitive freeze and broader reuse
- Immediate Action:
  - formalize hint-aware governance as explicit consumer behavior
- Done Criteria:
  - at least one stable governance path reads feedback hints under explicit advisory semantics
- Required Test Pack:
  - unit: hint -> governance mapping
  - integration: feedback prepared -> governance read path
  - invariant: feedback never auto-upgrades into rule or policy

### Module 1.3

- Layer: `Governance`
- Module: `HumanApprovalGate`
- Why: future supervisor workflows need a first-class approval primitive
- Priority: `P1`
- Type: `Core`
- Current Reality:
  - missing
- Immediate Action:
  - define approval record and approval-aware gate interface
- Done Criteria:
  - at least one action family can be blocked on approval
- Required Test Pack:
  - unit: approval state validation
  - integration: action blocked until approval
  - invariant: no approved-missing action may produce success receipt

## 2. Intelligence

### Module 2.1

- Layer: `Intelligence`
- Module: `HintAwareContextBuilder`
- Why: this is the cleanest next step toward a real learning loop
- Priority: `P0`
- Type: `Core`
- Current Reality:
  - partially real
  - next need is formalized channel semantics
- Immediate Action:
  - make hint channel explicit in runtime context building
- Done Criteria:
  - analyze context carries explicit derived-guidance input
- Required Test Pack:
  - unit: hint injection builder
  - integration: review -> feedback -> future analyze context
  - invariant: hints must not override canonical state

### Module 2.2

- Layer: `Intelligence`
- Module: `TaskTaxonomy`
- Why: runtime is still too analyze-centric
- Priority: `P1`
- Type: `Core`
- Current Reality:
  - missing as a formalized taxonomy
- Immediate Action:
  - add:
    - `analyze`
    - `clarify_intent`
    - `summarize`
    - `lesson_draft`
- Done Criteria:
  - at least one non-analyze task becomes real in runtime and persistence
- Required Test Pack:
  - unit: task contracts
  - integration: new task run persistence

## 3. Execution

### Module 3.1

- Layer: `Execution`
- Module: `ReviewFamilyAdapter`
- Why: review actions must stay under one family execution discipline
- Priority: `P0`
- Type: `Core`
- Current Reality:
  - already real
  - next need is platform-neutral contract formalization
- Immediate Action:
  - freeze review-family adapter contract inside execution platform semantics
- Done Criteria:
  - review submit / complete remain request/receipt/failure consistent under one contract
- Required Test Pack:
  - unit: review adapter request/receipt
  - integration: review API -> request/receipt/audit/state
  - failure-path: invalid transition / failure path
  - invariant: no success receipt, no completed state

### Module 3.2

- Layer: `Execution`
- Module: `ValidationFamilyAdapter`
- Why: validation should not remain a one-off family
- Priority: `P1`
- Type: `Core`
- Current Reality:
  - already real in first form
  - next need is contract normalization
- Immediate Action:
  - align validation family with the same adapter contract as recommendation/review
- Done Criteria:
  - at least one validation action family cleanly conforms to platform execution semantics
- Required Test Pack:
  - unit: validation adapter
  - integration: validation path -> request/receipt
  - invariant: failed receipt never accompanies success row mutation

### Module 3.3

- Layer: `Execution`
- Module: `AdapterRegistry`
- Why: family adapters exist but there is no common platform contract
- Priority: `P1`
- Type: `Core`
- Current Reality:
  - missing
- Immediate Action:
  - define common adapter contract
  - create minimal registry
- Done Criteria:
  - recommendation and review families resolve through the same registry contract
- Required Test Pack:
  - unit: registry lookup / contract enforcement
  - integration: multi-family adapter resolution

### Module 3.4

- Layer: `Execution`
- Module: `Progress / Heartbeat`
- Why: future long-running work will need observable action progress
- Priority: `P1`
- Type: `Core`
- Current Reality:
  - missing
- Immediate Action:
  - define progress marker and heartbeat model at activity level
- Done Criteria:
  - at least one longer-running activity can emit progress or heartbeat
- Required Test Pack:
  - unit: progress update / heartbeat expiry
  - integration: long-step progress persistence

## 4. State

### Module 4.1

- Layer: `State`
- Module: `TraceGraph`
- Why: this is what makes the object system truly coherent
- Priority: `P0`
- Type: `Core`
- Current Reality:
  - trace exists
  - generalized trace graph primitive still not frozen
- Immediate Action:
  - unify trace relation resolution for:
    - workflow_run
    - recommendation
    - review
- Done Criteria:
  - given workflow_run or recommendation, core upstream/downstream objects can be traced through one graph contract
- Required Test Pack:
  - unit: relation builder / missing handling
  - integration: main-path trace query
  - invariant: no metadata-only relation invention

### Module 4.2

- Layer: `State`
- Module: `OutcomeGraph`
- Why: no outcome graph means no durable loop foundation
- Priority: `P0`
- Type: `Core`
- Current Reality:
  - partial recommendation -> review -> outcome chain is real
  - graph-level primitive is still missing
- Immediate Action:
  - strengthen recommendation -> review -> outcome relation model
- Done Criteria:
  - outcome becomes a clearly modeled downstream object, not only a backfilled side record
- Required Test Pack:
  - integration: recommendation -> outcome relation
  - state/data: outcome link correctness
  - invariant: absent outcome must not appear present

### Module 4.3

- Layer: `State`
- Module: `CheckpointState`
- Why: wake/resume needs state anchors
- Priority: `P1`
- Type: `Core`
- Current Reality:
  - missing
- Immediate Action:
  - add blocked reason / wake reason / resume marker
- Done Criteria:
  - at least workflow/task state can record resume points
- Required Test Pack:
  - unit: checkpoint schema
  - integration: pause/resume state record

## 5. Knowledge

### Module 5.1

- Layer: `Knowledge`
- Module: `FeedbackRecord`
- Why: feedback needs a richer formal record than ad hoc packet consumption history
- Priority: `P1`
- Type: `Core`
- Current Reality:
  - packet object exists
  - dedicated consumption/record model still missing
- Immediate Action:
  - define minimal feedback record object
- Done Criteria:
  - feedback becomes queryable, traceable, and auditable as a formal record
- Required Test Pack:
  - unit: feedback record validation
  - integration: review complete -> feedback persisted

### Module 5.2

- Layer: `Knowledge`
- Module: `RecurringIssueAggregator`
- Why: recurring issues must become a first-class contract, not just a helper
- Priority: `P1`
- Type: `Core`
- Current Reality:
  - partially real
  - next need is primitive freeze and broader contractization
- Immediate Action:
  - freeze recurring-issue identification rules and output schema
- Done Criteria:
  - at least one recurring issue type can be recognized from multiple lessons through a formal aggregator contract
- Required Test Pack:
  - unit: aggregation logic
  - integration: multi-lesson -> recurring issue
  - invariant: recurring issue is not policy

### Module 5.3

- Layer: `Knowledge`
- Module: `CandidateRule`
- Why: this is the bridge from knowledge into governance without direct policy mutation
- Priority: `P1`
- Type: `Core`
- Current Reality:
  - missing
- Immediate Action:
  - define candidate rule schema and review path
- Done Criteria:
  - candidate rule can be recorded without automatic activation
- Required Test Pack:
  - unit: candidate rule validation
  - invariant: candidate rule must not auto-promote to policy

## Phase 2: Supervision Workspace And Long-Running Support

## 6. Experience

### Module 6.1

- Layer: `Experience`
- Module: `ReviewConsole`
- Why: supervisor UX needs a real review-centered surface
- Priority: `P0`
- Type: `Core`
- Current Reality:
  - partial review detail surfaces exist
  - no dedicated supervisor-grade console yet
- Immediate Action:
  - create dedicated review view with:
    - trace refs
    - outcome
    - feedback
    - supervisor actions
- Done Criteria:
  - review is no longer only list-surface plus API shell
- Required Test Pack:
  - type check
  - unit: render / conditional states
  - integration: review surface smoke
  - invariant: hint never displayed as truth

### Module 6.2

- Layer: `Experience`
- Module: `Tabbed Workspace`
- Why: future work will need browser/IDE-like multi-object supervision
- Priority: `P1`
- Type: `Core`
- Current Reality:
  - missing
- Immediate Action:
  - support object tabs for:
    - recommendation detail
    - review detail
    - trace detail
- Done Criteria:
  - multiple object views can coexist with preserved context
- Required Test Pack:
  - unit: tab state / route state
  - integration: object-to-object navigation

### Module 6.3

- Layer: `Experience`
- Module: `TrustTierSemantics`
- Why: trust semantics must become systematic, not local helper usage
- Priority: `P1`
- Type: `Core`
- Current Reality:
  - partially real
  - not yet system-wide
- Immediate Action:
  - formalize one UI semantic layer for:
    - fact
    - relation
    - artifact
    - outcome signal
    - hint
- Done Criteria:
  - key pages stop mixing truth/hint/artifact semantics
- Required Test Pack:
  - unit: semantic copy assertions
  - integration: surface semantic smoke

## 7. Orchestration

### Module 7.1

- Layer: `Orchestration`
- Module: `HandoffArtifact`
- Why: long-running work and future subtasking require explicit handoff objects
- Priority: `P1`
- Type: `Core`
- Current Reality:
  - missing
- Immediate Action:
  - define partial-result / blocked-reason / next-action artifact schema
- Done Criteria:
  - at least one workflow can emit a handoff artifact
- Required Test Pack:
  - unit: artifact schema
  - integration: workflow -> artifact -> next step

### Module 7.2

- Layer: `Orchestration`
- Module: `Wake / Resume Policy`
- Why: not for daemon fantasy, but for honest recoverable long-running work
- Priority: `P1`
- Type: `Core`
- Current Reality:
  - missing as a generalized policy
- Immediate Action:
  - define wake reason / resume reason model
- Done Criteria:
  - at least one task can pause and resume honestly
- Required Test Pack:
  - unit: wake/resume policy
  - integration: paused -> resumed task flow

### Module 7.3

- Layer: `Orchestration`
- Module: `FallbackPolicy`
- Why: retry and compensation alone are not enough
- Priority: `P1`
- Type: `Core`
- Current Reality:
  - partial policy exists
  - explicit fallback path is still weak
- Immediate Action:
  - add at least one concrete analyze-step fallback or honest-fail path
- Done Criteria:
  - retry exhaustion leads to explicit fallback or explicit honest fail
- Required Test Pack:
  - integration: retry exhausted path
  - invariant: fallback never masquerades as success

## 8. Infrastructure

### Module 8.1

- Layer: `Infrastructure`
- Module: `Scheduler`
- Why: future long-running and automation paths need bounded scheduling
- Priority: `P1`
- Type: `Core`
- Current Reality:
  - missing
- Immediate Action:
  - implement one minimal scheduled-work trigger
- Done Criteria:
  - at least one periodic task can be scheduled
- Required Test Pack:
  - integration: scheduler -> task trigger
  - failure-path: honest reporting when dependency unavailable

### Module 8.2

- Layer: `Infrastructure`
- Module: `Health / Monitoring`
- Why: signals are real, but broader operational observation still lags
- Priority: `P1`
- Type: `Core`
- Current Reality:
  - partially real
  - next need is stronger monitoring system and history
- Immediate Action:
  - deepen runtime/workflow/execution failure visibility
- Done Criteria:
  - critical component and failure metrics are visible beyond minimal snapshot
- Required Test Pack:
  - integration: health endpoint
  - failure-path: unhealthy component reporting

### Module 8.3

- Layer: `Infrastructure`
- Module: `AgentRegistry`
- Why: future runtimes, packs, and adapters should not depend on hidden wiring
- Priority: `P2`
- Type: `Core`
- Current Reality:
  - missing
- Immediate Action:
  - define minimal registry
- Done Criteria:
  - at least one runtime and one pack can be registered and discovered
- Required Test Pack:
  - unit: registration / lookup
  - integration: registered runtime resolution

## Phase 3: Formal Pack / Adapter Separation

## 9. Finance Pack

### Module 9.1

- Layer: `Pack Layer`
- Module: `Finance Pack Extraction`
- Why: finance must stop masquerading as system identity
- Priority: `P1`
- Type: `Pack`
- Current Reality:
  - semantic freeze exists
  - physical and import-level extraction does not
- Immediate Action:
  - inventory finance objects / workflows / policies / surfaces
  - mark what remains core vs what belongs to finance pack
- Done Criteria:
  - recommendation / review / finance-specific context have explicit pack ownership
- Required Test Pack:
  - architecture tests
  - import-boundary tests

## 10. Adapters

### Module 10.1

- Layer: `Adapter Layer`
- Module: `Hermes Runtime Adapter`
- Why: Hermes must become a replaceable runtime implementation, not the system body
- Priority: `P1`
- Type: `Adapter`
- Current Reality:
  - conceptually classified as adapter
  - not yet extracted into explicit adapter-boundary structure
- Immediate Action:
  - migrate Hermes integration toward `adapters/runtimes/hermes`
- Done Criteria:
  - Hermes enters through `AgentRuntime` interface
- Required Test Pack:
  - runtime adapter contract tests
  - integration: Hermes-backed analyze still works

### Module 10.2

- Layer: `Adapter Layer`
- Module: `NotebookLM Research Adapter`
- Why: external research systems should stay supplemental, not become truth owners
- Priority: `P2`
- Type: `Adapter`
- Current Reality:
  - missing
- Immediate Action:
  - design research-ingestion adapter only
- Done Criteria:
  - external research -> evidence bundle -> knowledge entry boundary is explicit
- Required Test Pack:
  - unit: ingestion mapping
  - invariant: external research never becomes state truth directly

## Strict Execution Order

The corrected strict order is:

1. freeze core primitives
2. deepen `DecisionLanguage / PolicySource / FeedbackHintConsumer`
3. define `AgentRuntime / MemoryPolicy / HintAwareContextBuilder`
4. formalize execution platform seams around review/validation families
5. freeze `TraceGraph / OutcomeGraph`
6. deepen `FeedbackRecord / RecurringIssue / CandidateRule`
7. build `ReviewConsole`
8. add `HandoffArtifact / WakeResume / Fallback`
9. deepen infra with `Scheduler / Monitoring`
10. extract `Finance Pack` and `Hermes Adapter`

## Final Summary

The next round for `AegisOS` / `CAIOS` is not feature-first.

It is substrate-first.

The most important load-bearing work is:

- decision
- policy
- runtime
- memory
- trace
- outcome
- execution-platform seams
- feedback

Compressed:

**next round is not feature growth; it is kernel completion.**
