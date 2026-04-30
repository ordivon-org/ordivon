# Ordivon Verify — User Journey

Status: **PROPOSAL** | Date: 2026-05-01 | Phase: PV-1
Tags: `product`, `verify`, `user-journey`, `scenarios`
Authority: `proposal` | AI Read Priority: 3

## Scenario A — Solo AI-Heavy Developer

### Before

Jane is a solo founder building a SaaS product. She uses Claude Code daily. Her workflow:

- Claude Code writes features, runs tests, produces completion receipts
- She reviews PRs manually, but can't verify every claim
- Last week: Claude claimed "all tests pass" but had skipped 3 integration tests
- She discovered this 2 days later when a customer reported the bug

Jane has receipts in `docs/runtime/` but no way to systematically verify them.

### Command

```bash
$ ordivon verify
```

### Output

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Ordivon Verify — Trust Report
 Project: jane-saas | Mode: standard
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Status: BLOCKED

 Receipts    ✗  15 scanned, 2 contradictions

   Hard failures:
   • docs/runtime/feature-x-receipt.md:12
     Claims "Skipped: None" but line 18 says
     "Integration tests not run — deferred to next phase"

   • docs/runtime/bugfix-y-receipt.md:8
     Claims "SEALED" but verification table shows
     2 of 7 checks still marked PENDING

 Debt        ✓  0 open, 3 closed
 Docs        ✓  42 registered, 0 stale
 Semantics   ✓  no dangerous phrases

 Trust decision: BLOCKED — 2 receipt contradictions.
 Fix the receipts or reclassify before merging.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Decision

Jane opens the two receipts. The first is an honest mistake — "not run" was the truth, "Skipped: None" was template copy-paste. She fixes it.

The second is a real problem — Claude sealed the phase but 2 checks were genuinely incomplete. She reopens the phase.

### Value

- Caught 2 honesty gaps before they became production bugs
- 15 receipts verified in 2 seconds instead of 30 minutes manual review
- Trust is now calibrated: she knows which receipts are verified and which need attention

---

## Scenario B — Small Team PR Workflow

### Before

A 5-person engineering team uses AI agents alongside human developers. Their workflow:

- Humans and agents open PRs
- CI runs lint, tests, build
- But no one checks whether agents are truthfully reporting completion

Last sprint: an agent opened a PR claiming "11/11 gates passing." A reviewer noticed the baseline had actually been weakened to 10/10 in a previous commit — one gate was silently removed.

### Command (in CI)

```yaml
# .github/workflows/verify.yml
- name: Ordivon Verify
  run: ordivon verify --json > verify-report.json
- name: Post Report
  if: failure()
  run: |
    ordivon report --markdown >> $GITHUB_STEP_SUMMARY
```

### Output (on PR)

```
## Ordivon Verify — Trust Report

**Project**: team-backend | **Mode**: strict | **Status**: BLOCKED

| Check | Result | Detail |
|-------|--------|--------|
| Receipts | ✅ | 8 scanned, 0 contradictions |
| Debt | ✅ | 0 open, 2 closed |
| **Gates** | **❌** | **Manifest/baseline mismatch** |
| Docs | ✅ | 55 registered, 0 stale |
| Semantics | ✅ | no dangerous phrases |

### Hard Failures

**Gate manifest mismatch**: Manifest declares 11 gates (pr-fast-v1).
Baseline runner (`run_verification_baseline.py`) reports 10 gates.
Gate `architecture_boundaries` (L4) present in manifest but missing
from runner output.

⚠️ A hard gate was removed without a Stage Summit.
This PR cannot be merged until this is addressed.
```

### Decision

The team lead investigates. The architecture checker script was accidentally deleted in a prior refactor commit — not malicious, just careless. They restore it, re-run, get 11/11, merge.

### Value

- Caught a silent gate removal before it became institutional drift
- CI integration makes verification automatic — no extra step for reviewers
- Markdown report posted directly to PR for visibility

---

## Scenario C — Governance-Heavy Internal Repo

### Before

A fintech company runs Ordivon as their governance OS. They have:

- Full DG Pack: document registry, debt ledger, gate manifest, receipt integrity checker
- Phase 7P closed, Phase 8 deferred
- 30+ docs registered with freshness timestamps
- AI agents update docs weekly

Problem: docs are drifting. A junior engineer's agent updated 3 docs last week but didn't update the registry or freshness timestamps. The Stage Summit still said "DG Pack CLOSING" even though it was closed 2 weeks ago. No one noticed until a new hire read stale docs and got confused about what was allowed.

### Command

```bash
$ ordivon verify docs
$ ordivon verify all
```

### Output

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Ordivon Verify — Trust Report
 Project: ordivon | Mode: full
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Status: BLOCKED

 Receipts    ✓  20 scanned, 0 contradictions
 Debt        ✓  0 open, 4 closed
 Gates       ✓  11/11
 Docs        ✗  31 registered, 1 stale, 2 dangerous phrases

   Stale docs:
   • docs/governance/README.md
     Status says "CLOSING" — DG-Z Stage Summit published 2026-04-30
     shows CLOSED. Freshness: 14 days stale.

   Dangerous phrases:
   • docs/ai/current-phase-boundaries.md:125
     "Document registry is hard gate — 8/8"
     Baseline is 11/11. Stale baseline count detected.

 Semantics   ✓  no CandidateRule/Policy confusion

 Trust decision: BLOCKED — stale truth + stale baseline count.
 Update stale docs before new AI agents read incorrect state.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Decision

The team lead runs `ordivon verify docs` to see the docs-only failures. They:

1. Update `README.md` status from CLOSING to CLOSED
2. Fix `current-phase-boundaries.md` baseline count from 8/8 to 11/11
3. Re-run `ordivon verify` — READY

### Value

- Prevented new team members from reading stale governance state
- Caught stale baseline count before it became an agent training data error
- Docs are now verified as systematically as code

---

## Scenario Comparison

| Aspect | Scenario A (Solo) | Scenario B (Team CI) | Scenario C (Governance) |
|--------|-------------------|---------------------|------------------------|
| User | Solo founder | 5-person eng team | Fintech governance team |
| Trigger | Manual, before merge | Automatic, in CI | Manual, periodic audit |
| Detection | Receipt contradiction | Gate removal | Stale docs + phrase drift |
| Action | Fix receipt, reopen phase | Restore deleted checker | Update stale docs |
| Value | Catch agent honesty gaps | Catch silent gate weakening | Prevent doc drift |
| Mode | standard | strict | full |

## Philosophy Connection

Ordivon Verify is not "more tooling." It is **trust calibration for AI-generated work**.

The three scenarios share a common thread: AI agents produce output faster than humans can verify it. The verification gap — between what was claimed and what evidence supports — grows with every agent-generated commit.

Ordivon Verify addresses this by checking the claims, not the code. It answers:

- Did the agent actually run what it said it ran? (receipts)
- Is the debt it mentioned actually registered? (debt)
- Have any gates been silently weakened? (gates)
- Is the documentation still current truth? (docs)
- Are dangerous semantic confusions present? (semantics)

These questions are not answered by traditional CI. They require meta-verification — checking the checker, auditing the auditor, verifying the veracity of verification claims.

## Boundary Confirmation

These scenarios describe product behavior under the Ordivon Verify proposal. They do not describe current Ordivon state, activate any trading capability, or authorize Phase 8. All NO-GO boundaries remain intact.
