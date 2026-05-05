# Governance Freeze Protocol (EGB-2)

Status: **CURRENT** | Date: 2026-05-05 | Phase: EGB-2
Tags: `egb-2`, `freeze`, `stage-template`, `governance-process`
Authority: `source_of_truth` | AI Read Priority: 1

## Purpose

The freeze protocol prevents late scope expansion from hiding unfinished
governance work. It is an Ordivon-local stage-control model inspired by mature
engineering release discipline, not a release approval process.

Freeze state is evidence for stage control. It does not authorize merge,
release, deployment, publication, trading, policy activation, or external
action.

## Freeze States

| State | Meaning | Allowed work |
|-------|---------|--------------|
| `open_scope` | Stage can still accept planned scope. | Planned design, implementation, docs, tests, registry updates. |
| `enhancement_freeze` | No new scope enters the stage. | Existing scope implementation, tests, evidence, blocker repair. |
| `verification_freeze` | Implementation should stop expanding. | Tests, receipts, registry repair, docs synchronization, blocker repair. |
| `closure_freeze` | Only closure evidence remains. | Final receipt, summit, current-truth sync, baseline verification. |
| `closed` | Stage is sealed. | No mutation except supersession or explicitly opened follow-up. |

## Stage Template Contract

Stage templates may define:

```yaml
freeze_protocol:
  state: open_scope
  allowed_states:
    - open_scope
    - enhancement_freeze
    - verification_freeze
    - closure_freeze
    - closed
  enforcement: record_only
```

EGB-2 first version is `record_only`: the stage runner records and displays
freeze state but does not block changes based on it.

## Future Enforcement

Future phases may promote freeze enforcement after red-team fixtures prove the
rules do not create false comfort or block legitimate repair work.
