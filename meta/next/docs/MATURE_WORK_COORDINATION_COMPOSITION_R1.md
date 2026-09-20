# Mature Work / Workflow / Agent Composition R1 — 2026-09-13

> **SUPERSEDED AS A MANDATORY HOST CUTOVER — 2026-09-14.** The provider analysis below remains useful, but Plane/MAF activation is no longer a prerequisite for retiring Host v1 or for considering Ordivon's work-continuity architecture acceptable. Host v1 is archived. `ordivon-host-v2` is retained as a deliberately small active continuity/work-state utility. Temporal, n8n, Runtime, MAF and Plane remain independent mature capabilities to activate only when a real workload needs their distinct responsibility.

## Current standing after supersession

- **Host v2:** `RETAIN_MINIMAL_ACTIVE`; active/enabled locally, clean source, local pytest green on 2026-09-14.
- **Plane:** optional/dormant candidate; staged installer is not an architectural debt and does not need activation merely to replace Host.
- **MAF:** optional agent-orchestration capability; use when a real multi-agent stage benefits from it, not as a Host replacement requirement.
- **Temporal:** durable long-running workflow substrate when such workflow semantics are actually needed.
- **n8n:** integration edge, not work-state authority.
- **Runtime:** physical execution truth.
- **Domain owners:** semantic acceptance.

The controlling rule is substitution economics: mature external capability is preferred when it solves a real responsibility better, but a larger external platform is not automatically preferable to a small, bounded, already-working local component.

## Purpose

This decision reopens the premature Host/Board responsibility closure and replaces it with an evidence-driven migration to mature external owners. Candidate project selection is restricted to GitHub projects with at least 10k stars at selection time; star count is a screening threshold, not sufficient evidence by itself.

The historical Host/Board implementation is not restored. Its useful responsibilities are transferred to specialized mature systems and only then may old ownership be considered fully retired.

## Previously selected candidate composition (reference, not mandatory cutover)

| Responsibility | Selected owner | Local standing | Authority boundary |
| --- | --- | --- | --- |
| human/agent work management, work items, boards, comments, relations, cycles/modules/pages | **Plane** | selected; Community v1.4.2 installer staged, runtime not activated | work-management state only; not domain/execution truth |
| durable long-running process, retry/timer/wait/recovery | **Temporal** | active through Operations v2 | workflow/process truth only |
| multi-agent orchestration inside an agentic stage | **Microsoft Agent Framework (MAF)** | v1.18.0 installed; concurrent fan-out/fan-in acceptance passed | agent-run/orchestration state only |
| API/SaaS/webhook/integration edge and optional MCP façade | **n8n** | active through Operations v2 | integration mechanics only |
| physical command/job execution and retained attempt evidence | **Ordivon Runtime** | active | mechanical execution truth only |
| operational metrics/alert facts | **Prometheus** | active | operational observation only |
| operator visualization | **Grafana** | active container | view only |
| ChatGPT provider occurrence materialization | **Agent Automation** | active MCP | provider-specific birth/continuation/effect fencing only |
| scientific/business/artifact/etc. acceptance | **domain-native V&V owner** | task-specific | semantic truth remains with the domain |

```text
Human / Controller Agent
          |
          v
        Plane  <---------------- work-management authority
          |
          | references/selects
          v
       Temporal <--------------- durable process authority
          |
          +-- agentic stage ---> Microsoft Agent Framework
          |                         |
          |                         +--> Agent Automation --> ChatGPT occurrences
          |                         +--> future native/A2A agents
          |
          +-- deterministic ----> Snakemake / CI / domain workflow
          |
          v
        Runtime <--------------- mechanical execution authority
          |
          v
        Reality
          |
          v
     Domain-native V&V

Integration edges: n8n
Operational observation: Prometheus -> Grafana
```

No component above is a replacement global Host. Each has a bounded authority.

## Why Plane

Plane is selected because its mature project model already includes Work Items, Cycles, Modules, Views, Pages and product/project-management behavior. The current Ordivon need is closer to modern issue/work management than to a universal semantic Task engine.

Plane may own: work-item existence, title/description, project/module/cycle membership, work-management status/priority, assignees, relationships, comments and board/list/view organization.

Plane must not own: scientific validity, Runtime execution, Temporal workflow mechanics, artifact validation, provider-effect truth or other domain acceptance.

### Plane local standing

- target: Community `v1.4.2`;
- official installer staged at `/root/.local/share/ordivon/plane-community-v1.4.2/setup.sh`;
- SHA-256 `466b2e0d6137f72b577e10bd8af20a1f5c11268fc1294445fed7571c99d40031`;
- activation: `HOLD_RESOURCE`;
- observed workstation memory before activation: about 7.8 GiB total / 5.2 GiB available while the existing Ordivon stack is running;
- upstream self-host guidance: 4 GiB minimum, 8 GiB recommended for production.

The service is deliberately staged but not started until coexistence headroom is safe.

## Why Microsoft Agent Framework

MAF is selected because it directly supplies sequential, concurrent fan-out/fan-in, handoff, group collaboration, checkpoint/restart, human-in-the-loop, observability and provider-flexibility patterns without requiring a new Ordivon coordination ontology.

### Local standing

- installed: `agent-framework==1.18.0`;
- environment: `/root/.local/share/ordivon/agent-framework-1.18.0/.venv`;
- Python 3.12.13;
- deterministic `ConcurrentBuilder` acceptance executed `A01` and `A02` and produced `A01:probe`, `A02:probe` followed by framework fan-in;
- standing: `MECHANICS_ACCEPTED / REAL_PROVIDER_INTEGRATION_PENDING`.

This proves local orchestration mechanics, not ChatGPT-provider integration or semantic multi-agent quality.

## Current ChatGPT-agent integration gap

Agent Automation already exposes campaign/birth/continue/reconcile/human-handoff operations. But the current continuation surface returns admission/census information and provider-submit evidence explicitly records `assistantOutputRead=false`.

Therefore a ChatGPT occurrence cannot yet be treated as a complete MAF participant. The justified residual adapter is:

```text
Agent Automation occurrence
  -> send/continue (already accepted)
  -> observe completed provider turn (missing)
  -> retrieve exact assistant output + turn identity (missing)
  -> MAF participant adapter
```

This must remain provider-specific and must not grow into a Task/Board system.

## Temporal vs MAF

Temporal owns macro durable process state across long waits, retries, external events, restarts and human waits. MAF owns collaboration among agents inside an agentic stage.

Example:

```text
Temporal: Paper-2 lifecycle
  literature
  -> experiment
  -> review
       -> MAF ConcurrentBuilder(A01..A08)
       -> synthesis
  -> revision
  -> submission
```

Do not encode the same durable state machine independently in both systems.

## n8n role

n8n remains the API/SaaS/webhook integration edge. After Plane activation a normal path is:

```text
Plane webhook/API -> n8n validation/routing -> Temporal signal/update OR notification OR bounded provider call
```

n8n may expose a thin MCP façade when useful, but authoritative read/write still occurs in Plane or the natural owner.

## Competition considered (>=10k GitHub-star screen)

### Work management

**Selected: Plane.**

**Alternative: OpenProject.** OpenProject is stronger when conventional PMO/portfolio needs dominate: Gantt/scheduling, time tracking, budgeting/cost reporting, formal project planning, meeting/wiki/forum features. Plane is preferred now because Ordivon's immediate need is lightweight work-item/cycle/module/view collaboration around one human and many agents. Re-evaluate OpenProject if formal portfolio/time/cost governance becomes recurrent.

### Multi-agent orchestration

**Selected: Microsoft Agent Framework.**

**Alternative A: LangGraph.** Strong low-level option for long-running stateful agents, durable execution, explicit graph state and human-in-the-loop. It is the primary fallback if MAF's participant/provider model proves incompatible with real Ordivon workloads.

**Alternative B: CrewAI.** Strong for role-oriented Crews plus event-driven Flows. Not selected because Ordivon already has separate durable-process and provider-materialization layers; adopting Crew/Flow as another broad ownership layer would overlap more responsibilities.

**Rejected for new use: AutoGen.** Upstream is in maintenance mode and directs new users to Microsoft Agent Framework.

### Durable process/workflow

**Selected: Temporal.** Apache Airflow, Prefect and Dagster are mature alternatives for scheduled/data/DAG orchestration, but Ordivon's common process need repeatedly includes long waits, event-driven continuation and recovery. Snakemake remains the scientific DAG owner where that domain fit is stronger.

### Integration automation

**Selected: n8n.** **Alternative: Node-RED.** Node-RED is mature for event/IoT/flow wiring; n8n is already accepted locally and better matches SaaS/API/human-approval/current MCP workloads. There is no evidence for operating two generic flow engines.

### Observability

**Selected: Prometheus + Grafana.** **Alternative: SigNoz.** SigNoz offers a more integrated product, but the current Prometheus/Grafana/OTel-oriented stack is already operational and no migration benefit is proven.

### Event bus

**Deferred: NATS/JetStream.** Activate only after repeated need for durable asynchronous cross-service delivery/replay or independently deployed services/agents. Current coordination does not justify a message bus.

## Interface rule

MCP is a transport/tool interface, not an ownership layer.

```text
Agent/MAF
  -> native MCP when a mature provider supplies one
  -> thin n8n/API MCP façade when stable Agent access is useful
  -> direct SDK/API inside a bounded service when MCP adds no value
```

Do not create a single `ordivon-host-mcp` that re-exports and re-owns every capability.

## Historical cutover gates — superseded as Host-v2 retirement prerequisites

Final Host/Board responsibility closure requires a real workload proving:

1. Plane can create/find/read/update its managed work item;
2. natural-language recovery can resolve that item without a Host Task ID;
3. Plane references the correct domain/workflow/agent/execution owners without claiming their truth;
4. Temporal resumes durable process where required;
5. MAF executes a real multi-agent stage;
6. Agent Automation returns exact provider output for ChatGPT occurrences used as participants;
7. results/decisions are written back to Plane without making Plane the semantic validator;
8. operational failure/attention is visible through existing observation/integration systems;
9. at least one historical Host/Board-backed workload is migrated and independently verified.

These gates remain useful if Ordivon later chooses to activate the full Plane + Temporal + MAF work-management composition, but they no longer gate Host v2 retention or Host v1 retirement.

Current standing:

`HOST_V1_RETIREMENT = COMPLETE`

`HOST_V2 = RETAIN_MINIMAL_ACTIVE`

`PLANE_ACTIVATION = OPTIONAL / DEMAND_GATED`

`MAF_ACTIVATION = OPTIONAL / WORKLOAD_GATED`
