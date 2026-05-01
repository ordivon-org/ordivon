# PV-N4 — Private Package Install Smoke

## Purpose

Validate that Ordivon Verify can be installed and executed as a private
package-shaped tool with console entrypoint, without publishing anything.

## What Package Install Smoke Means

- **Private:** The package is installed in a local/editable context only.
- **Smoke:** A lightweight integration check that all entrypoints work and
  the trust ladder is preserved.
- **Not publishing:** No PyPI, no public repo, no license activation.

## What Changed

- `pyproject.toml`: added `ordivon-verify` console entrypoint (private prototype),
  `where = [".", "src"]` for package discovery, `ordivon_verify*` in find.include.
- `scripts/smoke_ordivon_verify_private_install.py`: 7-check smoke script.
- `tests/unit/product/test_ordivon_verify_private_install.py`: 16 tests.

## Entrypoints Tested

| Entrypoint | Command | Result |
|-----------|---------|--------|
| Script wrapper | `python scripts/ordivon_verify.py all` | READY |
| Module | `python -m ordivon_verify all` | READY |
| Console | `uv run ordivon-verify all` | READY |
| Console JSON | `uv run ordivon-verify all --json` | READY |

## Private Install Smoke Result

```
7/7 checks pass:
  1. Package imports        ✅
  2. Module entrypoint      ✅
  3. Console entrypoint     ✅
  4. Script wrapper         ✅
  5. Quickstart fixture     ✅
  6. Bad external fixture   ✅
  7. Package boundary       ✅
```

## Behavior Preservation Matrix

| Scenario | Expected | Result |
|----------|----------|--------|
| Native script | READY | PASS |
| Native module | READY | PASS |
| Console script | READY | PASS |
| Quickstart example | READY | PASS |
| Standard external | READY | PASS |
| Clean advisory | DEGRADED | PASS |
| Bad external | BLOCKED | PASS |
| Product schemas | valid | PASS |
| Coverage checker | 0 violations | PASS |
| Package boundary | no broker imports | PASS |

## What PV-N4 Proves

1. Ordivon Verify can be installed as an editable package with console entrypoint.
2. All three entrypoints (script, module, console) preserve trust semantics.
3. Quickstart and external fixtures remain unchanged.
4. Package source has zero broker/finance/RiskEngine imports.
5. Private package structure is ready for future public extraction.

## What PV-N4 Does NOT Prove

- No public release, package publishing, or license activation.
- No PyPI/npm upload, no marketplace action.
- No production readiness.
- No external user validation.
- No Phase 8 readiness.

## Boundary Confirmation

- Private install smoke only
- No public release / public repo / license activation / package publishing
- No CI change / SaaS / MCP server
- No broker/API / paper/live order / Policy/RiskEngine activation
- READY does not authorize execution
- Phase 8 remains DEFERRED

## Next Recommended Phase

PV-N5 — Release Readiness Audit

---

*Closed: 2026-05-01*
*Phase: PV-N4*
*Task type: code/docs implementation + private packaging smoke*
*Risk level: R1*
