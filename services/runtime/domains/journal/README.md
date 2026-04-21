# Journal Domain

`domains/journal/` owns review-centered learning artifacts.

## This Package Is For

- reviews
- lessons derived from reviews
- issues raised from validation, review, or workflow breakdowns

## Core Files

- `models.py` / `orm.py`
  - review truth object
- `repository.py`
  - review persistence and ref attachment helpers
- `service.py`
  - review completion flow, lesson persistence, outcome backfill hookup, feedback packet preparation
- `state_machine.py`
  - review lifecycle constraints
- `lesson_models.py` / `lesson_repository.py` / `lesson_service.py`
  - lesson truth and persistence
- `issue_models.py` / `issue_repository.py` / `issue_service.py`
  - issue truth and persistence for validation/workflow breakdowns

## Most Important Runtime Role

This domain is where review-centered truth gets created and completed.

The critical path is:

`review submit -> review complete -> lesson persistence -> outcome backfill -> feedback packet preparation`

Execution adapters now sit above some of these actions, but the domain still owns the truth semantics.

## This Package Is Not For

- final governance allow/block decisions
- audit trace storage rules
- generic operator state

## Boundary Decision

Issues currently stay in `domains/journal/` because they are review and workflow learning artifacts first. If a future incident-management or approval workflow is added, governance may own a separate incident layer without taking over this journal-facing issue model.
