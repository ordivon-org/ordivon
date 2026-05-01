# Ordivon Verify — Quickstart Example

> **Local example fixture only.** Not a public release. Not a published package.
> Ordivon is the current project identity. PFIOS/AegisOS are historical.

## What This Is

A minimal self-contained project that reaches **READY** when verified with
Ordivon Verify in standard mode. It demonstrates the three governance artifacts
and a clean receipt.

## Files

```
ordivon.verify.json          — Config (standard mode)
receipts/clean-receipt.md    — A receipt with no contradictions
governance/
  verification-debt-ledger.jsonl   — One example debt entry
  verification-gate-manifest.json  — Two gates
  document-registry.jsonl          — Two registered docs
```

## Run

```bash
uv run python scripts/ordivon_verify.py all \
  --root examples/ordivon-verify/quickstart \
  --config examples/ordivon-verify/quickstart/ordivon.verify.json
```

Expected: **READY** (exit 0). JSON output with `--json`.

## Status Semantics

- **READY** — selected checks passed. Evidence, not authorization.
- **BLOCKED** — hard failure detected. Do not claim complete.
- **DEGRADED** — no hard failures, but governance incomplete. Review needed.

## Important

- This fixture has no broker, API, or live trading behavior.
- Verify output is evidence, not execution authority.
- Coverage-aware governance: PASS is scoped to the declared universe.
- Exclusions are explicit and reasoned — silent omission is not governance.
