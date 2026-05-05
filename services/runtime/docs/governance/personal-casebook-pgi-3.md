# Personal Casebook — PGI-3

Status: **CURRENT** | Date: 2026-05-04
Phase: PGI-3.04
Tags: `pgi`, `casebook`, `privacy`, `externalization`, `learning`
Authority: `source_of_truth` | AI Read Priority: 1

## Purpose

Personal Casebook asks:

```text
Which lived or builder cases are safe and useful enough to become durable
learning material?
```

The casebook is not a diary dump. It is a curated evidence set with privacy and
externalization boundaries.

## Object

`PGIPersonalCaseEntry` records:

- domain
- case type
- privacy level
- summary
- artifact refs
- review refs
- lesson summary
- self-model refs
- public-safe summary
- raw-private-data flag
- externalization flag
- authority boundary

## Privacy Levels

| Level | Meaning |
|-------|---------|
| private | Internal only; not safe to externalize. |
| sensitive | Redacted use only; do not publish. |
| public_safe | Can be used as public-safe example after separate approval. |

## Validator Seed

```text
scripts/validate_pgi_personal_case_entry.py
```

It rejects:

- raw private data
- private/sensitive entries marked for externalization
- missing artifacts or review refs
- non-public entries without redacted public-safe summary
- missing non-authorization / non-publication boundary

## Boundary

This casebook does not authorize action or publication. Externalization remains
a separate governed decision.

Next stage:

```text
PGI-3.05 - Memory and Content Hygiene
```
