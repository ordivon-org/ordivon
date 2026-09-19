# ORDIVON REMOTE DELIVERY OBSERVATION STORE ELIMINATION R19

Date: 2026-09-19
Status: SIXTEENTH_PRODUCTION_DELETION
Parent: ORDIVON EXECUTION QUIESCENCE PROOF STORE ELIMINATION R18

## Result

R19 removes the specialized durable `RemoteDeliveryObservationStore`, `remote_delivery_observations` table, and `service.remote_observations` façade.

`RemoteDeliverySnapshot` remains only as a projection over an append-only generic event stream.

Deleted authority:

- `RemoteDeliveryObservationStore`
- `remote_delivery_observations`
- `service.remote_observations`
- package export `agent_service.RemoteDeliveryObservationStore`
- foreign-key authority `remote_delivery_observations.binding_id -> transport_bindings.id`

No replacement observation store, registry, reader class, or specialized event-store class was introduced.

## Durable remote observation stream after deletion

```text
aggregate_type = RemoteDeliveryObservation
aggregate_id   = binding_id
event_type     = RemoteDeliveryObserved
sequence       = ServiceEvent sequence
payload        = bindingId / providerStatus / terminal / successful /
                 remoteTaskId / remoteContextId / artifactRefs /
                 evidenceRef / observedAtMs
```

The generic event id is the durable snapshot id.

The generic event sequence is the durable remote snapshot sequence.

## Historical semantics retained

The retired Store exposed exactly three behavioral operations:

- list the complete observation history for one Binding;
- read the latest observation for one Binding;
- append a new observation.

R19 maps them directly onto the generic aggregate event stream.

Consecutive exact duplicate observations remain idempotent at the domain layer: the latest existing snapshot is returned and no new event is appended.

A changed observation appends the next event in the Binding aggregate stream.

## Correlation safety retained

Remote task/context correlation remains checked before appending an observation:

- if the Delivery receipt already established a remote task id, observations may not change it;
- if the Delivery receipt already established a remote context id, observations may not change it;
- once an observation establishes either identity, later observations may not change it.

Therefore replacing the specialized table does not weaken correlation ownership.

## Cross-layer consumers

These consumers now read the same generic event stream:

- RemoteCorrelationReconciler;
- AuditEnvelopeProjector;
- RemoteTaskCompletionReconciler;
- ExecutionQuiescenceCoordinator;
- ReplaySafetyCoordinator;
- ExecutionClaimTransferCoordinator;
- failover safety history checks;
- control-stability witness script.

No `remote_observations` façade remains in later Agent Service revisions.

## Destructive migration

A database containing the obsolete `remote_delivery_observations` table fails closed during R10 initialization.

No compatibility shim or silent migration is retained.

## CORE_ZERO ratchet

```text
R3 baseline: 171
R4:          170
R5:          169
R6:          168
R7:          167
R8:          165
R9:          164
R10:         162
R11:         161
R12:         160
R13:         159
R14:         158
R15:         157
R16:         156
R17:         155
R18:         154
R19:         153
cumulative retired top-level types: 18
```

`RemoteDeliverySnapshot` remains because it is now a non-authoritative projection type.

Structural audit:

```text
observed top-level Agent Service classes = 153
legacy ceiling                           = 153
unexpected new classes                   = []
retired overlap                          = []
old RemoteDeliveryObservationStore/table = none
remote_observations façade refs          = none
replacement observation stores           = none
```

## Validation

Trust / remote-evidence / failover targeted regression:

```text
Ran 41 tests
OK
```

CORE_ZERO / structural deletion gate:

```text
Ran 47 tests
OK
```

Agent Service regression suite:

```text
Ran 234 tests
OK (skipped=5)
```

Full repository regression suite:

```text
Ran 333 tests
OK (skipped=5)
```

## Next deletion pressure

R20 should re-run the authority inventory.

Prefer immutable evidence/receipt stores whose downstream foreign-key authority has already disappeared.

Do not delete `ExecutionQuiescenceRequestStore` or `TaskExecutionClaimStore` merely to reduce the class count: both still own live mutable control state.

Credential and identity-proof persistence remain security-boundary candidates and require explicit ownership analysis before deletion.
