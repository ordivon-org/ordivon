# Gateway B01 — Stable Northbound Vertical Slice Acceptance

Date: 2026-09-21
Status: IMPLEMENTATION ACCEPTED / WINDOWS REMOTE OWNER BINDING DEFERRED TO C02

## Scope

B01 introduces a thin, non-authoritative MCP Gateway under `services/gateway`.

It owns only:

- stable northbound tool names;
- capability-to-owner routing;
- owner-specific lowering;
- request/response compatibility normalization;
- non-authoritative capability/system projection.

It does not own Runtime Job/Attempt state, Host continuity state, Harness runs, credentials, OAuth, Skills, Plugins, or domain completion.

## Stable northbound tools

- `system.describe`
- `capability.describe`
- `execution.submit`
- `execution.get`
- `execution.cancel`
- `artifact.read`
- `continuity.get`
- `continuity.list`

Fast-moving Runtime context values are data:

```text
capability: string
context: string | null
```

They are not closed MCP schema enums. The unit suite proves `active_user` and an unknown future provider context lower to the Windows owner without changing Gateway schema.

## Owner bindings

| Capability | Natural owner | Current B01 standing |
|---|---|---|
| execution.linux | Linux Runtime | LIVE PASS |
| execution.windows | Windows Runtime | lowering/schema PASS; remote machine binding waits for C02 edge auth |
| continuity.external | Host | LIVE PASS |
| artifact.runtime | Runtime selected by operationRef | implementation/unit PASS |

## Live evidence

### Host

Gateway -> Host `task.resume` succeeded for:

`task:arch-convergence-r1-a01r2`

Observed through normalized Gateway projection:

- revision: 2
- state: completed

### Linux Runtime

Gateway -> authenticated Linux Runtime -> `workspace.exec` produced:

- operationRef: `ordivon-exec:v1:runtime.linux:job-01a0c284-3d15-7522-8fc9-beec55f96887`
- Runtime Job: `job-01a0c284-3d15-7522-8fc9-beec55f96887`
- workspace: `ws-gateway-b01-live-target-20260921`
- sourceRevision: `b73667693296be2f06dcb1a967ce1448cc455270`
- resolution: succeeded
- mechanicallyConverged: true
- exitCode: 0
- artifactCount: 4

Gateway `execution.get` normalized the Runtime canonical nested `job.get` projection to:

- state: succeeded
- terminal: true
- exitCode: 0
- artifactCount: 4

No Runtime execution truth was copied into Gateway storage.

## Runtime compatibility adapter

The current Rust Runtime and Python MCP 2.2 client expose one cross-SDK incompatibility:

- Runtime rmcp `tools/list` output schemas currently omit the top-level `type` expected by Python `mcp-types` validation;
- Python `ClientSession.call_tool` performs a tool-output-schema lookup before accepting results.

Gateway therefore uses the official MCP HTTP/session transport but disables that second client-side result-schema lookup **only for Runtime owner sessions**. Gateway then validates every field it consumes and normalizes only its own stable contract.

Host keeps full SDK tool-result validation.

This compatibility adapter is isolated and replaceable; it is not a reason to change Runtime Core or Gateway ABI.

The Python client also logs `Session termination failed: 202` against Runtime legacy-session close semantics. Calls and owner truth remain successful. This is retained as a compatibility observation, not promoted into execution failure.

## Authentication boundary

Linux Runtime owner binding uses a private token-file **reference**. Gateway reads the private file at call time only to construct the owner Authorization header. It does not persist, emit, hash, log, or project token material.

Windows public ingress is currently Cloudflare-managed:

`canary-mcp.ordivon.com -> Cloudflare Tunnel -> Windows Runtime 127.0.0.1:18997`

Machine-to-machine Windows owner authentication is therefore deliberately deferred to C02, where Cloudflare/OAuth remains the edge authority. B01 does not invent a second Windows credential path.

## Verification

Owner-local verification:

```text
uv lock --check
uv sync --locked
ruff check
ruff format --check
pytest
```

Current B01 suite: 7/7 PASS before canonical Runtime job.get normalization, then 7/7 PASS after compatibility/auth work; the final suite is rerun by `mise run gateway:verify`.

## Acceptance boundary

B01 implementation is accepted as the stable northbound vertical slice because:

- Gateway is non-authoritative;
- Linux Runtime execution is live-proven;
- Host continuity is live-proven;
- Windows schema/lowering is stable and future-context tolerant;
- owner authentication remains external;
- the remaining Windows remote machine binding is an explicit C02 edge-auth dependency, not hidden Gateway work.

B01 does **not** authorize connector cutover yet.
