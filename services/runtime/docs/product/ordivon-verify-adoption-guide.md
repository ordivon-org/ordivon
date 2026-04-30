# Ordivon Verify — Adoption Guide

Status: **PROPOSAL** | Date: 2026-05-01 | Phase: PV-5
Tags: `product`, `verify`, `adoption`, `ci`, `agent`
Authority: `proposal` | AI Read Priority: 3

## Who This Is For

- **Solo AI-heavy developer**: using Claude Code, Cursor, or Copilot daily; needs to verify agent claims before commit
- **Small engineering team**: AI agents and humans both open PRs; needs automated verification of agent honesty
- **Agent-heavy repo**: most commits are AI-generated with receipts; needs trust calibration
- **Governance-sensitive repo**: Phase boundaries, NO-GO rules, debt tracking are load-bearing; needs meta-verification

## Adoption Levels

### Level 0 — Manual Advisory

Run Ordivon Verify manually before trusting an AI-generated receipt:

```bash
uv run python scripts/ordivon_verify.py all
```

Read the human report. Fix BLOCKED items. Re-run. This is the minimum.

### Level 1 — Agent Skill

Add the Ordivon Verify skill to your AI coding agent's instruction set. The agent runs Verify before claiming completion. See `skills/ordivon-verify/SKILL.md`.

### Level 2 — PR Check

Run Ordivon Verify in CI and post the result. BLOCKED prevents merge. DEGRADED requires human review. READY passes but does not auto-merge.

### Level 3 — Strict Governance

Require receipt integrity, debt tracking, gate manifest, and document registry checks before merge. Missing governance files are hard failures, not warnings.

## First 10 Minutes

### 1. Get the Config

Copy this minimal `ordivon.verify.json` to your repo root:

```json
{
  "schema_version": "0.1",
  "project_name": "my-project",
  "mode": "advisory",
  "receipt_paths": ["docs/runtime", "docs/product"],
  "output": "human"
}
```

### 2. Run Advisory Mode

```bash
uv run python scripts/ordivon_verify.py all --root . --config ordivon.verify.json
```

### 3. Inspect the Report

- **READY**: Your receipts are clean so far. Consider adding debt/gate/docs governance files.
- **BLOCKED**: A receipt has contradictory claims. Fix it.
- **DEGRADED**: Missing optional governance files. Not blocking today, but address before strict mode.

### 4. Fix BLOCKED Results

BLOCKED results are concrete:
- "Status SEALED but integration tests not run" → fix the receipt or run the tests
- "Skipped: None but ruff not run" → run ruff or register the skip
- "clean working tree with untracked residue" → clean up or qualify the claim

### 5. Move Toward Standard/Strict

Once advisory mode runs clean:
- Add `verification-debt-ledger.jsonl` (can start empty)
- Add `verification-gate-manifest.json` (can mirror your CI gates)
- Switch mode to `standard` or `strict`

## External Repo Minimal Setup

Non-Ordivon repos need only one file: `ordivon.verify.json`.

```json
{
  "schema_version": "0.1",
  "project_name": "my-project",
  "mode": "advisory",
  "receipt_paths": ["docs"],
  "checks": {
    "receipts": true,
    "debt": false,
    "gates": false,
    "docs": false
  }
}
```

That's it. No dependencies. No database. No SaaS. Just a JSON file and the CLI.

## What Not to Do

| Don't | Why |
|-------|-----|
| Treat Verify as approval | READY means checks passed. It does not authorize merge, deploy, or execute. |
| Skip existing CI | Verify complements CI. It does not replace tests, lint, or build. |
| Hide warnings | Warnings today become BLOCKED tomorrow in strict mode. Address them. |
| Add strict mode before repo has governance files | Strict mode requires debt ledger + gate manifest + document registry. Add them first. |
| Let agents self-certify without verification | Agent claims must be verified. "I ran the tests" is a claim. Verify checks the claims. |

## Recommended Rollout

| Week | Action |
|------|--------|
| 1 | Run advisory mode manually on existing receipts. Fix contradictions. |
| 2 | Add Ordivon Verify skill to AI agent instructions. |
| 3 | Add CI step that runs Verify and posts report to PR. |
| 4 | Switch to strict mode for governed repos. Configure blocking merge on BLOCKED. |

## Philosophy

Ordivon Verify is **trust calibration**, not more automation. It does not trust AI output. It verifies the claims AI makes about its own work. The gap between "agent claimed" and "evidence supports" is where Verify operates.

READY is not an endorsement. It is evidence that the claims are internally consistent. The human reviewer remains responsible for the decision.
