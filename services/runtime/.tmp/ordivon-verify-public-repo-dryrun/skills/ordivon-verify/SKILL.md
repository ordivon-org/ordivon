---
name: ordivon-verify
description: Run Ordivon Verify before claiming AI-generated work is complete, sealed, or ready. Verifies receipt integrity, debt tracking, gate manifest, and document registry.
---

# Ordivon Verify — Agent Skill

## Purpose

Use Ordivon Verify before claiming AI-generated work is complete, sealed, ready to merge, or ready for handoff. Verify checks the claims AI agents make — not the code itself, but the verification claims surrounding it.

## When to Use

Run Ordivon Verify when you:

- modify code and produce a completion receipt
- modify governance docs (AGENTS.md, boundaries, stage summits)
- modify verification gate manifests or debt ledgers
- modify the document registry
- claim a phase is complete
- claim "all tests passed" in a receipt
- prepare a handoff receipt
- operate in a repo with `ordivon.verify.json`

## Commands

### Native Ordivon Repo

```
uv run python scripts/ordivon_verify.py all
uv run python scripts/ordivon_verify.py all --json
```

### External Repo with Config

```
uv run python scripts/ordivon_verify.py all --root <repo> --config <repo>/ordivon.verify.json
uv run python scripts/ordivon_verify.py all --root <repo> --config <repo>/ordivon.verify.json --json
```

### Focused Checks

```
uv run python scripts/ordivon_verify.py receipts    # receipt contradictions
uv run python scripts/ordivon_verify.py debt        # debt ledger invariants
uv run python scripts/ordivon_verify.py gates       # gate manifest integrity
uv run python scripts/ordivon_verify.py docs        # document registry + semantics
```

## Status Interpretation

| Status | Meaning | Agent Must |
|--------|---------|-----------|
| **READY** | Selected checks passed | Report status. Do NOT claim authorization for merge, execution, live trading, broker write, Policy activation, or RiskEngine enforcement. |
| **BLOCKED** | Hard failure detected | Do NOT claim completion. Do NOT write "sealed". Identify failures. Fix if in scope. Otherwise report HOLD with evidence. |
| **DEGRADED** | Warnings present, no hard failures | Explain warnings. Ask for human review or follow configured policy. |
| **NEEDS_REVIEW** | Ambiguous signals | Do not proceed silently. Request human review. |

## Required Agent Behavior

### If BLOCKED

```
Ordivon Verify returned BLOCKED.
This task is NOT complete. Hard failures:
- [file]: [reason]
- [file]: [reason]

These must be fixed before completion can be claimed.
```

### If READY

```
Ordivon Verify returned READY.
Selected checks: receipts, debt, gates, docs — all PASS.
This does NOT authorize execution, merge, deployment, trading, policy activation, or RiskEngine enforcement.
```

### In Receipts

Include this block in every completion receipt:

```
Ordivon Verify:
  Command: uv run python scripts/ordivon_verify.py all
  Status: READY | BLOCKED | DEGRADED
  Hard failures: N (or list)
  Warnings: N (or list)
  Interpretation: [what this means for trust]
  Action authorization: Not granted by Ordivon Verify
```

## Anti-Patterns — Forbidden

| Forbidden | Correct Alternative |
|-----------|-------------------|
| "Verify failed but task is complete" | "BLOCKED — task not complete until failures are fixed" |
| "Skipped Verification: None" when a command was not run | "Skipped: [list what was skipped]" |
| "READY means approved" | "READY means selected checks passed; it does not authorize execution" |
| "Checker passed, therefore action is authorized" | "Checker validates consistency; it does not authorize action" |
| "CandidateRule is Policy" | "CandidateRule is advisory only — NOT Policy" |
| "Ledger authorizes execution" | "Ledger is evidence, not execution authority" |
| "External fixture BLOCKED means tool failure" | "External fixture BLOCKED is expected when bad receipt is intentional" |

## Boundaries

Ordivon Verify is:

- **Read-only** — never writes files, never modifies state
- **Local-first** — runs on the filesystem, no network by default
- **Evidence-only** — reports trust; does not authorize action
- **No broker/API** — never calls Alpaca, financial APIs, or external services
- **No auto-fix** — never changes code, receipts, or config automatically
- **No auto-commit** — never stages or commits changes
- **No policy activation** — never activates RiskEngine rules
- **No execution authorization** — READY is a verification pass, not a permission

## Quick Reference

```
# Verify everything
uv run python scripts/ordivon_verify.py all

# Verify just receipts
uv run python scripts/ordivon_verify.py receipts

# Verify with JSON output (for CI / programmatic use)
uv run python scripts/ordivon_verify.py all --json

# Verify external repo
uv run python scripts/ordivon_verify.py all --root /path/to/repo --config /path/to/ordivon.verify.json
```
