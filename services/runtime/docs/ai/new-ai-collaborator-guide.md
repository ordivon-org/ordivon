# New AI Collaborator Guide — Ordivon Project

> For AI agents working in this repository. Read before writing.
> **Full system details**: `docs/ai/systems-reference.md`

## What Ordivon Is

Ordivon is a **governance operating system**. We govern AI/agent/human
collaboration through evidence, policy, shadow evaluation, and review.

We are not a trading bot, an AI wrapper, a dashboard, or a CI pipeline.

## Quick Start

```bash
# 1. Read context
cat AGENTS.md
cat docs/ai/current-phase-boundaries.md

# 2. Run verification (must pass before commit)
uv run python scripts/run_baseline.py --pr-fast

# 3. Run tests
scripts/run_tests.sh
```

## How to Work Here

### 1. Read the Context First

Before doing anything, read:
- `AGENTS.md` — root entry point, current status
- `docs/ai/systems-reference.md` — ALL systems, commands, substance ← NEW
- `docs/ai/current-phase-boundaries.md` — what's active, what's NO-GO
- `docs/ai/agent-output-contract.md` — required output shape
- `docs/governance/extension-processes.md` — how to extend any layer ← NEW

### 2. Understand the Governance Vocabulary

These are not optional. They're the grammar of the system:

| Term | What It Means |
|------|--------------|
| **Capability ≠ Authorization** | can_X describes technical ability. It does not grant permission. |
| **READY ≠ Approval** | READY means checks passed. It does not authorize execution. |
| **Evidence ≠ Approval** | Evidence supports review. Evidence does not approve. |
| **CandidateRule ≠ Policy** | Advisory observation. Promotion requires: shadow→redteam→owner. |
| **Receipt ≠ Approval** | Records what happened. Does not authorize future action. |
| **BLOCKED** | Hard boundary violation. Cannot proceed without fix. |
| **NO-GO** | Permanently out of scope in current state. |
| **DEGRADED** | Governance incomplete but honest. Needs review. |

### 3. Know the Hard Boundaries

These are NEVER allowed:
- Live financial / broker / trading action — NO-GO (Phase 8 DEFERRED)
- Credential access — BLOCKED by default
- Promoting CandidateRule to Policy without: shadow eval + red-team review + owner signoff
- Self-promoting a checker from draft to active
- Activating a Policy without named Owner + explicit signoff
- Treating READY as authorization
- Claiming "Ruff clean" without qualifying scope

### 4. Follow the Phase Discipline

Every task has: Allowed / Forbidden / Verification / Receipt.

When you receive a phase prompt:
1. Check boundaries: what's allowed, what's forbidden
2. Do only what's in scope
3. Run verification (pr-fast baseline minimum)
4. Produce receipt with: files changed, work summary, verification table, known debt, New AI Context Check
5. Commit with descriptive message

### 5. Use the Tools

```bash
# ── Primary verification ──────────────────────────
uv run python scripts/run_baseline.py --pr-fast     # PR gate (12 checkers)
uv run python scripts/run_baseline.py               # Full baseline (36 checkers)
uv run python -m ordivon_verify run <gate_id>        # Single gate

# ── Run tests ─────────────────────────────────────
scripts/run_tests.sh                                 # Full suite (hermetic, CI-parity)
uv run python -m pytest tests/unit/<domain>/ -v      # Specific domain

# ── Format before push ────────────────────────────
uv run ruff format --preview .

# ── Checker ecosystem ─────────────────────────────
uv run python checkers/<name>/run.py                 # Run any checker
uv run python scripts/run_baseline.py --sync         # Sync manifest
uv run python scripts/run_baseline.py --manifest     # Show manifest

# ── Document governance ───────────────────────────
uv run python checkers/document-registry/run.py      # Registry check
uv run python checkers/document-freshness/run.py     # Freshness check

# ── Entropy governance ────────────────────────────
uv run python checkers/entropy-telemetry/run.py      # Measure metrics
uv run python checkers/entropy-gate/run.py           # Check gates

# ── Governance learning loop ──────────────────────
uv run python checkers/lesson-extraction/run.py      # Extract CandidateRules
uv run python checkers/policy-shadow/run.py          # Shadow evaluation
```

### 6. Register Your Work

After every phase:
- Add new docs to `docs/governance/document-registry.jsonl`
- Run document-registry checker
- Update `AGENTS.md` current status line
- Update `docs/ai/current-phase-boundaries.md` phase timeline
- If you discover debt, register it in `docs/governance/verification-debt-ledger.jsonl`
- If you discover a workflow worth reusing, save it as a skill

### 7. Handle Debt Honestly

- New test failures must be classified as new vs pre-existing with baseline evidence
- Pre-existing failures must be registered in the debt ledger
- Never mask new regressions as "known baseline"
- Skipped verification must be declared with justification
- "I don't know" is valid. "I assume it's fine" is not.

### 8. Write Receipts That Can Be Verified Later

Every receipt must answer:
- What files changed?
- What commands were run and what did they return?
- What verification passed/skipped/failed and why?
- What debt existed before and after?
- Would a new AI reading this understand the current state?

## Current Systems (2026-05-05)

```
Checker ecosystem: 36 checkers, L3-L10, pr-fast 12/12, full 36/36 ALL PASS (26 hard + 10 escalation)
Document governance: 213 registered docs, 0 stale, 0 missing freshness
Entropy governance: L4.5 telemetry + L4.5A gates, Lehman's Laws applied
Governance loop: Checker→Lesson→CandidateRule→Shadow→Review — fully closed
Maturity model: draft→shadow_tested→red_teamed→active, no self-promotion
Owner veto: Policy activation requires named Owner + explicit signoff
Extension processes: Core/Pack/Adapter/Checker/Test — PEP+RFC+KEP inspired

Phase 8 (live trading): DEFERRED
Open debt: 3 entries (all classified, tracked)
```

## Key Files Map

```
AGENTS.md                                    ← Start here
docs/ai/systems-reference.md                ← ALL systems: commands + substance
docs/ai/current-phase-boundaries.md          ← Phase timeline + boundaries
docs/ai/agent-output-contract.md             ← Required output format
docs/governance/extension-processes.md       ← How to extend any layer
docs/governance/entropy-governance-design.md  ← Anti-entropy system
docs/governance/document-registry.jsonl      ← 197 registered documents
docs/governance/entropy-telemetry.jsonl      ← Entropy metrics
docs/governance/candidate-rule-drafts.jsonl  ← CandidateRule proposals
docs/governance/shadow-evaluation-log.jsonl  ← Shadow evaluation results
docs/governance/lesson-ledger.jsonl          ← Lessons from findings
docs/governance/verification-debt-ledger.jsonl ← Known debt
checkers/                                    ← 36 checker packages
src/ordivon_verify/                          ← Registry + runner
domains/                                     ← Domain models
scripts/run_baseline.py                      ← Primary verification entry
```

## Remember

The system's moat is not any single artifact. It's the accumulated evidence
that every phase was dogfooded, tested, receipted, and verified. Every new
phase adds to that evidence. Every shortcut erodes it.

When in doubt: document, test, verify, register. Don't overclaim. Don't hide
debt. Don't treat READY as authorization. Don't confuse capability with
permission. Don't self-promote — independent review is required.

You're part of the governance loop now. Welcome.
