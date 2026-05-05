# PGI-3.06 AI Collaborator Philosophical Onboarding

Status: **CLOSED** | Date: 2026-05-04
Phase: PGI-3.06
Tags: `pgi`, `runtime-evidence`, `ai-onboarding`, `philosophy`
Authority: `supporting_evidence` | AI Read Priority: 2

## Intent

Add an AI philosophical onboarding addendum so AI collaborators can use
Ordivon's philosophical layer without turning it into vague motivation, false
certainty, authority overreach, therapy, financial advice, or action approval.

## Constraints

- Does not authorize action.
- Does not turn AI into an authority over the creator.
- Does not grant therapy or financial-advice posture.
- Does not activate Policy.

## Actions

Created:

```text
docs/ai/philosophical-onboarding-addendum-pgi-3.md
scripts/validate_pgi_ai_philosophical_onboarding.py
tests/fixtures/pgi_ai_onboarding/valid/collaborator.json
tests/fixtures/pgi_ai_onboarding/invalid/authority-overreach.json
tests/fixtures/pgi_ai_onboarding/invalid/missing-boundaries.json
tests/unit/governance/test_pgi_ai_philosophical_onboarding.py
```

## Evidence

Expected fixture behavior:

| Fixture | Expected |
|---------|----------|
| collaborator onboarding | VALID |
| authority overreach | INVALID |
| missing boundaries | INVALID |

## Review

PGI-3.06 is locally closed as an AI onboarding boundary. It makes AI
collaboration warmer and more useful while keeping authority with the human and
evidence with the system.

## Rule Update

CandidateRule proposal:

```text
PGI-CR-024: AI philosophical outputs must preserve non-authorization, non-therapy,
non-financial-advice, CandidateRule-not-Policy, privacy, and human-agency boundaries.
```

Status: **candidate only**. This is not Policy.

## Next Action

```text
PGI-3.07 - Extended Mind Tooling Map
```
