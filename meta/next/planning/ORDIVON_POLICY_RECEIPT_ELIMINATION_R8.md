# ORDIVON POLICY RECEIPT ELIMINATION R8

Date: 2026-09-19  
Status: FIFTH_PRODUCTION_DELETION  
Parent: ORDIVON REVISION-NATIVE ROUTE ELIMINATION R7

## Result

R8 removes the specialized route-time policy decision authority instead of renaming it.

Deleted from the live production path:

- `PolicyDecision`
- `PolicyDecisionStore`
- `policy_decisions`
- `service.policy_decisions`
- package export `agent_service.PolicyDecisionStore`
- `transport_bindings.policy_decision_id -> policy_decisions.id`

No `PolicyReceiptStore`, `DecisionRegistry`, `PolicyRegistry`, `OPADecisionStore`, or equivalent replacement authority was introduced.

Top-level Agent Service type debt:

```text
R3 baseline: 171
R4:          170
R5:          169
R6:          168
R7:          167
R8:          165
retired types: 6
```

## Ownership after deletion

Current policy evaluation remains behind `PolicyAdapter`, whose intended mature owner is an external PDP such as OPA.

Historical route-time evaluation replay is represented only as a receipt in the existing generic `service_events` journal:

```text
aggregate_type = PolicyEvaluation
aggregate_id   = client_policy_request_id
event_type     = PolicyEvaluated
payload        = delegationId / allowed / reason / policyRevision / grantedPermissions
```

This journal entry records that an evaluation occurred. It is not a new policy engine, policy ontology, or policy-specific persistence service.

An allowed route freezes only the material needed by later composition into immutable `TransportBinding` state:

- `policy_receipt_id`
- `policy_revision`
- `granted_permissions`

Credential binding therefore checks the immutable binding snapshot rather than reopening a second policy-decision database authority.

## OPA boundary

OPA remains the candidate owner for policy evaluation semantics. OPA Decision Logs expose decision identifiers, inputs/results, and bundle revision metadata for auditing/debugging, but R8 does not treat Decision Logs as a synchronous application transaction database.

Canonical references:

- https://www.openpolicyagent.org/docs/management-decision-logs
- https://www.openpolicyagent.org/docs/rest-api

## Effect-time authority remains separate

R15 current-effect authorization is intentionally preserved.

Route-time replay answers:

> What policy result was bound to this exact route admission?

Effect-time authorization answers:

> Is the first external effect currently authorized now?

The latter still re-evaluates current policy immediately before the first external effect. Deleting the route-time specialized store does not collapse these two authorities.

## Destructive migration

A database containing the obsolete `policy_decisions` table now fails closed during R9+ schema initialization.

There is no compatibility shim or silent migration. Explicit destructive migration is required.

## Validation

Targeted R8 / public API / CORE_ZERO / delivery / credential checks:

```text
Ran 33 tests
OK
```

Agent Service regression suite:

```text
Ran 204 tests
OK (skipped=5)
```

Full repository regression suite:

```text
Ran 303 tests
OK (skipped=5)
```

Final structural audit:

```text
observed top-level Agent Service classes = 165
legacy ceiling                           = 165
unexpected new classes                   = []
retired overlap with source              = []
retired overlap with ceiling             = []
replacement policy-store classes         = none
old live policy authorities              = none
```

## Next deletion pressure

The next policy-family candidate is `PolicyEvaluationCoordinator`.

It should only be deleted if its remaining composition/idempotent-receipt behavior can be expressed without inventing another local policy authority. `PolicyAdapter`, `PolicyRequest`, and `PolicyObservation` are boundary types and should be judged separately under the non-authoritative adapter rule.
