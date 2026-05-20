# Claim Audit Prompt

Use this prompt when asking an AI agent to audit claims in any text.

## Source Text

[Paste the text to audit here]

## Audit Instructions

For each claim in the text:
1. Extract the exact claim statement
2. Identify what evidence is PRESENT (cited data, sources, references)
3. Identify what evidence is MISSING (unverified assertions, unsupported numbers)
4. Flag overclaim (claim exceeds evidence)
5. Assign confidence: low / medium / high

## Output Format

| Claim | Evidence Present | Evidence Missing | Overclaim? | Confidence |
|-------|-----------------|------------------|------------|------------|
|       |                 |                  |            |            |

## Boundary

This is a CLAIM AUDIT, not a verdict. Claims are not declared true or false.
Missing evidence is noted; conclusions are not drawn without evidence.
