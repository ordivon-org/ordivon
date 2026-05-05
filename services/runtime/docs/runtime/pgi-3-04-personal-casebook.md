# PGI-3.04 Personal Casebook

Status: **CLOSED** | Date: 2026-05-04
Phase: PGI-3.04
Tags: `pgi`, `runtime-evidence`, `casebook`, `privacy`
Authority: `supporting_evidence` | AI Read Priority: 2

## Intent

Add a PersonalCaseEntry object so Ordivon can preserve useful cases without
collapsing private experience into publishable content.

## Constraints

- Does not authorize action.
- Does not approve publication.
- Does not store raw private data.
- Does not treat every life event as a case.

## Actions

Created:

```text
docs/governance/personal-casebook-pgi-3.md
scripts/validate_pgi_personal_case_entry.py
tests/fixtures/pgi_personal_case/valid/builder-case.json
tests/fixtures/pgi_personal_case/invalid/private-externalized.json
tests/fixtures/pgi_personal_case/invalid/no-artifacts.json
tests/unit/governance/test_pgi_personal_case_entry.py
```

## Evidence

Expected fixture behavior:

| Fixture | Expected |
|---------|----------|
| builder case | VALID |
| private externalized | INVALID |
| no artifacts | INVALID |

## Review

PGI-3.04 is locally closed as a seed Personal Casebook. It creates a safe bridge
from personal dogfood to future public examples without treating that bridge as
publication approval.

## Rule Update

CandidateRule proposal:

```text
PGI-CR-022: Personal cases require artifact refs, review refs, privacy level,
and separate externalization approval before public use.
```

Status: **candidate only**. This is not Policy.

## Next Action

```text
PGI-3.05 - Memory and Content Hygiene
```
