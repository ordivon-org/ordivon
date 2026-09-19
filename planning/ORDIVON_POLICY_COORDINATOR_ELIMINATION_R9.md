# ORDIVON POLICY COORDINATOR ELIMINATION R9

Date: 2026-09-19  
Status: SIXTH_PRODUCTION_DELETION  
Parent: ORDIVON POLICY RECEIPT ELIMINATION R8

## Result

R9 removes `PolicyEvaluationCoordinator` and the `service.policy` control surface.

The old two-stage caller flow:

```text
service.policy.evaluate(...)
        ↓ policy receipt id
service.routes.plan(...)
```

is replaced by one route-admission operation:

```text
service.routes.plan(
    delegation_id,
    client_policy_request_id=...,
    preferred_transports=...
)
```

No replacement coordinator, registry, service object, or policy authority was introduced.

## LEGO ownership after deletion

`PolicyAdapter`, `PolicyRequest`, and `PolicyObservation` remain non-authoritative boundary bricks for an external policy decision point.

The route planner now owns only composition:

```text
client policy request identity
        ↓
_evaluate_policy_receipt(...)   [pure orchestration function]
        ↓
existing generic service_events receipt
        ↓
allow / deny
        ↓
route selection
        ↓
immutable TransportBinding
```

`_evaluate_policy_receipt` is a function, not a new semantic object or persistence authority. Exact request replay still reuses the existing generic receipt and does not re-evaluate changed current route-time policy.

R15 effect-time authorization remains a separate current-policy check immediately before the first external effect.

## Deleted surfaces

- top-level class `PolicyEvaluationCoordinator`
- package export `agent_service.PolicyEvaluationCoordinator`
- service surface `service.policy`
- R10-R12 compatibility forwarding of `policy`

No compatibility shim was retained.

## CORE_ZERO ratchet

```text
R3 baseline: 171
R4:          170
R5:          169
R6:          168
R7:          167
R8:          165
R9:          164
cumulative retired top-level types: 7
```

Final structural audit before regression:

```text
observed top-level Agent Service classes = 164
legacy ceiling                           = 164
unexpected new classes                   = []
old PolicyEvaluationCoordinator refs     = none
service.policy / .policy.evaluate refs   = none
replacement coordinator classes          = none
```

## Validation

CORE_ZERO / public API / R9 elimination guard:

```text
Ran 9 tests
OK
```

R9-R15 governed-delivery chain:

```text
Ran 90 tests
OK
```

Agent Service regression suite:

```text
Ran 206 tests
OK (skipped=5)
```

Full repository regression suite:

```text
Ran 305 tests
OK (skipped=5)
```

## Next deletion pressure

The remaining `PolicyAdapter`, `PolicyRequest`, and `PolicyObservation` are not automatically deletion targets merely because their names contain Policy. They are adapter-boundary types and must be evaluated under the CORE_ZERO rule for non-authoritative external-owner adapters.

The next broad audit should therefore move from name-based deletion to authority-based decomposition of the remaining delivery and effect-state stores.
