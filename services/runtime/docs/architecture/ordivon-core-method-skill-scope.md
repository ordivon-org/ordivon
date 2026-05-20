# Ordivon Core Method Skill — Scope Freeze

> **Status:** `current`
> **Type:** `source_of_truth`
> **Canonical:** Canonical document #6. Extends the AI-Native Project Object Model.
> **Prerequisite:** `docs/architecture/ai-native-project-object-model.md` (canonical #5)
> **Last verified:** 2026-05-20
> **Stale after:** 90 days

---

## 1. Purpose

Freeze the boundary of the `ordivon-core-method` Skill V0 before writing a single line of `SKILL.md`.

This document answers:

```text
What does this skill do?
What does it explicitly NOT do?
What constraints bind it from D1-D5 debt processing?
What inputs does it accept?
What outputs does it produce?
What hard prohibitions does it carry?
How does it prevent self-authorization?
```

If the scope is not frozen first, the skill will bloat into a system.

---

## 2. Skill Identity

| Field | Value |
|-------|-------|
| **Skill name** | `ordivon-core-method` |
| **Trust level** | S1 — Project-Owned Skill |
| **Owner** | ordivon-core-maintainer |
| **Version** | 0.1.0 |
| **Source** | local_project |
| **Activation** | Triggered when agent must audit claims, frame execution, govern AI output, classify debt, or draft receipts |

---

## 3. Five Capabilities — In / Out / Prohibit

### 3.1 Claim Audit

**What it does:**
- Extracts explicit and implicit claims from text
- Separates claim from narrative
- Identifies missing evidence for each claim
- Flags overclaim (claim exceeds evidence)
- Assigns confidence annotation per claim

**What it does NOT do:**
- Adjudicate whether a claim is "true" or "false"
- Replace human judgment on ambiguous cases
- Close a claim as resolved

**Hard prohibitions:**
- May not declare a claim "verified"
- May not suppress counter-evidence
- May not fabricate evidence to fill gaps
- May not upgrade claim status without external verification

**Input:** Any text containing claims (report, article, AI output, receipt, PR description, meeting notes)

**Output:** Structured claim audit:
```
claim_id, claim_text, evidence_present, evidence_missing,
overclaim_flag, confidence, boundary_note
```

**Constraint from D5 (External Validation):** Must pass E1 (Overclaim Detection Case) and E4 (Generated View Confusion Case).

---

### 3.2 Execution Frame

**What it does:**
- Given a task, produce a bounded execution plan
- Declare intent, scope, non-goals, verification method, seal condition
- Identify required tools and their risk levels (T0-T3)
- Identify authority boundaries (what requires approval)

**What it does NOT do:**
- Execute the plan
- Authorize any action
- Decide tool permissions
- Replace the agent's execution loop

**Hard prohibitions:**
- May not mark a task as "ready to execute" without authority check
- May not skip non-goals declaration
- May not omit seal condition
- May not claim a frame is "approved" — it is always a proposal

**Input:** Task description (engineering task, analysis task, governance task)

**Output:** Execution frame:
```
intent, scope, non_goals, tools_required (with T-level),
authority_required, verification_method, seal_condition
```

**Constraint from D2 (MCP Permission):** Tools listed must carry risk level annotation. T3 tools must be flagged as requiring human approval.

**Constraint from D5:** Must pass E5 (Engineering Prompt Compiler Case).

---

### 3.3 AI Output Governance

**What it does:**
- Audit AI-generated output for governance violations
- Detect generated-view-masquerading-as-source
- Detect receipt-masquerading-as-resolution
- Detect overclaim in agent output
- Detect missing boundary declaration

**What it does NOT do:**
- Grade output quality holistically
- Rewrite the output
- Decide whether output should be published

**Hard prohibitions:**
- May not suppress findings to make output look clean
- May not mark "no issues" if boundary is missing
- May not treat "well-written" as "well-governed"

**Input:** Any AI-generated text (agent response, PR description, receipt draft, summary, analysis)

**Output:** Governance audit:
```
finding_id, violation_type, location, severity, recommendation
```

**Constraint from D1 (Skill Trust):** This capability must audit its own output when used recursively.

**Constraint from D5:** Must pass E3 (Tool Authority Case) and E8 (Memory Conflict Case).

---

### 3.4 Debt Classification

**What it does:**
- Classify unresolved items into A1/A2/A3/A4
- Assign severity (high/medium/low)
- Propose close criteria for each debt
- Flag debts that appear stale (reference files/systems that no longer exist)

**What it does NOT do:**
- Close any debt
- Decide debt priority (that's owner decision)
- Convert A4 into A1 by hand-waving

**Hard prohibitions:**
- May not mark a debt CLOSED
- May not reclassify A4 (system redesign) as A1 (quick fix)
- May not omit close criteria
- May not suppress debt to make a phase look clean

**Input:** Task artifacts (test failures, missing files, design gaps, operational issues)

**Output:** Debt classification:
```
debt_id, description, classification (A1-A4), severity,
close_criteria, due_stage, staleness_check
```

**Constraint from D2:** If debt references tool/MCP risks, classification must note required permission level.

**Constraint from D5:** Must pass E6 (Debt Classification Case).

---

### 3.5 Receipt Draft

**What it does:**
- Generate a structured receipt draft from execution evidence
- Classify receipt type (R1-R5)
- Include all required fields for the receipt type
- Declare remaining debt explicitly
- Assign status (PASS / DEGRADED / BLOCKED)

**What it does NOT do:**
- Seal the receipt (draft only)
- Upgrade status without evidence
- Close debt
- Replace human receipt review

**Hard prohibitions:**
- May not generate a PASS receipt if verification is missing
- May not omit debt declaration
- May not fabricate evidence
- May not self-seal — all receipts are drafts until reviewed

**Input:** Execution evidence (traces, test results, commands run, diffs, approval events)

**Output:** Receipt draft:
```
receipt_type (R1-R5), scope, actions, evidence, verification,
remaining_debt, status (PASS/DEGRADED/BLOCKED), draft_flag: true
```

**Constraint from D3 (Trace-to-Receipt):** Must cite specific traces. Must not treat trace as receipt. Must distinguish draft from sealed.

**Constraint from D5:** Must pass E2 (Fake Receipt Case) — skill must detect a structurally complete but evidence-free receipt as DEGRADED or BLOCKED.

---

## 4. Cross-Cutting Constraints

These apply to ALL five capabilities. They are non-negotiable.

### From D1: Skill Trust Model
```
1. This skill is S1 (Project-Owned). It must be versioned and reviewed.
2. Skill output = proposal, draft, classification. Never authority.
3. This skill must not self-authorize. Any status upgrade requires external gate.
4. When this skill is used recursively, it must audit its own output.
```

### From D2: MCP Permission Model
```
1. Any tool recommendation carries risk level (T0-T3) annotation.
2. T3 tool usage must be flagged as requiring explicit human authorization.
3. MCP tool discovery is not trust — external tools must be noted as such.
4. Tool access capability does not imply execution permission.
```

### From D3: Trace-to-Receipt Model
```
1. Receipts are drafts until reviewed. Self-sealing is forbidden.
2. Every receipt must cite specific trace evidence.
3. Trace completeness does not imply task completeness.
4. Status upgrades require evidence, not narrative.
```

### From D4: AI Memory Governance
```
1. Memory (MEM0-MEM6) may inform context, never replace source.
2. If memory conflicts with repo source, source wins (unless source is under active review).
3. Generated summaries in memory must be treated as lossy.
4. This skill must not write conclusions to memory that bypass the receipt system.
```

### From D5: External Validation
```
1. All five capabilities must be evaluable against the 8 eval cases (E1-E8).
2. Baseline agent (no skill) vs skill-equipped agent comparison is required.
3. Average score < 1.6 or any critical failure means skill revision, not expansion.
4. Validation failures become debt, not suppressed.
```

---

## 5. What This Skill Is NOT

This table prevents scope creep. Each row is a boundary that must survive the SKILL.md draft.

| This Skill Is... | This Skill Is NOT... |
|-----------------|---------------------|
| A method capsule | A system |
| A proposal generator | An authorizer |
| A draft generator | A sealer |
| A classifier | A decider |
| A boundary enforcer | A policy maker |
| A debt categorizer | A debt closer |
| A receipt drafter | A receipt approver |
| A risk annotator | A risk suppressor |

---

## 6. Activation Triggers

The skill activates when the agent encounters:

1. **Ambiguous claims** — text making assertions without clear evidence
2. **Unframed tasks** — task description missing scope, non-goals, verification, seal condition
3. **Ungoverned AI output** — agent-generated text that may contain overclaim, false completion, or boundary violation
4. **Unclassified failures** — bugs, gaps, or issues that need A1-A4 classification
5. **Incomplete closure** — task ending without structured receipt

**Deactivation:** The skill does NOT activate for:
- Routine code edits with clear scope
- Simple factual queries
- Tasks with pre-existing structured receipts
- System orchestration or deployment

---

## 7. Output Contract

Every capability output is a **draft**, not a final artifact:

| Capability | Output type | Draft flag | Seal requires |
|-----------|-------------|------------|---------------|
| Claim Audit | claim audit record | true | External verification |
| Execution Frame | execution frame | true | Authority check |
| AI Output Governance | governance audit | true | Human review |
| Debt Classification | debt record | true | Owner acknowledgment |
| Receipt Draft | receipt (R1-R5) | true | Evidence verification + review |

**No output from this skill is ever final on generation.** Every output carries `draft: true`.

---

## 8. Relationship to Other Skills

This skill is the **method kernel**. Other skills may extend it, but must not override its boundaries.

Future extension skills:
- `ordivon-engineering-reentry` — specializes Execution Frame for engineering tasks
- `ordivon-receipt-seal` — specializes Receipt Draft for formal closure
- `ordivon-red-team` — inverts Claim Audit to test for boundary violations

Each extension skill inherits all cross-cutting constraints and must declare its own trust level.

---

## 9. Open Debts After Scope Freeze

| ID | Description | Severity |
|----|-------------|----------|
| SCOPE-SKILLMD | `SKILL.md` not yet written — scope is frozen, implementation pending | medium |
| SCOPE-EVAL | 8 eval cases designed but not yet instantiated as runnable tests | high |
| SCOPE-BASELINE | Baseline agent behavior (without skill) not yet measured | high |
| SCOPE-RECURSIVE | Skill's self-audit behavior not yet tested (auditing its own output) | medium |
| SCOPE-EXTENSION | Extension skills (engineering-reentry, receipt-seal) not yet scoped | low |

---

## 10. Next Gate

Before writing `SKILL.md`, confirm:

```
1. All 5 capabilities have clear IN / OUT / PROHIBIT boundaries ✅
2. Cross-cutting constraints from D1-D5 are integrated ✅
3. "Is NOT" table is complete and non-negotiable ✅
4. Output contract is explicit (all outputs are drafts) ✅
5. Activation triggers are defined ✅
6. Skill trust level is S1 (Project-Owned) ✅
```

Gate is open for:

```
Phase 3: SKILL.md Draft
```

But the next document the user may want before SKILL.md is the **eval case instantiation** — turning the 8 eval cases into concrete test fixtures, because without them we cannot validate the skill after writing it.

---

## References

- `docs/architecture/ai-native-project-object-model.md` — the 15-object, 4-layer taxonomy this skill operates within
- `docs/ai/ordivon-core-thesis.md` — the Trust Compiler thesis
- `docs/architecture/semantic-firebreak.md` — the invariant boundary system
