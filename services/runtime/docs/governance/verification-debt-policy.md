# Verification Debt Policy

Status: **ACCEPTED** | Date: 2026-04-30 | Phase: DG-6B
Tags: `governance`, `verification`, `debt`, `meta-verification`, `receipt-integrity`
Authority: `current_status` | AI Read Priority: 2

## 1. Purpose

This document defines how verification debt is tracked, bounded, and prevented
from becoming hidden system risk. It is the policy layer for the verification
debt ledger and meta-verification checkers.

**Core principle**: Debt may exist, but hidden debt may not become truth.

## 2. Debt Categories

| Category | Description | Example |
|----------|-------------|---------|
| `object_defect` | The checked object genuinely has a defect | Code fails lint; doc has formatting issues |
| `tool_limitation` | Tool does not support the feature or requires preview/experimental mode | Ruff Markdown formatting requires --preview |
| `command_mismatch` | Verification command is incomplete or uses wrong flags | Missing --preview on ruff markdown check |
| `environment_mismatch` | Path, shell, cache, or platform causes detection drift | Passes locally, fails in CI |
| `spec_mismatch` | The checker is checking the wrong thing or rule is ambiguous | Checking "ruff stable supports Markdown" instead of "AGENTS.md is formatted" |
| `historical_noise` | Pre-existing, never introduced by current work, already triaged | 4 F401 in Phase 5/H-era test files |
| `skipped_verification` | A required verification gate was not executed | Ruff not run during seal phase |
| `pre_existing_tooling_debt` | Legacy category — superseded by more specific categories above | Legacy debt entries VD-001 through VD-004 |
| `untracked_residue` | Files present in working tree but never staged | .coveragerc, .pre-commit-config.yaml |
| `baseline_gate_gap` | A gate exists in baseline but not in receipt | Receipt says 7/7 but baseline is now 8/8 |
| `receipt_integrity_gap` | Receipt claims sealed/clean but evidence shows gaps | "Skipped: None" but text mentions "not run" |
| `checker_degradation` | A checker was weakened, removed, or downgraded | Hard gate changed to soft without approval |
| `stale_baseline_count` | Baseline count in docs/receipts does not match current | AGENTS.md says 7/7 when baseline is 8/8 |
| `semantic_overclaim` | Dangerous word used without safe context | "validated" applied to CandidateRule |

## 3. Debt Severity

| Severity | Meaning | Action Required |
|----------|---------|-----------------|
| `low` | Cosmetic or tooling-only; no systemic risk | Tracked, can be deferred |
| `medium` | Potential for confusion or drift | Must have follow-up phase |
| `high` | Actively misleads or suppresses verification | Blocks stage seal until addressed |
| `blocking` | Would cause system to act on false information | Blocks current phase |

## 4. Required Debt Fields

| Field | Type | Description |
|-------|------|-------------|
| `debt_id` | string | Unique ID (e.g., `VD-2026-04-30-001`) |
| `opened_phase` | string | Phase when debt was first opened |
| `category` | string | From §2 debt categories |
| `scope` | string | What files/checks are affected |
| `description` | string | Human-readable explanation |
| `risk` | string | What could go wrong if unaddressed |
| `severity` | string | From §3 debt severity |
| `introduced_by_current_phase` | boolean | True if this phase caused the debt |
| `owner` | string | Who is responsible for resolution |
| `follow_up` | string | Planned resolution approach |
| `expires_before_phase` | string | Phase before which this debt must be closed |
| `status` | string | open, closed, accepted_until, superseded |
| `opened_at` | ISO8601 | When debt was first registered |
| `closed_at` | ISO8601 or null | When debt was resolved |
| `evidence` | string | Reference to receipt/checker output confirming debt |
| `notes` | string or null | Additional context |
| `failure_class` | string | From §8: object_defect, tool_limitation, command_mismatch, environment_mismatch, spec_mismatch, historical_noise, misclassification |
| `closure_reason` | string | How the debt was closed: fixed_by_code_change, fixed_by_doc_change, fixed_by_command_correction, closed_by_reclassification, closed_as_tool_limitation, closed_as_out_of_scope, superseded_by_tool_update |

## 5. Status Values

| Status | Meaning |
|--------|---------|
| `open` | Active debt, needs resolution |
| `closed` | Resolved — closure_reason field documents how |
| `accepted_until` | Acknowledged, bounded by expiry date |
| `superseded` | Replaced by a newer debt or policy change |

## 6. Rules

### 6.1 Registration
- Any skipped verification must be recorded in the debt ledger.
- Any pre-existing debt mentioned in current docs/receipts must have a ledger entry.
- Open debt must have owner, follow-up, and expiry.

### 6.2 Boundedness
- Overdue open debt fails the checker.
- High/blocking debt blocks stage seal.
- Debt must expire — indefinite open debt is not allowed.

### 6.3 Language Precision
- "clean working tree" must be written as "Tracked working tree clean" if untracked residue exists.
- Baseline gate count in receipts must match current baseline.
- "Ruff clean" requires that all scoped files pass; otherwise say "DG scope clean".
- "sealed" requires all required verification executed or explicitly recorded as debt.

### 6.4 Stage Summit
- Every Stage Summit must include an Open Verification Debt section.
- High/blocking open debt prevents full seal.

## 7. Relationship to Other Packs

| Pack | Relationship |
|------|-------------|
| Document Governance Pack | This policy is part of DG Pack |
| Agent Output Contract | Defines receipt requirements this checker validates |
| Baseline Runner | pr-fast includes verification debt + receipt integrity gates |

## 8. Before Remediation: Classify the Signal

**Core rule**: A failed verification command is an observation, not a verdict.
It must be classified before acting.

### 9.1 Failure Classes

When a checker fails, classify the failure before deciding action:

| Class | Meaning | Correct Action |
|-------|---------|----------------|
| `object_defect` | The checked object genuinely has a defect | Fix the object |
| `tool_limitation` | Tool does not support the feature or requires experimental mode | Document limitation; use correct flags; do NOT fix the object |
| `command_mismatch` | Verification command is incomplete or incorrect | Fix the command |
| `environment_mismatch` | Path, shell, cache, or platform mismatch | Fix the environment |
| `spec_mismatch` | Checker is checking the wrong thing | Fix the spec or gate definition |
| `historical_noise` | Pre-existing, never caused by current work | Explicitly classify as out-of-scope; do not hide |
| `misclassification` | Previous classification was wrong | Reclassify; close as misclassified |
| `expected_negative_control` | Checker is expected to fail (reject test) | Record as intentional; no action needed |

### 9.2 Core Rules

1. **Do not mutate authoritative documents to satisfy a misclassified checker.**
   Source-of-truth documents (AGENTS.md, Stage Summits, ontology) must not
   be modified to quiet a checker whose signal has been misread.

2. **External tool output is evidence, not authority.**
   Ruff, pytest, mypy, pnpm, and all other external tools produce evidence.
   Their exit codes are signals to be classified, not commands to be obeyed.

3. **Debt may be closed by reclassification.**
   A properly classified issue that is not an object defect may be closed
   without changing the checked object. Valid closure reasons include:
   `closed_by_reclassification`, `closed_as_tool_limitation`,
   `closed_as_out_of_scope`, `superseded_by_tool_update`.

4. **Verification commands must declare tool maturity.**
   When a tool feature is experimental, preview, or deprecated, the
   verification gate must document this. The command, its required flags,
   and the tool's maturity level are part of the governance contract.

5. **Both false positives and false negatives are forms of self-deception.**
   Calling a tool limitation a system failure is a false negative —
   just as damaging as calling an unchecked system sealed (false positive).

### 9.3 VD-001 Case Study

VD-2026-04-30-001 was initially registered as "AGENTS.md ruff markdown
preview issue" (category: `pre_existing_tooling_debt`). Investigation
showed:

- `ruff format --check AGENTS.md` → FAIL (exit 2). Reason: "Markdown
  formatting is experimental, enable preview mode."
- `ruff format --check --preview AGENTS.md` → PASS (exit 0). "Already
  formatted."
- `ruff format --diff --preview AGENTS.md` → PASS. Zero diff.

AGENTS.md had no formatting defect. The failure was a `tool_limitation`
(Ruff Markdown formatter is experimental) combined with a `command_mismatch`
(verification command lacked `--preview`). The original classification
as `pre_existing_tooling_debt` was incomplete — it captured the tool
aspect but not the command/spec aspects.

VD-001 was closed by reclassification (`closed_by_reclassification`)
in Post-DG-H2. No change was made to AGENTS.md.

## 9. Non-Activation Clause

This policy defines debt tracking rules. It does not authorize trading, activate
Policy, or modify RiskEngine behavior. Phase 7P remains CLOSED. Phase 8
remains DEFERRED.
