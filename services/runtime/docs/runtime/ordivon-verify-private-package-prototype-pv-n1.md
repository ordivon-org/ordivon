# PV-N1 — Private Package Prototype Closure

## Purpose

PV-N1 proves that Ordivon Verify can be reshaped from a 711-line monolith script into a modular Python package structure without changing behavior, exposing private core, publishing anything, or weakening verified semantics.

## What Changed

The 711-line `scripts/ordivon_verify.py` was decomposed into `src/ordivon_verify/`:

```
src/ordivon_verify/
  __init__.py          # Public API (explicit re-exports)
  __main__.py          # python -m entrypoint
  cli.py               # argparse + main() + parse_args()
  config.py            # load_config / validate_config / is_ordivon_native
  report.py            # determine_status / build_report / print_human / status_to_exit_code
  runner.py            # run_check / run_external_receipts / run_external_checker
  checks/
    __init__.py
    receipts.py        # scan_receipt_files
    debt.py            # validate_debt_ledger
    gates.py           # validate_gate_manifest
    docs.py            # validate_document_registry
```

`scripts/ordivon_verify.py` → thin 24-line wrapper:
```python
from ordivon_verify.cli import main
import sys
sys.exit(main())
```

`pyproject.toml` updated to add `src/` to `pythonpath` for test imports.

## Compatibility Guarantee

Existing commands all work identically:
- `uv run python scripts/ordivon_verify.py all` → READY
- `uv run python scripts/ordivon_verify.py all --json` → READY JSON
- `PYTHONPATH=./src uv run python -m ordivon_verify all` → READY (new)

All external fixture modes preserved.

## Behavior Preservation Matrix

| Fixture | Expected Status | Exit Code | Result |
|---------|----------------|-----------|--------|
| Native Ordivon | READY | 0 | PASS |
| Standard external | READY | 0 | PASS |
| Clean advisory | DEGRADED | 2 | PASS |
| Bad external | BLOCKED | 1 | PASS |
| JSON schema | Compatible with PV-4/PV-8/PV-9 | — | PASS |
| No file writes | All mtimes unchanged | — | PASS |
| No shell injection | No shell=True | — | PASS |
| No network | No remote imports | — | PASS |

## What PV-N1 Proves

1. Ordivon Verify's architecture is cleanly decomposable — logic separated by concern.
2. Script wrapper backward compatibility is trivially maintained.
3. `python -m` entrypoint works when `src/` is on PYTHONPATH.
4. Package does not need to import private core modules (finance/broker/RiskEngine).
5. Running the external checker through the package produces identical results to the script.
6. Tests can import from the package directly, enabling finer-grained unit testing.

## What PV-N1 Does NOT Prove

1. The package is NOT installed (no `pip install`, no pyproject [project] section).
2. The package is NOT published (no PyPI, no public repo).
3. No license is activated.
4. No CI workflow is modified or added.
5. Does not prove the package works outside the Ordivon repo context.
6. Does not implement public schemas — this is a private prototype.
7. `python -m ordivon_verify` requires manual PYTHONPATH for now.

## Boundary Confirmation

- Private package prototype only
- No public release
- No repo visibility change
- No license activation
- No package publishing
- No active CI change
- No SaaS
- No MCP server
- No broker/API
- No paper/live order
- No Policy activation
- No RiskEngine activation
- CLI remains read-only
- No file writes by Verify
- READY does not authorize execution
- Phase 8 remains DEFERRED
- Core never imports Pack/domain nouns
- Package does not import adapters.finance or domains.finance

## Verification Results

All checks passed:
- Product tests: 111/111
- Governance tests: 192/192
- Finance regression: 188/188
- Frontend test: 57/57
- Frontend build: static output clean
- Eval corpus: 24/24
- pr-fast: 11/11 PASS
- Architecture boundary: clean
- Runtime evidence: clean
- Existing checkers: all 5 pass
- External ladder: standard READY, clean DEGRADED, bad BLOCKED
- Ruff check: clean (src, scripts, tests, docs)
- Ruff format: all files formatted
- Import boundary: no finance/broker imports in src/ordivon_verify
- No file modifications by Verify: confirmed

## Next Recommended Phase

PV-N2: Public schema extraction — define and validate the public-facing JSON schema without activating publishing infrastructure.

---

Closed: 2026-05-01
Phase: PV-N1
Task type: code-implementation / private package extraction prototype
Risk level: R0/R1 read-only local tooling
