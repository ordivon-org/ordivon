# Network Stoppage Recovery Census R2 — 2026-09-27

## Purpose

This is the currentness-bounded successor to `NETWORK_STOPPAGE_RECOVERY_CENSUS_R1_20260926.md`. R1 is retained as historical evidence and is not rewritten.

R2 answers one question: which historical Ordivon work that once stopped on network/egress failure is still a Network problem now?

The governing rule remains:

```text
historical blocker
  -> current owner
  -> current source
  -> current physical transport
  -> consumer consequence
  -> RESOLVE | HANDOFF | RECONCILE | RETIRE | HOLD
```

The standing laws are unchanged: `OPEN != current work`, `service active != consumer consequence`, `dirty Workspace != unfinished project`, and provider admission/authentication failure is not physical network failure.

## Source and evidence cut

Canonical source revision: `7cd4b62ccc6fbb1d7b49998716e2c71c742d8135`.

Primary fresh Runtime evidence:

- core service/carrier census: `job-01a0e345-db05-7f20-91fa-ca499b3c1a1a`;
- Finance/Supply-Chain/Docker consequence census: `job-01a0e346-c6f9-7530-9b40-de7e529ca6c4`;
- OPA/X/Public-Web closeout census: `job-01a0e347-e287-7413-baf6-550bfbc9e66b`;
- Host PostgreSQL stale-continuity census: `job-01a0e349-a934-7471-af96-65f7c57c32d2`;
- control-plane projection/tool-surface census: `job-01a0e34a-20e7-7c50-8a9e-17a690426e40`.

This document is navigation/recovery evidence, not financial-write authority, provider-account authority, authentication authority, Security authorization, or production identity selection.

## Current physical Network standing

The Network recovery substrate is now converged around one provider identity/session and one shared physical carrier:

```text
th-bkk / provider-b
        |
ONE WireGuard identity/session
        |
nv2-browserless-prod
        |
shared provider carrier :19680
    +---+-------------------+
    |                       |
 Finance                Supply-Chain
 exact fencing          exact OCI fencing
 19283..19292           19581
```

Fresh physical facts:

- `network-v2-browserless.target`, WireGuard, DNS and provider-carrier services are active and enabled;
- selected provider site is `th-bkk`, endpoint `151.240.88.133:51820`;
- provider-carrier readiness is `READY` with application consequences for OpenAI, Docker Registry, Anthropic and OKX;
- Finance is `READY`, mode `all`, with no direct fallback;
- Supply-Chain is `READY`; Docker Registry/Auth, GCR, Artifact Registry and Elastic Registry all return expected application responses while an unknown destination is rejected;
- `/etc/network-v2/finance/provider-endpoints.json` and `/etc/network-v2/supply-chain/provider-endpoints.json` are absent and no duplicate provider-session process exists;
- Docker is bound to `http://127.0.0.1:19581` and the retired `10.254.177.2:19381` proxy is no longer the daemon authority;
- all nine Archivematica containers recovered and remain running after the Docker restart;
- the locked OPA image digest is present locally and the unchanged policy suite passed 34/34 tests;
- bounded X Reality transport is active on `127.0.0.1:19681`, returns an X application-layer `401`, rejects unknown destinations and has no direct fallback;
- the old Public-Web units are `not-found`, `/etc/network-v2/public-web` is absent, and ports 19380/19381 have no listener.

## Recovery reclassification

### Market Capital / SOXL decision support

Historical network blocker: Finance target/egress inactive, followed by current-destination failures.

Current Network standing: **NETWORK_RECOVERED / HANDOFF_TO_CAPITAL**.

Finance target and egress are active and current `finance-ready all` is `READY`. The old Host checkpoint that says `consumer:finance:converge` is required is stale. Resume only the Capital read-only evidence/decision workflow. This closeout grants no external financial write authority.

### Admission Fabric pinned OPA OCI replay

Historical network blocker: `BLOCKED_EXTERNAL_TRANSPORT` through the stale Docker registry proxy.

Current Network standing: **NETWORK_BLOCKER_RESOLVED / HANDOFF_TO_SECURITY_IDENTITY**.

`meta/next/evidence/acceptance/admission-fabric-r2-20260927.json` records the exact pinned OPA image, OPA 1.20.2 and 34/34 policy tests PASS through the current Supply-Chain transport. AF-S2/AF-S3/AF-S4/AF-S5 remain separate authorization, workload-identity and reference-witness work. Network recovery does not close them.

### Security ClusterFuzzLite / registry acquisition

Historical blocker: Docker/GCR/Artifact Registry acquisition unavailable.

Current Network standing: **TRANSPORT_RECOVERED / HANDOFF_TO_SECURITY_PROVIDER_VERIFICATION**.

The shared Supply-Chain consumer now proves Docker Hub, GCR and Artifact Registry transport consequences. Any remaining ClusterFuzzLite/OSS-Fuzz orchestration gap must be re-entered as Security/provider-runtime verification, not as generic Network debt.

### X Reality connector

Historical network blocker: `api.x.com` unreachable across tested routes.

Current Network standing: **NETWORK_RECOVERED / HANDOFF_TO_IDENTITY_AUTH**.

The bounded X authority is active and `x-reality-ready` returns `READY` with X HTTP 401, unknown-destination rejection, no direct fallback, and no authentication attempt. The remaining frontier is explicitly principal/user-context authentication: `credentialMaterialized=false`, `userContextProven=false`. Do not add more Network machinery to solve this identity gate.

### Public-Web scoped proxy

R1 standing: inactive orphan deployment awaiting retirement/reconciliation.

Current standing: **PHYSICAL_RETIREMENT_COMPLETE**.

The former Public-Web target, egress and bridge units are not installed, `/etc/network-v2/public-web` is absent, and no 19380/19381 listener remains. Historical workspace/source provenance may still be retained, but there is no live deployment to restart or delete.

### Operations D2, Gatus observability, old Finance OKX false-green, Network E2E R8

Current standing: **STALE_HOST_CONTINUITY_RECONCILIATION_REQUIRED**.

Read-only Host PostgreSQL authority still reports these historical works as `open`, but their checkpoints reference retired observers, dependency-acquisition failures, legacy egress-pool semantics, or Runtime 502 conditions that are no longer current physical blockers. Preserve their history; re-enter their objectives against current owners or mark Host continuity complete/superseded once the Host task northbound surface is usable.

### Host Market-Capital and X tasks

Current standing: **STALE_HOST_CONTINUITY_RECONCILIATION_REQUIRED**.

The Market-Capital checkpoint still says Finance is inactive, while Finance is currently `READY`. The X checkpoint still says destination transport is unavailable, while bounded X transport is currently `READY`. These are direct examples of `OPEN != current work` and historical `nextAction != current action`.

## Control-plane debt discovered during closeout

Network data-plane recovery is not blocked by the following, but Agent UX/currentness is:

1. direct Linux Runtime and Windows Runtime project `available=true`, while Gateway 0.5.0 currently projects both execution owners as `available=false` with `ExceptionGroup` observation errors;
2. Host PostgreSQL authority and `host.status` are healthy, but `task.list`, `task.resume`, `task.observe` and `board.search` are exposed to clients while the deployed Host MCP returns `Unknown tool` for those names.

Classification: **PROJECTION_AND_NORTHBOUND_UX_DEBT**, not Network failure.

Do not repair these by widening Network ownership. Route them to the existing Agent UX / Gateway / Host convergence work.

## Current owner handoff map

| Former Network recovery item | Network standing | Current owner/frontier |
|---|---|---|
| Finance / SOXL transport | recovered | Capital read-only evidence/decision workflow |
| OPA OCI replay | recovered | Security/Identity AF-S2+ |
| ClusterFuzzLite registries | transport recovered | Security provider-runtime qualification |
| X destination transport | recovered | Identity/Auth user-context proof |
| Public-Web orphan | retired | historical evidence only |
| stale Host Network tasks | physical wake occurred | Host continuity reconciliation |
| Gateway owner availability projection | owner healthy, projection false-negative | Gateway/Agent UX |
| Host task tool catalog | Host healthy, northbound dispatch inconsistent | Host/Agent UX |

## Network project closeout rule

The historical Network-stoppage recovery campaign should no longer grow by absorbing authentication, authorization, Host bookkeeping, or Gateway projection defects.

Network re-entry is warranted only when a fresh named consumer consequence proves a physical transport failure under the current owner/source. Otherwise hand off to the domain authority above.

The remaining campaign work is evidence/currentness reconciliation, not another Network platform redesign.
