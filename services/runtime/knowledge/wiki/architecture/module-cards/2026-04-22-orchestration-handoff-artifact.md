# Module

Orchestration | HandoffArtifact

## Layer

Orchestration

## Type

Core

## Role

Introduce a formal blocked-work artifact so long-running or supervisor-routed work leaves an objectized handoff instead of only narrative failure text.

## Current Value

- Workflow runs already exist
- Checkpoint semantics exist on lineage refs
- Recovery detail exists

## Remaining Gap

- There is no formal handoff artifact object
- Blocked analyze paths do not leave a structured next-action artifact

## Immediate Action

- Add `HandoffArtifact` contract
- Add runtime helper to build/attach artifacts
- Persist handoff ref on workflow/task-run lineage
- Emit one blocked analyze-path artifact

## Wrong Placement To Avoid

- Do not put handoff into `knowledge/`
- Do not treat handoff as state truth
- Do not generate UI-only narrative blobs in place of structured artifact refs

## Required Test Pack

- `python -m compileall orchestrator domains/workflow_runs`
- `pytest -q tests/unit/test_handoff_artifact.py tests/unit/test_task_run_resume_state.py`
- `pytest -q tests/unit/test_workflow_recovery.py tests/integration/test_workflow_run_lineage_api.py`

## Done Criteria

- `HandoffArtifact` exists
- Analyze blocked path writes handoff artifact ref
- Workflow/task-run persistence exposes handoff ref and resume_from_ref

## Next Unlock

Orchestration | WakeResume / Fallback

## Not Doing

- No handoff UI
- No wake/resume execution engine
- No knowledge extraction from handoff artifacts
