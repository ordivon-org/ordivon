# ORDIVON LEGO — AGENT BIRTH COMMAND R24

Date: 2026-09-19
Base: 7c1423eecea29d63271819b2f62291dca7e650e8

## Finding

BirthCoordinator owns no durable state and no independent authority.

Its transaction is important; its class identity is not.

## LEGO decomposition

| LEGO | Owner | Role |
|---|---|---|
| birth request uniqueness | agent_instances.birth_request_id UNIQUE | exactly-once identity |
| revision validity | AgentRevisionStore | source revision truth |
| instance record/state | AgentInstanceStore | AgentInstance truth |
| desired placement | DesiredPlacementStore | placement intent truth |
| birth event | ServiceEventStore | event truth |
| atomic commit/rollback | SQLite transaction | transaction boundary |
| BirthCoordinator | none | application-command composition only |

## Replacement

BirthCoordinator.birth(request, revision)
  -> AgentServiceSlice1.birth(request, revision)
  -> _birth_agent(connection, revisions, instances, placements, events, request, revision)

The existing ServiceEventStore.append_in_transaction is used instead of a private event insertion helper.

## API cleanup

Old: service.birth.birth(request_id, revision_id)
New: service.birth(request_id, revision_id)

Later AgentService revisions may continue forwarding the bound birth command as self.birth = previous.birth; this forwards a callable, not a custom coordinator object.

## Proof obligations

1. BirthCoordinator absent.
2. old .birth.birth(...) call shape absent.
3. same birth_request_id + same revision is idempotent.
4. same birth_request_id + different revision fails closed.
5. AgentInstance + DesiredPlacement + AGENT_BIRTH_REQUESTED remain one transaction.
6. concurrent uniqueness recovery remains correct.
7. ServiceEventStore owns event sequencing; no private duplicate event writer.
8. no replacement BirthManager/BirthService/BirthRegistry class.
