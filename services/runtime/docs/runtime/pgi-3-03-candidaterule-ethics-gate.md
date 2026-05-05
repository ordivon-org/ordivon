# PGI-3.03 CandidateRule Ethics Gate

Status: **CLOSED** | Date: 2026-05-04
Phase: PGI-3.03
Tags: `pgi`, `runtime-evidence`, `candidate-rule`, `ethics`
Authority: `supporting_evidence` | AI Read Priority: 2

## Intent

Add an ethics gate for CandidateRule proposals so Ordivon can learn without
over-controlling life or silently activating Policy.

## Constraints

- Does not activate Policy.
- Does not authorize action.
- Does not allow control obsession to hide as governance.
- Does not remove exception/review paths.

## Actions

Created:

```text
docs/governance/candidaterule-ethics-gate-pgi-3.md
scripts/validate_pgi_candidate_rule_ethics.py
tests/fixtures/pgi_candidate_rule_ethics/valid/scoped-rule.json
tests/fixtures/pgi_candidate_rule_ethics/invalid/over-control.json
tests/fixtures/pgi_candidate_rule_ethics/invalid/policy-activation.json
tests/unit/governance/test_pgi_candidate_rule_ethics.py
```

## Evidence

Expected fixture behavior:

| Fixture | Expected |
|---------|----------|
| scoped rule | VALID |
| over-control rule | INVALID |
| policy activation | INVALID |

## Review

PGI-3.03 is locally closed as a seed CandidateRule ethics gate. It adds human
cost and exception-path pressure before rules can even remain candidate.

## Rule Update

CandidateRule proposal:

```text
PGI-CR-021: CandidateRules require ethics review for consequences, boundaries,
virtues, false positives, human cost, exception path, and expiry/review date.
```

Status: **candidate only**. This is not Policy.

## Next Action

```text
PGI-3.04 - Personal Casebook
```
