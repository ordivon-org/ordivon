# Gateway C02 — Public Cutover Acceptance

Date: 2026-09-21  
Status: ACCEPTED

## Decision

The public Ordivon Gateway cutover is accepted for the C02 boundary.

The accepted public semantic waist is:

```text
ChatGPT / Agent client
  -> Cloudflare Managed OAuth / Access
  -> gateway-mcp.ordivon.com
  -> Cloudflare Tunnel
  -> loopback-only Ordivon Gateway :8899
       -> Linux Runtime
       -> Host
       -> Windows Runtime through canary-mcp.ordivon.com
```

Gateway remains a non-authoritative routing/projection owner. This acceptance does not transfer Runtime, Host, Skill, Plugin, or domain truth into Gateway.

## E01 — Exact Cloudflare plan

The fixed-root Cloudflare/OpenTofu controller produced reviewed plan:

`0869b0cd6500f62fe2e074c96ac0e67ceec6f9153388046172957ba4d34d637a`

Source identity:

- source commit: `18976e1f0ac64a7bff198548527ec2fbdde270ba`
- source digest: `sha256:f3c9c126f7a3ae03979ddd5da4a6e99e627518abdb35ad3f6a7dfe8be7e24466`

Observed plan:

- create: 0
- update: 0
- delete: 0
- replace: 0
- no-op: 10
- dangerous changes: none
- unexpected mutations: none
- semantic gate: PASS
- Windows Service Auth census: PASS
- eligible_for_apply: true

The plan confirmed exactly one Gateway ingress mapping:

`gateway-mcp.ordivon.com -> http://127.0.0.1:8899`

and retained the existing catch-all rule last.

## E02 — Reviewed plan application

The exact reviewed plan digest was applied.

Result:

- status: applied
- zero_drift: true
- Gateway public hostname: `gateway-mcp.ordivon.com`
- Gateway Access audience: `033a28ccc44c7a696b0e09bf7b8c533a8ab3454e198c8d10aad570ab992e04ae`
- Windows Runtime Access application: existing and verified
- Windows Service Auth policy disposition: existing
- Gateway Windows service credentials materialized: true

Private credential files:

- `/etc/ordivon/gateway/windows-access-client-id`
- `/etc/ordivon/gateway/windows-access-client-secret`

Both were observed as root-owned mode 0600. Secret values are not recorded in this acceptance.

Plan and apply receipts are also root-owned mode 0600 under the operations-v2 Cloudflare handoff receipt owner.

## E03 — Gateway deployment binding

Observed live deployment:

- current Gateway release: `c0d6f94fd69c10d7c3112f515c00dc6d66d25688`
- service: active
- service: enabled
- bind: `127.0.0.1:8899`
- public Access drop-in: loaded
- Windows service-identity drop-in: loaded
- `ORDIVON_GATEWAY_TRUST_CF_ACCESS=true`
- health: `{"status":"ok","service":"ordivon-gateway"}`

The MCP path intentionally does not trust loopback source identity. When public Access verification is enabled, direct unauthenticated loopback `/mcp` requests are rejected because no Cloudflare Access assertion exists. `/health` remains the unauthenticated local health surface.

## E04 — Public live E2E

### Unauthenticated public boundary

An unauthenticated request to:

`https://gateway-mcp.ordivon.com/mcp`

returned HTTP 401 with Cloudflare Managed OAuth `WWW-Authenticate` metadata. The request did not receive Gateway MCP business data.

### Authenticated discovery and projection

The connected ChatGPT Ordivon Gateway connector successfully called the live public Gateway.

Observed system owners:

- `runtime.linux` — configured
- `runtime.windows` — configured
- `host` — configured

Observed capabilities:

- `artifact.runtime` — available
- `continuity.external` — available
- `execution.linux` — available, contexts `trusted_local`, `contained_local`
- `execution.windows` — available, contexts `limited`, `elevated`, `active_user`

Observed capability projection digest:

`sha256:9389efa988373d5e921c982185c4ba907dcc8f0db186e5b09677dfb4cb4d296f`

A Host continuity list call succeeded and returned current Host-owned task projections.

### Linux execution

Public Gateway submission:

- capability: `execution.linux`
- Runtime owner: `runtime.linux`
- command: `/usr/bin/true`
- operation: `ordivon-exec:v1:runtime.linux:job-01a0c412-3113-78a2-84c1-1547ec4ac080`

Terminal observation:

- state: succeeded
- terminal: true
- deliveryDisposition: committed
- executionDisposition: succeeded
- exitCode: 0
- recoveryRequired: false
- Runtime artifacts: 4

### Windows execution

The first Windows attempt intentionally demonstrated owner separation: a Linux-owned workspace ID was rejected by Windows Runtime with `WORKSPACE_NOT_FOUND`.

The corrected E2E used the Windows Runtime-owned clean workspace:

`ws-win-launch-identity-diagnosis-r1-20260921`

Public Gateway submission:

- capability: `execution.windows`
- Runtime owner: `runtime.windows`
- command: `C:\\Windows\\System32\\cmd.exe /d /c exit 0`
- authority: `limited`
- operation: `ordivon-exec:v1:runtime.windows:job-01a0c413-2594-76c3-8c2d-e8b411696f25`

Terminal observation:

- state: succeeded
- terminal: true
- deliveryDisposition: committed
- executionDisposition: succeeded
- exitCode: 0
- recoveryRequired: false
- Runtime artifacts: 5
- includes a Runtime-owned `windows-start` identity artifact

This proves the public Gateway route reaches the native Windows Runtime owner without treating a Linux workspace as portable execution state.

## E05 — Frozen acceptance and rollback coordinates

Current Gateway release:

`c0d6f94fd69c10d7c3112f515c00dc6d66d25688`

Retained Gateway release inventory includes earlier immutable releases under:

`/opt/ordivon/gateway/releases/<commit>`

The Gateway installer changes `/opt/ordivon/gateway/current` atomically through a `current.next` symlink rename. A Gateway release rollback therefore remains a local deployment-owner operation over retained immutable releases.

Cloudflare requires no reverse mutation for this acceptance because the reviewed plan and post-apply plan were zero-drift/no-op. The exact reviewed plan and apply receipt remain available under the private operations-v2 owner.

## Consumer metadata residual

The connected ChatGPT connector still advertises the retired `capability.list` tool in its cached tool catalog. Calling it reaches the current Gateway and returns `Unknown tool: capability.list`.

The current Gateway service correctly exposes `capability.describe` as the canonical capability projection. This residual is therefore classified as a consumer connector metadata/cache refresh issue and is carried into the Plugin/real-consumer P03 gate. It is not Gateway semantic authority and does not reopen C02.

## Non-claims

This acceptance does not claim:

- Agent Plugin cutover is complete;
- ChatGPT connector metadata cache has refreshed;
- direct Runtime/Host public endpoints are retired;
- Skills MCP bridge retirement is complete;
- Runtime physical success implies domain semantic success;
- Gateway owns durable task, workflow, artifact, or domain truth.

C02 acceptance authorizes W3 Plugin cutover work.
