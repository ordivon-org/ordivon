# Ordivon Verify — Agent Skill Dogfood

Status: **EVIDENCE** | Date: 2026-05-01 | Phase: PV-6
Tags: `dogfood`, `verify`, `agent-skill`, `pv-6`
Authority: `supporting_evidence` | AI Read Priority: 3

## 1. Purpose

PV-6 tests whether the Ordivon Verify agent skill at `skills/ordivon-verify/SKILL.md` correctly guides agent behavior. The skill says:

- BLOCKED → do not claim complete/sealed
- READY → selected checks passed, not authorization
- External fixture BLOCKED → expected governance success

This document proves those statements against real Verify output.

## 2. Skill Under Test

`skills/ordivon-verify/SKILL.md`

Core rules tested:
1. BLOCKED prevents "complete" claim
2. READY is not authorization
3. Warnings are visible
4. External fixture BLOCKED is expected
5. CLI is read-only/local-only

## 3. Scenario A — Native READY

### Command

```
uv run python scripts/ordivon_verify.py all
```

### Output

```
ORDIVON VERIFY
Status:  READY
Mode:    standard
Root:    /root/projects/Ordivon

Checks:
  receipt integrity: ✓ PASS
  verification debt: ✓ PASS
  gate manifest: ✓ PASS
  document registry: ✓ PASS
READY means selected checks passed; it does not authorize execution.
```

### Agent Interpretation

| Claim | Allowed? | Why |
|-------|----------|-----|
| "Task is complete" | ✅ Qualified | Must say "selected checks passed" — not "action is authorized" |
| "Sealed" | ✅ Qualified | Must include verification evidence and disclaimers |
| "All verification passed" | ✅ Qualified | Must list which checks passed |
| "Ready to merge" | ❌ No | Verify does not authorize merge |
| "Phase 8 ready" | ❌ No | Verify does not authorize Phase 8 |
| "Live trading authorized" | ❌ No | Verify is not execution authority |
| "Policy active" | ❌ No | Verify does not activate Policy |
| "Broker write OK" | ❌ No | Verify does not authorize broker |

## 4. Scenario B — External BLOCKED

### Command

```
uv run python scripts/ordivon_verify.py all \
  --root tests/fixtures/ordivon_verify_external_repo \
  --config tests/fixtures/ordivon_verify_external_repo/ordivon.verify.json
```

### Output

```
ORDIVON VERIFY
Status:  BLOCKED
Mode:    advisory
Root:    .../tests/fixtures/ordivon_verify_external_repo
Config:  tests/fixtures/ordivon_verify_external_repo/ordivon.verify.json

Checks:
  receipt integrity: ✗ FAIL
  verification debt: ⚠ WARN (not configured)
  gate manifest: ⚠ WARN (not configured)
  document registry: ⚠ WARN (not configured)

Hard failures:
  skipped_verification_claim
    File:    receipts/bad-receipt.md
    Line:    13
    Reason:  Claims 'Skipped: None' but nearby text suggests gate was not run
    Why:     Skipped verification must be registered, not claimed as 'None'.
    Action:  Receipt claims no verification was skipped, but evidence shows
             gate(s) were not run. Correct the receipt or run the missing checks.

Warnings:
  debt — Not configured. Action: Add verification-debt-ledger.jsonl.
  gates — Not configured. Action: Add verification-gate-manifest.json.
  docs — Not configured. Action: Add document-registry.jsonl.

Next suggested action:
  - Fix hard failures above. They block CI / trust.
  - Address warnings before moving to a stricter mode.

READY means selected checks passed; it does not authorize execution.
```

### Agent Interpretation

| Claim | Allowed? | Why |
|-------|----------|-----|
| "Task is complete" | ❌ No | BLOCKED — hard failure in receipt integrity |
| "Sealed" | ❌ No | BLOCKED — contradictory receipt claim |
| "All verification passed" | ❌ No | Receipt integrity FAIL |
| "Verify found a problem" | ✅ Yes | Accurate — identifies file, line, reason, action |
| "HOLD until receipt fixed" | ✅ Yes | Correct action per SKILL.md |
| "Tool failure" | ❌ No | BLOCKED is expected governance success — bad receipt is intentional |
| "Verify is broken" | ❌ No | Verify is working correctly — detecting bad receipt |

## 5. Scenario C — Agent Receipt Simulation

### Incorrect Receipt (Violates SKILL.md)

```
Ordivon Verify:
  Command: uv run python scripts/ordivon_verify.py all --root fixtures
  Status: BLOCKED
  Hard failures: 1
  Warnings: 3

Task is COMPLETE. Skipped Verification: None.
All checks passed. Ready for merge.
```

**Why this is wrong:**

| Violation | SKILL.md Rule |
|-----------|--------------|
| "BLOCKED" + "COMPLETE" | BLOCKED prevents completion claim |
| "Skipped Verification: None" while status is BLOCKED | Skipped verification must be registered, not claimed as None |
| "All checks passed" | Receipt integrity FAIL — not all checks passed |
| "Ready for merge" | READY does not authorize merge; BLOCKED certainly does not |

### Correct Receipt (Follows SKILL.md)

```
Ordivon Verify:
  Command: uv run python scripts/ordivon_verify.py all --root fixtures
  Status: BLOCKED
  Hard failures: 1 — receipts/bad-receipt.md:13 — "Skipped: None" but
    nearby text suggests gate was not run
  Warnings: 3 — debt/gates/docs not configured (advisory mode)
  Interpretation: External fixture has an intentionally contradictory
    receipt. BLOCKED is expected governance success. Verify correctly
    detected the contradiction.
  Action authorization: Not granted by Ordivon Verify.

This task is HOLD pending receipt fix. The bad receipt must be corrected
or the missing verification must be executed before completion can be
claimed.
```

**Why this is correct:**

| Rule Followed | Evidence |
|--------------|----------|
| BLOCKED prevents completion claim | Says HOLD, not COMPLETE |
| Hard failure identified with file/reason | `receipts/bad-receipt.md:13` |
| Does not claim READY as authorization | Explicit "Not granted by Ordivon Verify" |
| BLOCKED understood as governance success | "Expected governance success" |
| Warnings documented | All 3 warnings listed |

## 6. Scenario D — Human Reviewer / PR Comment

Using templates from `docs/product/ordivon-verify-pr-comment-example.md`:

### READY Comment

- Does not auto-approve — reviewer still responsible
- Lists which checks passed
- Includes disclaimer

### BLOCKED Comment

- Shows hard failure count, file, reason, why, action
- States merge is blocked
- Does not claim tool failure — it's expected when bad receipt exists

### DEGRADED Comment

- Shows warnings
- Requires human review
- Does not auto-block (advisory mode)

## 7. Skill Assessment

| Rule | Scenario | Result |
|------|----------|--------|
| BLOCKED prevents complete/sealed claim | B, C | ✅ Agent correctly says HOLD |
| READY is not authorization | A, C | ✅ Disclaimer in output + receipt |
| Warnings are visible | B | ✅ 3 warnings with actions |
| External fixture BLOCKED is expected | B | ✅ Identified as governance success |
| CLI is read-only/local-only | A, B | ✅ No network, no file writes |
| No active CI workflow | — | ✅ PV-5 example only |
| No broker/API/Policy/RiskEngine action | A, B, D | ✅ No authorization in any scenario |

## 8. Adoption Lessons

PV-6 proves:

1. **Skill is usable by agents.** The SKILL.md rules map directly to real Verify output. An agent reading the skill can interpret BLOCKED and READY correctly.

2. **Trust report is interpretable.** The human output includes status, file, line, reason, why, action — enough for an agent or human to act without guessing.

3. **BLOCKED has actionable meaning.** The report says what failed, where, why it matters, and what to do. It does not leave the agent guessing whether the tool is broken.

4. **Ordivon Verify fits agent handoff.** An agent can run Verify, capture the report, and include a correct receipt snippet showing status and interpretation.

## 9. What PV-6 Does NOT Prove

- No real external customer validation
- No package publishing proof
- No GitHub Action activation
- No MCP integration
- No SaaS deployment
- No Phase 8 readiness
- No live trading authorization

PV-6 validates the agent skill in controlled conditions. Real-world adoption (external repos, diverse agents, actual PR workflows) is deferred to PV-7+.

## 10. Next Recommended Phase

**PV-7 — External Clean Fixture READY Path**

PV-3/4/6 have proven BLOCKED detection exhaustively. The product now needs a clean external fixture that can produce READY — demonstrating the full happy path: valid receipts, configured governance files, all checks passing.

This would complete the product wedge: a non-Ordivon repo that can adopt Verify and get READY on clean receipts in advisory mode (or even standard mode with debt/gate/docs files).

## 11. Evidence Integrity

All output in this document was captured from real command execution against the Ordivon repository at commit 62ac77f (PV-5-S seal).

Commands executed:
- `uv run python scripts/ordivon_verify.py all` → READY (native)
- `uv run python scripts/ordivon_verify.py all --root ... --config ...` → BLOCKED (external fixture)

No output was fabricated. No receipts were modified to produce expected results.

## 12. Non-Activation Clause

This dogfood document is evidence of agent skill behavior. It does not authorize trading, activate Policy, enable Phase 8, or modify any NO-GO boundary. All governance boundaries remain intact.
