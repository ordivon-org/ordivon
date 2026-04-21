# Architecture Diagram

This diagram is governed by the canonical baseline in [architecture-baseline](./architecture-baseline.md).

## Canonical Layer Diagram

```text
+-------------------------------------------------------------------+
|                        EXPERIENCE LAYER                           |
| Web UI / Chat UI / Dashboard / Wiki UI / Reports UI / Alerts     |
| Purpose: user interaction, result presentation, task entry       |
+-------------------------------------------------------------------+
                               |
                               v
+-------------------------------------------------------------------+
|                        CAPABILITY LAYER                           |
| Market Brief / Asset Analysis / Portfolio Review / Journal       |
| Postmortem / Strategy Search / Thesis Management                 |
| Purpose: package lower-level abilities into product actions      |
+-------------------------------------------------------------------+
                               |
                               v
+-------------------------------------------------------------------+
|                      ORCHESTRATION LAYER                          |
| Task Router / Workflow Engine / Context Builder / Scheduler      |
| Model Router / Skill Dispatcher / Result Writer / Retry/Fallback |
| Purpose: runtime control plane and task organization             |
+-------------------------------------------------------------------+
            |                     |                     |
            |                     |                     |
            v                     v                     v
+---------------------+ +---------------------+ +---------------------+
| GOVERNANCE LAYER    | | INTELLIGENCE LAYER  | | EXECUTION LAYER     |
| Risk / Permission   | | Models / Prompt /   | | Tools / Skills /    |
| Audit / Guardrails  | | Summarize / Extract | | Connectors / Reports|
| HITL                | | Classify / Embed    | |                     |
| Purpose: constrain  | | Purpose: think      | | Purpose: act        |
+---------------------+ +---------------------+ +---------------------+
            |                     |                     |
            +---------------------+---------------------+
                                  |
                        +---------+---------+
                        |                   |
                        v                   v
+-----------------------------------+ +--------------------------------+
| KNOWLEDGE DOMAIN                  | | STATE DOMAIN                   |
| Wiki / Research / Journal / Thesis| | Portfolio / Positions          |
| Strategy Library / Postmortems    | | Orders / Trades / Risk Budget  |
| Memory / Retrieval / Indexes      | | Task State                     |
| Purpose: learned knowledge        | | Purpose: source of truth       |
+-----------------------------------+ +--------------------------------+
                        |                   |
                        +---------+---------+
                                  |
                                  v
+-------------------------------------------------------------------+
|                      INFRASTRUCTURE LAYER                         |
| PostgreSQL / Object Storage / Vector Index / Cache / Queue       |
| Scheduler / Monitoring / Logging / Secrets / Docker / Deploy     |
| Purpose: storage, scheduling, monitoring, deployment support     |
+-------------------------------------------------------------------+
```

## Core Runtime Flow

```text
User Request
   |
   v
Experience Layer
   |
   v
Capability Layer
   |
   v
Orchestration Layer
   |
   +--> Governance Layer
   |
   +--> State Domain
   |
   +--> Knowledge Domain
   |
   +--> Execution Layer
   |
   +--> Intelligence Layer
   |
   v
Orchestration aggregates results
   |
   +--> Governance re-check
   +--> Write to Knowledge
   +--> Update State
   +--> Generate reports and dashboard outputs
   |
   v
Experience Layer renders the result
```

## Mental Model

```text
[How the user uses the system]
Experience + Capability

[How the system organizes work]
Orchestration + Governance

[How the system thinks and acts]
Intelligence + Execution

[What the system remembers and treats as true]
Knowledge + State + Infrastructure
```

## Boundary Reminders

```text
Model is not system truth
Tool is not business workflow
Wiki is not the state ledger
Orchestrator is not the risk judge
Frontend is not the business core
Knowledge is not State
```

## Functional Summary

```text
Intelligence  = knows how to think
Execution     = knows how to act
Orchestration = knows how to organize
Governance    = knows how to constrain
Knowledge     = knows what was learned
State         = knows what is true now
Infrastructure= keeps everything running
```
