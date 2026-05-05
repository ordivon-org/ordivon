# Memory and Content Hygiene — PGI-3

Status: **CURRENT** | Date: 2026-05-04
Phase: PGI-3.05
Tags: `pgi`, `memory`, `content`, `hygiene`, `freshness`, `authority`
Authority: `source_of_truth` | AI Read Priority: 1

## Purpose

Memory/Content Hygiene asks:

```text
Can this memory be safely reused without laundering stale, degraded, private, or
advisory content into current truth?
```

## Object

`PGIMemoryContentRecord` records:

- content type
- source reference
- source receipt
- last verified
- freshness state
- authority class
- claim status
- contamination flags
- safe use
- next review
- privacy boundary
- authority boundary

## Contamination Flags

```text
candidate_rule_as_policy
degraded_as_fact
stale_as_current
private_as_public
missing_source
none
```

## Validator Seed

```text
scripts/validate_pgi_memory_content_record.py
```

It rejects:

- stale/superseded/unknown memory marked `safe_to_use`
- CandidateRule memory marked `source_of_truth`
- degraded facts, private-as-public, or candidate-as-policy contamination not marked `do_not_use`
- missing source receipts without `missing_source`
- unsafe instructions such as use as truth, treat as policy, or publish as public

## Boundary

Memory records do not authorize action and are not source of truth by themselves.
They are reusable only through freshness, authority, privacy, and evidence
checks.

Next stage:

```text
PGI-3.06 - AI Collaborator Philosophical Onboarding
```
