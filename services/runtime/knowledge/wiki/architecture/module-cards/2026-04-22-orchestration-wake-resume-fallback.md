# Module

Orchestration | WakeResume / Fallback

## Layer

Orchestration

## Type

Core

## Role

Formalize wake/resume reasons and one honest fallback path for analyze.

## Current Value

- Recovery policy exists
- Retry semantics exist
- Checkpoint semantics exist

## Remaining Gap

- Wake/resume reasons are not formal runtime objects
- Retry exhaustion has no explicit fallback contract

## Immediate Action

- Add wake/resume runtime semantics
- Extend task-run persistence with wake/resume metadata
- Extend recovery with fallback decisions/results
- Add one analyze fallback path for Hermes retry exhaustion

## Wrong Placement To Avoid

- Do not put wake/resume in `intelligence/`
- Do not let fallback pretend success
- Do not bypass governance when falling back

## Required Test Pack

- `python -m compileall orchestrator domains/workflow_runs`
- `pytest -q tests/unit/test_wake_resume.py tests/unit/test_fallback_policy.py tests/unit/test_workflow_recovery.py`
- `pytest -q tests/integration/test_hermes_analyze_api.py`

## Done Criteria

- Wake/resume runtime types exist
- Workflow/task-run can persist wake/resume semantics
- Hermes retry exhaustion has fallback or honest degraded path

## Next Unlock

Infrastructure | Scheduler

## Not Doing

- No generic resume scheduler
- No UI surface
- No multi-workflow fallback matrix
