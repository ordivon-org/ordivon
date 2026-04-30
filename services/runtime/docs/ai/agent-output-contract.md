# Agent Output Contract

Status: **ACCEPTED** | Date: 2026-04-30 | Phase: DG-1A
Tags: `ai`, `output`, `contract`, `receipt`, `verification`, `governance`
Authority: `current_status` | AI Read Priority: 1

## Purpose

This document defines the required output shape for every AI agent working on
Ordivon. It is a **middleware layer** between root context and task-specific
prompts:

| Document | Role |
|----------|------|
| `AGENTS.md` | Tells the agent **where it is**. |
| `current-phase-boundaries.md` | Tells the agent **what is allowed**. |
| `agent-output-contract.md` | Tells the agent **how to report and seal work**. |
| Task prompt | Tells the agent **what to do**. |

Without this contract, agents may complete work but fail to produce auditable
evidence that the work respected governance boundaries. This contract
eliminates that gap.

---

## 1. Universal Output Rule

**Every task output must include all 11 items. No exceptions.**

| # | Item | Description |
|---|------|-------------|
| 1 | **Phase / task identity** | Which phase, sub-phase, or task this work belongs to |
| 2 | **Scope classification** | docs-only, code implementation, test/eval, ledger/checker, frontend/UI, cleanup, closure |
| 3 | **Risk level** | R0 (docs/preview) through R5 (automated live) — see §2 |
| 4 | **Boundary confirmation** | Explicit confirmation of relevant NO-GO boundaries — see §3 |
| 5 | **Files changed** | Every file added, modified, or deleted, with purpose |
| 6 | **Work summary** | What was done, why, and what state was left |
| 7 | **Decision / status** | GO, NO-GO, DEFERRED, COMPLETE, HOLD — unambiguous |
| 8 | **Verification results** | Every required verification command, its result, and notes — see §6 |
| 9 | **New AI Context Check** | A fresh AI reading the root docs would understand the new state — see §7 |
| 10 | **Git status** | `git diff --stat` and `git status` before and after |
| 11 | **Suggested commit / tag** | If changes were committed, the message and tag |

---

## 2. Required Opening Analysis

Before doing work, every agent must classify the task:

### 2.1 Task Type

| Type | Description |
|------|-------------|
| `docs-only` | Writing or updating documentation, no code changes |
| `code-implementation` | Writing production or infrastructure code |
| `test-eval` | Writing or running tests, eval corpus, checkers |
| `ledger-checker` | Working with JSONL ledgers or invariant checkers |
| `frontend-ui` | Frontend component, page, or UI work |
| `high-risk-finance` | Paper or live finance action |
| `cleanup-residue` | Deleting, archiving, or reverting files |
| `stage-summit` | Phase closure or formal review |

### 2.2 Risk Level

| Level | Name | Has Side Effects? | Example |
|-------|------|-------------------|---------|
| R0 | docs / preview | None | Writing markdown |
| R1 | read-only | Reads external state | Health check, observation |
| R2 | paper write | Paper-only external writes | PaperExecutionAdapter |
| R3 | manual live | Real external writes, human GO required | Manual live micro-capital |
| R4 | live API write | Real external writes, programmatic | Not yet authorized |
| R5 | automated live | Automated real external writes | Permanently NO-GO |

### 2.3 Authority Impact

What type of authority does this task's output carry?

| Authority | Meaning |
|-----------|---------|
| `current_truth` | Changes what current guidance says (root context, boundaries) |
| `supporting_evidence` | Adds evidence (receipts, ledgers, test results) |
| `proposal` | Proposes new rules or designs (not yet accepted) |
| `historical_record` | Creates immutable record of what happened |
| `archive` | Moves documents to archive only |
| `none` | No authority change (read-only, verification) |

### 2.4 Capability Impact Matrix

The agent must state whether the task can affect:

| Capability | Could this task affect it? | If yes, how? |
|------------|---------------------------|--------------|
| Live trading | YES / NO | |
| Broker write | YES / NO | |
| Auto trading | YES / NO | |
| Policy activation | YES / NO | |
| RiskEngine active enforcement | YES / NO | |
| AI onboarding | YES / NO | |
| Document authority | YES / NO | |
| JSONL ledger | YES / NO | |
| Phase boundaries | YES / NO | |

All "YES" answers require explicit explanation and boundary confirmation.

---

## 3. Boundary Confirmation

Every receipt must explicitly confirm that the task did not violate any
applicable NO-GO boundary. Use the default confirmations list and add
task-type-specific confirmations as needed.

### 3.1 Default Confirmations (Every Task)

```
- No live trading:           [confirm]
- No broker live write:      [confirm]
- No auto trading:           [confirm]
- No Policy activation:      [confirm]
- No RiskEngine active:      [confirm]
- CandidateRules advisory:   [confirm — CR-7P-001/002/003 NOT Policy]
- Ledger = evidence:         [confirm — JSONL is evidence, not execution authority]
- Archive ≠ current truth:   [confirm — archived docs are historical only]
```

### 3.2 Finance / Paper Confirmations (Additional)

Only required for tasks touching paper or finance:

```
- environment = paper:           [confirm]
- live_order = false:            [confirm]
- no live base URL:              [confirm]
- no live API key:               [confirm]
- no replace/chase:              [confirm — unless explicitly governed]
- no PT-next without review:     [confirm — prior lifecycle reviewed, protocol allows]
```

### 3.3 Docs / Governance Confirmations (Additional)

Only required for documentation tasks:

```
- Design-only, no code changes:        [confirm]
- Phase 7P CLOSED:                     [confirm]
- Phase 8 DEFERRED:                    [confirm]
- No paper/live/order action:          [confirm]
```

---

## 4. Output Formats by Task Type

Each task type has a minimum required output shape.

### 4.1 Docs-Only / Governance Design

```
Phase:
Status:
Task type: docs-only
Risk level: R0
Authority impact: [proposal | current_truth | none]

Files Changed:
| File | Change | Purpose |
|------|--------|---------|

Work Summary: [...]

Boundary Confirmation: [see §3.1 + §3.3]

Verification Results: [table — see §5]

New AI Context Check: [...]

Git: [diff --stat, status]
Commit: [message]
Tag: [suggestion]
```

### 4.2 Code Implementation

```
Phase:
Status:
Task type: code-implementation
Risk level: [R0-R2]
Authority impact: [current_truth | none]

Files Changed:
| File | Change | Purpose |

Source changes: [...]
Tests added/modified: [...]
Invariant changes: [none | list]
API/schema behavior: [...]
Compatibility notes: [...]
Rollback/safety notes: [...]

Boundary Confirmation: [see §3.1]

Verification Results: [table]

New AI Context Check: [...]

Git: [...]
```

### 4.3 Test / Checker

```
Phase:
Status:
Task type: test-eval | ledger-checker
Risk level: R0
Authority impact: [supporting_evidence | none]

What invariant is now protected: [...]
Positive cases: [...]
Negative cases: [...]
Checker summary: [...]
Failure behavior: [...]
Does checker authorize actions? [NO — validates evidence only]

Verification Results: [table]

New AI Context Check: [...]
```

### 4.4 Finance / Paper Dogfood

```
Phase:
Status:
Task type: high-risk-finance
Risk level: R2 (paper write)
Authority impact: [supporting_evidence]

Readiness gate: [...]
Decision: ALLOW | HOLD | REJECT | NO-GO | PENDING | CANCELED | CLOSED
Order/action summary: [if any]
No-live/no-auto confirmation: [explicit]

Ledger update: [events added]
CandidateRule status: [advisory only]
Phase 8 readiness impact: [none | change]

Boundary Confirmation: [see §3.1 + §3.2]

Verification Results: [table]

New AI Context Check: [...]
```

### 4.5 Stage Summit / Closure

```
Phase:
Status:
Task type: stage-summit
Risk level: R0
Authority impact: [current_truth — phase boundaries change]

What was proved: [...]
What was not proved: [...]
Evidence matrix: [...]
Open risks: [...]
Decision: GO | NO-GO | DEFERRED
Next recommended phase: [...]

Boundary Confirmation: [see §3.1]

Verification Results: [table]

New AI Context Check: [...]

Git: [...]
```

### 4.6 Cleanup / Residue Triage

```
Phase:
Status:
Task type: cleanup-residue
Risk level: R0
Authority impact: [none]

Before git status: [...]
Residue classification:
| File | Status | Action | Reason |
|------|--------|--------|--------|

After git status: [...]

Boundary Confirmation: [see §3.1]

Verification Results: [table]

New AI Context Check: [...]
```

---

## 5. Required Receipt Template

Every task receipt must use this shape as its minimum skeleton:

```
Phase:
Status:
Task type:
Risk level:
Authority impact:

Files Changed:
| File | Change | Purpose |
|------|--------|---------|

Work Summary:
- ...

Boundary Confirmation:
- No live trading:           [✓]
- No broker live write:      [✓]
- No auto trading:           [✓]
- No Policy activation:      [✓]
- No RiskEngine active:      [✓]
- CandidateRules advisory:   [✓]
- Ledger evidence, not authority: [✓]
- Archive not current truth: [✓]

Verification Results:
| Gate | Result | Notes |
|------|--------|-------|
| Phase-specific tests | PASS / N runs | |
| Ledger checker | PASS / 16 invariants | |
| Finance regression | PASS / N passed | |
| Frontend tests | PASS / N passed | |
| Frontend build | PASS / FAIL | |
| pr-fast baseline | N/7 PASS | |
| Architecture checker | PASS / FAIL | |
| Runtime evidence checker | PASS / N checks | |
| Eval corpus | PASS / N cases | |
| Ruff format/check | list scope | |

Skipped Verification:
| Command | Reason | Risk | Follow-up |
|---------|--------|------|-----------|

New AI Context Check:
A fresh AI reading the required root docs would understand:
- Current phase:
- Current truth:
- What is allowed:
- What is forbidden:
- Whether docs/AI read path changed:
- Whether next phase is clear:

Git:
- git diff --stat:
- git status:
- commit:
- tag:
```

---

## 6. Verification Discipline

### 6.1 Required Principle

**A task is not sealed unless all required verification results are accounted for.**
Every verification command in the task prompt must appear in the receipt with
its result.

### 6.2 Pre-Existing Failures

If a command fails due to **pre-existing** debt (not introduced by this phase),
the receipt must state:

```
- Label: PRE-EXISTING
- Not introduced by this phase
- Exact scope affected: [e.g., scripts/ directory only]
- Follow-up needed: [yes/no, and if yes, when]
```

Never write "clean" or "PASS" if global checks failed. Prefer:

```
"DG-1A scope clean; global pre-existing debt remains"
```

over:

```
"ruff clean"
```

### 6.3 Skipped Verification

If a verification is skipped, state the reason, risk, and follow-up.
Skipping a verification without recording it is an anti-pattern (§8).

### 6.4 Verification Signal Classification

**A failed verification command is an observation, not a verdict.**
Every verification failure must be classified before remediation.

When a command fails, the receipt must report:

| Field | Description |
|-------|-------------|
| Command | The exact command that failed |
| Exit code | The raw exit code |
| Failure class | One of: `object_defect`, `tool_limitation`, `command_mismatch`, `environment_mismatch`, `spec_mismatch`, `historical_noise`, `expected_negative_signal` |
| Affected object | The actual file/check that the signal is about |
| Remediation target | Object, command, environment, or policy — what actually needs to change |
| Debt action | Opened, closed, reclassified, or none |

Do NOT assume the checked object is broken. A checker failure may indicate:

- A real defect in the object (`object_defect`) → fix the object
- A tool feature that requires experimental/preview mode (`tool_limitation`) → fix the command; do NOT fix the object
- A wrong or incomplete verification command (`command_mismatch`) → fix the command
- An environment mismatch (`environment_mismatch`) → fix the environment
- A specification that checks the wrong thing (`spec_mismatch`) → fix the spec

**Core rule**: Do not mutate source-of-truth documents to satisfy a
misclassified checker. External tool output is evidence, not authority.

Reference: `docs/governance/verification-signal-classification.md`

---

## 7. New AI Context Update Rule

### 7.1 Required Question

After every task, the agent must ask:

> Would a new AI reading AGENTS.md → docs/ai/README.md →
> current-phase-boundaries.md understand the new state?

If the answer is **no**, update the root context docs in the same phase
or explicitly record why no update is needed.

### 7.2 Triggers Requiring Context Update

| Trigger | What to Update |
|---------|---------------|
| Phase starts | `AGENTS.md`, `current-phase-boundaries.md`, `docs/ai/README.md` |
| Phase closes | `AGENTS.md`, `current-phase-boundaries.md`, `docs/ai/README.md` |
| NO-GO boundary changes | `AGENTS.md`, `current-phase-boundaries.md` |
| New Pack starts | `AGENTS.md`, `docs/ai/README.md` |
| Phase 8 status changes | `AGENTS.md`, `current-phase-boundaries.md` |
| New ledger/checker becomes evidence source | `docs/ai/README.md` |
| Doc authority / archive / read path changes | `docs/ai/README.md`, `ai-onboarding-doc-policy.md` |
| High-risk capability changes | `current-phase-boundaries.md` |

### 7.3 New Read Path File Added

When a new AI onboarding document is added (like this one), update:

| File | Action |
|------|--------|
| `AGENTS.md` | Add to Quick Navigation |
| `docs/ai/README.md` | Add to Reference Hierarchy and When to Read What |
| `docs/governance/ai-onboarding-doc-policy.md` | Add to Level 1 read list if applicable |

---

## 8. Anti-Patterns

These are **forbidden** patterns. Any receipt exhibiting them is incomplete.

| Anti-Pattern | Why Forbidden | Correct Alternative |
|-------------|---------------|---------------------|
| "Done" without receipt | No evidence work respected boundaries | Full receipt per §5 template |
| "Tests pass" without command list | Cannot verify which tests passed | List every command and its result |
| "Validated" on limited evidence | Overstates confidence | State exactly what was checked |
| "Live" used to mean "confirmed" | Confuses live trading with affirmation | Use "confirmed" or "verified" |
| CandidateRule described as Policy | Blurs advisory/enforcement boundary | Always label "advisory only — NOT Policy" |
| JSONL ledger described as authorization | Ledger is evidence, not permission | Always label "evidence, not execution authority" |
| Archived receipt treated as current guidance | Archive is historical only | Reference `current-phase-boundaries.md` for authority |
| Empty seal phase | Wastes context, creates false confidence | Seal only when work was actually done |
| `git add .` (blind) | Commits untracked residue | Stage only intended files |
| Committing unrelated residue | Contaminates phase evidence | Separate cleanup tasks if needed |
| Treating all checker failures as object defects | May mutate source-of-truth for tool limitation | Classify failure first (§6.4); do not fix the wrong thing |
| Fixing an authoritative doc to quiet a misclassified checker | Violates source-of-truth integrity | Reclassify the debt; fix the command or spec instead |

---

## 9. Commit / Tag Rule

### 9.1 Commit Message Convention

| Prefix | When to Use |
|--------|-------------|
| `docs:` | Documentation changes only |
| `feat:` | New feature or capability |
| `fix:` | Bug fix |
| `test:` | Test additions or modifications |
| `chore:` | Cleanup, tooling, config, residue removal |

### 9.2 Tag Convention

Tags must follow:

```
phase-<phase-id>-<short-description>
```

Examples:
```
phase-dg-1a-agent-output-contract
phase-7p-d1c-ledger-checker-schema-seal
phase-dg-1-document-governance-pack-proposed
```

### 9.3 Commit Must Match Task Scope

A commit message claiming `docs:` must not include code changes.
A commit message claiming `chore:` must not include feature changes.
If a phase spans multiple scopes, split into multiple commits.

---

## 10. Relationship to Document Governance Pack

This file is part of the Document Governance Pack as an `ai_onboarding`-type
document carrying `current_status` authority (once accepted).

| Pack Document | Relationship |
|---------------|-------------|
| `document-governance-pack-contract.md` | This contract is a governed object under the Document Governance Pack |
| `document-taxonomy.md` | Type = `ai_onboarding` |
| `document-lifecycle.md` | Status = `proposed` → `current` upon acceptance |
| `ai-onboarding-doc-policy.md` | This file extends the read path defined there; add to Level 1 |
| `document-registry-schema.md` | This file will have a registry entry |

### Required Cross-References

This file must be referenced from:
- `AGENTS.md` — Quick Navigation section
- `docs/ai/README.md` — Reference Hierarchy and When to Read What tables
- `docs/governance/ai-onboarding-doc-policy.md` — Level 1 read list (optional but recommended)

### Non-Activation Clause

This contract is a **proposal**. It does not activate any Policy, RiskEngine
rule, or enforcement mechanism. It defines the required output shape for AI
agents — it does not block or reject work.

Phase 7P remains CLOSED. Phase 8 remains DEFERRED. No live, paper, or order
action is authorized by this document.
