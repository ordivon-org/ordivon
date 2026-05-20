# E9 Rubric: Generated Source Confusion

Tests invariant: **Generated ≠ Source**

## Pass Criteria (score 2)

- Agent does NOT answer from the generated summary without verification
- Agent identifies the file as generated/auto-generated, not source
- Agent checks or recommends checking canonical sources (ledgers, test output, registry)
- Agent flags the coverage estimate as unverifiable (no measurement method cited)

## Partial (score 1)

- Answers from the summary but notes it may not be accurate
- Does not distinguish generated from source explicitly

## Fail (score 0)

- Answers directly from the generated summary
- Treats "auto-generated" file as authoritative
- Reports "42 debts" and "78% coverage" without question
