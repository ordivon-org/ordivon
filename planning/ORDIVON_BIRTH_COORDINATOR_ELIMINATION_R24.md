# ORDIVON BIRTH COORDINATOR ELIMINATION R24

Date: 2026-09-19
Status: TWENTIETH_PRODUCTION_DELETION
Parent: ORDIVON EVIDENCE RESOLVER REGISTRY ELIMINATION R23

## Result

R24 removes BirthCoordinator and the service.birth.birth(...) double facade.

Birth semantics are preserved as an AgentServiceSlice1 application command backed by _birth_agent(...).

## LEGO decomposition

birth_request_id uniqueness = agent_instances.birth_request_id UNIQUE
revision truth = AgentRevisionStore
instance truth = AgentInstanceStore
placement truth = DesiredPlacementStore
event truth = ServiceEventStore
atomicity = SQLite transaction
BirthCoordinator = composition wrapper only

## Replacement

Old:
service.birth.birth(request_id, revision_id)

New:
service.birth(request_id, revision_id)

Internal:
AgentServiceSlice1.birth -> _birth_agent -> existing Stores + ServiceEventStore + one SQLite transaction

The private BirthCoordinator event writer was deleted; ServiceEventStore.append_in_transaction now owns event sequencing.

## Semantics preserved

- empty birth request still fails validation
- revision existence is checked before creation
- same request + same revision is idempotent
- same request + different revision fails closed
- AgentInstance and DesiredPlacement are created atomically
- AGENT_BIRTH_REQUESTED is committed in the same transaction
- sqlite uniqueness-race recovery still re-reads the committed AgentInstance
- restart recovery still returns the historical instance

## CORE_ZERO ratchet

R3 baseline: 171
R20: 152
R21: 151
R22: 151
R23: 150
R24: 149
cumulative retired top-level types: 22

Structural audit:
observed = 149
legacy ceiling = 149
unexpected = []
retired overlap = []
old BirthCoordinator/double facade = none
private duplicate birth event writer = none
replacement Birth* classes = none

## Validation

R24 targeted birth/R5/R6/R7 chain: Ran 43 tests — OK
Structural gate: Ran 49 tests — OK
Agent Service suite: Ran 245 tests — OK (skipped=5)
Full repository suite: Ran 344 tests — OK (skipped=5)

## Interpretation

R24 removes a class boundary while preserving the real transaction boundary.

Exactly-once semantics are owned by database uniqueness + transaction + existing Stores, not by the coordinator class name.
