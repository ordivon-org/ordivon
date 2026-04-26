# Ordivon System Definition

> **Status**: Canonical identity document
> **Date**: 2026-04-26
> **Phase**: Docs-D2 — core baseline documentation
> **Supersedes**: Scattered identity fragments in aegisos-overview.md, aegisos-working-identity.md, and aegisos-design-doctrine.md (those remain valid but this is the single-entry definition)

## Purpose

This document answers the question: **What is Ordivon, and what is it not?**

It is the definitive identity anchor. Every other architecture document defers to this one for system boundaries.

---

## One-Sentence Definition

> Ordivon is a governance-first AI workflow operating system where intelligence participates in judgment but governance, execution, state, knowledge, and supervision remain separate, non-collapsible layers.

---

## What Ordivon Is

### 1. A Governance-First System

Governance is not an optional plugin. It is the system's legality layer.

Every consequential action passes through governance before execution. The system does not allow intelligence to bypass governance, even when the model is "confident."

### 2. A Truth-Layered System

State is reality. Knowledge is interpretation. Narratives are artifacts.

The system maintains:
- **State** — fact-bearing objects with formal relations (TraceLink, Outcome, ExecutionReceipt)
- **Knowledge** — structured experience (FeedbackPacket, CandidateRule, Lesson)
- **Artifacts** — generated outputs (reports, analysis text, wiki pages)

These three categories are never collapsed into one.

### 3. A Long-Running-Capable System

Work is not one-request-one-response. The system models:
- Blocked states
- Handoff artifacts
- Checkpoint state
- Wake and resume reasons
- Fallback paths

A task can pause, wait for human review, and resume with full context.

### 4. A Core/Pack/Adapter Platform

The system body is organized into three ownership categories:

| Category | Owns | Does NOT own |
|----------|------|-------------|
| **Core** | Stable system order (workflows, governance, state primitives, trace, audit) | Domain semantics, provider identity |
| **Pack** | Domain meaning (finance objects, policies, workflows, defaults) | System primitives, runtime identity |
| **Adapter** | Replaceable integration (model runtimes, storage backends, tool connectors) | System semantics, domain meaning |

### 5. A Supervisor-Facing System

The user is not only a requester. The user may also be:
- Supervisor
- Reviewer
- Approver
- Override source

The frontend is evolving into a command center, execution workspace, and review workbench — not a single report page.

---

## What Ordivon Is NOT

### 1. NOT a Chat Product

The system does not present itself as a conversational interface. Model output is structured into work objects (recommendations, reviews, receipts), not chat bubbles.

### 2. NOT a Finance-Specific Tool

Finance is the first domain pack (`packs/finance`), not the system identity. The system is designed to support multiple domain packs (research, ops, compliance, personal cognition).

### 3. NOT a Model Wrapper or Prompt Bundle

The system does not wrap a single model provider. Intelligence is a judgment layer that can use any runtime adapter (Hermes Bridge, OpenAI, Anthropic, future providers). Provider identity is adapter concern, not system concern.

### 4. NOT a Direct Agent

Agents do not own:
- Truth definition
- Action authorization
- Policy interpretation
- Execution success

Agents participate in judgment. The system owns everything else.

### 5. NOT a Production-Complete Platform (Yet)

Current stage: **load-bearing systems phase**. The system has frozen primitives, a real primary workflow, governance boundaries, execution receipts, and knowledge feedback structure. But it is not yet a multi-pack ecosystem or a finished platform.

---

## System Architecture Invariants

These are hard constraints. No feature, module, or refactor may violate them.

### Invariant 1: Intelligence is not sovereignty

Intelligence may judge, infer, classify, summarize, and propose. It may not own truth, authorization, policy, or execution success.

### Invariant 2: State is reality, knowledge is interpretation

State objects carry fact. Knowledge objects carry structured experience. Reports carry artifacts. These are never collapsed.

### Invariant 3: Governance gates every consequential action

No action with side effects may execute without a governance decision. Governance must run before execution, never after.

### Invariant 4: Execution produces receipts

Every governed action must produce an immutable receipt. Receipts are append-only. No receipt means no action occurred.

### Invariant 5: Core stays stable, packs stay domain-owned, adapters stay replaceable

- Finance nouns do not enter core
- Provider identity does not define system identity
- Adapters implement contracts, not mutate system meaning

### Invariant 6: Failure hardens into structure

Every meaningful failure must produce at least one durable system asset: deterministic code, policy, contract, fallback rule, test, monitoring signal, runbook, recurring issue, or candidate rule.

### Invariant 7: Long-running work is recoverable

Work can block, hand off, wait, wake, resume, and degrade honestly. No task is abandoned without a formal fallback or escalation path.

---

## Naming Convention

The system exists under multiple names due to historical lineage:

| Name | Usage | Scope |
|------|-------|-------|
| **AegisOS** | Working product/system identity | Current architecture and execution docs |
| **PFIOS** | Repository lineage | Code paths, env vars, historical continuity |
| **Ordivon** | Future external brand anchor | Forward-looking docs only; deferred rename |
| **CAIOS** | Internal architectural shorthand | Internal discussions |

**Current rule**: Use AegisOS for current architecture docs. Preserve PFIOS where repository continuity requires it. Ordivon is deferred.

---

## Relationship to Existing Documents

This document is the definitive identity anchor. It does not replace:

- [architecture-baseline.md](architecture-baseline.md) — canonical architecture structure
- [LANGUAGE.md](LANGUAGE.md) — shared vocabulary
- [aegisos-design-doctrine.md](aegisos-design-doctrine.md) — philosophy-to-engineering mapping
- [aegisos-overview.md](aegisos-overview.md) — layer-by-layer snapshot

It does supersede scattered identity claims in those documents. If wording conflicts, this document wins on identity questions; architecture-baseline.md wins on structure questions.

---

## Compressed Statement

> Ordivon builds AI work systems where intelligence works under governance, state, execution, knowledge, and infrastructure constraints to produce work that is runnable, recoverable, auditable, and accumulable — and where the platform body is not colonized by any single domain, provider, or runtime.
