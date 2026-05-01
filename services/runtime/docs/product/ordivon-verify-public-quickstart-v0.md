# Ordivon Verify — Quickstart

> **v0 prototype.** Local-first. Read-only. Not a public release. Not production-ready.
> **READY is evidence, not authorization.**

## What You'll Do

Run Ordivon Verify locally on a minimal example project. See READY. Then see
DEGRADED and BLOCKED on fixtures with incomplete or broken governance.

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- This repository cloned locally
- No broker, API key, or network access required

## 1. Native Mode

Verify Ordivon itself:

```bash
uv run python scripts/ordivon_verify.py all
```

Expected: **READY** (exit 0).

JSON output:

```bash
uv run python scripts/ordivon_verify.py all --json
```

## 2. Package Module Mode

```bash
uv run python -m ordivon_verify all
```

Expected: **READY**.

## 3. Quickstart Example

A minimal project with clean governance:

```bash
uv run python scripts/ordivon_verify.py all \
  --root examples/ordivon-verify/quickstart \
  --config examples/ordivon-verify/quickstart/ordivon.verify.json
```

Expected: **READY**.

## 4. Clean Advisory Fixture

A project that passes its receipt check but is missing most governance files:

```bash
uv run python scripts/ordivon_verify.py all \
  --root tests/fixtures/ordivon_verify_clean_external_repo \
  --config tests/fixtures/ordivon_verify_clean_external_repo/ordivon.verify.json
```

Expected: **DEGRADED** (exit 2). No hard failures, but governance incomplete.

## 5. Bad External Fixture

A project with a contradictory receipt:

```bash
uv run python scripts/ordivon_verify.py all \
  --root tests/fixtures/ordivon_verify_external_repo \
  --config tests/fixtures/ordivon_verify_external_repo/ordivon.verify.json
```

Expected: **BLOCKED** (exit 1). The receipt claims verification was skipped
but the checker found evidence of gate omissions.

## Status Interpretation

| Status | Meaning |
|--------|---------|
| **BLOCKED** | Hard failure detected. Do not claim complete. Fix the issue. |
| **DEGRADED** | No hard failure, but governance incomplete or review needed. An honest midpoint. |
| **READY** | Selected checks passed. Evidence — NOT authorization. Does not approve execution. |

## Minimal Config

`ordivon.verify.json`:

```json
{
  "schema_version": "0.1",
  "project_name": "my-project",
  "mode": "standard",
  "receipt_paths": ["receipts"],
  "debt_ledger": "governance/verification-debt-ledger.jsonl",
  "gate_manifest": "governance/verification-gate-manifest.json",
  "document_registry": "governance/document-registry.jsonl"
}
```

## Minimal Governance Files

- `verification-debt-ledger.jsonl` — Registered verification debt. Empty file = no debt (valid).
- `verification-gate-manifest.json` — Gates that must pass. No no-op commands.
- `document-registry.jsonl` — Governed documents with status, authority, freshness.

See `examples/ordivon-verify/quickstart/governance/` for example files.

## Schemas

Prototype schemas in `src/ordivon_verify/schemas/`:

- `ordivon.verify.schema.json` — Config schema
- `trust-report.schema.json` — JSON report schema
- `verification-debt-ledger.schema.json` — Debt entry schema
- `verification-gate-manifest.schema.json` — Gate manifest schema
- `document-registry.schema.json` — Registry entry schema

**Not a stable public contract yet.** Schema version 0.1. Prototype only.

## Coverage-Aware Governance

Ordivon Verify now checks not just registered items, but whether all relevant
items are registered:

- **PASS is scoped.** Every PASS declares its coverage universe.
- **Coverage precedes confidence.** You cannot trust a check without knowing
  what it checked.
- **Silent omission is not governance.** Every exclusion must be explicit
  and reasoned.
- **Identity-bearing surfaces are governance-relevant.** Package names,
  README headers, and config identities are checked.

See `docs/architecture/ordivon-coverage-plane.md`.

## Common Mistakes

| Mistake | Reality |
|---------|---------|
| Treating READY as approval | READY is evidence, not authorization |
| Treating BLOCKED as tool failure | BLOCKED is governance success — it caught a real problem |
| Hiding DEGRADED warnings | DEGRADED is honest. Fix it, don't hide it |
| Using strict mode before governance files exist | Start in advisory, graduate to standard, then strict |
| Assuming Verify replaces tests | Verify checks claims, not code correctness |
| Assuming public release has happened | This is a v0 prototype |
| Assuming schemas are stable | Schema version 0.1 — pre-stability |
| Assuming Verify authorizes action | Verify never authorizes — it only reports evidence |

## Next Steps

- **Agent skill:** `skills/ordivon-verify/SKILL.md` — teach AI agents to use Verify
- **CI example:** `examples/ordivon-verify/github-action.yml.example` — run in CI
- **Package install:** Future — `pip install ordivon-verify` (not yet available)
- **Public release:** Future — when governance gates are met
