# LangSmith Deployment — Agent Service Kernel R1

Status: **CURRENT OFFICIAL-DOC DECOMPOSITION / PROTOTYPE-READY**
Checked: 2026-09-17
Scope: LangSmith Deployment / Agent Server public architecture and APIs.

## 1. One-sentence model

**LangSmith Deployment is a stateful agent application hosting system whose control plane stores desired deployment state while a polling/reconciling data plane materializes Agent Servers that persist assistants, threads, runs, checkpoints, schedules and memory behind a stable API.**

It is not primarily LangGraph the library: the deployment/runtime layer can host application code beyond graph-only logic, and the public service kernel is the Agent Server plus control/data-plane lifecycle.

Primary sources:
- https://docs.langchain.com/langsmith/data-plane
- https://docs.langchain.com/langsmith/self-hosted
- https://docs.langchain.com/langsmith/server-api-ref
- https://docs.langchain.com/langsmith/data-storage-and-privacy
- https://docs.langchain.com/langsmith/diagnostics-self-hosted

## 2. Shell / kernel / mature substrates

| Class | Elements |
| --- | --- |
| Product shell | LangSmith UI, Studio, SaaS tenancy/pricing, GitHub deployment integration |
| Transferable kernel | desired-state deployment control plane, listener/operator reconciliation, Agent Server resource model, worker/run queue, persistent state/checkpoints, cancellation/streaming channels, revisions, A2A/MCP endpoints |
| Mature substrates | containers/Kubernetes, PostgreSQL, Redis/PubSub, HTTP, A2A, MCP, tracing/telemetry |

## 3. Kernel graph

```text
                CONTROL PLANE

 UI/API -> Deployment desired state / revision
                    |
             polled by Listener
                    |
                    v
                DATA PLANE

 Listener -> task queue -> deployment worker/operator
                         -> Agent Server deployment
                               |
            +------------------+------------------+
            |                  |                  |
        HTTP API            Run workers       Persistence
            |                  |                  |
 assistants/threads/runs       |              PostgreSQL
 crons/store/A2A/MCP           |             checkpoints/store
            |                  |
            +------ Redis communication --------+
                    wake/cancel/stream
```

The unusually valuable detail is the explicit split between **durable facts in PostgreSQL** and **ephemeral worker communication in Redis**.

## 4. Responsibility map

| Module | Responsibility | Durable truth? | Notes |
| --- | --- | --- | --- |
| Control plane | desired deployments/revisions and management API/UI | yes | does not need to execute agent runs itself |
| Listener | poll desired state and enqueue reconciliation work | no/ephemeral progress | bridges control to data plane |
| Operator/deployment worker | materialize/update/delete compute resources | current infrastructure state | substrate-specific in production |
| Agent Server | stable agent application service/API | yes through backing stores | exposes assistants/threads/runs/crons/store/A2A/MCP |
| Assistant | configured instance of a graph/application | yes | configuration identity separate from run/thread |
| Thread | continuity namespace for accumulated run outputs/state | yes | not universal user identity |
| Run | one invocation of an assistant/graph | yes | background worker executes it |
| Cron | scheduled run definition | yes | scheduling surface |
| Store | long-term key-value memory | yes | separate from thread/checkpoint semantics |
| PostgreSQL | durable server resources and default checkpoint store | yes | authoritative persistence for threads/runs/assistants/crons/store |
| Redis | wake workers, cancel requests, stream events, transient retry metadata | no user/run truth | communication/ephemeral only |
| Run worker | execute queued run | no independent domain truth | retrieves durable run data from Postgres |

## 5. State and identity model

Minimum identities:

```text
DeploymentId + Revision
AssistantId
ThreadId
RunId
CronId
StoreNamespace/Key
CheckpointId
Trace/RequestId
```

Control-plane deployment identity must remain distinct from Agent Server application state.

### Run lifecycle hypothesis from public contracts

```text
create durable Run record
    |
wake queue worker via Redis sentinel
    |
worker loads Run from PostgreSQL
    |
execute application / checkpoint transitions
    |
stream transient events via Redis PubSub
    |
persist resulting durable state
    |
terminal Run status
```

Cancellation is a control message to the worker; Redis is not the durable record of the run itself.

## 6. End-to-end deployment flow

```text
1. user/API creates or updates deployment revision
2. control plane persists desired deployment state
3. listener polls control-plane API
4. listener enqueues reconciliation task
5. worker/operator creates/updates/deletes Agent Server infrastructure
6. deployment becomes available behind stable service endpoint
7. clients create assistants/threads/runs through Agent Server API
```

This is classic desired-state reconciliation and should be treated as a generic service pattern rather than a LangSmith-specific invention.

## 7. End-to-end run flow

```text
1. client invokes Assistant, optionally within Thread
2. Agent Server persists Run metadata
3. queue wake-up makes a worker eligible
4. worker reads authoritative run/application state
5. graph/agent code executes and checkpoints state
6. worker emits stream events for connected clients
7. cancellation may arrive over the control channel
8. durable final/intermediate state remains in backing store
```

This gives Ordivon a concrete reference for separating **service Task/Run truth** from **worker notification transport**.

## 8. Interface contracts worth retaining

A vendor-neutral reconstruction needs:

```text
Deployment.create(spec, revision) -> deployment
Deployment.update(id, revision) -> desiredState
Deployment.delete(id) -> desiredState
Deployment.observe(id) -> desired/observed state

Assistant.create(config) -> assistant
Thread.create(metadata) -> thread
Run.create(assistant, thread?, input) -> run
Run.cancel(runId) -> ack
Run.stream(runId) -> Event*
Run.get(runId) -> durable state

Store.get/put(namespace, key, value)
```

A2A and MCP should remain adapters/endpoints, not replacement service ontologies.

## 9. Failure / durability boundaries

### Desired vs observed deployment state
A deployment request is not the same as a materialized Agent Server. The listener/operator closes that gap through reconciliation.

### Durable run truth vs queue wake-up
The worker should retrieve work from durable storage; an ephemeral wake-up message can be lost/repeated without becoming the canonical run record.

### Streaming vs persistence
Redis PubSub transports live output but does not retain events. Durable state/checkpoints live elsewhere.

### Retry
Retry metadata is not semantic success. A repeated worker attempt belongs to the same durable run identity unless the application explicitly defines a new run.

### Cancellation
A cancellation request is a control signal; final observed cancellation must still be reflected in durable run state.

## 10. Mechanisms worth retaining

1. Control plane owns **desired state**, not execution.
2. Data plane owns **materialization and execution**, not global product intent.
3. Listener/reconciler connects desired and observed deployment state.
4. Durable work is stored before ephemeral worker wake-up.
5. Queue communication is replaceable and must not become domain truth.
6. Service resources have typed identities: assistant/thread/run/cron/store.
7. Long-running state/checkpoints belong to the application runtime surface.
8. A2A and MCP are first-class protocol endpoints at the service edge.
9. Standalone Agent Server remains possible without the control plane, proving the runtime server is independently meaningful.

## 11. What Ordivon should not copy

- LangGraph graph ontology as the universal Ordivon agent model;
- one global PostgreSQL schema mirroring LangSmith resource names;
- Redis specifically when another queue/pubsub substrate is already mature locally;
- Kubernetes operator machinery when Ordivon Host/Runtime can satisfy the current scale;
- LangSmith UI/Studio as the Agent Board;
- Thread as universal user/task/session identity;
- checkpoint state as external-world effect truth.

## 12. Minimal clone

```text
ControlStateStore
    |
DeploymentController API
    |
Listener/Reconciler
    |
RuntimeAdapter
    |
AgentServer
├── AssistantStore
├── ThreadStore
├── RunStore
├── RunQueue
├── WorkerPool
├── CheckpointStore
└── EventStream
```

### Minimal build order

1. Durable `Deployment{desiredRevision, observedRevision, state}`.
2. Reconciler that converges one local AgentServer process to desired revision.
3. `Assistant`, `Thread`, `Run` persistent records.
4. Background worker that consumes durable pending runs.
5. Ephemeral wake-up channel separate from durable run record.
6. Cancellation and streaming channels.
7. One checkpointed application execution.
8. A2A and MCP edge adapters.
9. Crash/restart reconciliation.

### Behavioral acceptance

1. Create desired deployment; reconciler starts server and records observed revision.
2. Change revision; reconciler updates server without losing service identity.
3. Create Run, lose a wake-up message, and still recover work from durable pending state.
4. Restart worker mid-run and preserve last committed checkpoint/run state.
5. Cancel a running task and reach a durable terminal state.
6. Stream output without treating stream transport as durable history.
7. Start AgentServer standalone without control plane.
8. Invoke the same server through ordinary HTTP plus one MCP/A2A adapter.

## 13. Mapping to Ordivon

| LangSmith | Ordivon | Decision |
| --- | --- | --- |
| control plane desired deployments | Agent Service desired fleet state | EXTRACT |
| listener/operator | Agent Service reconciler + Host local supervision | EXTRACT/ADAPT |
| Agent Server | service-facing Agent endpoint above Harness/Runtime | EXTRACT thin interface |
| Run | Agent Service Task execution/run mapping | ADAPT; do not equal Runtime Job automatically |
| Thread | Session/conversation namespace | ADAPT |
| PostgreSQL durable work state | Agent Service durable store | ADOPT mature DB semantics |
| Redis wake/cancel/stream | transport | ADOPT/replaceable |
| checkpoint | Harness/application logical checkpoint | ON_DEMAND / separate from Runtime effect evidence |
| A2A/MCP endpoints | Agent Service protocol adapters | ADOPT standards |

### Direct lesson for Host

LangSmith's listener/operator pair helps separate two roles that Ordivon has historically mixed:

```text
Agent Service Reconciler
  decides desired agent/deployment presence
        |
        v
Host
  proves/localizes node/process continuity
        |
        v
Runtime
  executes accepted work
```

Host should not become the global desired-state service merely because it observes local continuity.

## Project-study acceptance

- **ONE-SENTENCE TEST: PASS**
- **MODULE-COMPLETENESS TEST: PASS**
- **MINIMAL-CLONE SPEC TEST: PASS**
- **BEHAVIORAL-ACCEPTANCE TEST: PASS (SPECIFIED, NOT YET IMPLEMENTED)**

## Verdict

**EXTRACT THE DESIRED-STATE + DURABLE-RUN SERVICE KERNEL: LangSmith's clearest contribution is the explicit control/data-plane reconciliation and the separation of durable Agent Server resources from ephemeral worker communication.**
