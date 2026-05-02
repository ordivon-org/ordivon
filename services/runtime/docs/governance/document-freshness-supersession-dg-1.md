# Document Freshness & Supersession Model (DG-1)

Status: **current** | Date: 2026-05-02 | Phase: DG-1
Tags: `dg-1`, `freshness`, `supersession`, `staleness`, `lifecycle`
Authority: `source_of_truth` | AI Read Priority: 1

## Core Principle

**A stale document with `current` status is a governance risk.**
**A superseded document in the AI read path is a misdirection risk.**
**Freshness metadata does not prove correctness, but its absence guarantees drift.**

## Freshness Requirements by Priority

| AI Priority | last_verified | stale_after_days | Enforcement |
|-------------|--------------|------------------|-------------|
| L0 | REQUIRED | REQUIRED | ADP3-DG-STALENESS (degraded) |
| L1 | REQUIRED | REQUIRED | ADP3-DG-STALENESS (degraded) |
| L2 | Recommended | Recommended | Not enforced (advisory) |
| L3 | Optional | Optional | Not enforced |
| L4 | Not required | Not required | Not enforced |

## Freshness Requirements by Authority

| Authority | last_verified | stale_after_days | Rationale |
|-----------|--------------|------------------|-----------|
| source_of_truth | REQUIRED | REQUIRED | Defines current truth — must not be stale |
| current_status | REQUIRED | Recommended | Reports current state — freshness matters |
| supporting_evidence | Optional | Optional | Dated at creation; archival after closure |
| historical_record | Optional | Optional | Immutable; does not expire |
| proposal | Optional | Optional | Stale after proposing phase closes |
| example | Not required | Not required | Illustrative only |
| archive | Not required | Not required | Preserved for traceability |

## Staleness Rules

| Condition | Action |
|-----------|--------|
| `last_verified` older than `stale_after_days` | Mark as stale; re-verify or supersede |
| No `last_verified` on L0/L1 doc | ADP3-DG-STALENESS flags as degraded |
| No `stale_after_days` on L0/L1 doc | ADP3-DG-STALENESS flags as degraded |
| Doc references a deferred/deprecated phase as active | Mark as stale |

## Supersession Rules

| Condition | Rule |
|-----------|------|
| `status=current` + `superseded_by` non-null | INVALID — ADP3-DG-SUPERSEDED flags as blocking |
| `superseded_by` doc does not exist in registry | INVALID — check registry consistency |
| Superseding doc has lower authority than superseded | SUSPICIOUS — review |
| Multiple docs claim to supersede the same doc | INVALID — check registry |

## Supersession Flow

```
Doc v1 (current) → Doc v2 created → v1.status=superseded, v1.superseded_by=v2.doc_id
                                      v2.supersedes=v1.doc_id, v2.status=current
```

## Degraded Lifecycle

DEGRADED entries require:

| Field | Required | Description |
|-------|----------|-------------|
| `owner` | YES | Who is responsible for resolution |
| `stale_after_days` or `due_stage` | YES | When resolution is required |
| `escalation_condition` | Recommended | What triggers escalation |
| `closure_condition` | Recommended | What constitutes resolution |

ADP3-DG-DEGRADED-LIFECYCLE flags entries missing `owner` and `stale_after_days`/`due_stage`.

## Current Registry Gaps (DG-1 baseline)

| Metric | Current | Target |
|--------|---------|--------|
| L0 docs with freshness | 1/1 (AGENTS.md) | 1/1 |
| L1 docs with freshness | 7/21 | 21/21 |
| source_of_truth with freshness | 6/26 | 26/26 |
| Total with last_verified | 8/79 | L0/L1 + source_of_truth = ~30 |
| Total with stale_after_days | 6/79 | L0/L1 + source_of_truth = ~30 |

Closing these gaps is DG-2 work. DG-1 defines the model and registers the gaps.

## DOC-WIKI-FLAKY-001 Status

The wiki generator (`scripts/generate_document_wiki.py`) was investigated during DG-1.
Current behavior: deterministic across multiple runs with current registry state.
The flaky behavior may be environment-specific (Python dict ordering, file glob ordering)
or may have been resolved by registry normalization in prior phases.

**Disposition**: Mark as `accepted_until` with re-verification at next registry change.
If flaky behavior recurs, escalate to DG-2 for ordering fix.
