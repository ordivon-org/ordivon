# Module Card

- Module: Orchestration | Recovery Policy Object
- Layer: Orchestration
- Role: Put the existing analyze-path retry and compensation behavior behind a formal recovery policy object so recovery semantics stop living only in ad hoc step attributes and metadata conventions.
- Current Value:
  - `PFIOSOrchestrator` already records `attempt`, `retrying`, and `recovery_action` in workflow step statuses.
  - `ReasonStep` currently exposes retry behavior through `max_retries` and `should_retry(...)`.
  - `WriteWikiStep` already records compensation detail through `_workflow_recovery_detail`.
- Remaining Gap:
  - Recovery semantics are still split across engine internals, step-local attributes, and a loose metadata key.
  - There is no single recovery policy object that explains retry versus terminal failure behavior.
  - Compensation detail is real but still hangs off a private convention rather than a first-class recovery helper.
- Immediate Action:
  1. Add `orchestrator/runtime/recovery.py` with a minimal `RecoveryPolicy` and `RecoveryDetail`.
  2. Refactor `PFIOSOrchestrator` to resolve step recovery through the policy object.
  3. Move `ReasonStep` onto an explicit recovery policy.
  4. Move `WriteWikiStep` compensation signaling onto a shared recovery helper.
- Required Test Pack:
  - `python -m compileall ...`
  - unit:
    - recovery policy retry evaluation
    - recovery detail round-trip through workflow context metadata
  - integration:
    - retrying reason step still records attempts correctly
    - failed wiki compensation still records `recovery_action=compensation` and `recovery_detail`
  - failure-path:
    - terminal failure still stays honest when no retry applies
    - compensation detail stays present without pretending fallback success
  - invariants:
    - retry semantics come from one recovery policy object
    - compensation remains an explicit recovery signal, not hidden cleanup
  - state/data:
    - workflow run step statuses remain consistent with retry and compensation outcomes
- Done Criteria:
  - Analyze workflow recovery is driven by a formal recovery policy object.
  - Step-local retry behavior is no longer only `max_retries / should_retry` convention.
  - Compensation still appears in persisted workflow step status with honest detail.
  - Tests prove retry and compensation behavior still works after the refactor.
- Next Unlock:
  - `Experience | Review Detail Surface`
  - `State | Trace Relation Hardening`
  - `Knowledge | Retrieval / Recurring Issue Aggregation`
- Not Doing:
  - Do not add cross-workflow coordination.
  - Do not add provider fallback routing.
  - Do not build a full orchestration control plane.
  - Do not redesign workflow state machines.
