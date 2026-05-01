# Ordivon Verify — GitHub Action Example

This directory contains an **example** GitHub Actions workflow for Ordivon Verify. It is **not active CI** — copy and adapt it for your own repository.

## Files

- `github-action.yml.example` — Example PR workflow that runs Ordivon Verify on pull requests.

## What It Checks

Ordivon Verify checks whether AI/agent-generated completion claims are honest:

- **Receipt integrity** — no "sealed" with pending checks, no "skipped: none" with gaps
- **Verification debt** — all debt registered, no overdue, no hidden skipped verification
- **Gate manifest** — baseline gates match manifest, no silent removal or downgrade
- **Document registry** — docs registered, no stale, no dangerous semantic phrases

## Exit Codes

| Code | Status | Meaning |
|------|--------|---------|
| 0 | READY | Selected checks passed. Does NOT authorize merge or execution. |
| 1 | BLOCKED | Hard failure detected. Should block merge until fixed. |
| 2 | DEGRADED | Warnings present. Human review required before merge. |
| 3 | Config error | Fix `ordivon.verify.json`. |
| 4 | Runtime error | Investigate tooling issue. |

## PR Policy

| Verify Result | Merge Policy |
|--------------|-------------|
| READY | Allowed, but reviewer still responsible. Not auto-merge. |
| BLOCKED | **Blocked.** Hard failure must be resolved. |
| DEGRADED | Allowed only with human review approval. |
| Error (3-4) | Blocked. Fix config/tooling. |

## Adoption

1. **Advisory mode** — Start here. Run manually. Fix contradictions.
2. **Add governance files** — debt ledger, gate manifest, document registry.
3. **Standard mode** — Switch when governance files exist and receipts are clean.
4. **CI integration** — Wire as PR check. BLOCKED blocks merge. DEGRADED requires review.

See `docs/product/ordivon-verify-adoption-guide.md` for full guidance.
