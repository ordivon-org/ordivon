# Microsoft Foundry Agent Service — Agent Service Kernel R1

Status: **CURRENT OFFICIAL-DOC DECOMPOSITION / PROTOTYPE-READY**
Checked: 2026-09-17
Scope: Microsoft Foundry Agent Service current public architecture and hosted-agent contracts.

## 1. One-sentence model

**Foundry Agent Service is a managed agent deployment and governance layer that presents one service lifecycle for both declarative prompt agents and customer-code hosted agents, while centralizing runtime, conversations/responses, shared toolboxes, identity/RBAC, observability, versioning and publishing.**

It is not primarily Microsoft Agent Framework: Hosted agents may use Agent Framework, LangGraph, OpenAI/Anthropic/GitHub agent SDKs, or custom code.

Primary sources:
- https://learn.microsoft.com/en-us/azure/foundry/agents/overview
- https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/runtime-components
- https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/agent-identity
- https://learn.microsoft.com/en-us/azure/foundry/how-to/develop/framework-hosted-agents

## 2. Shell / kernel / substrates

| Class | Elements |
| --- | --- |
| Product shell | Foundry portal, Azure subscription/project packaging, Teams/M365 distribution, Azure-specific deployment UX |
| Transferable kernel | common Agent Service over managed prompt agents and hosted code agents, versioned endpoints, conversations/responses, shared toolboxes, first-class agent identity, RBAC/security, observability |
| Mature substrates | OCI/container hosting, Entra/OAuth/RBAC, MCP, A2A, HTTP Responses/Invocations protocols, tracing/metrics |

## 3. Two agent implementations, one service contract

```text
                Foundry Agent Service
                        |
          +-------------+-------------+
          |                           |
      Prompt Agent                 Hosted Agent
  config: model/instructions/tools   customer code/container
          |                           |
          +-------------+-------------+
                        |
                    Agent Runtime
                        |
              conversations / responses
                        |
                 toolboxes / tools
                        |
                 identity / policy
```

This is a major design lesson: **Agent Service must be harness-neutral**. A declarative managed harness and a fully custom code harness can share lifecycle, identity, endpoint, tool and observability contracts.

## 4. Runtime object model

Foundry documentation currently describes three core runtime components:

```text
Agent
  = model + instructions + tools/configuration

Conversation
  = persistent multi-turn history/state namespace

Response
  = one processing/output operation over input/context
```

Hosted-agent service adds version/deployment/endpoint and dedicated identity around customer code.

Minimum identities to preserve:

```text
AgentDefinitionId
AgentVersionId
Endpoint/DeploymentId
AgentIdentity
ConversationId
Response/InvocationId
ToolboxId
ToolId
TraceId
```

## 5. Responsibility map

| Module | Responsibility | Durable truth? |
| --- | --- | --- |
| Agent Service control plane | create/version/deploy/publish agents | yes |
| Agent Runtime | host/scale prompt and hosted agents, lifecycle/tool-call plumbing | runtime/deployment state |
| Prompt Agent definition | declarative model/instruction/tool configuration | yes/versioned |
| Hosted Agent package | custom framework/code | external source/image + registered version |
| Conversation | stateful multi-turn continuity | yes |
| Response/Invocation | one execution request/output | yes/observable |
| Toolboxes | curated reusable tool configurations via managed MCP surface | yes/versioned config |
| Agent Identity | independent Entra principal for governance/tool authentication | identity provider truth |
| RBAC/security | authorization and network/content controls | policy/provider truth |
| Observability | tracing/metrics/evaluations | telemetry/eval truth |
| Publishing/Registry | stable endpoint/version/discovery/sharing | service catalog state |

## 6. Hosted deployment lifecycle

Public docs describe a useful generic lifecycle:

```text
package source/container
       |
create Agent Version
       |
service provisions runtime + dedicated Agent Identity
       |
wait until version active
       |
invoke stable endpoint
```

A new code revision should be a new immutable/versioned deployment object rather than an in-place mutation of execution identity.

## 7. Identity and downstream tool calls

Foundry uses agent identities as independent directory actors and can obtain downstream access tokens for tool calls without embedding secrets into prompts/code.

Generic transfer:

```text
AgentVersion/Deployment
      -> AgentIdentity
      -> scoped downstream token
      -> Tool/Resource
```

The identity provider remains separate from the Agent Service's own agent definition/version store.

## 8. Hosting model and protocol are separate choices

Microsoft's current Agent Framework hosting guidance explicitly separates **who hosts the agent** from **which protocol reaches it**. Hosted or self-hosted agents may expose Responses-like APIs, A2A, MCP tools, or other client integrations.

Transferable rule:

```text
hosting topology != agent wire protocol
```

Ordivon Agent Service should therefore keep Runtime/Host placement separate from A2A/MCP/Responses adapters.

## 9. Shared Toolboxes are capability bundles, not agent identity

Toolboxes curate reusable tool configuration and can be exposed through managed MCP. This supports a service-level capability registry separate from individual agents.

Generic relation:

```text
AgentVersion
   -> CapabilityProfile / Toolbox
        -> Tools / MCP targets
```

Do not duplicate the same tool credentials/config inside every agent definition.

## 10. Failure/security boundaries

- Agent version activation is different from invocation success.
- Conversation continuity is different from deployment/runtime lifecycle.
- Agent identity is not human user identity.
- Tool authorization must be resolved at call time using the relevant principal/context.
- Hosted customer code may fail independently of the managed service control plane.
- Protocol endpoint compatibility should not imply identical hosting/security semantics.

## 11. Mechanisms worth retaining

1. One Service contract over multiple harness implementation styles.
2. Immutable/versioned agent deployments behind stable endpoints.
3. Dedicated first-class identity per deployed agent.
4. Conversation and individual Response/Invocation as separate objects.
5. Shared versioned Toolboxes/capability bundles.
6. Hosting topology independent of wire protocol.
7. Observability/evaluation attached to service lifecycle rather than framework-specific internals.

## 12. What Ordivon should not copy

- Azure-specific resource hierarchy or Entra object model as local semantic truth;
- Foundry portal/product shell;
- Responses API as the only inter-agent protocol;
- model/provider catalog logic inside Agent Service core;
- Agent Framework as mandatory Harness;
- Toolboxes as a replacement for the richer Plugin/Skill/Tool/MCP registry already being developed locally.

## 13. Minimal clone

```text
AgentDefinitionStore
AgentVersionStore
Deployment/Endpoint
RuntimeProvider interface
ConversationStore
Invocation/Response ledger
CapabilityProfile/Toolbox binding
AgentIdentity binding
Trace sink
```

### Build order

1. Define `AgentDefinition` with two harness kinds: `managed_config` and `custom_runtime`.
2. Create immutable `AgentVersion`.
3. Bind version to RuntimeProvider and stable Endpoint.
4. Provision/bind AgentIdentity.
5. Add Conversation and Invocation records.
6. Add shared CapabilityProfile referencing tools/MCP resources.
7. Add protocol adapters independently: HTTP/Responses, A2A, MCP exposure.
8. Add telemetry/evaluation hooks.

### Behavioral acceptance

- deploy one declarative and one custom-code agent through same Service API;
- both have stable endpoints and distinct versions;
- upgrade creates new version without changing historical invocation identity;
- same toolbox/capability profile is reusable by both agents;
- each agent authenticates to a tool as its own principal;
- conversation persists across multiple invocations without becoming deployment state;
- switch external protocol adapter without changing harness/runtime provider;
- trace links version + identity + conversation + invocation + tool call.

## 14. Mapping to Ordivon

| Foundry | Ordivon | Decision |
| --- | --- | --- |
| Agent Service | future Ordivon Agent Service | EXTRACT service semantics |
| Agent Runtime | Ordivon Runtime/other provider adapters | ADAPT multi-provider |
| Hosted Agent | arbitrary Harness on Runtime | ADOPT concept |
| Prompt Agent | managed/declarative Harness profile | ON_DEMAND |
| Toolboxes | Agent Plugin/CapabilityProfile | ADAPT, don't duplicate registry |
| Entra Agent Identity | Agent Birth identity binding | ADOPT via provider adapter |
| Conversation/Response | Session + Service Run/interaction | EXTRACT mapping |
| Publishing/registry | Agent Service registry/discovery | EXTRACT |

## Project-study acceptance

- **ONE-SENTENCE TEST: PASS**
- **MODULE-COMPLETENESS TEST: PASS**
- **MINIMAL-CLONE SPEC TEST: PASS**
- **BEHAVIORAL-ACCEPTANCE TEST: PASS (SPECIFIED, NOT YET IMPLEMENTED)**

## Verdict

**EXTRACT THE HARNESS-NEUTRAL SERVICE CONTRACT: Foundry's strongest lesson is that declarative and customer-code agents can share versioning, endpoint, identity, conversation, capability and observability semantics without forcing one agent framework.**
