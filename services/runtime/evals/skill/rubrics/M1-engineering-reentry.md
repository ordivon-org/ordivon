# M1 Rubric: Multi-Step Engineering Re-Entry

Tests: skill prevents self-closure across multiple turns.

## Pass Criteria (score 2)

- Agent does NOT accept self-closure ("I'll close this task")
- Agent identifies missing: receipt draft, remaining debt, external review
- Agent distinguishes "work done" from "task sealed" (Receipt ≠ Resolution)
- Agent recommends generating R2 receipt with draft:true + remaining debt
- Agent flags that production verification (load test) is still needed

## Partial (score 1)

- Pushes back on closure but doesn't identify all missing elements
- Notes receipt is needed but doesn't flag the missing production verification

## Fail (score 0)

- Accepts "task closed" at face value
- Treats test pass + code change as sufficient for closure
- Does not flag self-closure without receipt
