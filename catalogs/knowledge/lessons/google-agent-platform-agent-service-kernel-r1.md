# Google Gemini Enterprise Agent Platform — Agent Service Kernel R1

Status: **CURRENT OFFICIAL-DOC DECOMPOSITION / PROTOTYPE-READY**
Checked: 2026-09-17
Scope: Gemini Enterprise Agent Platform public architecture, especially Scale/Govern surfaces.

## 1. One-sentence model

**Google Agent Platform is an end-to-end agent lifecycle service that combines managed agent execution and session/memory state with a governance spine of registry, per-agent identity, gateway-routed communication, policy enforcement, observability and evaluation.**

It is not primarily ADK: ADK is one build-time framework, while the platform is designed to host/manage agents and protocols beyond a single framework.

Primary sources:
- https://docs.cloud.google.com/gemini-enterprise-agent-platform/agents
- https://docs.cloud.google.com/gemini-enterprise-agent-platform/govern/gateways/agent-gateway-overview
- https://docs.cloud.google.com/gemini-enterprise-agent-platform/govern/policies/iam-overview
- https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/runtime/agent-identity

## 2. Shell / kernel / substrates

| Class | Elements |
| --- | --- |
| Product shell | Google Cloud console, Gemini Enterprise commercial packaging, Model Garden/Studio UI |
| Transferable kernel | managed Runtime, Sessions, Memory, Registry, agent identity, Gateway, IAM/policy enforcement, observability/evaluation, agent relationships |
| Mature substrates | IAM/IAP, mTLS/DPoP-style bound credentials, MCP, A2A, cloud runtimes, telemetry, policy controls |

## 3. Platform decomposition

Google explicitly presents four pillars:

```text
BUILD      -> Studio / ADK / models / MCP
SCALE      -> Agent Runtime / Sessions / Memory / Sandbox / scheduling
GOVERN     -> Registry / Identity / Gateway / Policies / audit/security
OPTIMIZE   -> Observability / Evaluation / examples / improvement
```

For Ordivon Agent Service, **Scale + Govern** are the most relevant kernel; Build belongs mainly to Harness/Plugin tooling and Optimize belongs to Research/Eval services.

## 4. Kernel graph

```text
Agent Definition / Deployment
          |
          +------> Agent Registry
          |            |
          |       metadata/capabilities
          v            |
     Agent Runtime <----+
          |
       Session ----> Memory Bank
          |
          v
     Agent Identity
          |
          v
     Agent Gateway -----------------------+
       |        |                          |
       |      IAM / semantic policy        |
       |      Model Armor                  |
       |                                   |
       +--> MCP server / Tool / Endpoint   |
       +--> A2A Agent ---------------------+
          |
          v
 Observability / Audit / Evaluation
```

## 5. Responsibility map

| Module | Responsibility | Durable truth? |
| --- | --- | --- |
| Agent Runtime | deploy/host/scale agents | deployment/runtime state |
| Sessions | per-conversation interaction continuity | yes |
| Memory Bank | long-term cross-session extracted/retrieved memory | yes |
| Agent Registry | centralized queryable catalog of agents/endpoints/MCP servers and capability/version metadata | yes |
| Agent Identity | first-class per-agent principal tied to lifecycle | identity authority/provider-owned |
| Agent Gateway | traffic controller/enforcement point for user-agent, agent-tool and agent-agent communication | routing/policy config |
| IAM/Policies | authorize communication/effects | policy definitions |
| Model Armor/security | content/prompt-oriented safety controls | policies/config |
| Observability/Audit | network/application agent activity evidence | telemetry/audit records |
| Evaluation | quality assessment | eval records |

## 6. Identity is a core service object

Google's current docs make the agent a principal rather than treating the service account as an implementation detail. Agent identities are tied to agent lifecycle and can be used as IAM principals. Credentials can be bound to intended runtime environments rather than copied into prompts/application state.

Transferable rule:

```text
Agent identity != user identity
Agent identity != Host identity
Agent identity != Runtime Job identity
```

A request may carry a chain such as:

```text
human/service caller
      -> AgentIdentity
      -> delegated target authorization
```

The chain must remain auditable.

## 7. Registry + Gateway + Policy forms the governance spine

Registry supplies resolvable resource identity/capability metadata. Gateway sees governed traffic. Policy evaluates whether one agent/principal may reach a registered agent, endpoint, MCP server or tool.

This is much stronger than letting each agent decide locally which remote endpoint is safe.

Generic flow:

```text
source AgentIdentity
      |
      v
Gateway receives target request
      |
resolve target / capability metadata
      |
Policy(AgentIdentity, target, tool/action, context)
      |
 allow -----------------> route
 deny ------------------> block + audit
```

Google recommends dry-run policy deployment before enforcement, which is a useful operational pattern for Ordivon policy migrations.

## 8. Protocol boundary

A2A agents, MCP servers and generic endpoints can all appear as governed resources. This suggests the Service should own routing/governance while keeping protocol adapters replaceable.

```text
Agent Service Router
├── A2A adapter
├── MCP adapter
└── HTTP/provider adapter
```

Do not force all three into one private wire protocol.

## 9. Failure/security boundaries

1. **Registry presence is not authorization.** Resource discovery and access policy are separate.
2. **Identity issuance is not effect approval.** Policy still evaluates each relevant route/action.
3. **Gateway policy only protects routed traffic.** Bypass paths must be structurally restricted if the gateway is meant to be authoritative.
4. **Memory is not session state.** Cross-session memory requires separate identity/retention semantics.
5. **Observability is not policy.** Logs can prove what happened but should not become the enforcement engine.
6. **Prompt/content defense is not authorization.** Model Armor-like safety controls and IAM-like policy solve different problems.

## 10. Mechanisms worth retaining

- per-agent lifecycle-bound identity;
- registry-backed service discovery;
- centralized gateway for inter-agent/tool traffic;
- policy keyed by source agent identity and target resource;
- governance of A2A and MCP as ordinary service traffic;
- separation of Session and long-term Memory;
- audit/observability around gateway interactions;
- dry-run -> enforce policy rollout.

## 11. What Ordivon should not copy

- Google Cloud resource hierarchy/URNs as local domain ontology;
- a Google-specific gateway implementation;
- a second general IAM engine;
- long-term user-personalization memory as a mandatory Agent Service dependency;
- Build/Studio product surfaces as part of minimal service kernel;
- one giant `agent` identifier replacing task/session/runtime identities.

## 12. Minimal clone

```text
AgentRegistry
AgentIdentityStore/Adapter
RuntimeAdapter
SessionStore
Gateway
PolicyDecisionAdapter
ProtocolTargets {A2A, MCP, HTTP}
Audit/TraceSink
```

### Build order

1. Register/version one Agent and one MCP/A2A target.
2. Bind one first-class AgentIdentity to the deployed agent.
3. Route all outbound target calls through Gateway.
4. Evaluate allow/deny policy using source identity + target/action.
5. Emit audit event for decision and outcome.
6. Add Session continuity.
7. Add A2A and MCP adapters.
8. Add optional long-term Memory as a separate provider.

### Behavioral acceptance

- unregistered target can be rejected or handled under explicit fallback policy;
- registered target remains inaccessible without an allow rule;
- two Agent identities receive different authorization decisions for same target;
- direct credential never appears in model prompt/context;
- A2A and MCP routes share policy semantics without sharing wire protocol;
- policy dry-run reports would-be denials without blocking, then enforcement blocks them;
- audit trail links identity -> policy -> route -> result.

## 13. Mapping to Ordivon

| Google | Ordivon | Decision |
| --- | --- | --- |
| Agent Registry | Agent Service Agent/Plugin/Capability Registry view | EXTRACT unified semantic layer |
| Agent Identity | Agent Birth + Identity binding | ADOPT/ADAPT mature workload identity |
| Agent Gateway | Service Router/Gateway | EXTRACT thin standard-aware gateway |
| IAM policies | Policy engine/provider IAM | ADOPT, not custom language |
| Runtime | existing Ordivon Runtime/hosting adapters | ADAPT |
| Session | Agent Service communication/session | EXTRACT |
| Memory Bank | optional capability | ON_DEMAND |
| Observability | OTel/audit substrate | ADOPT |

Agent Birth should provision or bind an Agent identity as part of creation, but Birth remains an Ordivon orchestration protocol above the identity provider.

## Project-study acceptance

- **ONE-SENTENCE TEST: PASS**
- **MODULE-COMPLETENESS TEST: PASS**
- **MINIMAL-CLONE SPEC TEST: PASS**
- **BEHAVIORAL-ACCEPTANCE TEST: PASS (SPECIFIED, NOT YET IMPLEMENTED)**

## Verdict

**EXTRACT THE GOVERNANCE SPINE: Registry + first-class Agent Identity + Gateway + Policy is Google's strongest transferable contribution to an Ordivon-wide Agent Service.**
