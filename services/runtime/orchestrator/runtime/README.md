# Orchestrator Runtime

`orchestrator/runtime/` contains workflow execution mechanics.

## Current Focus

- workflow engine
- recovery policy
- persisted step-status discipline

## Read These Files First

- `engine.py`
  - top-level workflow runner
  - run persistence
  - step attempt/retry/failure recording
- `recovery.py`
  - `RecoveryPolicy`
  - recovery detail helpers
  - compatibility bridge from older retry conventions

## Current Runtime Shape

The active runtime is centered on:

- `PFIOSOrchestrator`
- `WorkflowContext`
- `WorkflowRun` persistence
- structured step-status recording

## Most Important Behavior

Today the main real runtime path is the `analyze` workflow.

The runtime now handles:

- workflow start
- per-step execution
- retry decisions via `RecoveryPolicy`
- compensation signal persistence
- completed/failed workflow run persistence

## Does Not Own

- governance policy
- prompt content
- business truth transitions
- tool implementations
