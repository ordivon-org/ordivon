# PGI-1.02 Claim and Argument Model

Status: **CLOSED** | Date: 2026-05-03
Phase: PGI-1.02
Tags: `pgi`, `runtime-evidence`, `claim`, `argument`, `checker`
Authority: `supporting_evidence` | AI Read Priority: 2

## Intent

Turn the "does this claim actually follow?" part of the Philosophical
Governance Layer into an explicit Ordivon model and a narrow local checker.

## Constraints

- Local static scanning only.
- Findings are review evidence, not authorization.
- No broad CI gate added yet.
- No claim that argument analysis is complete.

## Actions

Created:

```text
docs/governance/claim-argument-model-pgi-1.md
scripts/check_philosophical_claims.py
tests/fixtures/pgi_claim_argument/clean/claim.md
tests/fixtures/pgi_claim_argument/false_comfort/narrative.md
tests/unit/governance/test_pgi_claim_checker.py
```

Updated:

```text
docs/governance/philosophical-governance-gap-ledger.jsonl
```

## Evidence

Checker scope:

- narrative/roadmap/philosophy used as proof
- feeling/belief used as proof
- uncalibrated certainty language

Expected fixture behavior:

| Fixture | Expected |
|---------|----------|
| clean claim | 0 findings |
| false comfort | BLOCKING findings |

## Review

PGI-1.02 is locally closed as a seed implementation. It does not solve natural
language argument analysis; it creates a bounded taxonomy, a false-comfort
checker, and regression fixtures. This is enough to prevent PGI from relying on
beautiful philosophical language without object-level evidence.

## Rule Update

CandidateRule proposal:

```text
PGI-CR-002: A roadmap, philosophy statement, or feeling cannot prove completion,
safety, correctness, or readiness. Such claims require explicit evidence,
uncertainty, and boundary language.
```

Status: **candidate only**. This is not Policy.

## Next Action

```text
PGI-1.03 - Evidence Ledger Model
```
