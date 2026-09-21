# Gateway → Host Northbound Acceptance — 2026-09-22

Status: **SERVER DEPLOYED / LIVE OWNER PATH ACCEPTED / CLIENT CATALOG REFRESH PENDING**

## Purpose

Close the composition gap between the Gateway-only default Agent Plugin and Host's normal semantic-continuity/collaboration surface without moving Host semantics into Gateway.

Gateway remains a non-authoritative ABI/router. Host remains the owner of Task identity, revision, WorkingCheckpoint validation, Board persistence, and semantic continuity.

## Canonical and live identity

- Gateway implementation commit: `268cfed5accdd7d89de8ae4bf04d6d9c869e5493`
- live Gateway release: `/opt/ordivon/gateway/releases/268cfed5accdd7d89de8ae4bf04d6d9c869e5493`
- Gateway package/server version: `0.2.0`
- live service: active/running, zero restarts at acceptance
- public ingress: `https://gateway-mcp.ordivon.com/mcp`

## Normal Host northbound seam

The deployed Gateway public tool set now contains 15 tools. Host-normal operations are:

- `continuity.get`
- `continuity.list`
- `continuity.observe`
- `continuity.adopt`
- `continuity.checkpoint`
- `continuity.attention`
- `collaboration.list`
- `collaboration.search`
- `collaboration.post`

`host.status` is deliberately absent. Host Doctor/admin remains a direct-owner recovery/operator surface.

Checkpoint payloads are opaque objects at the Gateway boundary. Gateway does not copy the Host WorkingCheckpoint schema; Host validates the currently deployed checkpoint contract.

## Verification

Static and repository gates:

- Gateway full verification: 38 tests PASS
- repository CI: PASS
- architecture documentation drift checks: PASS
- exact Gateway tool-set regression gate updated to the 15-tool deployed surface
- `capability.list` remains absent

Read-only real-owner vertical slice through candidate Gateway code against live Host:

- continuity.list: PASS
- continuity.get: PASS
- continuity.observe: PASS
- continuity.attention: PASS
- collaboration.list: PASS
- collaboration.search: PASS

Live mutation/collaboration acceptance used one explicitly disposable historical Task:

- Task: `task:gateway-host-northbound-acceptance-r1-20260922`
- adopt revision 1: committed
- Board message sequence: 17795
- attention route to exact Task: PASS
- exact Board list: PASS
- Board search: PASS
- checkpoint revision 2 with `abandon`: committed
- final Task state: `abandoned`
- observed event order: checkpoint, adopt

The acceptance Task is terminal and is not current product work.

After deployment, the already-authorized public Gateway connector successfully returned `system.describe` with Gateway version `0.2.0` and Host configured, and `continuity.get` successfully read the acceptance Task through Cloudflare → Gateway → Host.

## Remaining consumer-side residual

The currently attached ChatGPT Gateway connector snapshot is still stale:

- it still advertises retired `capability.list`;
- calling that name reaches the live Gateway and returns `Unknown tool: capability.list`;
- it has not yet surfaced the seven newly deployed Host-normal northbound tools.

No server-side connector reload/invalidation action is exposed to Ordivon in the current tool environment.

Therefore the remaining action belongs to the MCP connector/client owner. Ordivon must not add a private surface epoch, copied tool catalog, compatibility alias, or Host/Gateway registry to compensate.

Owner source and authenticated live MCP `tools/list` are capability truth. A connector snapshot is a consumer projection.

## Result

The previous composition gap is closed server-side:

```text
default Agent Plugin
    -> Gateway
       -> Host normal continuity/collaboration
```

Direct Host is no longer required by the portable default Plugin for normal operations. It remains an explicit operator/admin/recovery surface. A currently stale external connector session may still require refresh before it can invoke the new Gateway names.
