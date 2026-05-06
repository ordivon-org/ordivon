# Ordivon Verify — AI Coding Trust Audit Dogfood

> Local examples only. Not a public release, standard, certification, or
> production-readiness claim.

These fixtures demonstrate the product wedge:

```text
CI verifies code. Ordivon verifies claims.
```

## Cases

| Case | Expected | Why |
|---|---|---|
| `clean-ai-task` | READY_WITHOUT_AUTHORIZATION | Receipt, test command evidence, review note, debt, gates, and docs are present. |
| `false-comfort-ai-task` | BLOCKED | The receipt claims local test success without reproducible command evidence. |
| `realistic-degraded-task` | DEGRADED | Receipt is clean, but debt/gates/docs are intentionally missing. |

## Run

```bash
uv run python scripts/ordivon_verify.py check examples/ordivon-verify/dogfood/clean-ai-task --config examples/ordivon-verify/dogfood/clean-ai-task/ordivon.verify.json --markdown
uv run python scripts/ordivon_verify.py check examples/ordivon-verify/dogfood/false-comfort-ai-task --config examples/ordivon-verify/dogfood/false-comfort-ai-task/ordivon.verify.json --markdown
uv run python scripts/ordivon_verify.py check examples/ordivon-verify/dogfood/realistic-degraded-task --config examples/ordivon-verify/dogfood/realistic-degraded-task/ordivon.verify.json --markdown
```

`READY` is evidence only. It does not authorize merge, deployment, release,
execution, trading, policy activation, token refresh, or external action.
