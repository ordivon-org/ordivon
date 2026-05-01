# Ordivon Verify

> **v0 prototype.** Not a public release. Not production-ready.
> READY is evidence, not authorization.

Ordivon Verify checks whether AI/agent work can be trusted. It validates
receipts, debt, gates, and documents — locally, read-only, with no API keys
or network access required.

## Quickstart

```bash
pip install ordivon-verify  # not yet available — local prototype
ordivon-verify all
```

Or run the quickstart example:

```bash
ordivon-verify all --root examples/quickstart --config examples/quickstart/ordivon.verify.json
```

## Status Semantics

| Status | Meaning |
|--------|---------|
| READY | Selected checks passed. Evidence, not authorization. |
| BLOCKED | Hard failure detected. Do not claim complete. |
| DEGRADED | Governance incomplete. Review needed. |

## License

Apache-2.0 (proposed, not yet activated).

This is a local dry-run extraction for testing. Not a published package.
