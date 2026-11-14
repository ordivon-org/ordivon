# Gateway R6: Native Owner Result Truth and Agent Consumers

Source-oriented architecture note (2026-11-14). The source revision is bound by
the Git commit that contains this file. This note is **not** installed-service
or domain-success evidence.

## Problem: the same Owner response reached different Agent truth

Runtime is authoritative for Job, Attempt, terminality, delivery and artifacts.
Gateway is a **non-authoritative** MCP adapter. The previous Gateway
`execution.submit` and `execution.cancel` strict-text repair was not applied to
`execution.get`: it used `str(status)`, `str(deliveryDisposition)`, and
`str(executionDisposition)`. Consequently malformed Owner JSON, including
`true`, lists and objects, could be recast as apparently meaningful status
strings on the Agent observation path.

This is a consumer-visible representation bug, not a missing scheduler or
Owner database. The correct response is one shared **pure wire projection**
contract. No Owner identity, effect, authority, or semantic completion migrates
into Gateway.

## Consumer and authority graph

| Producer/consumer | Native contract | Responsibility |
| --- | --- | --- |
| PG Runtime / native Windows Runtime | `workspace.exec`, `job.cancel`, `job.observe` | Original physical Job/Attempt, terminality, delivery and effect evidence |
| Gateway `ExecutionCommandMethods` | `execution.submit`, `execution.cancel` | Project Job reference and typed Owner receipt without inventing status |
| Gateway `ExecutionObservationMethods` | `execution.get` | Project same typed Owner wire fields, retain genuine reconciliation/UNKNOWN |
| Gateway `owner_protocol` | `_owner_receipt_state`, `_owner_optional_disposition` | Shared pure JSON-value recognition; no separate state store |
| MCP Tool consumers / Harness `plugin_gateway_effect.py` | `execution.submit/get/cancel` receipt, `delivery_disposition` | Decide continuation/reconciliation from typed receipt; no completion inferred from string alone |
| Domain owner (e.g. Research) | verified experiment/result contract | Separately judges scientific or business success |

The graph was inspected from original
`services/gateway/src/ordivon_gateway/` and
`services/harness/src/ordivon_harness/plugin_gateway_effect.py`, with
`services/gateway/tests/test_pg_real_runtime_owner.py` as a native
Runtime consumer. It is a **partial** consumer graph; external connectors and
all Principal/Actor scopes remain separately qualified.

## Logical contract (thought → logic → ability)

- **Thought:** Design by Contract, refinement, open-world status vocabulary,
  fail closed on malformed evidence, single authoritative Owner.
- **Logic:** `Native JSON → typed state/disposition | GatewayError`;
  successful Gateway projection never converts a non-string into a status.
  Presence of a native status key with wrong type is an error; completely
  absent state is `"unknown"`. Missing or null optional disposition remains
  `None` / UNKNOWN. Valid non-empty Owner strings are forwarded unchanged;
  Gateway does not define or freeze the Owner state enum.
- **Ability:** existing Python `owner_protocol.py` helper reused by both
  `execution_commands.py` and `execution_observations.py`; pytest
  characterization and adversarial tests; original MCP SDK, Pydantic and
  Runtime are unchanged.

```text
Valid(owner, state) -> StateString OR "unknown" if state entirely absent
Valid(owner, disposition) -> String OR None if absent/null
Invalid(nonstring/empty claimed state or non-null disposition) -> reject
Terminal, ResultAvailable, DomainSuccess are independent propositions.
```

## Refinement and installation acceptance

1. Unit-level source-bound negative control:
   `tests/test_execution_observation_contract_r6.py` (15 malformed
   observations initially pass incorrectly against source baseline, then
   must fail closed after the fix). Cross-check
   `tests/test_execution_receipt_types.py` for submission/cancellation.
2. Reuse existing `mise run gateway:verify` route/Owner tests and
   `gateway:formal:verify` for its existing distinct route/status/authz
   models. These models **do not** formally verify the new text helper:
   full TLA-to-Python refinement is UNKNOWN, not PASS.
3. Verify real Owner `job.observe` and Gateway `execution.get` on Linux
   and Windows with exact OperationRef/Artifact identities; reject false
   return types in source tests. Do not inject malformed JSON into production
   Runtime or fake a successful domain action.
4. Release is independently gated by `packaging/check_live_host_admission.py`,
   installed SourceCut, Security's genuine Principal→Actor grants, a genuine
   Host Owner bearer, direct Host migration and positive/negative Agent
   canaries. Source/PR merge does not satisfy any of these stages.

## Non-goals / pending

Do not add a Gateway Job registry, second scheduler, policy engine, forced
retry on uncertain side effects, Host actor impersonation, or closed Runtime
state enum. Remaining work: complete cross-Agent/HTTP principal scope
verification, Owner outputSchema normalization, external connector consumer
graph, positive service-account Host release canary, and an explicit formal
refinement mapping if the complexity is economically justified.
