# PGI-2.05 Body and Energy Pack Seed

Status: **CLOSED** | Date: 2026-05-03
Phase: PGI-2.05
Tags: `pgi`, `runtime-evidence`, `body`, `energy`, `privacy`
Authority: `supporting_evidence` | AI Read Priority: 2

## Intent

Add a privacy-first Body/Energy Pack seed so Ordivon can prevent depleted states
from silently degrading high-consequence decisions.

## Constraints

- Does not authorize action.
- Is not medical advice.
- Does not collect intimate raw data.
- Does not turn life into body-metric optimization.

## Actions

Created:

```text
docs/governance/body-energy-pack-seed-pgi-2.md
scripts/validate_pgi_body_energy_review.py
tests/fixtures/pgi_body_energy/valid/tired-low-risk.json
tests/fixtures/pgi_body_energy/invalid/exhausted-high-risk.json
tests/fixtures/pgi_body_energy/invalid/raw-private-data.json
tests/unit/governance/test_pgi_body_energy_review.py
```

## Evidence

Expected fixture behavior:

| Fixture | Expected |
|---------|----------|
| tired low-risk local work | VALID |
| exhausted high-risk decision allowed | INVALID |
| raw private data recorded | INVALID |

## Review

PGI-2.05 is locally closed as a seed Body/Energy Pack. It keeps the governance
surface intentionally coarse: enough to protect decision quality, not enough to
become surveillance or medical authority.

## Rule Update

CandidateRule proposal:

```text
PGI-CR-014: Exhausted/ill/high-fatigue states block high-consequence decisions.
```

Status: **candidate only**. This is not Policy.

## Next Action

```text
PGI-2.06 - Finance Pack Philosophical Hardening
```
