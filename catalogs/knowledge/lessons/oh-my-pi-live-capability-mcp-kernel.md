# Oh My Pi Live Capability + MCP Binding Kernel — extracted design and prototype specification

Status: **REGISTERED / PROTOTYPE-READY**  
Registered: 2026-09-14

## One-sentence model

**Discover capability providers independently of the Agent loop, normalize and connect them asynchronously, then refresh the live available Tool catalog without confusing discovery with Run or turn authorization.**

## Problem

A modern Agent environment may have:

- built-in Tools;
- project/user plugins;
- MCP servers;
- late network connections;
- OAuth-gated servers;
- providers that appear/disappear;
- server-side `tools/list_changed` updates.

Blocking Agent startup until every provider is healthy is slow and fragile. But dynamically adding discovered Tools directly to model authority is unsafe.

OMP separates config discovery, canonical server normalization, connection/listing and live session registry refresh. Ordivon should adopt the live mechanism while retaining stronger three-stage authority semantics.

## Core authority model

```text
Provider discovered
      |
      v
Available Capability Catalog
      |
  caller/Run admission
      v
Run Capability Binding
      |
  per-turn projection
      v
Turn Tool Surface
```

Absolute law:

```text
available != Run-admitted != turn-admitted
```

A Tool arriving from MCP after the Run started MUST NOT become callable unless the Run's authority policy already permits that capability or the caller explicitly updates/creates authority according to the Harness contract.

## Minimum data structures

```ts
type ProviderId = string;

type ProviderConfig = {
  id: ProviderId;
  transport: "stdio" | "http" | "sse";
  endpoint?: string;
  command?: string[];
  enabled: boolean;
  authRef?: string;
  source: string;
  priority: number;
};

type CapabilityDescriptor = {
  capabilityId: string;
  providerId: ProviderId;
  remoteName: string;
  schema: object;
  description?: string;
  versionDigest: string;
};

type ProviderState = {
  providerId: ProviderId;
  state: "discovered" | "connecting" | "ready" | "auth_required" | "failed" | "disabled";
  capabilities: CapabilityDescriptor[];
  errorClass?: string;
  revision: number;
};
```

## Discovery pipeline

```text
config sources
  -> discovery providers
  -> normalize ProviderConfig
  -> dedupe by stable provider id/name + priority
  -> apply enable/disable policy
  -> asynchronous connect
  -> list capabilities
  -> Available Catalog revision
```

Do not expose raw config precedence to the model. The Agent sees only admitted capabilities and bounded provider status when useful.

## Connection manager

Minimum interface:

```ts
startAll(): void
connect(providerId): Promise<void>
disconnect(providerId): Promise<void>
reloadConfigs(): Promise<void>
getAvailableCapabilities(): CapabilityDescriptor[]
subscribeCatalogChanges(cb): unsubscribe
```

The manager owns connection lifecycle, not semantic Tool permission.

## Deferred capability wrapper

For providers expected but not ready, an optional deferred descriptor may exist in the **available/discovery plane**.

Do not put a deferred Tool into the turn surface unless invoking it has defined behavior such as:

- bounded wait for provider readiness;
- explicit `PROVIDER_NOT_READY` result;
- no hidden retry that could duplicate an external effect.

For the first prototype, simply omit unavailable Tools from turn admission and refresh once ready.

## Live refresh

When provider catalog changes:

```text
MCP list_changed / reconnect / reload
   -> ProviderState revision++
   -> recompute Available Catalog
   -> evaluate existing Run Binding
   -> update next-turn Tool projection only if authorized
```

The current in-flight model request should not have its Tool schema mutated underneath it. Apply catalog changes at a clear turn boundary.

## Stable Tool identity

Do not use only display names.

Recommended identity:

```text
providerId + remoteToolName + schema/version digest
```

A model-facing alias may be generated, but receipts/evidence should retain the stable capability identity.

If schema changes during a Run, treat it as a new capability revision and require the binding policy to decide whether it is compatible.

## Invocation flow

```text
1. Model emits Tool call from current Turn Tool Surface.
2. Harness resolves turn Tool -> Run binding -> current CapabilityDescriptor.
3. Verify provider is still usable or return typed not-ready/unavailable result.
4. Dispatch exactly once according to Tool effect semantics.
5. Record Tool intent/receipt in Harness.
6. Provider result becomes observation, not semantic truth.
```

MCP transport success does not prove external-world effect success.

## Reload/add/remove operations

Operator/application actions may:

- add provider;
- remove provider;
- enable/disable;
- reconnect;
- reauthenticate;
- reload discovery sources.

These mutate provider availability only.

If a removed provider owns an unresolved Tool effect, its removal does not erase the effect identity; recovery may require external/operator reconciliation.

## Failure classes

| Class | Example | Agent action |
|---|---|---|
| configuration invalid | malformed command/url | operator/config repair |
| auth required | OAuth not complete | caller/operator authentication |
| provider unavailable | process/network down | wait/reconnect or choose other capability if semantically equivalent |
| schema changed | server tool changed | refresh next-turn surface and reassess |
| response lost after dispatch | uncertain external effect | reconcile original Harness Tool intent; do not blindly call replacement provider |

## Capability equivalence

Two providers exposing similar Tools are not automatically interchangeable after dispatch.

Before any effect, a higher layer may route between equivalent capabilities. After uncertain dispatch, provider substitution is not a recovery strategy unless external semantics prove it safe.

## Minimum prototype

- load two static MCP server configs;
- connect asynchronously;
- normalize tools into `CapabilityDescriptor`;
- maintain monotonic catalog revision;
- Harness Run binds an exact allowlist/pattern at creation;
- next turn projects only currently available + Run-authorized Tools;
- simulate provider appearing late and `list_changed`;
- preserve exact Tool capability id in call receipt.

No marketplace or OAuth UI is required for the first prototype.

## Acceptance tests

1. Agent Run starts while one MCP provider is still connecting.
2. Late provider readiness changes available catalog without restarting Run.
3. Tool not permitted by Run remains unavailable even after discovery.
4. Authorized late Tool appears only on the next turn.
5. Provider removal removes future projection but does not delete historical Tool receipts.
6. Tool schema revision changes capability version identity.
7. Duplicate configs resolve deterministically by precedence.
8. Provider failure does not crash unrelated provider Tools.
9. Lost response after effect dispatch is not handled by switching providers and repeating the action.
10. Catalog refresh is inspectable and does not become a second durable Harness state owner.

## Project-study acceptance

### One-sentence test

PASS: OMP's MCP subsystem shows that capability discovery/connection can be live and asynchronous while the Agent session continues.

### Prototype test

PASS: the discovery pipeline, catalog revision, authority stages and turn-bound refresh rules are explicit enough to implement a two-provider live MCP prototype.

## Verdict

**PASS — ADOPT LIVE DISCOVERY; STRENGTHEN WITH ORDIVON RUN/TURN AUTHORITY SEPARATION.**
