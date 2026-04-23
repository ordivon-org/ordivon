# AegisOS Layer Roadmap

## Purpose

This roadmap turns the current AegisOS overview into an execution map.

It answers three questions for each layer:

- what is already real
- what is still incomplete
- what should happen next

This document is meant to sit one level below the design doctrine and one level above individual module cards.

## Current Program Frame

The system has already completed:

- Phase 0 primitive freeze
- Phase 1 core load-bearing strengthening
- serial boundary batches for pack, adapter, orchestration, infrastructure, and workspace
- post-serial refinement for finance extraction, Hermes reduction, scheduler persistence, monitoring history, and shared workspace behavior

The next program frame should focus on:

1. compressing the MVP gold path
2. continuing pack and adapter extraction
3. strengthening supervisor-facing workflow usage
4. preparing for production-grade long-running operation

## Experience

### Already real

- homepage command center direction
- `/analyze` as execution workspace
- `/reviews` as review workbench
- shared workspace tabs across console surfaces
- trust-tier semantics

### Still incomplete

- homepage, analyze, and reviews still need tighter product ownership boundaries
- knowledge, outcome, and recommendation detail surfaces are still uneven
- workspace is console-scoped, not yet a broader but still disciplined shell

### Next

- make the MVP gold path the obvious default across homepage, analyze, and reviews
- deepen review -> trace -> outcome -> knowledge object flow
- strengthen cross-page object continuity without turning the app into a tab-only shell

## Capability

### Already real

- capability split across `domain`, `workflow`, `view`, and `diagnostic`
- analyze and review product surfaces
- recommendation, dashboard, validation, and report capabilities

### Still incomplete

- capability layer still leans finance-first in product shape
- pack-aware capability ownership is not yet fully explicit
- general-purpose capabilities beyond finance remain early

### Next

- keep moving finance-specific product semantics behind `packs/finance`
- define the MVP capability chain explicitly around analyze -> recommendation -> review -> outcome
- avoid new route-local capability drift

## Orchestration

### Already real

- `ANALYZE_WORKFLOW`
- `TaskRun`
- `WorkflowRun`
- `HandoffArtifact`
- wake/resume semantics
- checkpoint state
- degraded fallback

### Still incomplete

- handoff is not yet pervasive across other workflows
- richer triggers and ambient orchestration are still weak
- resume behavior is structured but still narrow in usage

### Next

- extend handoff and checkpoint semantics beyond analyze
- add richer wake paths without letting scheduler own business semantics
- keep fallback honest and non-silent across more workflow branches

## Governance

### Already real

- `DecisionLanguage`
- `PolicySource`
- `ApprovalRecord`
- `HumanApprovalGate`
- approval-aware blocking
- advisory feedback hint consumption

### Still incomplete

- governance reporting and explainability are still thin
- candidate rule intake into governance is not yet a strong chain
- policy versioning and policy diff visibility remain weak

### Next

- deepen policy visibility and explanation surfaces
- define a formal candidate-rule-to-governance intake path
- continue keeping hints advisory-only and non-sovereign

## Intelligence

### Already real

- `AgentRuntime`
- `MemoryPolicy`
- `HintAwareContextBuilder`
- adapter-first runtime resolution
- Hermes runtime extraction and shim reduction

### Still incomplete

- Hermes compatibility residue still exists
- intelligence task taxonomy remains narrow
- verifier / clean-context / multi-intelligence patterns are not yet engineered in

### Next

- continue Hermes shim reduction until runtime ownership is fully adapter-local
- expand task taxonomy carefully without collapsing latent and deterministic roles
- keep memory injection policy-bound and truth-safe

## Execution

### Already real

- `ActionRequest`
- `ActionReceipt`
- execution family adapters
- `ExecutionAdapterRegistry`
- `ExecutionProgressRecord`

### Still incomplete

- more action families need formalization
- approval-aware execution is not yet evenly applied
- action catalog clarity can improve further

### Next

- keep turning side effects into first-class action families
- expand progress and heartbeat use where long-running work matters
- keep receipts and state transitions aligned so failed actions never masquerade as success

## State

### Already real

- `TraceLink`
- `TraceGraph`
- `Outcome`
- `OutcomeGraph`
- `TaskRun`
- `WorkflowRun`
- `CheckpointState`

### Still incomplete

- artifact and report relationships are still not fully first-class
- some cross-object traces still rely on historical or transitional shapes
- run and outcome graph queries can still become richer

### Next

- continue strengthening graph-style state truth
- keep report and artifact semantics honest and linked
- improve trace traversal for review, recommendation, run, and outcome chains

## Knowledge

### Already real

- `FeedbackPacket`
- `FeedbackRecord`
- `RecurringIssueAggregator`
- `CandidateRule`
- hint-aware retrieval paths

### Still incomplete

- retrieval quality and query ergonomics remain early
- experience-to-rule intake is only partially built
- taste or workflow skill transfer is not yet formalized as a knowledge program

### Next

- improve recurring issue and candidate rule usage
- deepen retrieval while keeping truth and feedback separate
- continue treating knowledge as accumulative structure rather than policy or truth

## Infrastructure

### Already real

- scheduler service
- scheduler persistence
- monitoring history
- `/health` and `/health/history`
- runbooks

### Still incomplete

- richer triggers remain sparse
- operator workflows are still early
- deployment and runtime discipline remain closer to strong MVP than mature service ops

### Next

- strengthen scheduler triggers without letting scheduler own business logic
- expand runbook discipline around real operational failure modes
- prepare a minimal production-grade operation loop

## Pack

### Already real

- `packs/finance`
- finance extraction plan
- finance pack policy refs
- finance pack tool refs
- analyze defaults, profiles, and frontend analyze surface ownership

### Still incomplete

- finance-specific surfaces still exist in generic product language
- finance context and policy ownership is not fully extracted
- finance remains the default visible domain in many places

### Next

- continue staged extraction beyond current analyze surface ownership
- keep moving finance semantics from generic UI and capability surfaces into pack-owned helpers
- preserve the rule that finance never redefines core identity

## Adapter

### Already real

- `adapters/runtimes/hermes`
- adapter-first runtime resolution
- runtime health through adapter paths

### Still incomplete

- Hermes cleanup is not fully finished
- adapter governance and gateway-like behavior are still early
- broader adapter patterns beyond runtime are not yet systematized

### Next

- continue removing compatibility residue
- keep adapter ownership explicit and non-sovereign
- prepare the system for future multi-runtime or multi-provider operation without identity drift

## Highest-Priority Cross-Layer Work

The next highest-leverage work should stay focused on a few threads:

1. **MVP gold path compression**
   - make homepage -> analyze -> reviews the clearest product chain

2. **Finance extraction continuation**
   - remove remaining finance ownership from generic UI and capability surfaces

3. **Hermes identity reduction**
   - finish moving runtime identity fully behind adapter boundaries

4. **Supervisor workspace strengthening**
   - deepen review, trace, outcome, and knowledge continuity

5. **Long-running operational maturity**
   - improve scheduler, monitoring, and recovery loops without over-expanding scope

## Module Planning Rule

Every future module should be framed against this roadmap and the doctrine:

- which philosophy it carries
- which layer it belongs to
- whether it is `Core`, `Pack`, or `Adapter`
- which chain it changes
- which wrong placement it must avoid
- which invariant it must preserve

That rule is how AegisOS keeps growing without sliding back into an “AI feature pile.”
