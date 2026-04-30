# Ordivon Verify — Product Brief

Status: **PROPOSAL** | Date: 2026-05-01 | Phase: PV-1
Tags: `product`, `verify`, `cli`, `verification`, `productization`
Authority: `proposal` | AI Read Priority: 2

## 1. Product One-Liner

**Ordivon Verify is a local CLI and CI-ready verification layer that checks whether AI-generated work is safe to trust before merge, handoff, or execution.**

It does not run your tests. It verifies that what was claimed about your tests, receipts, gates, docs, and debt is actually true.

## 2. Target User — First Wedge

**Solo founder or AI-heavy engineer** working with AI coding agents (Codex, Claude Code, Cursor, Hermes Agent, Windsurf, Copilot) who has experienced:

- An agent saying "done" when tests were skipped
- A receipt claiming "sealed" while pending checks remain
- A PR where a gate was silently weakened in the last commit
- Documentation drifting from current truth without detection

**Second wedge**: small engineering teams where AI agents modify code, docs, and write completion receipts as part of PR workflow.

## 3. Primary Pain

Concrete problems this product addresses:

| Pain | Example |
|------|---------|
| **AI says "done" — tests were skipped** | Agent output: "All tests pass." Verification: 3 of 8 test commands never ran. |
| **Receipt claims "sealed" — verification incomplete** | Receipt: "SEALED." Checker: 2 required verifications still marked pending. |
| **Agent changes forbidden files** | Agent modified `.env`, `uv.lock`, or migration files without detection. |
| **Pre-existing debt gets hidden** | Debt was registered once, then silently dropped from docs. |
| **Gate count gets weakened** | Baseline was 11/11 last week. Today it's 10/10 — one gate removed without notice. |
| **Docs drift from current truth** | AGENTS.md says "Phase 7P ACTIVE" — was closed 2 weeks ago. |
| **CandidateRule masquerades as Policy** | Doc says "this rule validates trades." Rule is advisory only. |
| **Ledger treated as execution authority** | Receipt says "ledger authorizes next trade." Ledger is evidence only. |

These are NOT coding errors. They are **verification honesty failures** — the gap between what was claimed and what evidence supports. Traditional CI cannot catch these because it trusts the claims.

## 4. Day-One Promise

**Run one command and get a trust report.**

```
$ ordivon verify
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Ordivon Verify — Trust Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Status: READY

 Receipts:       ✓ 20 receipts scanned, 0 contradictions
 Debt:           ✓ 0 open, 4 closed
 Gates:          ✓ 11/11, no removal or downgrade
 Docs:           ✓ 31 registered, 0 stale
 No dangerous phrases detected.

 Trust decision: safe to proceed.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 5. Non-Goals

Ordivon Verify is NOT:

| Not | Why |
|-----|-----|
| A trading bot | Ordivon is a governance OS, not a trading system |
| An AI model | It does not generate, predict, or reason about code |
| An IDE agent | It does not modify files, suggest edits, or open PRs |
| A replacement for CI | It augments CI with meta-verification; it does not run test suites |
| An autonomous executor | It reports trust; it does not merge, deploy, or activate |
| A source of truth by itself | It checks consistency between claims and evidence |
| A live trading or broker tool | Phase 8 remains DEFERRED |
| A SaaS product | v0 is local CLI only |
| A database-backed system | v0 uses filesystem: markdown + JSONL |

## 6. Product Wedge — Smallest Useful External Product

**Ordivon Verify CLI v0:**

- **CLI-first**: single binary or script entry point
- **Local repo scan**: reads markdown, JSONL, config files on disk
- **Checker-based**: wraps existing checkers with unified interface
- **CI compatible**: exit codes map to CI pass/fail
- **No SaaS dependency**: runs entirely offline
- **No database required**: all state is filesystem documents
- **Adoptable incrementally**: works with Ordivon-native repos AND external repos via minimal config

### Adoption Spectrum

| Repo Type | Config Needed | Verdicts Available |
|-----------|--------------|-------------------|
| Ordivon-native (full DG Pack) | None — auto-detects | All: receipts, debt, gates, docs |
| External repo + ordivon.verify.json | One JSON file | Receipts, basic debt |
| External repo (advisory mode) | None | Receipt scan only |

## 7. Trust Report — Output Model

Four status levels, no ambiguity:

| Status | Meaning | Exit Code | CI Implication |
|--------|---------|-----------|----------------|
| **READY** | All hard gates pass, no contradictions, no overdue debt | 0 | Pass |
| **BLOCKED** | Hard gate failure: receipt contradiction, overdue debt, gate removed, dangerous phrase | 1 | Fail |
| **DEGRADED** | Warnings present but no hard failures (advisory mode, optional files missing) | 2 | Optional fail |
| **NEEDS_REVIEW** | Non-blocking issues found (pre-existing noise, tool limitations, config gaps) | 2 | Advisory |

### What Gets Checked

| Check Category | What It Verifies |
|---------------|-----------------|
| **Receipts** | No "sealed" with pending checks, no "skipped: none" while text says "not run", no stale baseline counts, no "clean working tree" with untracked residue |
| **Debt** | All verification debt registered, no overdue open debt, no high/blocking debt unaddressed |
| **Gates** | Baseline gates match manifest, no gate removed or downgraded without Stage Summit, no no-op gate commands |
| **Docs** | Registry consistent, no stale docs, no dangerous semantic phrases ("Phase 8 active", "CandidateRule is Policy", "ledger authorizes") |
| **Semantics** | CandidateRule ≠ Policy, receipt ≠ authority, evidence ≠ execution permission, paper ≠ live |

## 8. Why Now

AI coding agents have created a new category of verification risk that existing tools don't address:

### The Agent Honesty Problem

Traditional CI verifies **code behavior** — does it compile, pass tests, follow lint rules?

Agent-generated work introduces a new layer: **claim honesty**. When an agent says:
- "All tests pass" — did they actually run?
- "Working tree clean" — are there untracked files?
- "Phase sealed" — were all required checks executed?
- "Debt registered" — is it in the ledger or just mentioned in prose?

These are not code defects. They are **evidence defects**. A passing test suite says nothing about whether the agent truthfully reported the test results.

### The Speed Problem

AI agents generate code, docs, and receipts faster than humans can review them. The gap between "committed" and "verified" is growing. Ordivon Verify closes that gap with automated meta-verification.

### The Trust Calibration Problem

Teams currently trust agent output on a binary: either they trust everything (dangerous) or they review everything manually (unscalable). Ordivon Verify provides calibrated trust — a structured report that says what is verified, what is uncertain, and what is contradicted.

## 9. Philosophy — Trust Calibration, Not More Automation

Ordivon Verify is not "more automation." It is **trust calibration**.

### Core Principles from Ordivon Governance

| Principle | What It Means for Verify |
|-----------|------------------------|
| **AI output is evidence, not authority** | Agent receipts are checked, not trusted |
| **Checker failure is observation, not verdict** | A failed check is classified before action |
| **Debt may exist, hidden debt may not become truth** | All debt must be registered in the ledger |
| **Unverified work may exist, but must not be called sealed** | "SEALED" requires all gates passed and evidence recorded |
| **External harness output is evidence, not source of truth** | Verify reports evidence; it does not create truth |
| **CandidateRule ≠ Policy** | Advisory observations are not blocking rules |

## 10. Boundary Confirmation

This product brief is a **proposal**. It does not:

- Reopen DG Pack (DG Pack foundation remains CLOSED)
- Start Phase 8 (remains DEFERRED)
- Enable live trading, broker write, auto trading
- Activate Policy or RiskEngine enforcement
- Change CandidateRule advisory status
- Elevate JSONL ledgers beyond evidence
- Implement any code (implementation deferred to PV-2+)
- Require any dependency, lockfile, or CI change

## 11. Next Phase Recommendation

**PV-2 — Ordivon Verify CLI Skeleton**: Create `scripts/ordivon_verify.py` entry point wrapping existing checkers with unified output, JSON report mode, and exit code contract. Tests in `tests/unit/product/test_ordivon_verify_cli.py`.

Not before: PV-1 contract is accepted and scope is clear.
