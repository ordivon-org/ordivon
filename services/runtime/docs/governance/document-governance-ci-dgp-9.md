# Document Governance CI — DGP-9

Status: **CURRENT** | Date: 2026-05-09 | Phase: DGP-9
Authority: current_status | Owner: Governance

## Command

```bash
ordivon-verify document-governance --check
```

## Exit Semantics

- `--check`: exits 0 if BLOCKED=0. DEGRADED is advisory. exits 1 if BLOCKED>0.
- `--summary`: compact status output.
- `--full`: detailed report with all DGP layers and check results.
- Default: JSON output.

## What It Checks

All 10 reconciler checks across DGP-1 through DGP-8:
- referenced-but-missing
- active-t0-t1-owner-gap
- generated-as-truth
- ledger-schema-artifact-gap
- registry-self-gap
- legacy-scope-gap
- config-surface-gap
- authority-over-elevation
- lifecycle-invariants
- authority-boundary

Plus DGP layer reporting (which governance layers are active).

## CI Integration

```bash
# In CI: hard gate
uv run python -m ordivon_verify document-governance --check || exit 1

# In PR review: summary
uv run python -m ordivon_verify document-governance --summary

# In audit: full report
uv run python -m ordivon_verify document-governance --full
```

## Non-Authorization Boundary

PASS does NOT mean merge/release/deploy authorization. It means BLOCKED=0 — no document governance hard gates are violated. DEGRADED findings are advisory operational signals.
