# AI Financial Assistant Roadmap

## Purpose

This document translates the architecture baseline into product-facing execution priorities.

Use [task-template-system](./task-template-system.md) as the default task definition format when turning this roadmap into concrete work.

The external product goal remains simple:

**build a trustworthy AI financial assistant.**

The nine responsibility surfaces are internal engineering structure. They exist to make the assistant controllable, traceable, and capable of learning.

## Current Situation

PFIOS has already completed important structural tightening:

- product truthfulness improved
- capability contracts were classified
- side-effect boundaries were tightened
- Hermes now participates in the intelligence layer
- `AgentAction` records AI execution lineage
- analyze can flow through:
  - capability
  - orchestration
  - Hermes-backed intelligence
  - governance
  - audit/report/state

But the system is not yet a full assistant.

It is currently:

- a partially real controlled analysis system
- a partially real governance and audit system
- an emerging AI runtime integration
- an incomplete learning loop

## Product Goal

The product goal is not to expose architecture.

The product goal is:

**an AI financial assistant that can help users analyze situations, generate controlled recommendations, explain risk, track outcomes, and accumulate lessons over time.**

That assistant should eventually do five things well:

1. understand financial questions
2. produce structured analysis and recommendations
3. operate under visible governance
4. preserve traceable history
5. learn from outcomes and feedback

## Product Loop

The assistant should ultimately operate through this loop:

`task -> analysis -> recommendation -> review/governance -> execution or rejection -> audit/report -> outcome -> lesson -> improved future behavior`

## What The User Should Feel

From the user perspective, the system should feel like:

- one assistant, not many scattered tools
- honest about confidence and uncertainty
- clear about consequences
- able to explain where a conclusion came from
- able to show what happened afterward
- increasingly useful over time

## Strategic Phases

### Phase 1: Assistant Core

Goal:

Make the product feel like one assistant rather than many disconnected surfaces.

Key work:

- unify product language for analyze, recommendation, review, and report
- strengthen object visibility in UI and API
- define the core assistant task set:
  - market analysis
  - portfolio analysis
  - recommendation support
  - risk explanation
  - review and postmortem support

Primary layers:

- Experience
- Capability
- Intelligence

Phase-complete when:

- the user can clearly understand what the assistant can do
- the assistant surface feels like one product

### Phase 2: Controlled Main Chain

Goal:

Make the assistant trustworthy as a controlled system.

Key work:

- harden `analyze -> recommendation -> review/governance -> audit -> report`
- expand side-effect boundaries
- objectify execution requests and receipts
- improve run lineage and state transitions

Primary layers:

- Governance
- Orchestration
- Execution
- State

Phase-complete when:

- at least one meaningful chain is fully traceable
- real action paths are controlled and auditable

### Phase 3: Learning Loop

Goal:

Make the assistant capable of learning from outcomes rather than only producing outputs.

Key work:

- define knowledge objects
- extract lessons from report, validation, and outcome
- connect lessons back into governance and intelligence
- establish flywheel metrics

Primary layers:

- Knowledge
- State
- Intelligence
- Governance

Phase-complete when:

- at least one learning path feeds forward into future behavior

### Phase 4: Personal Financial Assistant

Goal:

Turn the controlled system into a genuinely valuable user assistant.

Key work:

- preference and user-profile awareness
- portfolio-level guidance
- risk-budget support
- longer-horizon tracking and reminders
- proactive follow-up on recommendations and outcomes

Primary layers:

- Experience
- Capability
- Intelligence
- Knowledge

Phase-complete when:

- the product behaves like an ongoing financial assistant, not a one-shot analysis engine

## Near-Term Priorities

The next priorities should remain:

1. stabilize Hermes-backed intelligence
2. harden state truth and lineage
3. expand governance coverage
4. formalize execution request / receipt
5. make outcomes and lessons part of the real loop

## What To Avoid

Avoid these failure modes:

- adding more assistant-like UI before the underlying loop is truthful
- letting intelligence swallow execution
- letting capability become a generic technical middle layer
- confusing knowledge with state
- growing infra convenience scripts into hidden runtime ownership

## Success Criteria

The roadmap is succeeding when:

- users can ask the assistant for meaningful financial help
- the assistant can explain what it did
- the system can show what actually happened
- important actions are governed
- lessons begin to improve future runs
