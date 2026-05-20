# Governance Verification Workflow

Runs all advisory checkers and reports findings. Does NOT block — this is a verification workflow, not an enforcement gate.

**Workflow ID:** `ordivon-governance-verify`
**Runtime:** CLI (`ordivon-verify all --check`) or Temporal
**Trigger:** Manual, scheduled, or post-reconciliation

## Steps (parallel)

```
skill-safety-checker      (advisory, exit 0)
receipt-integrity-checker  (advisory, exit 0)
mcp-permissions-checker    (advisory, exit 0)
document-registry-checker  (advisory, exit 0)
```

## Activities

| Step | Checker | Permission | Description |
|------|---------|------------|-------------|
| skill_safety | checkers/skill-safety/run.py | M1 | OPA-powered skill boundary check |
| receipt_integrity | checkers/receipt-integrity/run.py | M1 | Receipt honesty check |
| mcp_permissions | checkers/mcp-permissions/run.py | M1 | MCP tool permission check |
| document_registry | scripts/check_document_registry.py | M1 | Registry consistency check |

## Output

- Per-checker findings (severity, finding_id, description)
- Overall status: BLOCKED=0, DEGRADED=0
- Trace captured to `traces/checker-run/`

## Invariant

```
Checker ≠ Policy
Advisory ≠ Blocking
Warning ≠ Closure
```

This workflow reports findings. It does NOT authorize, block, or close.
