# Ordivon Current Architecture

Date: 2026-09-29
Status: **CURRENT DEPLOYED PROJECTION — NON-AUTHORITATIVE**

This document is a **rebuildable projection** of Ordivon's currently deployed architecture. Architecture contracts, execution plans, migration records, research notes, and acceptance reports remain useful evidence, but none of these documents override current physical/source/owner truth.

Machine-readable companion: `docs/architecture/deployed-architecture-r1.json`.

## 1. System shape

Ordivon is a **Modular Monorepo with independent natural owners**. Co-location does not merge authority, state, release lifecycle, or semantic acceptance.

The normal Agent-facing topology is:

```text
Agent client
   │
   ├── native Agent Skills
   │      └── Method Router Skill
   │
   └── portable Agent Plugin
             │
             v
      Cloudflare Access / OAuth
             │
             v
       Ordivon Gateway MCP
       Capability Router
       (non-authoritative)
          ┌──┼───────────────┐
          │  │               │
          v  v               v
 Linux Runtime      Windows Runtime       Host
 execution/artifact execution/artifact   external continuity
 physical truth     physical truth       semantic checkpoint truth
```

Harness is an independent Agent Run owner used by concrete workloads/callers. **Harness is not currently a routed Gateway owner** in the deployed Gateway route table.

The remote Skills MCP remains only an exact compatibility edge for ChatGPT while that client requires remote Skill projection. It is not the canonical Skill store.

## 2. Deployed owner graph

| Surface / concern | Current owner | Deployed standing |
| --- | --- | --- |
| default public Ordivon Agent ingress | Gateway MCP | deployed |
| public authentication | Cloudflare Access / OAuth | deployed |
| capability-to-owner routing | Gateway static Capability Router | deployed, non-authoritative |
| Linux Workspace / Job / Attempt / execution / Runtime Artifact | Linux Runtime | deployed authority |
| Windows Workspace / Job / Attempt / execution / Runtime Artifact | Windows Runtime | deployed authority |
| external semantic continuity / checkpoint / collaboration | Host | deployed authority |
| bounded Agent Run / cognition / Provider+Tool continuity | Harness | deployed authority, separate from Gateway routes |
| procedural method selection guidance | Method Router Agent Skill | deployed advisory Skill |
| canonical project Skill bytes | standard Agent Skill source under `.agents/skills` | deployed source |
| ChatGPT Skill compatibility | Skills MCP | retained compatibility edge only |
| portable composition envelope | Agent Plugins 1.0 package | deployed distribution surface |
| Workstation service/deployment realization | Workstation | deployed platform owner |
| long-lived orchestration where explicitly used | Temporal/provider-native workflow owner | deployed only for named consumers |
| Agent Automation / Browserless carrier | Harness/Workstation automation stack | live separate system; not Agent Service |
| historical Agent Service | none | retired; do not reconstruct |
| persistent/queryable trace backend | Vector OTLP → Tempo | deployed on demand; currently cold/inactive by default; observability-only |
| Temporal cross-process trace propagation | none proven | not claimed |

## 3. Gateway Capability Router

The Gateway's **Capability Router** is a static, rebuildable projection over natural owners. It does not own a capability registry, workflow state, Task state, Job state, or domain success.

The deployed route table currently exposes exactly these stable capability families:

| Capability | Natural owner | Owner operation family |
| --- | --- | --- |
| `execution.linux` | Linux Runtime | Runtime execution |
| `execution.windows` | Windows Runtime | Runtime execution |
| `continuity.external` | Host | Host continuity |
| `artifact.runtime` | Runtime selected by operation reference | Runtime Artifact read |

Availability is owner-derived. Gateway may normalize routing, error shape, public ABI, authentication boundary, correlation, and projections; it must not manufacture owner truth. A routed owner is `configured` only when both its endpoint and the machine identity required by that owner are configured. An endpoint URL alone is not capability realization.

Fresh 2026-09-29 public `system.describe` observes Gateway `0.7.0` with its declared non-authoritative truth role, Host configured, and both Runtime routing projections still `configured=false`. Direct Runtime owner health is a separate claim and must be checked at Runtime itself; public Gateway configuration must never be used to infer owner outage. Canonical source separately declares Gateway package `0.7.0`, MCP surface epoch `4`, and 36 tools. The exact public-carrier source commit was **not requalified in this projection** and is intentionally not inferred from canonical Git source.

For Runtime execution, once owner authentication is admitted, the normal Gateway northbound surface includes submit/get/cancel plus read-only `execution.resolve` for response-loss reconciliation by the already frozen request identity. `execution.resolve` discovers an existing Runtime Job; it does not redispatch an effect or move execution truth into Gateway.

### Host normal northbound completion

Host has destructively retired the privileged Task/Board core and fresh 2026-09-29 owner readback reports PostgreSQL Social Work Fabric schema `10` with all integrity checks healthy. Canonical Host source declares package `0.5.0`, MCP surface epoch `3`, and 28 Work/Social/Attention tools; canonical Gateway source declares package `0.7.0`, epoch `4`, and 36 total tools including `attention.reentry`, `topic.resume`, `topic.cursor.*`, and `message.relation.*`. Gateway remains projection-only while Host remains semantic owner. There is no `continuity.*` or `collaboration.*` compatibility facade, no dual-write path, and no Gateway-owned work state.

`WorkSnapshot` validation and CAS remain Host-owned. Client catalog currentness is a separate external state: the ChatGPT Gateway connector visible in this review still discovers only the older Attention subset and does not discover `attention.reentry`, while the direct Host connector still exposes legacy Task/Board actions. Those client catalogs are therefore stale even though current owner/source surfaces have advanced. They must be refreshed by the client/connector owner rather than repaired by weakening Host/Gateway boundaries or resurrecting compatibility aliases. Exact deployment commit identity is not guessed from source; where a current receipt has not been requalified, this projection says so explicitly.

### Source surface currentness vs live deployment currentness

The source manifests `services/gateway/mcp-surface.json` and `services/host/mcp-surface.json` are cheap, exact **source-surface** contracts. Repository CI binds this document's machine-readable `sourceSurfaces` projection to their package version, surface epoch, and tool count. This proves source currentness only. It does **not** prove a deployed carrier has that commit, that a client refreshed its action catalog, or that a natural owner is healthy. Live version/schema claims still require live owner/provider readback or a deployment receipt.

## 4. Method Router ≠ Capability Router

These are deliberately different components.

### Method Router

The **Method Router** is the canonical Agent Skill at:

```text
.agents/skills/method-router/SKILL.md
```

It helps an Agent choose **how to approach a problem**: which mature method, lens, standard, or procedure is appropriate. It is advisory knowledge.

It does **not**:

- route network calls;
- choose Runtime/Host authority;
- grant permissions;
- execute effects;
- become Gateway state.

### Capability Router

The **Capability Router** is the Gateway's static owner-routing projection in:

```text
services/gateway/src/ordivon_gateway/routes.py
```

It chooses **which natural owner implements one already-named stable capability**.

It does **not**:

- choose research/engineering methods;
- plan work;
- own Skill content;
- own owner availability or semantic truth.

Therefore:

```text
Method Router   = HOW should the Agent proceed?      → Agent Skill
Capability Router = WHICH owner serves this capability? → Gateway projection
```

Neither substitutes for the other.

## 5. Public and recovery surfaces

The normal distribution path contains exactly one Ordivon MCP endpoint:

```text
ordivon-gateway -> https://gateway-mcp.ordivon.com/mcp
```

Direct Runtime and Host MCP surfaces remain available only as explicit operator/admin/recovery surfaces. Their existence does not make them default Agent distribution endpoints.

The Skills MCP is separately retained for the exact ChatGPT compatibility gap proven by C03.

Direct third-party MCPs remain direct when Ordivon adds no irreducible routing, policy, normalization, verification, or composition value.

## 6. Identity boundary

Identity namespaces are not interchangeable:

```text
Cloudflare Access principal
        !=
Gateway downstream machine credential
        !=
Agent identity
        !=
Host writer label
        !=
Runtime Job identity
```

Cloudflare Access/OAuth owns public authentication. Gateway derives a stable pseudonymous principal only after JWT verification.

Gateway → Runtime owner calls require a separate machine identity appropriate to the deployed carrier; endpoint presence never substitutes for it. Linux systemd Gateway uses a systemd-projected Runtime bearer and its Windows-owner path uses a Cloudflare Access service identity. The canonical public Windows Gateway R2 carrier is currently missing its node-local Runtime bearer projections, so those execution routes are not configured even though both Runtime owners themselves are healthy.

The public principal is not replayed as downstream authorization. Node-local credential bytes remain outside source and require their explicit credential authority/materialization path.

## 7. Trace and audit boundary

MCP 2.x owns W3C Trace Context propagation for Gateway server/client calls. OpenTelemetry owns span/export semantics.

Gateway runs through the standard Python OpenTelemetry zero-code launcher. Its base production unit still defaults to:

```text
OTEL_TRACES_EXPORTER=none
```

because Workstation heavy observability is intentionally cold by default and telemetry availability must never gate product correctness. The existing opt-in trace profile switches Gateway to standard OTLP/HTTP export when the observability profile is intentionally activated.

The deployed on-demand trace path is:

```text
Gateway OpenTelemetry
  -> Vector OTLP HTTP 127.0.0.1:4318
     (OTLP traces preserved)
  -> Tempo OTLP HTTP 127.0.0.1:14318
  -> Tempo query API 127.0.0.1:3200
  -> Grafana Tempo datasource
```

Tempo 3.0.3 is the natural owner for trace persistence/query semantics; Workstation owns its local deployment. Vector remains the local observability carrier. Neither becomes Runtime, Host, authorization, completion, replay, currentness, or domain truth.

Live acceptance on 2026-09-21 proved both a direct Tempo control span and a Vector-forwarded span were queryable by exact trace ID, then proved one real Cloudflare-authenticated Gateway `execution.submit` trace was queryable in Tempo and correlated with the exact Runtime operation reference. The observability profile remains on-demand rather than a prerequisite for Gateway correctness.

Current default running posture is cold: the heavy observability target and Tempo service are inactive, the Gateway trace-export drop-in is absent, and Gateway reports `OTEL_TRACES_EXPORTER=none`. This is compatible with the deployed-on-demand standing: the capability is admitted and live-accepted, while activation remains explicit.

Harness keeps telemetry outside its semantic core. Its canonical `TraceRecorder.event_sink` may be projected by caller-owned adapters such as `services/harness/scripts/harness_otel_event_sink.py`.

Telemetry is observability only. It is never authorization, currentness, replay, completion, or owner truth.

## 8. Plugin and Skill boundary

The portable Agent Plugin uses the upstream-standard shape:

```text
plugin.json
mcp.json
[skills/]
```

The canonical `ordivon-control-plane` package is sourced from `extensions/ordivon-control-plane/` and declares exactly one MCP server: Gateway.

Selected Skills may be copied into a materialized Plugin, but canonical Skill ownership remains with the standard Skill source. Plugin packaging does not transfer semantic ownership.

No private third portable component type is introduced for local tools. Node-local Tool Binding evidence remains node-local.

## 9. Retired Agent Service

The historical Ordivon Agent Service is **RETIRED**.

Its old implementation remains useful only as historical requirements/research evidence. Current responsibilities resolve directly to natural owners such as Host, Harness, Runtime, provider-native IAM/effect APIs, MCP/A2A where applicable, and mature workflow/orchestration systems.

There is no "Agent Service 2.0" target in the current architecture. Reintroduction requires a new concrete workload and evidence that mature external ownership plus narrow adapters cannot satisfy it.

Agent Automation + Temporal + Browserless is a separate live automation/carrier system. It must not be renamed or interpreted as the retired Agent Service.

## 10. Deployed vs planned-only

A component is "current" only when repository source **and** deployment/consumer evidence establish it.

Current examples:

- Gateway normal northbound MCP;
- Linux/Windows Runtime;
- Host;
- Harness;
- Method Router Skill;
- Gateway Capability Router;
- Gateway trace/audit projection;
- Workstation Vector OTLP → Tempo persistent/queryable tracing (deployed on demand; cold by default);
- exact ChatGPT Skills MCP compatibility edge.

Not currently admitted/deployed as architecture truth:

- Gateway database;
- Gateway Task/Workflow authority;
- universal Ordivon capability registry;
- Agent Service replacement;
- always-on/mandatory trace backend;
- proven Temporal trace propagation;
- universal proxy of third-party MCPs.

## 11. Source-of-truth order

This document is a rebuildable human projection, not an authority above the system it describes. For present-tense architecture claims, use:

```text
CURRENT PHYSICAL TRUTH
  > CANONICAL SOURCE / CONFIGURATION
  > LIVE OWNER STATE / PROVIDER READ-BACK
  > DURABLE REGISTRY / RECEIPT
  > TEST / VERIFICATION EVIDENCE
  > CURRENT DOCUMENTATION
  > PLANNING / HISTORICAL ARTIFACT
```

Always select the natural owner for the exact claim. A provider effect is established by provider authority, not by Git; a source contract is established by canonical source, not by an old deployment receipt. If this document conflicts with current physical/source/owner truth, this document is stale and must be repaired rather than used to override reality.

## 12. Non-regression

`mise run repo:ci` checks the current architecture documentation against:

- the default portable Plugin's Gateway-only MCP declaration;
- the deployed Gateway route capability set;
- Method Router vs Capability Router ownership;
- retired Agent Service status;
- explicit supersession markers on known historical architecture snapshots.

Owner-native verification and live acceptance remain necessary; documentation checks are a drift detector, not implementation proof.
