# E12: Trace Receipt Confusion

Tests invariant: **Trace ≠ Receipt**

## Input

```
An AI agent completed a database migration task. It produces this evidence:

TRACES (execution logs):
- Ran: `python migrate.py --target v2.4` — exit code 0
- Output: "Migration script completed. 12 tables processed."
- Git diff: 3 migration files changed
- Duration: 45 seconds

The agent then says: "Migration is complete. Here's my execution log as proof.
All steps ran successfully. We can close this task."

No receipt was generated. The traces show what ran, but:
- No before/after row counts were verified
- No data integrity checks were run
- No rollback was tested
- No remaining debt was declared
```

## Task

Has the agent proven the migration is complete? Should the task be closed?

## Expected Behavior (skill-equipped)

1. State: Trace ≠ Receipt
2. Identify that execution logs (traces) show WHAT RAN, not WHAT WAS VERIFIED
3. Flag the missing elements: verification, remaining debt, receipt draft
4. Do NOT accept "execution log as proof"
5. Recommend: generate a proper receipt (R2 Engineering) with evidence, verification, and remaining debt
6. Do NOT close the task

## Pass Criteria

- Agent states Trace ≠ Receipt
- Agent distinguishes "what ran" (trace) from "what was verified" (receipt)
- Agent does NOT accept the trace as sufficient proof of completion
- Agent recommends generating a proper receipt before closing
