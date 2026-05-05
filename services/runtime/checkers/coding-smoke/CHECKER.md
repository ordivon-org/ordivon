---
gate_id: coding_smoke
display_name: Coding Governance Smoke
layer: L5C
hardness: hard
purpose: Verify the Coding Pack governance CLI produces correct decisions — valid input → execute, forbidden input → reject
protects_against: "CodingDisciplinePolicy regression, RiskEngine integration failure, reject→execute false negative"
profiles: ['pr-fast', 'full']
timeout: 30
tags: [coding, governance, smoke, cli]
---

# Coding Governance Smoke Checker

## Purpose

Exercises the Coding Pack's governance pipeline end-to-end:
`repo_governance_cli.py → classify_repo_intent() → RiskEngine → CodingDisciplinePolicy`

Two smoke tests:
1. **Valid input** (fix test naming, low impact) → must return `execute`
2. **Forbidden input** (modify .env) → must return `reject`

## Why This Matters

This is the only checker that tests the **runtime governance decision pipeline**,
not static document analysis. If CodingDisciplinePolicy breaks, if RiskEngine
integration fails, or if the CLI regresses, this checker catches it.
