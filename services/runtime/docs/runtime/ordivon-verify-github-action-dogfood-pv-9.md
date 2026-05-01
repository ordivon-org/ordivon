# Ordivon Verify — GitHub Action Example Dogfood

Status: **EVIDENCE** | Date: 2026-05-01 | Phase: PV-9
Tags: `dogfood`, `verify`, `ci`, `github-actions`, `pv-9`
Authority: `supporting_evidence` | AI Read Priority: 3

## 1. Purpose

PV-9 validates the CI adoption story for Ordivon Verify without activating a real workflow. It tests whether the four-status ladder (READY/DEGRADED/BLOCKED) maps correctly to CI behavior and PR comments.

## 2. Example Workflow

`examples/ordivon-verify/github-action.yml.example` — copy to `.github/workflows/` when ready. Not active in this repo.

Key behaviors:
- BLOCKED → exit 1, blocks merge
- DEGRADED → exit 0, posts warning comment
- READY → exit 0, passes CI but does not auto-merge

## 3. Scenario A — Native READY as CI Result

### Command

```
uv run python scripts/ordivon_verify.py all --json
```

### JSON Summary

```json
{"status": "READY", "hard_failures": [], "warnings": []}
```

### CI Interpretation

| Field | Value |
|-------|-------|
| Exit code | 0 |
| PR should pass | Yes |
| Auto-merge | No — reviewer still responsible |
| Execution authorization | Not granted |

## 4. Scenario B — Standard External READY as CI Result

### Command

```
uv run python scripts/ordivon_verify.py all \
  --root tests/fixtures/ordivon_verify_standard_external_repo \
  --config tests/fixtures/ordivon_verify_standard_external_repo/ordivon.verify.json \
  --json
```

### JSON Summary

```json
{"status": "READY", "hard_failures": [], "warnings": []}
```

### CI Interpretation

Standard external fixture has clean receipts and valid governance files — CI-ready as a minimal governed repo. READY still does not authorize execution.

## 5. Scenario C — Clean Advisory DEGRADED as CI Result

### Command

```
uv run python scripts/ordivon_verify.py all \
  --root tests/fixtures/ordivon_verify_clean_external_repo \
  --config tests/fixtures/ordivon_verify_clean_external_repo/ordivon.verify.json \
  --json
```

### JSON Summary

```json
{"status": "DEGRADED", "hard_failures": [], "warnings": [
  {"check": "debt", "reason": "Not configured: ...verification-debt-ledger.jsonl not found"},
  {"check": "gates", "reason": "Not configured: ...verification-gate-manifest.json not found"},
  {"check": "docs", "reason": "Not configured: ...document-registry.jsonl not found"}
]}
```

### CI Interpretation

| Field | Value |
|-------|-------|
| Exit code | 2 |
| PR should merge | With human review only |
| Why | Receipts clean but governance files missing |
| Next | Add governance files → standard → READY |

## 6. Scenario D — Bad External BLOCKED as CI Result

### Command

```
uv run python scripts/ordivon_verify.py all \
  --root tests/fixtures/ordivon_verify_external_repo \
  --config tests/fixtures/ordivon_verify_external_repo/ordivon.verify.json \
  --json
```

### JSON Summary

```json
{"status": "BLOCKED", "hard_failures": [
  {
    "file": "receipts/bad-receipt.md",
    "reason": "Claims 'Skipped: None' but nearby text suggests gate was not run",
    "why_it_matters": "Skipped verification must be registered, not claimed as 'None'.",
    "next_action": "Correct the receipt or run the missing checks."
  }
], "warnings": [...]}
```

### CI Interpretation

| Field | Value |
|-------|-------|
| Exit code | 1 |
| PR should merge | **No** — blocked |
| Why | Receipt has contradictory claim |
| Fix | Correct bad-receipt.md or run missing checks |
| Note | BLOCKED is governance success, not tool failure |

## 7. PR Comment Mapping

Using templates from `docs/product/ordivon-verify-pr-comment-example.md`:

| Status | PR Comment |
|--------|-----------|
| READY | "Selected checks passed. Reviewer still responsible." |
| DEGRADED | "Warnings present. Human review required." |
| BLOCKED | "Hard failure detected. File: receipts/bad-receipt.md. Fix before merge." |

## 8. What PV-9 Proves

1. **CI adoption path is clear.** The example workflow is self-contained and comments inline.
2. **JSON report is CI-usable.** Status, hard_failures, warnings are programmatically accessible.
3. **Standard external fixture can be CI-ready.** Five files + clean receipts = READY.
4. **BLOCKED/DEGRADED/READY have distinct CI behaviors.** No ambiguity between tool failure and governance success.

## 9. What PV-9 Does NOT Prove

- No active GitHub Action was installed
- No package published
- No marketplace Action
- No real customer CI validation
- No SaaS
- No MCP server
- No Phase 8 readiness
- No live trading authorization

## 10. Next Recommended Phase

**PV-10 — Public README / Landing Copy for Ordivon Verify.**

The CLI, fixture ladder, agent skill, and CI story are now coherent enough to explain externally. A public README or landing page copy would complete the productization story.

## 11. Non-Activation Clause

This dogfood document validates CI adoption semantics using examples only. It does not activate CI, authorize trading, enable Phase 8, or modify any NO-GO boundary.
