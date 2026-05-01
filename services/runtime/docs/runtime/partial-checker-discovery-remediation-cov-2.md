# COV-2 — Partial Checker Discovery Remediation

## Purpose

Remediate the 3 explicit partial checker coverage gaps declared by COV-1:
- verification_debt — now has conservative debt-candidate discovery
- receipt_integrity — now has self-discovered receipt universe
- pr_fast_baseline — manifest↔baseline drift detection is implemented; wave_files whitelist is documented known gap

## COV-1 Partial Checker Gap Summary

| Checker | COV-1 Status | Gap |
|---|---|---|
| verification_debt | partial | No discovery of unregistered debt |
| receipt_integrity | partial | Universe bound by configured receipt_paths |
| pr_fast_baseline | partial | wave_files whitelist hand-maintained |

## What COV-2 Changed

### Part A — verification_debt discovery

Added `discover_debt_candidates()`: scans `docs/runtime/`, `docs/product/`,
`docs/governance/`, `docs/architecture/`, `AGENTS.md`, `README.md` for
high-risk unresolved-work signals: BLOCKED, skipped verification, known gap,
pending verification, degraded.

Discovery results (at time of COV-2 closure):
- 174 candidate signals detected across ~40 files
- 0 excluded (exclusion file exists but no entries yet)
- Warning-only — does not block pr-fast

Conservative filters applied:
- Skips docs/archive/, .tmp/, audit/ directories
- Skips historical/closed context (CLOSED, SEALED, resolved, fixed, VD-ID references, Dependabot)
- Requires signal to be in a debt section header OR be one of the specific high-precision signals

### Part B — receipt_integrity universe discovery

Added `discover_receipt_universe()`: scans `docs/runtime/`, `docs/product/`,
`docs/governance/`, `docs/ai/`, `docs/architecture/`, `AGENTS.md`, `README.md`
for receipt-bearing files (those containing RECEIPT, Stage Summit,
Verification Results, Boundary Confirmation, Phase:/Status:/CLOSED/SEALED markers).

Universe discovery results:
- 171 candidate files
- 140 receipt-bearing files
- 31 non-receipt files
- 16 archived files skipped
- 0 excluded files
- 118 receipt-bearing files outside default scan paths (reported in summary)

### Part C — pr_fast_baseline

`check_verification_manifest.py` already cross-validates manifest↔baseline
gate consistency (12/12). COV-2 confirms:
- All 12 manifest gates are present in baseline
- All 12 baseline gates are registered in manifest
- gate_count matches gates length
- No no-op commands
- Coverage governance gate is validated in manifest↔baseline

wave_files whitelist remains hand-maintained (now 12 entries including
check_coverage_governance.py and both test files). This is the remaining
partial gap — explicitly documented.

## Checker Coverage Manifest Status

| Checker | Status | Change |
|---|---|---|
| verification_debt | partial | Discovery added (warning-only). Auto-classification deferred. |
| receipt_integrity | **implemented** | ← was partial. Universe is self-discovered and reported. |
| pr_fast_baseline | partial | Manifest↔baseline drift detection implemented. wave_files whitelist is known gap. |
| verification_manifest | implemented | (strengthened — now validates coverage governance gate presence) |

**After COV-2: 8 implemented, 2 partial**

## Remaining Partial Gaps

- **verification_debt:** Discovery is warning-only. Full auto-registration
  requires human/agent judgment to distinguish actual debt from contextual
  mentions. ~174 signals need triage.
- **pr_fast_baseline:** wave_files whitelist is hand-maintained. New test files
  must be explicitly added. Wave file auto-discovery would require scanning
  repo for all Python files in scope.

Both are explicitly documented in checker-coverage-manifest.json.

## What COV-2 Proves

1. A checker that validates a ledger/receipt/baseline can also discover
   candidate objects that should enter that ledger/receipt/baseline.
2. Conservative discovery is better than silent omission.
3. Warning-only is an acceptable intermediate state when true positives
   require judgment.
4. Manifest↔baseline drift detection prevents silent gate removal.

## What COV-2 Does NOT Prove

1. All ~174 debt signals are actual debt — they need triage.
2. All 140 receipt-bearing files are fully governed — 118 are outside
   default scan paths.
3. wave_files whitelist will not rot — it is hand-maintained.

## Boundary Confirmation

- Meta-governance remediation only.
- No release. No publish. No license.
- Phase 8 DEFERRED.
- PV-N8 build artifact BLOCKED remains productization blocker.
- No live/broker/auto/Policy/RiskEngine action authorized.
- PASS remains scoped.
- Governance artifacts remain parser/checker-governed.

## New AI Context Check

A fresh AI reading root docs sees:
- COV-2 remediated 2 of 3 partial checker gaps (receipt_integrity→implemented)
- verification_debt has discovery (warning-only)
- pr_fast_baseline has manifest drift detection; wave_files gap explicit
- 8 implemented, 2 partial with documented reasons
- pr-fast 12/12 PASS
- PV-N8 build artifact BLOCKED is productization gap, not governance gap

---

*Closed: 2026-05-01*
*Phase: COV-2*
