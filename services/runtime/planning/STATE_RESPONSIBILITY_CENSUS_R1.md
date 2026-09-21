# Runtime State Responsibility Census R1

Source revision: `97a8d1b48b2e10e20f4b6869dc12ecb8380a8ee8`

## Key correction

The current Runtime is already partially decomposed. The engine is not one undifferentiated file: it has `admission`, `execution`, `reconciliation`, `workspace`, `release`, `control_query`, and `construction` submodules. Registry likewise has `admission`, `lifecycle`, `query`, `recovery`, `reconciliation`, and `storage`.

Therefore R02/R03 are **not** a request to perform another cosmetic module split.

The remaining gap is:

```text
current:  control-phase / verb ownership
         admission → execution → reconciliation → query

target:   stable state laws + control services
         Workspace / Job / Attempt / Reservation / Artifact
                       ↑
         admission / execution / reconciliation consume them
```

A move is justified only when one durable law is currently encoded in more than one control-phase module.

## Workspace

Already localized:
- public Workspace orchestration: `engine/workspace.rs`;
- mature Git/worktree mechanics: universal workspace primitives.

Still distributed:
- source-state / Git-authority facts;
- active/held Job guard projection;
- reconciliation-before-lifecycle control;
- projection/error vocabulary;
- operator retention/quarantine versus exact core close.

First extraction should be a **WorkspaceStateContract**, not a new Workspace implementation.

It owns:
- opening `sourceRevision`;
- exact current-head projection semantics;
- `sourceStateDigest` expected-state law;
- dirty/force close preconditions;
- shared Git-authority dependency identity;
- closed tombstone replay law.

It explicitly does **not** own:
- Git clone/worktree mechanics;
- reconciliation loop;
- retention policy;
- Job semantics.

## Job / Attempt / Reservation

Current code is already separated by control phase:
- `engine/admission.rs`;
- `engine/execution.rs`;
- `engine/reconciliation.rs`;
- `engine/control_query.rs`;
- Registry admission/lifecycle/query/recovery modules.

The noun-level laws still span those phases.

First extraction targets:
1. `JobIdentityContract`: request/operation identity and replay/conflict law.
2. `AttemptLifecycleContract`: generation/state/termination/physical-owner/terminal-evidence law.
3. `ReservationContract`: Workspace/global capacity holders and acquire/hold/release transitions.

Provider realization and reconciliation stay separate consumers of those contracts.

## Rejection rule

Reject a proposed extraction if it only:
- moves lines between files;
- creates another facade;
- creates a new crate with no independent lifecycle;
- duplicates Registry state;
- introduces queue/workflow/effect semantics;
- cannot name a hidden authority or duplicate law that it removes.
