# Ordivon Verify — Clean External READY Path

Status: **EVIDENCE** | Date: 2026-05-01 | Phase: PV-7
Tags: `dogfood`, `verify`, `external`, `clean`, `pv-7`
Authority: `supporting_evidence` | AI Read Priority: 3

## 1. Purpose

PV-7 validates the positive external path for Ordivon Verify. Previous phases proved:
- PV-3/4: External bad fixture → BLOCKED (contradictory receipt detected)
- PV-6: Agent skill correctly interprets BLOCKED

PV-7 asks: can a clean non-Ordivon repo get a positive result?

## 2. Fixture

```
tests/fixtures/ordivon_verify_clean_external_repo/
  ordivon.verify.json          # advisory mode, receipt_paths: ["receipts"]
  receipts/
    clean-receipt.md           # honest receipt — all checks executed
```

The clean receipt has:
- Status: COMPLETE
- Verification Results table with concrete commands and results
- Skipped Verification: None
- No "will verify later" / "not run" / "pending"
- No contradictory language

No governance files (debt/gates/docs) are present — this is a minimal advisory-mode adoption.

## 3. Scenario A — Clean External Fixture

### Command

```
uv run python scripts/ordivon_verify.py all \
  --root tests/fixtures/ordivon_verify_clean_external_repo \
  --config tests/fixtures/ordivon_verify_clean_external_repo/ordivon.verify.json
```

### Output

```
ORDIVON VERIFY
Status:  DEGRADED
Mode:    advisory
Root:    .../tests/fixtures/ordivon_verify_clean_external_repo
Config:  tests/fixtures/ordivon_verify_clean_external_repo/ordivon.verify.json

Checks:
  receipt integrity: ✓ PASS
  verification debt: ⚠ WARN (not configured)
  gate manifest: ⚠ WARN (not configured)
  document registry: ⚠ WARN (not configured)

Warnings:
  debt — Not configured. Action: Add verification-debt-ledger.jsonl.
  gates — Not configured. Action: Add verification-gate-manifest.json.
  docs — Not configured. Action: Add document-registry.jsonl.

Next suggested action:
  - Address warnings before moving to a stricter mode.

READY means selected checks passed; it does not authorize execution.
```

### Interpretation

| Field | Value | Meaning |
|-------|-------|---------|
| Status | DEGRADED | Warnings present, no hard failures |
| Receipt | PASS | Clean receipt — no contradictions |
| Debt | WARN | Not configured — expected in advisory mode |
| Gates | WARN | Not configured |
| Docs | WARN | Not configured |
| Hard failures | 0 | No contradictory claims |

**DEGRADED is the honest result.** A repo with clean receipts but no governance infrastructure is not fully trusted. It means: "Your receipts are honest. Now add debt/gate/docs files for full verification."

## 4. Scenario B — Bad External Fixture Comparison

### Command

```
uv run python scripts/ordivon_verify.py all \
  --root tests/fixtures/ordivon_verify_external_repo \
  --config tests/fixtures/ordivon_verify_external_repo/ordivon.verify.json
```

### Output (abbreviated)

```
Status:  BLOCKED
receipt integrity: ✗ FAIL
  skipped_verification_claim
    File:    receipts/bad-receipt.md:13
    Reason:  Claims 'Skipped: None' but nearby text suggests gate was not run
```

### Comparison

| | Clean Fixture | Bad Fixture |
|---|-------------|------------|
| Receipt status | PASS | FAIL |
| Hard failures | 0 | 1 |
| Warnings | 3 (expected) | 3 (expected) |
| Overall | DEGRADED | BLOCKED |
| Meaning | "Clean receipts, add governance" | "Fix contradictory receipt" |

## 5. Scenario C — Native Ordivon Comparison

```
Status:  READY
receipt integrity: ✓ PASS
verification debt: ✓ PASS
gate manifest: ✓ PASS
document registry: ✓ PASS
```

Native Ordivon has all governance files → READY. This is the target state for external repos after adding debt/gate/docs files.

## 6. Advisory Warning Semantics

PV-7 makes explicit the semantics that were implicit in PV-3/4:

| Mode | Missing governance files | Status | Why |
|------|------------------------|--------|-----|
| Advisory | Expected | WARN → DEGRADED | Repo is in early adoption; warnings are guidance, not blocks |
| Standard | Expected for configured files | WARN → DEGRADED (if unconfigured) or FAIL (if configured but missing) | Standard expects configured files to exist |
| Strict | Not allowed | FAIL → BLOCKED | Strict mode requires all governance files |

**DEGRADED is not failure.** It means: "Receipts pass, but you're not yet at full trust. Add governance files to reach READY."

**BLOCKED is failure.** It means: "Your receipts contain contradictory claims. Fix them before proceeding."

This distinction is the core product value of Ordivon Verify.

## 7. What PV-7 Proves

1. **External adoption can start minimal.** One JSON file + one clean receipt directory = working Verify.

2. **Honest receipts pass.** The clean receipt has no contradictory language → PASS.

3. **Contradictory receipts block.** The bad receipt still produces BLOCKED — unchanged.

4. **Trust report differentiates clean vs bad.** DEGRADED (clean) ≠ BLOCKED (bad). The distinction is actionable.

5. **Governance gap is visible, not hidden.** Missing debt/gates/docs files produce explicit warnings with next-action advice.

6. **Path to READY is clear.** Address warnings → add governance files → switch to standard/strict → READY.

## 8. What PV-7 Does NOT Prove

- No real external customer validation
- No package publishing
- No GitHub Action activation
- No MCP integration
- No SaaS deployment
- No Phase 8 readiness
- No live trading authorization

PV-7 validates the clean path in controlled conditions. Real-world adoption is deferred.

## 9. Next Recommended Phase

**PV-8 — External Config Standard/Strict Mode**

PV-7 proved advisory clean path. Next: what happens when the clean fixture adds governance files and switches to standard/strict mode? This would complete the adoption journey from minimal advisory → standard with governance → strict with full verification.

## 10. Non-Activation Clause

This dogfood document is evidence of the clean external path. It does not authorize trading, activate Policy, enable Phase 8, or modify any NO-GO boundary. All governance boundaries remain intact.
