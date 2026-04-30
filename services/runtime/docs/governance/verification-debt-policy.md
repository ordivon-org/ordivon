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
| `skipped_verification` | A required verification gate was not executed | Ruff not run during seal phase |
| `pre_existing_tooling_debt` | Tool-level debt present before current work | Ruff issues in scripts/ not introduced by DG-5 |
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

## 5. Status Values

| Status | Meaning |
|--------|---------|
| `open` | Active debt, needs resolution |
| `closed` | Resolved with evidence |
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

## 8. Non-Activation Clause

This policy defines debt tracking rules. It does not authorize trading, activate
Policy, or modify RiskEngine behavior. Phase 7P remains CLOSED. Phase 8
remains DEFERRED.
