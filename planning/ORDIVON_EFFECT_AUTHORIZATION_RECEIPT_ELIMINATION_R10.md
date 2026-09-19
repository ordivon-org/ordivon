# ORDIVON EFFECT AUTHORIZATION RECEIPT ELIMINATION R10

Date: 2026-09-19  
Status: SEVENTH_PRODUCTION_DELETION  
Parent: ORDIVON POLICY COORDINATOR ELIMINATION R9

## Result

R10 removes the specialized durable effect-authorization decision authority while preserving the current-policy safety semantics immediately before the first external effect.

Deleted from the live production path:

- `EffectAuthorizationDecision`
- `EffectAuthorizationDecisionStore`
- `effect_authorization_decisions`
- `service.effect_authorization_records`
- package exports for both deleted types
- foreign-key authority from the specialized table to `transport_bindings` and `delegation_envelopes`

No `EffectAuthorizationReceiptStore`, registry, or replacement policy store was introduced.

## Safety semantics preserved

The current effect gate remains:

```text
exact TransportBinding
        ↓
current external PolicyAdapter evaluation
        ↓
generic immutable ServiceEvent receipt
        ↓
allow / deny
        ↓
first external delivery effect
```

The receipt stream is keyed by exact `binding_id`:

```text
aggregate_type = EffectAuthorization
aggregate_id   = binding_id
event_type     = EffectAuthorizationEvaluated
payload        = bindingId / delegationId / allowed / reason /
                 policyRevision / grantedPermissions
```

This preserves the important distinction:

- a new binding/effect identity requires a current policy evaluation;
- a retry of the same exact effect identity reuses the frozen authorization receipt;
- a denied effect identity stays denied even if policy later changes;
- an existing delivery receipt replays without creating a new authorization event.

## Destructive migration

A database containing the obsolete `effect_authorization_decisions` table fails closed during R15 initialization.

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
cumulative retired top-level types: 9
```

Structural audit:

```text
observed top-level Agent Service classes = 162
legacy ceiling                           = 162
unexpected new classes                   = []
retired overlap                          = []
old effect authorization authorities     = none
replacement effect stores                = none
```

## Validation

Targeted receipt + R15 + CORE_ZERO checks:

```text
Ran 14 tests
OK
```

Agent Service regression suite:

```text
Ran 208 tests
OK (skipped=5)
```

Full repository regression suite:

```text
Ran 307 tests
OK (skipped=5)
```

## Next deletion pressure

The next candidate is `EffectAuthorizationCoordinator`.

It should be removed only if its remaining responsibility is composition rather than authority. The required safety property is unchanged: current policy must be evaluated immediately before the first external effect for a new exact binding, while retries of the same exact effect identity must reuse the frozen receipt.
