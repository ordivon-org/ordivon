# Reconciliation Workflow

Triggers governance reconciliation: validate registry, update coverage, generate views, run verification.

**Workflow ID:** `ordivon-reconciliation`
**Runtime:** Temporal (worker: `src/ordivon_governance_core/temporal_worker.py`)
**Local fallback:** Runs activities synchronously when Temporal unavailable
**Trigger:** `trigger_reconciliation("full")` or `trigger_reconciliation("registry_changed")`

## Steps (DAG)

```
validate_registry
    ↓
update_coverage_boundary
    ↓
update_path_map
    ↓
reconcile_registry_path (can_fail)
    ↓
generate_wiki
    ↓
ordivon_verify (can_fail)

detect_overclaim (parallel, can_fail)
```

## Activities

| Step | Activity | Script | M-Level | Description |
|------|----------|--------|---------|-------------|
| validate_registry | activity_validate_registry | scripts/check_document_registry.py | M1 | Validate registry consistency |
| update_coverage_boundary | activity_update_coverage_boundary | scripts/update-coverage-boundary.py | M3 | Update coverage from registry |
| update_path_map | activity_update_path_map | scripts/update-path-map.py | M3 | Regenerate path map |
| reconcile_registry_path | activity_reconcile_registry_path | scripts/reconcile-registry-path.py | M3 | Reconcile claims vs observations |
| generate_wiki | activity_generate_wiki | scripts/generate_document_wiki.py | M3 | Regenerate wiki index |
| ordivon_verify | activity_ordivon_verify | ordivon_verify CLI | M1 | Full governance verification |
| detect_overclaim | activity_detect_overclaim | scripts/detect_overclaim.py | M1 | Check receipts for overclaim |

## Output

- Activity results (status, exit_code, duration, error)
- NATS event published to `ordivon.observation.reconcile_executed`
- Trace captured to `traces/reconciliation/`

## Authority

- May run M1-M3 activities automatically
- M5 activities excluded from this workflow
- Results are advisory — does not authorize state changes

## Receipt

After completion, generate R4 Governance Receipt with:
- Workflow status (PASS/DEGRADED/BLOCKED)
- Per-step results
- Remaining debt from reconciliation findings
