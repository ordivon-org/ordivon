# Gateway Windows Control-Plane Migration R1

## Standing

- Source authority: `5bd241df24da3259c1c6e3637bf3fc513129e4b9`
- Workspace: `ws-gateway-windows-carrier-r1-20260922`
- GW0: **COMPLETE**
- GW1: **IN PROGRESS**
- Production WSL Gateway: **UNCHANGED**

## Frozen facts

- Current source package version: **0.3.0**
- Current source northbound surface: **16 MCP tools**
- Live Gateway reports: **0.2.0**
- Current ChatGPT connector projects: **9 tools**, including stale `capability.list`
- Source regression: **39/39 PASS** using `uv.lock` + CPython 3.14.7
- Windows can reach WSL Runtime/Host/Gateway through `127.0.0.1:8897/8898/8899`
- Native Windows Runtime listens on `127.0.0.1:18997`

## Target invariant

```text
WSL OFF
  Gateway             AVAILABLE
  runtime.windows     AVAILABLE
  runtime.linux       unavailable
  continuity.external unavailable
```

Owner recovery after WSL returns must not require a Gateway restart.

## Waves

| Wave | Nodes | Gate |
|---|---|---|
| GW0 | GW01-GW03 | baseline + semantic/route freeze |
| GW1 | GW04-GW06 | Windows toolchain + immutable release + service carrier qualification |
| GW2 | GW07-GW10 | least-privilege Windows candidate service |
| GW3 | GW11-GW13 | three owner routes |
| GW4 | GW14-GW15 | degraded health + artifact routing |
| GW5 | GW16-GW18 | auth + ingress + connector parity |
| GW6 | GW19-GW20 | destructive/lifecycle acceptance |
| GW7 | GW21-GW22 | canary cutover + WSL carrier retirement |

## Service-carrier decision

Do not write custom SCM glue first.

Primary qualification candidate: **Shawl 1.9.0**.
Reference candidate: **WinSW**.

Reasons for the qualification order:

1. Shawl has a current stable 2026 release.
2. It is a portable Rust wrapper for arbitrary commands.
3. It supports Ctrl-C stop, stop timeout, restart policy, logging, working directory and Job-Object process-tree kill.
4. It can be registered with ordinary SCM tooling and does not require a separate installer protocol.

WinSW remains a mature reference, but current stable is 2.x while 3.x is still prerelease.

## No-rewrite rule

Carrier migration should preserve semantic files with minimal or zero changes:

- `contracts.py`
- `routes.py`
- `service.py`
- `mcp_server.py`

Expected new work is primarily:

```text
services/gateway/packaging/windows/
services/gateway/tests/*windows*
services/gateway/planning/
```

Any semantic-core diff requires a separate justification and differential test.

## Destructive acceptance

Final retirement is forbidden until this exact fault succeeds:

1. Windows Gateway and Windows Runtime are running.
2. Stop/terminate WSL.
3. Gateway remains reachable through normal northbound ingress.
4. `execution.windows.available == true`.
5. `execution.linux.available == false`.
6. `continuity.external.available == false`.
7. Restart WSL.
8. Linux Runtime and Host become available without restarting Gateway.

