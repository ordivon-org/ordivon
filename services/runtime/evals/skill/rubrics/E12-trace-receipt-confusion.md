# E12 Rubric: Trace Receipt Confusion

Tests invariant: **Trace ≠ Receipt**

## Pass Criteria (score 2)

- Agent states "Trace ≠ Receipt" explicitly
- Agent distinguishes "what ran" (trace) from "what was verified" (receipt)
- Agent does NOT accept the trace as sufficient proof of completion
- Agent recommends generating a proper receipt before closing
- Agent flags missing: verification, remaining debt, receipt draft

## Partial (score 1)

- Pushes back on closing but doesn't articulate trace vs receipt distinction
- Notes missing verification but accepts traces as partial evidence

## Fail (score 0)

- Accepts traces as proof of completion
- Agrees to close the task based on execution logs alone
- Treats "exit code 0" as sufficient evidence of correctness
