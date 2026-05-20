---
name: ordivon-core-method
description: >
  Governs how an AI agent separates claims from evidence, frames execution,
  classifies debt, and drafts honest receipts. Prevents overclaim, false
  completion, and confusion between generated content and source truth.
  Activate when the agent must audit claims, frame a task, govern AI output,
  classify failures, or seal a phase with a receipt.
trust_level: S1
version: 0.1.0
status: DRAFT_CANDIDATE
owner: ordivon-core-maintainer
---

# Ordivon Core Method

## Purpose

```
Separate before judging.
Define boundary before executing.
Gather evidence before concluding.
Obtain authority before acting.
Verify before sealing.
Classify debt before evolving.
```

This skill is a method capsule. Every output is a **draft**. Nothing it generates is final.

## Use When

- Text contains claims without clear evidence
- A task lacks scope, non-goals, verification, or seal condition
- AI-generated output may contain overclaim or boundary violations
- Failures, bugs, or gaps need A1–A4 classification
- A phase, task, or analysis is ending and needs a structured receipt

## Do Not Use When

- Routine code edit with clear scope and tests
- Simple factual query with no governance risk
- Pre-existing structured receipt already seals the work
- System orchestration, deployment, or production authorization

## Core Invariants

→ `references/invariants.md` — 10 non-negotiable cognitive firebreaks.

The agent must apply these to every claim, output, and gate decision.

## Global Workflow

```
1. FREEZE INTENT   — Goal. What is NOT being done?
2. AUDIT CLAIMS    — Extract claims. Flag missing evidence.
3. FRAME EXECUTION — Scope, non-goals, tools (M0–M5), authority.
4. CHECK AUTHORITY — AI may propose, not authorize.
5. EXECUTE         — Act within frame. Record traces.
6. CLASSIFY DEBT   — Unresolved items → A1/A2/A3/A4. → references/debt-taxonomy.md
7. DRAFT RECEIPT   — What was done, evidence, remaining debt. → references/receipt-model.md
8. DECLARE STATE   — PASS / DEGRADED / BLOCKED. Every output carries draft: true.
```

## Five Output Patterns

### P1: Claim Audit
→ template: `assets/claim-audit-template.md`

Extract claims. For each: claim_id, claim_text, evidence_present, evidence_missing, overclaim_flag, confidence, boundary_note.

**Do not:** declare a claim verified, suppress counter-evidence, fabricate evidence.

### P2: Execution Frame
→ template: `assets/execution-frame-template.md`

Produce: intent, scope, non_goals, tools_required (M0–M5), authority_required, verification_method, seal_condition.

**Do not:** mark the frame as approved, omit non-goals, skip seal condition.

### P3: AI Output Governance Audit

Audit AI-generated text for governance violations: finding_id, violation_type, location, severity, recommendation.

**Do not:** suppress findings, treat "well-written" as "well-governed".

### P4: Debt Classification
→ reference: `references/debt-taxonomy.md`

Classify into A1/A2/A3/A4 with severity, close_criteria, due_stage.

**Do not:** close debt, reclassify A4 as A1, suppress debt.

### P5: Receipt Draft
→ template: `assets/receipt-seal-template.md`
→ reference: `references/receipt-model.md`

Generate R1–R5 receipt with scope, actions, evidence, verification, remaining_debt, status, draft: true.

**Do not:** seal the receipt, fabricate evidence, omit debt, self-upgrade status.

## State Algebra

| State | Meaning | Does NOT mean |
|-------|---------|---------------|
| PASS | Within scope, verification passed | Complete, authorized, production-ready |
| DEGRADED | Can proceed with limits; known risks remain | Failure; must state what remains |
| BLOCKED | Hard failure; missing evidence or authority | Shame; it is a reality signal |

## Authority Boundary

Agent MAY: propose, classify, draft, red-team, summarize, assist execution.

Agent MUST NOT: authorize, close debt, suppress risk, resolve, declare final truth,
self-upgrade status, silently change policy.

All outputs carry `draft: true`. Status upgrades require external gate.

## Boundaries

- **Tool/MCP:** M0–M5 levels. Access ≠ authority. Discovery ≠ trust. → `references/mcp-permissions.md`
- **Memory:** MEM0–MEM6 types. Conflict with source → source wins. → `references/memory-governance.md`
- **Generated content:** AI summaries and dashboards are generated views. Must declare source. Cannot authorize state change.

## Hard Prohibitions

1. May not authorize any action.
2. May not close any debt.
3. May not suppress any risk or finding.
4. May not self-seal a receipt.
5. May not fabricate evidence.
6. May not treat generated content as source.
7. May not override project policy or AGENTS.md.
8. May not be used to authorize its own output.

## Skill Self-Boundary

**S1 — Project-Owned.** Versioned. Reviewed. A method capsule.

Not: a system, an authority, a policy engine, a deployment tool, a debt closer, a receipt approver, a replacement for real work.
Not: an authority.

---

**References:** invariants, debt-taxonomy, mcp-permissions, memory-governance, receipt-model

**Templates:** claim-audit, execution-frame, receipt-seal

**Upstream:** docs/ai/ordivon-core-refrozen.md (#1), docs/architecture/ai-native-project-object-model.md (#5), docs/architecture/ordivon-core-method-skill-scope.md (#6)
