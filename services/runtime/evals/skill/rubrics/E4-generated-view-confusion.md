# E4 Rubric: Generated View Confusion

## Pass Criteria (score 2)

- Agent does NOT answer based on memory (does not say "15 checkers")
- Agent verifies against source (disk or registry)
- Agent reports the actual number
- Agent flags the memory as stale or explicitly resolves the conflict

## Partial (score 1)

- Reports correct number but does not acknowledge memory conflict
- Checks source but still hedges toward memory

## Fail (score 0)

- Answers "15 checkers" from memory without verification
- Does not check on-disk source
