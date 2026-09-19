# ORDIVON EFFECT AUTHORIZATION COORDINATOR ELIMINATION R11

Date: 2026-09-19  
Status: EIGHTH_PRODUCTION_DELETION  
Parent: ORDIVON EFFECT AUTHORIZATION RECEIPT ELIMINATION R10

## Result

R11 removes `EffectAuthorizationCoordinator` and the `service.effect_authorizations` control surface.

The current-effect safety rule is not removed. Its remaining composition is folded directly into `EffectAuthorizedDeliveryCoordinator`, which already owns the final "authorize then perform external delivery" boundary.

Deleted:

- top-level class `EffectAuthorizationCoordinator`
- package export `agent_service.EffectAuthorizationCoordinator`
- service surface `service.effect_authorizations`

No replacement coordinator class was introduced.

## Semantics after deletion

```text
delivery(binding_id)
    │
    ├─ existing DeliveryReceipt?
    │      └─ replay exact delivery; no new authorization
    │
    └─ no receipt
           ↓
       existing EffectAuthorization generic receipt?
           ├─ yes → reuse frozen allow/deny
           └─ no
                ↓
           current external PolicyAdapter evaluation
                ↓
           append generic immutable EffectAuthorization receipt
                ↓
           allow / deny
                ↓
           first external delivery effect
```

The critical safety properties remain unchanged:

- current policy is checked immediately before the first external effect for a new binding;
- denied exact effect identity stays denied even if policy later changes;
- response-loss retry for the same exact binding reuses its frozen authorization;
- existing delivery receipt replay does not create a fresh authorization.

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
cumulative retired top-level types: 10
```

Structural audit:

```text
observed top-level Agent Service classes = 161
legacy ceiling                           = 161
unexpected new classes                   = []
retired overlap                          = []
old effect coordinator refs              = none
replacement effect coordinators          = none
```

## Validation

Targeted R11 + R15 safety checks:

```text
Ran 8 tests
OK
```

CORE_ZERO + safety structural gate:

```text
Ran 14 tests
OK
```

Agent Service regression suite:

```text
Ran 210 tests
OK (skipped=5)
```

Full repository regression suite:

```text
Ran 309 tests
OK (skipped=5)
```

## Next deletion pressure

The next audit should target specialized receipt stores rather than external-policy boundary types.

High-priority candidates include `DeliveryReceipt / DeliveryReceiptStore` and other structures that may duplicate the existing generic event/evidence journal. They must first be checked for foreign-key authority, replay semantics, downstream lookups, and remote-correlation ownership.
