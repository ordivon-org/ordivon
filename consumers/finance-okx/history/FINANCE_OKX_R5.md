# R5 — First Consumer Differential: finance-okx

## Scope

R5 selects one low-risk real consumer for migration evidence without changing consumer authority: the public, read-only OKX time endpoint.

Target:

- host: `openapi.okx.com`
- TCP port: `443`
- URL: `https://openapi.okx.com/api/v5/public/time`
- expected application result: HTTP 200 with OKX `code == "0"`

No API credential, signing material, order endpoint, account endpoint, WebSocket effect path, or live financial write was used.

## Legacy semantics observed before the differential

The current production `finance-okx` realization exposes one stable consumer listener with two provider-backed members. Its relevant policy is:

- two VPN/provider members;
- destination allowlist `openapi.okx.com:443`;
- current active member selected from the admitted pool;
- alternate provider member available for failover;
- no native-direct member;
- no eligible provider member => fail closed.

This policy is materially stricter than the generic R4 `provider -> direct` demonstration. R4 therefore cannot be copied unchanged into Finance.

## Differential composition

The temporary comparison harness used the same physical provider namespaces that were already serving the legacy production members, but did not mutate or restart those providers.

For each provider namespace, a temporary sing-box HTTP CONNECT carrier was started on a separate test-only port. HAProxy 3.4.4 then exposed a separate test-only listener with:

- the legacy pool's current active member as primary;
- the other provider member as `backup`;
- active CONNECT health checks against `openapi.okx.com:443`;
- TCP content inspection that admitted only `CONNECT openapi.okx.com:443`;
- no direct/native backend;
- no binding to production ports `19083`, `19084`, or `19085`.

HAProxy runtime statistics were used to prove which backend actually carried each test request rather than inferring path choice from application success alone.

## Observed runs

Two independent post-allowlist runs passed.

### Run 1

- legacy active member: `finance-okx-b`
- primary: `finance-okx-b`
- backup: `finance-okx-a`
- legacy proxy latencies: `0.672469`, `0.650009`, `0.757635` seconds
- Network v2 primary request: `0.524268` seconds, B sessions `1`, A sessions `0`
- after stopping only the B test carrier: request completed through A, A sessions `1`, B sessions `0`
- both test carriers stopped: CONNECT failed, curl rc `56`, HTTP code `000`
- after B test carrier recovery: request completed through B, B sessions `1`, A sessions `0`
- production proxy after test: `0.781710` seconds
- disallowed host CONNECT rejected
- disallowed port CONNECT rejected

### Run 2

- legacy active member: `finance-okx-b`
- primary: `finance-okx-b`
- backup: `finance-okx-a`
- legacy proxy latencies: `0.658881`, `0.688756`, `0.728999` seconds
- Network v2 primary request: `0.521601` seconds, B sessions `1`, A sessions `0`
- after stopping only the B test carrier: request completed through A, A sessions `1`, B sessions `0`
- both test carriers stopped: CONNECT failed, curl rc `56`, HTTP code `000`
- after B test carrier recovery: request completed through B, B sessions `1`, A sessions `0`
- production proxy after test: `0.689206` seconds
- disallowed host CONNECT rejected
- disallowed port CONNECT rejected

The backup-path request in both runs incurred approximately the configured connection-timeout interval before succeeding. That is acceptable for semantic equivalence at R5 but is a performance/recovery-latency item for the later production candidate.

## Non-interference evidence

Across the repeated differential:

- `ordivon-egress-pool-finance-okx.service` retained PID `9346`;
- `ordivon-exterior-connect-finance-okx-a.service` retained PID `100062`;
- `ordivon-exterior-connect-finance-okx-b.service` retained PID `7749`;
- production listeners `19083`, `19084`, and `19085` remained present;
- all temporary Network v2 differential services were inactive after cleanup;
- Cloudflare production A/B/canary each retained HA connection count `4`;
- Runtime remained active/listening on `127.0.0.1:8897`.

## Standing

**R5 read-only differential: PASSED.**

This result proves that the mature Network v2 carrier + HAProxy composition can preserve the observed `finance-okx` consumer behavior over the same physical providers while keeping the old production authority untouched.

It does **not** authorize cutover.

The remaining P0 is provider authority independence: Network v2 must be able to create, identify, health-check, recover, and rotate the required provider paths without reading legacy Workstation state or relying on legacy provider lifecycle ownership. Only after that is proven can an independently owned shadow listener be created and a real consumer cutover be considered.

## Why the temporary harness is not committed

The differential harness intentionally read legacy runtime state to discover the exact A/B provider namespaces and the current active member. That was appropriate for an old-vs-new comparison, but making it part of Network v2 would create the very legacy runtime dependency the greenfield rebuild is intended to remove.

R5 therefore persists the evidence and semantic contract, not the legacy-bound comparison mechanism.
