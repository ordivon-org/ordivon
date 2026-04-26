# Ordivon Constitution

> **Status**: Canonical — Docs-D5C
> **Owner**: Core (constitution governs all layers)
> **Scope**: Highest-level invariant document. Every architecture, implementation, and operational decision must comply.
> **Non-goals**: Does not define implementation details, directory structure, provider choice, or tool configuration.
> **Last verified**: 2026-04-26

## Purpose

This document defines the **non-negotiable invariants** of the Ordivon system. It is the constitution, not a design doc. No feature, module, refactor, or runtime may violate these principles.

When any other document contradicts this one, this one wins.

---

## Constitutional Invariants

### 1. Intelligence is not sovereignty

**Principle**: Intelligence providers (models, agents, reasoning runtimes) may analyze, classify, summarize, and propose. They may not own truth, authorization, policy, or execution success.

**Rationale**: A system that defers authority to model output has no governance. The system must remain the decision-maker regardless of model confidence.

**Prohibited drift**: Any code path where model output directly alters State, creates a Receipt, writes an AuditEvent, promotes a CandidateRule, or determines its own completion status.

---

### 2. Ordivon Core owns truth, governance, receipt, review, and policy lifecycle

**Principle**: The Core layer is the single authority for: State Truth (SQLAlchemy ORM), Governance decisions (approve/deny/escalate), Execution Receipts (immutable proof of action), Reviews (outcome assessment), and Policy lifecycle (adoption, versioning, deprecation).

**Rationale**: These functions are cross-domain system laws. They must not be reimplemented per-pack or per-adapter.

**Prohibited drift**: Domain packs or adapters creating their own truth stores, governance paths, or receipt semantics outside Core.

---

### 3. State Truth is authoritative

**Principle**: The SQLAlchemy ORM is the single source of truth for all domain entities. DuckDB is a secondary analytics engine, never a truth source.

**Rationale**: A system with multiple truth sources cannot guarantee consistency. One truth source, one schema authority.

**Prohibited drift**: Writing governance-significant data to DuckDB, cache, or filesystem as a truth store. Using DuckDB as a fallback when the ORM is unavailable.

---

### 4. Context cannot override truth

**Principle**: Context is a data engineering object assembled before reasoning. If any context fragment contradicts State Truth, the context is stale and must not enter the intelligence input.

**Rationale**: Context is derived evidence. State is fact. Fact always wins.

**Prohibited drift**: Context assembly that silently overwrites ORM data with fresher-but-unverified external input. Context that promotes Knowledge to fact status without governance.

---

### 5. Reasoning cannot self-certify completion

**Principle**: No reasoning output may declare itself correct, complete, or authoritative. Completion is determined by the system (state machine transition), not by the model.

**Rationale**: Model self-certification is not evidence. The system owns run status, not the provider.

**Prohibited drift**: IntelligenceRun status being set to `completed` by the model response itself. Normalization treating model "done" signals as completion proof.

---

### 6. Governance precedes execution

**Principle**: Every action with side effects must pass through a Governance gate before execution. Governance runs before, never after.

**Rationale**: Post-hoc governance is not governance. It is audit after the fact.

**Prohibited drift**: Any code path where a tool, broker call, file write, or state mutation occurs before the Governance decision is recorded.

---

### 7. Receipt is evidence index, not summary

**Principle**: An ExecutionReceipt records what action was attempted, under which governance decision, with which intelligence run as input. It is an immutable evidence pointer, not a narrative summary of what happened.

**Rationale**: Receipts enable audit, lineage, and review. If they summarize instead of index, they become another opinion layer.

**Prohibited drift**: Receipts containing model-generated text as the primary truth record. Receipts that omit governance decision references.

---

### 8. Knowledge is advisory

**Principle**: Knowledge objects (Lessons, KnowledgeFeedback packets) inform future analysis. They do not command behavior. Knowledge becomes constraint only through Policy adoption via CandidateRule promotion.

**Rationale**: Collapsing knowledge into policy creates a self-reinforcing loop with no human review gate.

**Prohibited drift**: Feedback packets directly altering governance thresholds. Lessons treated as executable rules without CandidateRule adoption.

---

### 9. CandidateRule is not Policy

**Principle**: A CandidateRule is a proposed policy derived from Lessons. It requires explicit human adoption before becoming active Policy. Policies are versioned and immutable once published.

**Rationale**: Automated policy generation without adoption creates governance drift. The adoption gate ensures human judgment remains in the policy loop.

**Prohibited drift**: CandidateRules automatically activating without adoption. Policy thresholds changing without version increment.

---

### 10. Finance is the first Pack, not system identity

**Principle**: The Finance Pack (`packs/finance/`) is the first domain mounted on Ordivon Core. It is not the system. Ordivon is designed to support multiple packs (research, ops, compliance, personal cognition).

**Rationale**: If finance nouns colonize Core, the system cannot support a second domain without a rewrite.

**Prohibited drift**: Finance-specific concepts (symbol, position, OHLCV, portfolio exposure) entering Core definitions, State primitives, or Governance contracts.

---

### 11. Harness is capability, not identity

**Principle**: The Harness (external model runtime) and Brain Runtime (Ordivon-side adapter) are replaceable capability providers. They do not define what Ordivon is. Hermes Bridge is the current harness, not the permanent one.

**Rationale**: Provider lock-in at the identity level prevents runtime evolution. The system must survive harness replacement.

**Prohibited drift**: Provider names (Hermes, OpenAI, Anthropic) appearing in Core contracts, State definitions, or Governance rules. Harness-specific behavior treated as system invariant.

---

### 12. Adapter cannot write Core truth directly

**Principle**: Adapters translate between external systems and Ordivon interfaces. They may deliver evidence, but they must not write to State Truth, create Receipts, or emit AuditEvents directly.

**Rationale**: Adapters are replaceable integrations. Giving them truth-writing authority creates multiple ungoverned truth paths.

**Prohibited drift**: Adapter code calling ORM repositories directly. Adapter output treated as authoritative without governance normalization.

---

### 13. Tool, shell, and broker permissions default deny

**Principle**: No tool, shell access, or external broker action is permitted by default. Every capability must be explicitly granted through governance, with scope, rate limits, and side-effect classification.

**Rationale**: An open tool surface is an unbounded risk surface. Default-deny is the only safe starting position.

**Prohibited drift**: Adding tools without corresponding governance rules. Runtime flag that globally enables tools without per-action gating.

---

### 14. Human approval is required for policy promotion

**Principle**: CandidateRules may be generated automatically from Reviews and Lessons. But promotion to active Policy requires explicit human approval. No policy may become active without a recorded adoption decision.

**Rationale**: Policy is the system's legality layer. Automated policy changes without human review create unaccountable governance drift.

**Prohibited drift**: Automated CandidateRule activation. Policy changes without audit trail linking to an adoption decision.

---

## Prohibited Drift (System-Level)

The following patterns are constitutional violations regardless of which invariant they touch:

1. **Truth fork**: Any code path where two sources claim authority over the same fact.
2. **Governance bypass**: Any code path where a side-effect action skips the governance gate.
3. **Receipt skip**: Any governed action that executes without creating an immutable receipt.
4. **Self-promotion**: Any knowledge object or model output that promotes itself to policy without adoption.
5. **Identity leak**: Any Core contract that references a specific provider, model, or harness by name as a system invariant.
6. **Finance colonisation**: Any finance-domain concept that enters Core definitions as if it were universal.

---

## Relationship to Architecture Docs

This Constitution is the root document. It is above:

| Document | Relationship |
|----------|-------------|
| [Ordivon System Definition](docs/architecture/ordivon-system-definition.md) | Expands identity; must not contradict |
| [Architecture Baseline](docs/architecture/architecture-baseline.md) | Expands structure; must not contradict |
| [Core/Pack/Adapter Baseline](docs/architecture/core-pack-adapter-baseline.md) | Classification rules; must not contradict |
| [State Truth Boundary](docs/architecture/state-truth-boundary.md) | Truth source rules; must not contradict |
| [Context Design Baseline](docs/context_design.md) | Context rules; must not contradict |
| [Reasoning Contract](docs/reasoning_contract.md) | Reasoning rules; must not contradict |
| [LANGUAGE.md](docs/architecture/LANGUAGE.md) | Vocabulary; must not contradict |

---

## Change Control

1. This constitution may only be amended by explicit, recorded decision.
2. Every amendment must reference the invariant it modifies and the rationale for the change.
3. Amendments must be versioned (`v1.0 → v1.1`).
4. No amendment may remove an invariant without replacing it with an equivalent constraint.
5. Amendments that weaken governance, truth, or receipt invariants are presumed invalid.

---

## Conclusion

Ordivon is a governance-first system. The constitution exists to ensure that no feature, no model, no adapter, and no domain pack can erode the invariants that make the system governable.

**The system owns truth. Intelligence participates in judgment. Governance decides. Execution records. Knowledge informs. Policy requires adoption.**

These are not design preferences. They are non-negotiable.
