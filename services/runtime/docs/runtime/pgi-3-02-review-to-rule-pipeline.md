# PGI-3.02 Review-to-Rule Pipeline

Status: **CLOSED** | Date: 2026-05-04
Phase: PGI-3.02
Tags: `pgi`, `runtime-evidence`, `review-to-rule`, `candidate-rule`
Authority: `supporting_evidence` | AI Read Priority: 2

## Intent

Add a ReviewToRuleCandidate object so Ordivon can turn repeated experience into
advisory CandidateRules without letting anecdotes, emotion, or control impulses
become law.

## Constraints

- Does not activate Policy.
- Does not authorize action.
- Does not turn single events into universal rules.
- Does not allow high emotion to legislate without cool-down review.

## Actions

Created:

```text
docs/governance/review-to-rule-pipeline-pgi-3.md
scripts/validate_pgi_review_to_rule_candidate.py
tests/fixtures/pgi_review_to_rule/valid/multiple-examples.json
tests/fixtures/pgi_review_to_rule/invalid/single-anecdote-candidate.json
tests/fixtures/pgi_review_to_rule/invalid/emotional-policy.json
tests/unit/governance/test_pgi_review_to_rule_candidate.py
```

## Evidence

Expected fixture behavior:

| Fixture | Expected |
|---------|----------|
| multiple examples candidate | VALID |
| single anecdote candidate | INVALID |
| emotional policy activation | INVALID |

## Review

PGI-3.02 is locally closed as a seed review-to-rule pipeline. It preserves the
Ordivon learning loop while keeping rules reversible, scoped, and advisory.

## Rule Update

CandidateRule proposal:

```text
PGI-CR-020: Experience can become CandidateRule only through multiple examples
or high-severity rationale, cool-down review when needed, and a retirement path.
```

Status: **candidate only**. This is not Policy.

## Next Action

```text
PGI-3.03 - CandidateRule Ethics Gate
```
