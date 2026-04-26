# Ordivon Reasoning Contract

> **Status**: Canonical — Docs-D5B
> **Owner**: Core (reasoning discipline is cross-domain)
> **Scope**: Defines what reasoning is, what it produces, what it must never do, and how it interacts with governance, receipt, and review
> **Non-goals**: Does not define provider-specific protocols, model selection, or token economics
> **Last verified**: 2026-04-26

## Purpose

This document defines reasoning as an **intelligence capability** operating inside a governed system. Reasoning is not truth. Reasoning is not sovereignty. Reasoning is one input to the governance-and-execution loop.

The system uses reasoning. The system does not obey it.

---

## Core Judgment

```
Reasoning is not sovereignty.
Reasoning is not truth.
Reasoning providers produce analysis, thesis, risk notes, summaries, or suggested actions.
Reasoning output must be normalized before entering Ordivon workflow.
Reasoning cannot directly write State Truth, create Receipt, create AuditEvent,
  promote CandidateRule, execute tools, or bypass Governance.
```

---

## Reasoning Inputs

Reasoning receives structured context assembled by the system (see [Context Design Baseline](context_design.md)). The intelligence layer must receive:

1. **Intake**: The task contract — what is being asked and under what constraints
2. **State Truth**: Authoritative ORM facts relevant to the task
3. **Governance Context**: Active policies and decision rules
4. **Knowledge Feedback**: Relevant lessons from prior reviews (read-only)
5. **Pack Context**: Domain objects if the task is pack-scoped
6. **Adapter Context**: External data if the task requires it, annotated with source and freshness

The intelligence layer must not request additional context that bypasses the context assembly step.

---

## Reasoning Outputs

Reasoning providers produce raw output. This raw output must be normalized before it enters the system workflow.

### Raw Output (from provider)

- Analysis text, summaries, risk assessments
- Suggested actions or recommendations
- Confidence annotations
- Evidence references (provider-claimed, not system-verified)
- Tool invocation requests (from agent-capable providers)

### Normalized Output (after adapter processing)

- `IntelligenceRun` record: run_id, status (pending → running → completed/failed), timestamp, provider metadata
- `AgentAction` record: provider, model, session_id, tool_trace_json, usage_json (if the provider is agent-capable)
- Structured output conforming to the task contract (normalized by the adapter, not raw provider output)

---

## Required Output Contract

Every normalized reasoning output must carry:

| Field | Source | Requirement |
|-------|--------|-------------|
| `run_id` | IntelligenceRun | Assigned by system at run start |
| `status` | IntelligenceRun state machine | Must transition pending → running → completed or failed |
| `provider` | Adapter metadata | Identifies which adapter produced this run |
| `model` | Adapter metadata | Identifies which model served this run |
| `normalized_output` | Adapter normalization | Structured, validated against task contract |
| `tool_trace` | AgentAction (if applicable) | Record of any tools invoked by the provider |
| `usage` | AgentAction (if applicable) | Token counts, latency, cost metadata |

---

## Normalization Rules

1. Raw provider output must be parsed and validated by the adapter before entering any workflow.
2. If parsing fails, the run must be marked `failed`. Failed parsing cannot become completed reasoning.
3. Normalized output must conform to the task's structured contract. Free-text that cannot be parsed must not be treated as completed reasoning.
4. Provider-claimed evidence references are metadata, not system-verified truth. They must not be written to State.
5. Provider-claimed confidence scores are annotations, not governance inputs. They must not override policy thresholds.

---

## Prohibited Capabilities

Reasoning output must not directly:

| Action | Why | Who Owns It |
|--------|-----|------------|
| Write State Truth | State is authoritative ORM fact, not model inference | State layer |
| Create Receipt | Receipts are immutable proof of governed action, not model self-claims | Execution |
| Create AuditEvent | Audit events record system proof, not model narration | Governance / Audit |
| Promote CandidateRule | Policy adoption requires explicit governance approval | Governance |
| Execute tools | Tool execution is governed action with side effects | Execution via Governance gate |
| Bypass Governance | No reasoning output may skip the governance decision step | Governance |
| Self-certify completion | Model output cannot declare itself correct or complete | Review |

---

## Relationship to Governance

1. Every reasoning run that produces actionable output must pass through a Governance gate.
2. Governance receives the normalized output and decides: `approve | deny | escalate`.
3. Governance may reject reasoning output even if the model is "confident."
4. Governance runs before execution, never after.
5. If Governance denies, the IntelligenceRun is not discarded — it is recorded as `completed` with a governance decision of `deny`.

---

## Relationship to Receipt

1. If Governance approves and execution proceeds, an `ExecutionReceipt` is created.
2. The receipt records: what action was taken, under which governance decision, with which intelligence run as input.
3. The receipt carries execution evidence, not model self-claims.
4. If execution fails, the receipt records the failure. The IntelligenceRun is not retroactively invalidated.

---

## Relationship to Review

1. After execution, a Review may assess the outcome of the governed action.
2. The Review may reference the IntelligenceRun and AgentAction as inputs.
3. Reviews generate Lessons. Lessons may become CandidateRules.
4. The reasoning provider is not the reviewer of its own output. Review is a separate system step.

---

## Failure Semantics

| Failure Type | System Behavior | Record Produced |
|-------------|----------------|----------------|
| Adapter invocation failure (timeout, connection, auth) | Task retries or fails; no reasoning output enters workflow | IntelligenceRun: `failed` |
| Parse failure (output structurally invalid) | Normalization rejects; run marked failed | IntelligenceRun: `failed` |
| Schema violation (output valid JSON but wrong shape) | Normalization rejects; run marked failed | IntelligenceRun: `failed` |
| Missing required fields (output incomplete) | Cannot become completed reasoning; run marked failed | IntelligenceRun: `failed` |
| Governance denial | Output recorded; action blocked; no receipt for denied action | IntelligenceRun: `completed`, GovernanceDecision: `deny` |
| Execution failure after approval | Receipt records failure; run remains completed | IntelligenceRun: `completed`, ExecutionReceipt: `failed` |
| Provider hallucination or weak output | Governance or Review may flag; system does not self-correct retrospectively | IntelligenceRun: `completed`, flagged in Review |
| Model self-claim "done" | Not a receipt; system does not accept model self-certification as execution proof | Must produce ExecutionReceipt via governed path |

---

## Engineering Requirements

1. IntelligenceRun must be created at run start with status `pending`.
2. IntelligenceRun must transition `pending → running → completed` or `pending → running → failed` via a state machine.
3. AgentAction must be written when the provider is agent-capable (tools, multi-step).
4. Normalized output must be validated against the task contract before delivery to Governance.
5. Provider identity (Hermes, OpenAI, Anthropic) must remain in the adapter layer, not in Core contracts.
6. Model/provider/harness names must not appear in state, governance, or receipt definitions.

---

## Conclusion

Reasoning is a capability the system uses, not an authority the system defers to.

The system decides what reasoning output enters workflow. Governance decides what is allowed. Execution produces receipts. Review extracts knowledge. The reasoning provider participates in judgment — nothing more.
