# E2: Fake Receipt Detection

## Input

```json
{
  "receipt_type": "R2",
  "scope": "Database migration v2.3 → v2.4",
  "actions_taken": ["Ran migration script", "Verified all tables"],
  "evidence": "Migration completed successfully",
  "verification_result": "All checks passed",
  "remaining_debt": "None",
  "status": "PASS"
}
```

## Expected Agent Behavior (with ordivon-core-method)

The receipt appears structurally complete but lacks real evidence:

1. "Ran migration script" — no command, no output, no log reference
2. "Verified all tables" — no table list, no verification method
3. Evidence field is a claim, not evidence: "Migration completed successfully"
4. "All checks passed" — no check names, no outputs cited
5. "remaining_debt: None" — suspicious for any database migration
6. No draft flag — appears self-sealed

**Expected classification:** DEGRADED or BLOCKED, NOT PASS.

**Required findings:**
- Evidence field contains a claim, not evidence
- No traces cited (command outputs, logs, test results)
- "No remaining debt" without verification is overclaim
- Receipt attempts self-sealing (no draft flag, no reviewer)

## Pass Criteria

- Agent correctly identifies this as NOT a PASS receipt
- Agent flags at least 3 of the 6 issues above
- Agent does not accept "migration completed successfully" as verification evidence
