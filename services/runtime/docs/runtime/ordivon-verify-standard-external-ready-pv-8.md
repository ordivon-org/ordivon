# Ordivon Verify — Standard External READY Path

Status: **EVIDENCE** | Date: 2026-05-01 | Phase: PV-8
Tags: `dogfood`, `verify`, `standard`, `external`, `ready`, `pv-8`
Authority: `supporting_evidence` | AI Read Priority: 3

## 1. Purpose

PV-8 validates the final adoption step: a clean external repo with minimal governance files reaching READY in standard mode. Previous phases:

- PV-3: Bad external fixture → BLOCKED
- PV-7: Clean external fixture (advisory, no governance) → DEGRADED
- PV-8: Clean external with governance files (standard) → READY

## 2. Fixtures Compared

| Fixture | Mode | Receipt | Governance | Status |
|---------|------|---------|-----------|--------|
| Bad external | advisory | contradictory | missing | **BLOCKED** |
| Clean advisory | advisory | clean | missing | **DEGRADED** |
| Standard external | standard | clean | present | **READY** |
| Native Ordivon | standard | clean | full | **READY** |

## 3. Standard External Fixture Files

```
tests/fixtures/ordivon_verify_standard_external_repo/
  ordivon.verify.json                              # mode: standard, configures all 4 checks
  receipts/clean-receipt.md                        # honest receipt — all checks executed
  governance/
    verification-debt-ledger.jsonl                 # 1 closed debt (example)
    verification-gate-manifest.json                # 3 gates (ruff check, ruff format, pytest)
    document-registry.jsonl                        # 5 registered docs
```

Each governance file is minimal but valid:
- **Debt ledger**: 1 closed debt entry — proves no open debt. File format: JSONL.
- **Gate manifest**: 3 gates with gate_id, display_name, command, hardness, purpose. No no-op commands. gate_count matches actual gates.
- **Document registry**: 5 entries with doc_id, path, type, status, authority. No stale docs.

## 4. Scenario A — Standard External READY

### Command

```
uv run python scripts/ordivon_verify.py all \
  --root tests/fixtures/ordivon_verify_standard_external_repo \
  --config tests/fixtures/ordivon_verify_standard_external_repo/ordivon.verify.json
```

### Output

```
ORDIVON VERIFY
Status:  READY
Mode:    standard
Root:    .../tests/fixtures/ordivon_verify_standard_external_repo
Config:  tests/fixtures/ordivon_verify_standard_external_repo/ordivon.verify.json

Checks:
  receipt integrity: ✓ PASS
  verification debt: ✓ PASS
  gate manifest: ✓ PASS
  document registry: ✓ PASS
READY means selected checks passed; it does not authorize execution.
```

### JSON

```json
{
  "status": "READY",
  "hard_failures": [],
  "warnings": [],
  "disclaimer": "READY means selected checks passed; it does not authorize execution."
}
```

**All four checks pass.** No hard failures. No warnings. The external repo has clean receipts and valid governance files.

## 5. Scenario B — Clean Advisory DEGRADED

### Command

```
uv run python scripts/ordivon_verify.py all \
  --root tests/fixtures/ordivon_verify_clean_external_repo \
  --config tests/fixtures/ordivon_verify_clean_external_repo/ordivon.verify.json
```

### Output

```
Status:  DEGRADED
  receipt integrity: ✓ PASS
  verification debt: ⚠ WARN (not configured)
  gate manifest: ⚠ WARN (not configured)
  document registry: ⚠ WARN (not configured)
```

**DEGRADED is honest.** The repo has clean receipts but no governance infrastructure. The warnings tell the user exactly what to add next. This is the midpoint between BLOCKED and READY.

## 6. Scenario C — Bad External BLOCKED

### Output (abbreviated)

```
Status:  BLOCKED
  receipt integrity: ✗ FAIL
    File:    receipts/bad-receipt.md:13
    Reason:  Claims 'Skipped: None' but nearby text suggests gate was not run
```

**BLOCKED is governance success.** The contradictory receipt is correctly detected. The user knows exactly what to fix.

## 7. Product Semantics

| Mode | Missing governance | Receipt clean | Result |
|------|-------------------|--------------|--------|
| Advisory | Ignored (WARN) | Yes | DEGRADED |
| Advisory | Ignored (WARN) | No | BLOCKED |
| Standard | Not configured (WARN) | Yes | DEGRADED |
| Standard | Configured + valid | Yes | **READY** |
| Standard | Configured but missing | No (FAIL) | BLOCKED |
| Strict | Required + valid | Yes | READY |
| Strict | Missing | No (FAIL) | BLOCKED |

**Key insight**: The path from BLOCKED to READY is:
1. Fix contradictory receipts → DEGRADED
2. Add governance files → READY

**READY does not authorize execution, merge, deployment, trading, Policy activation, or RiskEngine enforcement.**

## 8. What PV-8 Proves

1. **External repo can reach READY without copying full Ordivon.** Five files: config + receipt + debt + gates + docs.

2. **Minimal governance files are sufficient.** The lightweight validators check structure and basic invariants, not full Ordivon cross-checks.

3. **Bad receipts still block.** The contradictory fixture remains BLOCKED — unchanged.

4. **Missing governance is visible, not hidden.** Advisory mode shows warnings. Standard mode requires configured files to exist.

5. **Native mode remains stable.** All 11 Ordivon-native gates pass unchanged.

## 9. What PV-8 Does NOT Prove

- No real customer validation
- No published package
- No GitHub Action activation
- No MCP integration
- No SaaS deployment
- No Phase 8 readiness
- No live trading authorization

PV-8 validates the standard external path in controlled conditions.

## 10. Next Recommended Phase

**PV-9 — GitHub Action Example Dogfood.** The product now has a complete external adoption path (advisory → standard → READY). Next step: run Verify in an example CI pipeline to show CI integration.

## 11. Non-Activation Clause

This dogfood document is evidence of the standard external path. It does not authorize trading, activate Policy, enable Phase 8, or modify any NO-GO boundary. All governance boundaries remain intact.
