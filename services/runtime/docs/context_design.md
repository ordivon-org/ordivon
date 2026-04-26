# Ordivon Context Design Baseline

> **Status**: Canonical — Docs-D5B
> **Owner**: Core (context discipline is cross-domain)
> **Scope**: Defines what context is, where it comes from, who owns it, and what it must not do
> **Non-goals**: Does not define prompt formats, token budgets, or model-specific injection strategies
> **Last verified**: 2026-04-26

## Purpose

This document defines context as a **data engineering object**, not as text that gets stuffed into a prompt.

Context is the structured evidence delivered to the intelligence layer before reasoning begins. Every context fragment must carry source, scope, freshness, owner, and evidence references. The system does not allow context to be assembled by guesswork.

---

## Core Judgment

```
Context is a data engineering object, not prompt stuffing.

Context must have source, scope, freshness, owner, and evidence references.

Context must not override State Truth.

Context must not silently promote Knowledge into Policy.

Context must not allow Adapter output to bypass Governance.
```

---

## Context Types

The system recognizes these context families. Each has a defined owner, freshness window, and constraint.

### 1. Intake Context
- **What**: The work definition — task type, explicit parameters, supervisor instructions
- **Owner**: Orchestrator
- **Freshness**: Per-run
- **Constraint**: Must be parseable into a structured task contract before context assembly

### 2. State Truth Context
- **What**: Authoritative fact from the SQLAlchemy ORM — entity state, lifecycle position, linked outcomes
- **Owner**: State layer
- **Freshness**: Query-at-read
- **Constraint**: This is the only context that carries fact status. No other context category may contradict it.

### 3. Governance Context
- **What**: Active policies, decision rules, risk flags, approval requirements
- **Owner**: Governance
- **Freshness**: Policy snapshot at context assembly time
- **Constraint**: Governance context applies constraints; it does not suggest actions.

### 4. Audit Context
- **What**: Relevant audit events, prior decisions, escalation history
- **Owner**: Governance / Audit
- **Freshness**: Query-at-read from AuditEvent table
- **Constraint**: Must not be filtered by the intelligence layer. The system delivers what exists.

### 5. Receipt Context
- **What**: Prior execution receipts linked to the current entity or workflow
- **Owner**: Execution
- **Freshness**: Query-at-read from ExecutionReceipt table
- **Constraint**: Receipts are evidence of past actions, not predictions of future outcomes.

### 6. Review Context
- **What**: Prior reviews, outcome assessments, supervisor annotations
- **Owner**: Journal / Review
- **Freshness**: Query-at-read from Review table
- **Constraint**: Reviews are human or automated assessments. They are not policy.

### 7. Lesson Context
- **What**: Durable insights extracted from reviews — stored facts, not executable rules
- **Owner**: Knowledge
- **Freshness**: Query-at-read from Lesson table
- **Constraint**: Lessons inform. They do not command. A lesson only becomes policy through Governance adoption.

### 8. Knowledge Feedback Context
- **What**: Feedback packets delivered from past reviews into current analysis
- **Owner**: Knowledge Feedback
- **Freshness**: Query-at-read, scoped by entity/domain relevance
- **Constraint**: Read-only in the analysis path. Feedback is a signal, not a decision.

### 9. Pack-Specific Context
- **What**: Domain objects, domain workflows, domain policies owned by a specific Pack
- **Owner**: Pack (e.g., `packs/finance/`)
- **Freshness**: Pack-defined
- **Constraint**: Pack context is domain meaning. It is not Core identity. Finance pack context (symbols, positions, market data) does not define the system.

### 10. Adapter-Provided Context
- **What**: External data delivered through adapters — market data feeds, research connectors, tool outputs
- **Owner**: Adapter
- **Freshness**: Adapter-defined, annotated with retrieval timestamp
- **Constraint**: Adapter context is external evidence. It must not bypass Governance. It carries no truth status until it passes through a governance gate.

### 11. Runtime Context
- **What**: Transient execution and session data — run state, checkpoint position, resume reason, fallback path, memory policy flags
- **Owner**: Intelligence / Runtime
- **Freshness**: Per-run, not persisted as State Truth
- **Constraint**: Runtime context is execution scaffolding. It must not become Policy. It must not persist as State. It is discarded when the run completes.

---

## Context Ownership

| Context Family | Owner | Truth Status |
|----------------|-------|-------------|
| Intake | Orchestrator | Task definition |
| State Truth | State | Authoritative fact |
| Governance | Governance | Active constraint |
| Audit | Governance / Audit | Historical record |
| Receipt | Execution | Historical record |
| Review | Journal / Review | Assessment |
| Lesson | Knowledge | Stored insight |
| Knowledge Feedback | Knowledge Feedback | Signal |
| Pack-specific | Pack | Domain meaning |
| Adapter-provided | Adapter | External evidence |
| Runtime | Intelligence / Runtime | Transient execution data |

---

## Allowed Context Flow

1. State Truth may enter any context assembly.
2. Governance context gates every context assembly.
3. Audit context may be delivered alongside any governed task.
4. Receipt context may be delivered for any task with prior execution history.
5. Review context may be delivered for any entity with prior reviews.
6. Lesson context may be delivered for any analysis task.
7. Knowledge Feedback may be delivered in the analysis path (read-only).
8. Pack context may be delivered for tasks within that pack's domain.
9. Adapter context may be delivered when the adapter contract is satisfied.

---

## Prohibited Context Flow

1. Context must not override State Truth. If a context fragment contradicts the ORM, the ORM wins.
2. Context must not silently promote Knowledge into Policy. A lesson must pass through CandidateRule adoption before it constrains behavior.
3. Context must not allow Adapter output to bypass Governance. External data enters as evidence, not as decision.
4. Context must not collapse Memory (stored fact) with Knowledge (interpretation) with State (truth).
5. Context must not inject model-provider identity (Hermes, OpenAI, Anthropic) as system identity.
6. Context must not leak finance pack nouns (symbol, position, OHLCV, portfolio exposure) into Core context definitions.
7. Runtime context must not become Policy. Transient execution state must not persist as State Truth.

---

## Context Quality Requirements

Every context fragment delivered to the intelligence layer must satisfy:

1. **Source identified** — which system component or adapter produced it
2. **Scope bounded** — what this fragment covers and what it explicitly does not
3. **Freshness annotated** — when it was retrieved or assembled
4. **Owner declared** — which Core/Pack/Adapter component is responsible for it
5. **Evidence references present** — links to State, Audit, Receipt, or Review records that support it

A context fragment missing any of these fields must not enter the reasoning input.

---

## Context and State Truth

State Truth (SQLAlchemy ORM) is the only context source that carries fact status.

- If context disagrees with State, the context is stale.
- If context adds interpretation on top of State, the interpretation must be marked as Knowledge, not State.
- If context is derived from State (e.g., computed aggregates), the derivation method must be traceable.

---

## Context and Packs

Packs own domain-specific context. The system enforces:

- Finance pack context (symbols, market data, portfolio state) is valid for finance-domain tasks only.
- Pack context must not leak into Core context definitions.
- When the system adds a second pack, that pack's context must not contaminate finance pack context or Core context.

---

## Context and Adapters

Adapters deliver external context. The system enforces:

- Adapter context is always annotated with retrieval source and timestamp.
- Adapter context is evidence, never truth.
- Adapter context must pass through governance before it can influence a decision.
- Harness / Model context (provider capability, token limits, model version) is adapter context, not Core truth.

---

## Engineering Requirements

1. Context assembly must be a traceable step in every governed workflow.
2. Context fragments must carry a `ContextSource` enum: `STATE_TRUTH | GOVERNANCE | AUDIT | RECEIPT | REVIEW | LESSON | KNOWLEDGE_FEEDBACK | PACK | ADAPTER`.
3. Context delivery to the intelligence layer must be logged as part of the IntelligenceRun.
4. The context assembly step must not be skippable by the intelligence layer.
5. Adapter-provided context must carry a retrieval timestamp and a source adapter identifier.

---

## Conclusion

Context is not a pile of text you hand to a model. It is a structured, owned, freshness-annotated, evidence-backed data object assembled by the system before intelligence work begins.

The system owns context. The model consumes it.
