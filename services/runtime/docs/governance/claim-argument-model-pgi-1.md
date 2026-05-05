# Claim and Argument Model — PGI-1

Status: **CURRENT** | Date: 2026-05-03
Phase: PGI-1.02
Tags: `pgi`, `claim`, `argument`, `logic`, `false-comfort`
Authority: `source_of_truth` | AI Read Priority: 1

## Purpose

This model defines how Ordivon classifies claims before trusting them.

Core rule:

```text
A claim is not trusted because it sounds coherent, inspiring, urgent, or
strategically useful. It is trusted only to the degree that its evidence,
inference, uncertainty, and boundary are explicit.
```

## Claim Types

| Type | Question | Example risk |
|------|----------|--------------|
| factual | What happened? | A stale or invented fact enters current truth. |
| completion | Is work done? | A plan is treated as completed work. |
| authorization | May action proceed? | READY is treated as merge/deploy/execution permission. |
| value | What matters? | A preference becomes a hidden universal rule. |
| forecast | What is likely? | A confident future claim lacks base rate. |
| identity | What are we / who am I becoming? | A temporary pattern becomes a fixed verdict. |
| risk | What can go wrong? | Downside is minimized by narrative. |
| outcome | What resulted? | Good outcome is used to prove good process. |
| lesson | What should change next time? | One event becomes an overbroad rule. |

## Argument Fields

Every high-consequence claim should be reducible to:

| Field | Meaning |
|-------|---------|
| claim | The exact assertion being made. |
| claim_type | One of the claim types above. |
| premise | Starting assumptions. |
| evidence | Verifiable support. |
| inference | Why the evidence supports the claim. |
| counterevidence | Known evidence or possibility against the claim. |
| uncertainty | What remains unknown. |
| boundary | What the claim does not authorize or prove. |
| review_trigger | What would require re-checking the claim. |

## Fallacy / False-Comfort Taxonomy

| ID | Pattern | Governance response |
|----|---------|---------------------|
| narrative_substitution | A compelling story stands in for evidence. | DEGRADED until evidence is cited. |
| authority_laundering | A tool/doc/checker output is treated as permission. | BLOCKED if it claims authorization. |
| success_bias | Good outcome proves good process. | REVIEW; separate process from outcome. |
| post_hoc_proof | It worked, so the reasoning was correct. | REVIEW; identify luck/base-rate. |
| binary_framing | Either total success or no meaning. | REVIEW; restore gradient states. |
| AI_confidence_leak | Fluent AI output becomes truth. | DEGRADED until verified. |
| philosophy_rationalization | Long-termism, autonomy, or discipline hides harm. | REVIEW/BLOCKED depending on action risk. |
| certainty_without_failure_path | A claim cannot fail in stated terms. | DEGRADED until failure predicate exists. |

## Checker Seed

Seed checker:

```text
scripts/check_philosophical_claims.py
```

Current scope:

- narrative/roadmap/philosophy used as proof of completion, truth, safety,
  success, or readiness
- feeling or belief used as proof
- uncalibrated certainty language

Current non-scope:

- full argument parsing
- semantic proof checking
- broad repo-wide blocking gate
- medical, legal, financial, or therapeutic judgment

This checker is deliberately narrow. Its purpose is to catch high-signal
false-comfort language without pretending to solve argument analysis.

## Fixtures

```text
tests/fixtures/pgi_claim_argument/clean/claim.md
tests/fixtures/pgi_claim_argument/false_comfort/narrative.md
```

The clean fixture states evidence and boundaries. The false-comfort fixture
uses roadmap/philosophy/feeling as proof.

## Boundary

This model does not authorize action, activate Policy, or make all philosophical
claims machine-verifiable. It provides a first claim-classification surface for
PGI-1.

Next stage:

```text
PGI-1.03 - Evidence Ledger Model
```
