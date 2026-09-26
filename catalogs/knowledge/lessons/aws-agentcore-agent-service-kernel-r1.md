# AWS AgentCore — Agent Service / Platform Kernel R1

Status: **CURRENT OFFICIAL-DOC DECOMPOSITION / PROTOTYPE-READY**
Checked: 2026-09-17
Subject: Amazon Bedrock AgentCore public platform contracts; private service internals are out of scope.

## 1. One-sentence model

**AgentCore is a modular managed agent operations substrate that separates the agent loop from the hosting runtime and surrounds execution with independently consumable registry, identity, gateway, policy, memory, sandbox, observability, evaluation, and optimization services.**

It is not primarily an agent framework: its Runtime explicitly accepts agents written with arbitrary frameworks, while Harness is the optional managed loop.

Primary evidence:
- https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/what-is-bedrock-agentcore.html
- https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness-vs-runtime.html
- https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/registry.html
- https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-security-best-practices.html

## 2. Product shell / transferable kernel / mature substrates

| Class | Elements | Interpretation |
| --- | --- | --- |
| Product shell | AWS Console, AWS billing, region catalog, ECR deployment workflow, CloudWatch product UI | Useful hosting/product integration, not the generic agent kernel |
| Transferable kernel | Harness/runtime split, Registry, per-workload identity, governed capability gateway, deterministic policy interception, isolated session execution, memory service, standard telemetry/evaluation | Reusable architecture independent of AWS branding |
| Mature substrates | OCI containers, IAM/OAuth/JWT, Cedar, MCP, A2A, OpenTelemetry, queues/storage/network isolation | Prefer existing standards/providers rather than local reinvention |

## 3. Kernel graph

```text
                   Agent Registry
                        |
                  resolve/version
                        v
Client -> Gateway -> Agent Runtime --------------------+
           |            |                               |
           |            +-> custom Harness / framework |
           |            |                               |
           |            +-> managed Harness (optional) |
           |                                            |
           +-> Policy Engine                            |
           +-> Identity / credential exchange           |
           +-> MCP tools / Runtime targets              |
                                                        |
Runtime session -> Memory / Browser / Code Interpreter |
        |                                               |
        +----------------> OTel Observability ----------+
                                  |
                             Evaluation
                                  |
                             Optimization
```

The key structural lesson is that **Harness runs inside/over Runtime but is not Runtime**. Runtime owns hosting/isolation/scaling/session/auth plumbing; Harness owns the orchestration loop.

## 4. Responsibility map

| Module | Primary responsibility | Durable truth? | Inputs | Outputs | Replaceability |
| --- | --- | --- | --- | --- | --- |
| Registry | catalog/discovery/version/approval of agents, tools, skills, MCP/custom resources | yes: registry records | published resource metadata | discoverable records / MCP surface | generic registry/catalog possible |
| Runtime | host and scale agent/tool workloads with session isolation and auth/observability plumbing | runtime/session metadata | deployable agent code + invocation | running isolated workload / endpoint | Kubernetes/serverless substrate + adapter |
| Harness | managed model/tool loop | logical run/session state | model, instructions, tools, memory, limits | responses/tool calls | any agent harness/framework |
| Gateway | governed entry/capability routing; MCP virtualization/targets | config | caller request, target metadata | routed tool/agent request | Envoy/API gateway + MCP/A2A adapters |
| Identity | workload identity and outbound credential brokering | identity/credential references | runtime identity + target service | scoped access token/credential | IAM/OAuth/workload identity provider |
| Policy | deterministic tool/action authorization | policy definitions | principal/action/resource/context | allow/deny/intercept | Cedar/OPA/provider IAM |
| Memory | short/long-term agent memory | yes | observations/session material | retrieved/derived memory | dedicated memory provider/store |
| Browser / Code Interpreter | isolated effectful tools | session-scoped state | agent requests | browser/code results | external sandbox/browser providers |
| Observability | traces/logs/metrics | telemetry | run/tool/runtime events | OTel-compatible telemetry | any OTel backend |
| Evaluation | quality measurement on sessions/traces/spans | eval datasets/results | telemetry/tasks | scores/findings | external eval framework |
| Optimization | controlled config improvement/A-B traffic | candidate configs/results | traces/evals | versioned prompt/tool config | optional experimentation layer |

## 5. State and identity model

A minimal reconstruction does not need AWS's full resource model. It needs these distinct identities:

```text
RegistryRecordId
AgentDefinitionId + Revision
Deployment/RuntimeId + Endpoint
AgentIdentity / WorkloadIdentity
SessionId
Invocation/RunId
Tool/CapabilityId
PolicyId + Version
MemoryNamespace/ActorId
TraceId / SpanId
```

Do not collapse them into one `agent_id`.

### Core lifecycle

```text
Agent definition/revision
   -> publish registry record
   -> deploy runtime revision
   -> create/invoke session
   -> harness/framework loop
   -> tool/agent calls through governed boundary
   -> telemetry/evaluation
   -> new config/revision
```

## 6. End-to-end control/effect flow

A useful generic path is:

```text
1. caller authenticates
2. gateway resolves target and caller/agent context
3. policy evaluates invocation/tool action
4. runtime selects/starts isolated session instance
5. harness or custom agent code runs
6. agent requests capability
7. outbound identity obtains scoped credential
8. gateway/policy enforce the capability request
9. target executes
10. result returns to harness
11. runtime/agent emits trace/log/event
12. evaluation consumes traces; optimization may propose a new version
```

This separates authorization from model judgement: the model may propose an action, but policy/gateway controls the executable effect.

## 7. Protocol and interface contracts

A minimal vendor-neutral clone needs only a few contracts:

```text
Registry.publish(ResourceRecord) -> Revision
Registry.search(Query, CallerContext) -> ResourceRecord[]

Runtime.deploy(AgentRevision, RuntimeProfile) -> Deployment
Runtime.invoke(Deployment, SessionContext, Input) -> Stream<Event>
Runtime.cancel(RunId) -> Ack

Gateway.route(CallerIdentity, Target, Request) -> Response
Policy.decide(Principal, Action, Resource, Context) -> Allow|Deny
Identity.issue(WorkloadIdentity, Audience, Scope) -> ScopedCredential

Telemetry.emit(TraceEvent)
```

MCP should be retained for tool/resource interoperability and A2A for remote agent interoperability where applicable rather than inventing private equivalents.

## 8. Failure / durability / security boundaries

### Runtime vs Harness
Runtime failure is infrastructure/process/session failure. Harness failure is loop/orchestration logic failure. The official distinction explicitly keeps orchestration under customer code for Runtime and provider-managed for Harness.

### Identity
Do not embed long-lived third-party credentials in prompts or agent code. Use workload identity plus scoped credential exchange/brokering.

### Gateway enforcement
A gateway is only an enforcement point if direct runtime/tool access is restricted; AWS explicitly warns that direct Runtime reachability can bypass gateway policy/guardrails/interceptors.

### Session isolation
Treat session/runtime isolation as an execution property. It does not imply semantic separation of shared memory stores or external services unless those are scoped separately.

### Policy
Policy belongs outside the model loop. A model output is a proposal, not authorization.

### Telemetry
OTel traces provide execution evidence and evaluation input; they do not independently prove domain semantic success.

## 9. Mechanisms worth retaining

1. **Harness / Runtime separation** — the clearest current external confirmation of our Ordivon boundary.
2. **Registry as governed discovery** — catalog agents, MCP servers, tools, skills and custom resources rather than maintaining disconnected registries forever.
3. **Gateway as agent traffic choke point** — interpose policy, auth, observability and protocol adaptation outside the agent process.
4. **Agent/workload identity** — first-class non-human principal bound to runtime lifecycle.
5. **Policy outside reasoning** — deterministic enforcement around effectful calls.
6. **Independent platform primitives** — memory/browser/code/eval can be used without forcing one harness/framework.
7. **Standard telemetry** — OTel rather than platform-private trace ontology.
8. **Evaluation -> optimization loop** — quality improvement consumes traces but remains a separate service.

## 10. What Ordivon should not copy

- AWS-specific ARN/IAM/ECR/CloudWatch ontology as Ordivon domain truth;
- another private model/tool protocol when MCP/A2A/HTTP suffice;
- a second generic sandbox/runtime if Ordivon Runtime already owns local execution evidence;
- a universal long-term memory service before concrete workloads demand it;
- automatic optimizer authority to change production behavior without explicit version/promotion policy;
- provider console/product packaging.

## 11. Minimal clone

The smallest clone that demonstrates the AgentCore architectural kernel is:

```text
Agent Registry
    |
Agent Definition + Revision
    |
Runtime Adapter ------------------------+
    |                                   |
Session / Run                           |
    |                                   |
Harness Adapter (one simple loop)       |
    |                                   |
Gateway -> Policy -> Tool Adapter       |
    |             -> Identity broker ---+
    |
Event/Trace sink
```

Memory, browser, code interpreter, evaluation, and optimization are extensions, not required to prove the basic service kernel.

### Minimal data model

```text
AgentDefinition { id, revision, harnessRef, capabilities[], runtimeProfile }
RegistryRecord  { id, kind, revision, metadata, approvalState }
Deployment      { id, agentRevision, runtimeRef, endpoint, desiredState, observedState }
Session         { id, deploymentId, actorId, stateRef }
Run             { id, sessionId, inputDigest, status, attempt, timestamps }
Capability      { id, protocol, endpoint, permissions }
PolicyBinding   { principal, action, resource, ruleRef }
Event           { runId, seq, type, payloadRef, traceId }
```

### Minimal build order

1. Registry with immutable revisions and deterministic resolve.
2. AgentDefinition -> Deployment desired/observed state.
3. Runtime adapter that starts one isolated local process/container and exposes `invoke/cancel`.
4. Session + Run ledger with explicit lifecycle.
5. One Harness adapter implementing `model -> tool -> observation -> model`.
6. Gateway with one Tool target.
7. Policy decision before tool execution.
8. Workload identity passed independently from prompt/context.
9. Append-only execution events + OTel mapping.
10. MCP tool endpoint and A2A agent endpoint adapters.

### Behavioral acceptance

1. Publish Agent revision A1; resolve exactly A1.
2. Deploy A1; observed state converges to running.
3. Invoke two sessions and prove execution/session state is distinct.
4. Harness requests an allowed tool; gateway/policy permits and result returns.
5. Same harness requests a denied tool; tool never executes.
6. Cancel an active Run and observe a terminal cancelled state.
7. Restart the service and recover registry/deployment/run records without inventing completion.
8. Replace the harness implementation while keeping Runtime/Registry/Gateway contracts unchanged.
9. Invoke one capability through MCP and one remote agent through A2A adapters.
10. Produce a trace linking request -> run -> policy decision -> tool/agent effect -> response.

If all ten pass, the AgentCore-derived structural kernel has been reconstructed without cloning AWS product infrastructure.

## 12. Mapping to Ordivon

| AgentCore concept | Ordivon owner | Decision |
| --- | --- | --- |
| Harness | existing `ordivon-harness` / model-facing loop | ADAPT; keep framework/provider replaceable |
| Runtime | existing `ordivon-runtime` | ADAPT; current durable execution substrate is already more evidence-oriented than a generic hosting label |
| Registry | future Agent Service + current Skill/Plugin registries | EXTRACT/UNIFY at Service layer |
| Gateway | future Agent Service networking/capability gateway | EXTRACT thin layer; prefer MCP/A2A/standard proxy substrates |
| Identity | future Agent Service identity plane | ADOPT/ADAPT mature IAM/OAuth/workload identity |
| Policy | future Agent Service policy/enforcement composition | ADOPT mature policy engine; do not invent language |
| Session/Run | Service semantic session/run + Runtime mechanical job/attempt | EXTRACT mapping; do not collapse authorities |
| Memory | workload-specific provider | ON_DEMAND |
| Observability | OTel substrate | ADOPT |
| Evaluation/Optimization | Research/Eval capability | ON_DEMAND with versioned promotion |

### Mapping the user's intended Ordivon Service objects

```text
Agent Birth
 ~= provision AgentDefinition + immutable revision + identity + initial deployment/runtime binding

Agent Goal
 = Ordivon service/domain objective layer above generic infrastructure;
   AgentCore does not provide this as the core platform object

Agent Task
 ~= service work unit that may create one or more Runtime Runs/Jobs

Agent Board
 = projection/control surface over Agent/Goal/Task/Run state;
   should not become the authoritative execution ledger

A2A
 = standard external/inter-agent transport adapter at the Service boundary
```

This is an important boundary: **Birth/Goal/Task/Board are Ordivon organization semantics built on top of the generic Agent Service kernel, not things we should falsely attribute to AgentCore.**

## 13. Project-study acceptance

- **ONE-SENTENCE TEST: PASS** — platform value and Runtime/Harness distinction are explicit.
- **MODULE-COMPLETENESS TEST: PASS** — major current official AgentCore primitives have a responsibility owner and boundary.
- **MINIMAL-CLONE SPEC TEST: PASS** — data model, interfaces and ten-step build order are sufficient to begin a clone.
- **BEHAVIORAL-ACCEPTANCE TEST: PASS (SPECIFIED, NOT YET IMPLEMENTED)** — ten concrete tests define successful reconstruction.

## Verdict

**EXTRACT THE SERVICE KERNEL, NOT THE AWS SHELL: the most valuable pattern is Registry + governed Gateway/Identity/Policy around a Runtime/Harness split, with standard telemetry and replaceable agent frameworks.**
