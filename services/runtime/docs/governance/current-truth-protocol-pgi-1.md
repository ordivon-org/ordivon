# Current Truth Protocol — PGI-1

Status: **CURRENT** | Date: 2026-05-03
Phase: PGI-1.04
Tags: `pgi`, `current-truth`, `freshness`, `supersession`
Authority: `source_of_truth` | AI Read Priority: 1

## Purpose

This protocol makes Ordivon's "current truth" explicitly revisable.

Core rule:

```text
current_truth is the best available project truth under known evidence and
freshness metadata. It is not permanent truth.
```

## Required Semantics

| Concept | Required meaning |
|---------|------------------|
| current_truth | Presently governing truth, subject to freshness and supersession. |
| source_of_truth | Authority to define current truth, not action permission. |
| last_verified | Date/time the source was checked. |
| stale_after_days | Maximum age before re-verification is required. |
| supersedes | Older document replaced by this one. |
| superseded_by | Newer document replacing this one. |

## Forbidden Semantics

Current truth must not be described as:

- permanent
- final
- forever true
- impossible to supersede
- proof that action is authorized

## Checker Seed

Seed checker:

```text
scripts/check_current_truth_protocol.py
```

It detects:

- `current_truth` described as permanent/final/unsupersedable
- `source_of_truth` registry entries missing `last_verified` or
  `stale_after_days`

## Fixtures

```text
tests/fixtures/pgi_current_truth/clean/
tests/fixtures/pgi_current_truth/unsafe/
```

## Boundary

This protocol does not replace the document registry checker. It adds a PGI
semantic check for philosophical misuse of "truth" language.

Next stage:

```text
PGI-1.05 - Confidence and Calibration Model
```
