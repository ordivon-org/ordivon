# PGI-1.08 Ethical Triad Review

Status: **CLOSED** | Date: 2026-05-03
Phase: PGI-1.08
Tags: `pgi`, `runtime-evidence`, `ethics`, `review`
Authority: `supporting_evidence` | AI Read Priority: 2

## Intent

Create a review object that checks consequences, rules, and character before
high-consequence action.

## Constraints

- Does not authorize action.
- Does not replace human judgment.
- Does not reduce ethics to a formula.
- Does not activate Policy.

## Actions

Created:

```text
docs/governance/ethical-triad-review-model-pgi-1.md
scripts/validate_pgi_ethical_triad_review.py
tests/fixtures/pgi_ethical_triad/valid/review.json
tests/fixtures/pgi_ethical_triad/invalid/outcome-proves-process.json
tests/fixtures/pgi_ethical_triad/invalid/missing-character.json
tests/unit/governance/test_pgi_ethical_triad_review.py
```

Updated:

```text
docs/governance/philosophical-governance-gap-ledger.jsonl
```

## Evidence

Expected fixture behavior:

| Fixture | Expected |
|---------|----------|
| valid ethical triad | VALID |
| good outcome proves good process | INVALID |
| missing character/tradeoff/boundary | INVALID |

## Review

PGI-1.08 is locally closed as a seed ethical review model. It creates a
validator-backed object that future DecisionGate and Pack reviews can reuse.

## Rule Update

CandidateRule proposal:

```text
PGI-CR-008: A high-consequence review must include consequence, rule, and
character lenses. Good outcome cannot prove good process.
```

Status: **candidate only**. This is not Policy.

## Next Action

```text
PGI-1.09 - Philosophical Red-Team Suite
```
