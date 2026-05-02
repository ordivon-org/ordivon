# New AI Collaborator Guide — Ordivon Project

> For AI agents working in this repository. Read before writing.

## What Ordivon Is

Ordivon is a **governance operating system**. We govern AI/agent/human
collaboration through evidence, policy, shadow evaluation, and review.

We are not a trading bot, an AI wrapper, a dashboard, or a CI pipeline.

## What We've Built (Phase Chain)

We've built a governance stack in 9 phases, from protocol foundation to
detector implementation. Every phase added one layer:

```
Layer 1 — OGAP-Z     Adapter protocol: how external systems make work governable
Layer 2 — HAP-1      Harness object model: what agents/tools can do (8 schemas)
Layer 3 — EGB-1      External benchmarks: how we compare to OpenAI/Anthropic/NIST
Layer 4 — ADP-1      Pattern taxonomy: 18 ways AI agents fail, mapped to controls
Layer 5 — HAP-2      Fixture dogfood: proving patterns with 14 BLOCKED scenarios
Layer 6 — GOV-X      Capability-scaled governance: C0-C5, AP-R0-R5, gate matrix
Layer 7 — ADP-2      Pattern detector: 12 static rules that find problems in text
Layer 8 — HAP-3      TaskPlan + ReviewRecord: completing all 10 HAP objects
Layer 9 — (next)     ADP-3: structure-aware detection + CI integration
```

Every phase produces: docs + schemas/fixtures + tests + receipt + commit.

## How to Work Here

### 1. Read the Context First

Before doing anything, read:
- `AGENTS.md` — root entry point, current status
- `docs/ai/current-phase-boundaries.md` — what's active, what's NO-GO
- `docs/ai/agent-output-contract.md` — required output shape

### 2. Understand the Governance Vocabulary

These are not optional. They're the grammar of the system:

| Term | What It Means |
|------|--------------|
| **Capability ≠ Authorization** | can_X describes technical ability. It does not grant permission. |
| **READY ≠ Approval** | READY_WITHOUT_AUTHORIZATION means checks passed. It does not authorize execution. |
| **Evidence ≠ Approval** | Evidence supports review. Evidence does not approve. |
| **CandidateRule ≠ Policy** | Advisory observation. Promotion requires 4 criteria. |
| **Receipt ≠ Approval** | Records what happened. Does not authorize future action. |
| **BLOCKED** | Hard boundary violation. Cannot proceed without fix. |
| **NO-GO** | Permanently out of scope in current state. |
| **DEGRADED** | Governance incomplete but honest. Needs review. |

### 3. Know the Hard Boundaries

These are NEVER allowed:
- Live financial / broker / trading action — NO-GO
- Credential access — BLOCKED by default
- External API / MCP / browser side effects — BLOCKED by default
- Claiming compliance/certification with external frameworks
- Promoting CandidateRule to Policy without 4 criteria
- Using `can_access_secrets` — use `can_read_credentials`
- Treating READY as authorization

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
# Primary verification gate — must pass before commit
uv run python scripts/run_verification_baseline.py --profile pr-fast

# Run tests (use the script, not raw pytest)
scripts/run_tests.sh

# Format before push
uv run ruff format --preview .

# HAP payload validation
uv run python scripts/validate_hap_payload.py <file.json>

# ADP pattern detection (local static only)
uv run python scripts/detect_agentic_patterns.py <path> [--json] [--fail-on-blocking]

# Document registry check
uv run python scripts/check_document_registry.py
```

### 6. Register Your Work

After every phase:
- Add new docs to `docs/governance/document-registry.jsonl`
- Regenerate wiki: `uv run python scripts/generate_document_wiki.py`
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

## Current Open Debt (What You Don't Need to Fix)

- DOC-WIKI-FLAKY-001 — wiki generator output non-deterministic (skip in verification)
- EGB-SOURCE-FRESHNESS-001 — external benchmark versions need checking before next use
- PV-N8 build artifact — pre-existing, not yours to fix

## How to Add a New Phase

1. Write a phase prompt with: phase ID, status OPEN, allowed scope, forbidden scope, verification checklist, closure predicate
2. Create artifacts (docs, schemas, fixtures, tests)
3. Run verification
4. Produce receipt
5. Update AI onboarding
6. Commit

## Key Files Map

```
AGENTS.md                          ← Start here
docs/ai/README.md                  ← AI onboarding index
docs/ai/current-phase-boundaries.md ← What's live/deferred/NO-GO
docs/ai/agent-output-contract.md   ← Required receipt format
docs/governance/                   ← All governance docs
docs/runtime/                      ← Phase closure evidence
docs/product/                      ← Stage summits + stage notes
src/ordivon_verify/schemas/        ← JSON schemas (OGAP + HAP)
examples/hap/                      ← HAP fixtures (basic + ADP scenarios + task-plan + review-record)
scripts/                           ← Checkers, validator, detector
tests/                             ← Test suite
docs/governance/document-registry.jsonl        ← Canonical doc index
docs/governance/verification-debt-ledger.jsonl  ← Debt tracking
```

## Remember

The system's moat is not any single artifact. It's the accumulated evidence
that every phase was dogfooded, tested, receipted, and verified. Every new
phase adds to that evidence. Every shortcut erodes it.

When in doubt: document, test, verify, register. Don't overclaim. Don't hide
debt. Don't treat READY as authorization. Don't confuse capability with
permission.

You're part of the governance loop now. Welcome.
