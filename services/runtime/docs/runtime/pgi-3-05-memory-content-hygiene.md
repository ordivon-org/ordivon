# PGI-3.05 Memory and Content Hygiene

Status: **CLOSED** | Date: 2026-05-04
Phase: PGI-3.05
Tags: `pgi`, `runtime-evidence`, `memory`, `content`, `hygiene`
Authority: `supporting_evidence` | AI Read Priority: 2

## Intent

Add a MemoryContentRecord object so Ordivon can reuse memory and content without
turning stale, degraded, private, or advisory material into current truth.

## Constraints

- Does not authorize action.
- Does not create a memory database.
- Does not publish private content.
- Does not treat memory as source of truth by itself.

## Actions

Created:

```text
docs/governance/memory-content-hygiene-pgi-3.md
scripts/validate_pgi_memory_content_record.py
tests/fixtures/pgi_memory_content/valid/current-receipt-summary.json
tests/fixtures/pgi_memory_content/invalid/candidate-policy.json
tests/fixtures/pgi_memory_content/invalid/stale-safe.json
tests/unit/governance/test_pgi_memory_content_record.py
```

## Evidence

Expected fixture behavior:

| Fixture | Expected |
|---------|----------|
| current receipt summary | VALID |
| CandidateRule as Policy | INVALID |
| stale degraded memory marked safe | INVALID |

## Review

PGI-3.05 is locally closed as a seed memory hygiene layer. It protects Ordivon
from the slow failure mode where old notes become false authority.

## Rule Update

CandidateRule proposal:

```text
PGI-CR-023: Memory reuse requires source receipt, freshness state, authority
class, privacy boundary, and explicit contamination flags.
```

Status: **candidate only**. This is not Policy.

## Next Action

```text
PGI-3.06 - AI Collaborator Philosophical Onboarding
```
