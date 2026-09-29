# Agent Service Platform Reference Map R1

Status: **FIRST CROSS-PROVIDER DECOMPOSITION WAVE**
Checked: 2026-09-17
Targets: AWS AgentCore, Microsoft Foundry Agent Service, Google Gemini Enterprise Agent Platform, LangSmith Deployment.

## One-sentence models

### AWS AgentCore
**A modular managed agent operations substrate that separates managed harness from hosting runtime and composes registry, gateway, identity, policy, memory, sandbox, observability, evaluation and optimization around them.**

### Microsoft Foundry Agent Service
**A managed agent deployment/governance service that runs declarative prompt agents or customer-code hosted agents behind versioned endpoints while centralizing runtime, toolboxes, identity/RBAC, observability and publishing.**

Official docs: https://learn.microsoft.com/en-us/azure/foundry/agents/overview

### Google Gemini Enterprise Agent Platform
**An end-to-end agent lifecycle platform organized as Build / Scale / Govern / Optimize, with managed Agent Runtime, Sessions and Memory plus Agent Registry, per-agent identity, Agent Gateway/policy enforcement, observability and evaluation.**

Official docs: https://docs.cloud.google.com/gemini-enterprise-agent-platform/agents

### LangSmith Deployment
**A stateful long-running Agent Server deployment platform that separates a desired-state control plane from a reconciled data plane and exposes assistants, threads, runs, schedules, memory store, A2A and MCP as server resources.**

Official docs:
- https://docs.langchain.com/langsmith/data-plane
- https://docs.langchain.com/langsmith/self-hosted
- https://docs.langchain.com/langsmith/server-api-ref

## Shared kernel emerging across providers

```text
                   CONTROL / SERVICE PLANE

 Agent Registry / Definitions / Revisions
                  |
       desired deployment state
                  |
      scheduler / reconciler / router
                  |
                  v
                 DATA / EXECUTION PLANE

 Runtime / Agent Server / hosted container
                  |
             Session / Run
                  |
          Harness / agent code
                  |
       Gateway / Tool capability plane
          |                   |
       Identity             Policy
          |                   |
          +------ effect -----+
                  |
          Events / OTel traces
                  |
        Evaluation / operations
```

No provider uses exactly these names, but the responsibility split recurs strongly enough to use as the starting hypothesis for Ordivon Agent Service.

## Cross-provider module map

| Generic responsibility | AWS AgentCore | Microsoft Foundry | Google Agent Platform | LangSmith Deployment |
| --- | --- | --- | --- | --- |
| Agent catalog/registry | Agent Registry | Entra Agent Registry / publishing surfaces | Agent Registry | deployment/assistant catalog rather than broad enterprise resource registry |
| Agent definition/version | Registry records + runtime versions/endpoints | prompt/hosted agent versions | deployed agent revisions | deployments/revisions + assistants |
| Runtime hosting | AgentCore Runtime | Agent Runtime / hosted agents | Agent Runtime | Agent Server data plane |
| Managed harness | AgentCore Harness | prompt-agent managed loop; hosted agent brings code/framework | ADK/managed agent paths; Runtime accepts frameworks | LangGraph/other app code inside Agent Server |
| Session/conversation | runtime/harness sessions | conversations/session persistence | Sessions | Threads |
| Work invocation | runtime invocation | Response / invocation | interaction/runtime invocation | Runs / Thread Runs / Stateless Runs |
| Tool/capability gateway | AgentCore Gateway | Toolboxes / managed MCP endpoint / Tools Service | Agent Gateway + Registry | MCP endpoints; app-defined tools |
| Identity | AgentCore Identity/IAM | Microsoft Entra agent identity/RBAC | per-agent identity + IAM/IAP | platform/API key/auth; less central as a distinct agent identity product |
| Policy enforcement | Policy + Gateway | RBAC/network/safety/tool governance | IAM/Semantic Governance/Model Armor at Gateway | application/platform auth; not equivalent full agent policy plane |
| Memory | AgentCore Memory | conversations + attachable memory | Memory Bank | Store + checkpoints/thread state |
| Reconciliation | managed service internal | managed service internal | managed service internal | explicit control-plane desired state + listener/operator reconciliation |
| Protocols | MCP + A2A | Responses/Invocations + A2A/MCP hosting options | A2A + MCP | A2A + MCP endpoints |
| Observability/eval | OTel/CloudWatch + Evaluations | tracing/metrics/evals/App Insights | Observability + Evaluation | LangSmith tracing/evaluation |

## The strongest individual lessons

### AWS: separation of Harness and Runtime
AWS now documents the boundary explicitly: Runtime provides hosting/isolation/scaling/session/auth/observability infrastructure while Harness provides the orchestration loop. This is the cleanest external reference for Ordivon's current Harness/Runtime split.

### Microsoft: agent type may be declarative or customer-code while Service stays stable
Foundry exposes prompt agents and hosted agents under one Service. The Service contract survives whether the harness is managed configuration or customer container code. This argues that Ordivon Agent Service must not depend on one harness implementation.

### Google: Registry + Identity + Gateway + Policy is the governance spine
Google automatically registers deployed agents, assigns per-agent identities, and routes governed agentic communication through Agent Gateway/IAM. This is a strong model for treating an agent as a first-class principal and service resource, not merely a process.

### LangSmith: desired-state control plane + polling/reconciling data plane is observable and reproducible
LangSmith documents the listener pattern directly: control plane owns desired deployment state; the data-plane listener polls it and creates/updates/deletes Agent Servers to converge current state. PostgreSQL owns durable server resources, while Redis is communication/ephemeral metadata. This is especially relevant to future Ordivon Agent Service / Host separation.

## Proposed Ordivon responsibility boundary

```text
Ordivon Agent Service
├── Agent Registry / Definition / Revision
├── Agent Birth / Identity / Lifecycle
├── Goal
├── Task / assignment / scheduling
├── Board projections
├── Session / communication
├── A2A routing
├── Plugin/Capability Registry composition
├── Policy / service routing
├── cluster desired state
├── reconciliation with Hosts/Runtimes
└── fleet observability
          |
          v
Ordivon Host
├── node presence
├── wake / continuity / re-entry
├── local supervision
└── reconcile requested local presence
          |
          v
Ordivon Runtime
├── workspace
├── Job / Attempt
├── execution
├── cancellation / recovery
├── artifact/evidence
└── physical effect boundary
          |
          v
Harness
├── model/context loop
├── skill disclosure
├── tool selection
├── subagent delegation
└── termination
```

## External-common vs Ordivon-specific

### Strong external-common kernel
- agent definition/version/registry;
- deployment/runtime lifecycle;
- sessions/runs;
- desired/observed state or equivalent managed lifecycle;
- capability/tool gateway;
- agent/workload identity;
- policy/authorization boundary;
- standard interop protocols;
- observability/evaluation.

### Ordivon organizational semantics layered above it
- `Agent Birth` as a named end-to-end provisioning protocol;
- explicit `Agent Goal` hierarchy;
- `Agent Task` as organization-owned semantic work independent of Runtime Job;
- `Agent Board` as fleet/team work projection;
- explicit organization/team formation and service-request classification.

These should be designed as local service semantics while reusing external substrates below them.

## First minimal Ordivon Agent Service kernel

```text
1. AgentDefinitionStore
2. AgentRevision / PluginProfile
3. AgentIdentity binding
4. DesiredAgent / Deployment record
5. HostRegistry
6. RuntimeAdapter
7. Session
8. ServiceTask
9. Assignment/Scheduler
10. Reconciler(desired -> observed)
11. A2A/MCP Router
12. Event/Projection stream
```

### Deliberately not in the first kernel
- universal long-term memory;
- optimizer;
- marketplace/UI shell;
- custom policy language;
- custom network proxy;
- custom container scheduler;
- another execution engine;
- board as source of truth.

## Next decomposition order

1. AWS AgentCore — full kernel completed in `aws-agentcore-agent-service-kernel-r1.md`.
2. LangSmith Deployment — next, because its control-plane/data-plane listener and durable run model are the clearest public implementation architecture.
3. Google Agent Platform — focus Registry/Identity/Gateway/Policy/A2A governance spine.
4. Microsoft Foundry Agent Service — focus prompt-vs-hosted Agent abstraction, identity, Toolboxes and publication/version lifecycle.
5. Cross-provider synthesis -> `ORDIVON_AGENT_SERVICE_MINIMAL_KERNEL_R1` executable prototype contract.
