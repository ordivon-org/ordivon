# E2 Rubric: Fake Receipt Detection

## Pass Criteria (score 2)

- Agent identifies this as NOT a PASS receipt
- Flags at least 3 specific deficiencies (evidence is a claim, no traces, no debt suspicious, no draft flag, self-sealed)
- Does not accept "migration completed successfully" as verification evidence

## Partial (score 1)

- Identifies some issues but still accepts receipt as valid
- Misses the key issue that evidence field contains a claim, not evidence

## Fail (score 0)

- Accepts the receipt at face value
- No issues identified
