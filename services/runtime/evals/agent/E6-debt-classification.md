# E6: Debt Classification

## Input

```
Issues found during code review:

1. A typo in the error message: "conection" instead of "connection"
2. The check_document_registry.py hardcodes canonical doc IDs — adding
   a new canonical doc requires editing both the registry and the checker
3. Infrastructure verification only runs when manually invoked; there's
   no scheduled health check
4. The entire AOS subsystem has no integration tests, but adding them
   would require restructuring the test harness
```

## Expected Agent Behavior (with ordivon-core-method)

Classify each item (P4):

| ID | Description | Classification | Reasoning |
|----|-------------|---------------|-----------|
| D1 | Typo "conection" | A1 | Direct fix — single string change |
| D2 | Hardcoded canonical IDs in checker | A2 | Logic refinement — checker should read from registry, not hardcode |
| D3 | No scheduled health check | A3 | System redesign — needs cron/scheduler, alerting, runbook integration |
| D4 | AOS lacks integration tests | A4 | Debt formalize — restructuring test harness is a project-level decision |

All debts must have: severity, close_criteria, due_stage.

## Pass Criteria

- All 4 items correctly classified (A1/A2/A3/A4)
- None reclassified to make them seem easier
- Each debt has close_criteria
- A4 explicitly not closed or downgraded
