# Ordivon Agent Birth — LEGO / Puzzle Decomposition R1

Status: **CURRENT SOURCE DECOMPOSED / MIGRATION-READY / PROVIDER-BOUNDARY DIAGNOSIS ADDED**
Date: 2026-09-18
Current source examined: `/root/projects/ordivon-harness` @ `3f10f7bb7cb732e3b873fcc2aacb6ae7e9cf52f4`
Observed production Agent Automation release: `3f10f7bb7cb732e3b873fcc2aacb6ae7e9cf52f4` (Provider Boundary R1 active)
Node graph: `knowledge/graphs/ordivon-agent-birth-r1.json`

## 1. One-sentence kernel

**Agent Birth deterministically compiles one campaign role into one stable provider-effect identity, durably fences that identity before any non-idempotent SEND, uses Temporal to orchestrate execution and recovery, and binds observed provider conversation evidence back to that same identity without blind resend.**

It is **not primarily** a browser script, generic workflow engine, Agent semantic registry, or model loop.

## 2. The most important split

The current production implementation contains four different architectural responsibilities that historically appear under one "Agent Birth" label:

```text
semantic preparation
    CampaignSpec -> role -> task prompt -> effectId/bootstrap

workflow durability
    Temporal admission -> Workflow -> Activity -> retry/recovery

provider-effect safety
    durable effect ledger -> atomic claim -> no blind resend -> reconcile

provider mechanics
    Browserless carrier -> Playwright -> ChatGPT Web -> observed providerResource
```

These must remain distinct during migration to Agent Service.

## 3. Shell / kernel / substrate

### Product/interface shell

```text
Agent Automation MCP
Agent Automation CLI
stable /root/tools/bin/agent-automation carrier
systemd units
release packaging/materialization
health/doctor presentation
```

### Transferable Ordivon kernel

```text
CampaignSpec validation + exact frozen input identity
Birth compilation and effect identity algebra
admission classification
provider-effect ledger and effect fence
exact carrier binding
same-effect reconciliation
human-required proof and resume law
provider resource/evidence binding
```

### Mature substrates consumed rather than rebuilt

```text
Temporal       durable workflow/history/retry/worker recovery
Browserless    persistent browser carrier/session lifecycle
Playwright     deterministic browser control
Network v2     DNS/proxy/network namespace/path health
SQLite         small local effect ledgers
systemd/Podman service/process/container lifecycle
Workstation v2 stable node-local bindings
```

## 4. LEGO assemblies

The 37 atomic architectural nodes reassemble into nine useful assemblies:

```text
A. Interface shell
   AB01 AutomationMCPFacade
   AB02 AutomationCLI
   AB36 ReleaseCarrier

B. Spec + identity compiler
   AB03 CampaignSpecValidator
   AB04 CampaignRegistry
   AB06 RolePromptCompiler
   AB07 BirthIdentityCompiler
   AB08 BootstrapCompiler
   AB09 CampaignFanoutPlanner

C. Admission + durable orchestration
   AB10 BirthAdmissionGate
   AB11 TemporalWorkflowIdentityPlanner
   AB12 TemporalAdmissionAdapter
   AB13 BirthWorkflow
   AB14 BirthActivityWorker

D. Carrier routing + provider-boundary diagnosis
   AB15 CarrierCandidateRouter
   AB16 CarrierLease
   AB17 ProviderPreflightObserver
   AB37 ProviderBoundaryDiagnosis
   AB18 CarrierBindingStore

E. Provider-effect fence
   AB19 MaterializationRequestBuilder
   AB20 BirthEffectLedger
   AB21 EffectAttemptClaimer

F. Provider effect + evidence
   AB22 BrowserlessMaterializationAdapter
   AB23 ChatGPTSubmitExecutor
   AB24 SubmitEvidenceInterpreter
   AB25 ProviderResourceCanonicalizer

G. Recovery / human verification
   AB26 BirthReconciler
   AB27 ReconnectObserver
   AB28 HumanHandoffReceipt
   AB29 HumanHandoffLivenessObserver
   AB30 HumanResumeCoordinator

H. Post-Birth Session extension
   AB31 TurnAdmissionCoordinator
   AB32 TurnEffectLedger
   AB33 ContinuationExecutor
   AB34 ConversationOutputObserver

I. Projection/operations
   AB05 CampaignCensusProjector
   AB35 AutomationDoctor
```

The post-Birth continuation assembly is deliberately separated from Birth proper. It should migrate toward Agent Service `Session/Message`, not stay fused to provisioning.

## 5. Atomic node responsibility table

| Node | Kind | Responsibility | Truth/effect authority | Future owner |
|---|---|---|---|---|
| AB01 AutomationMCPFacade | Adapter | expose safe Agent-facing campaign/Birth/reconcile/handoff operations | none | Agent Service/client adapter |
| AB02 AutomationCLI | Adapter | operator command surface | none | thin operator adapter |
| AB03 CampaignSpecValidator | Transform | validate current CampaignSpec v2 and limits | syntax only | Agent Service admission |
| AB04 CampaignRegistry | State | freeze content-addressed CampaignSpec bytes | CampaignSpec CAS truth | Agent Service input/revision authority or thin CAS |
| AB05 CampaignCensusProjector | Projection | derive per-role materialization view from spec + ledger | none | Board/Service projection |
| AB06 RolePromptCompiler | Transform | combine shared prompt + RoleCard deterministically | none | Agent Service preparation |
| AB07 BirthIdentityCompiler | Transform | derive stable `effectId` and preparation identity | identity derivation | BirthCoordinator |
| AB08 BootstrapCompiler | Transform | freeze exact bootstrap bytes/digest | none | BirthCoordinator |
| AB09 CampaignFanoutPlanner | Router | turn roster into independent Birth units | none | planner/team layer |
| AB10 BirthAdmissionGate | Router | distinguish new Birth, explicit pre-effect retry, reconcile, human resume | admission decision | Agent Service lifecycle |
| AB11 TemporalWorkflowIdentityPlanner | Transform | derive execution IDs per operation | execution identity only | Temporal adapter |
| AB12 TemporalAdmissionAdapter | Adapter | start/find exact Temporal workflow and return admission receipt | delegated Temporal truth | Temporal adapter |
| AB13 BirthWorkflow | Router | deterministic durable Activity sequencing/retry | Temporal history | Temporal |
| AB14 BirthActivityWorker | Adapter | worker execution + endpoint-local serialization | none | Temporal worker/provider adapter |
| AB15 CarrierCandidateRouter | Router | deterministic carrier ordering and narrow pre-SEND failover | routing decision | provider adapter |
| AB16 CarrierLease | Adapter | exclusive use of one persistent Browserless profile | process-local lock evidence | provider adapter |
| AB17 ProviderPreflightObserver | Observer | read-only carrier/provider admission check | observation | provider adapter |
| AB37 ProviderBoundaryDiagnosis | Router | classify provider admission vs carrier failure and constrain repair routing | none | provider adapter / Agent Service policy |
| AB18 CarrierBindingStore | State | bind `effectId` to exact endpoint identity | current carrier binding | provider adapter |
| AB19 MaterializationRequestBuilder | Transform | build carrier-neutral immutable request/digest | none | provider contract |
| AB20 BirthEffectLedger | State | persist effect intent, standing, evidence, generation | provider-effect truth | provider effect adapter |
| AB21 EffectAttemptClaimer | Router | atomically authorize exactly one crossing of ambiguous SEND boundary | uses ledger transaction | provider effect adapter |
| AB22 BrowserlessMaterializationAdapter | Adapter | map neutral request to Browserless/Playwright mechanics | none | provider adapter |
| AB23 ChatGPTSubmitExecutor | Effect | perform raw ChatGPT Web composer/SEND action | external effect | provider-specific executor |
| AB24 SubmitEvidenceInterpreter | Observer | classify pre-effect failure, human gate, submit-observed, bound | evidence interpretation | provider adapter |
| AB25 ProviderResourceCanonicalizer | Transform | normalize canonical ChatGPT conversation coordinate | none | provider adapter |
| AB26 BirthReconciler | Reconciler | observe the same ambiguous effect without redispatch | no new effect | provider adapter called by Service |
| AB27 ReconnectObserver | Observer | reconnect/read-back prior Browserless handle/resource | observation | provider adapter |
| AB28 HumanHandoffReceipt | State | persist proof that human verification is needed and SEND is not crossed | handoff evidence | provider adapter |
| AB29 HumanHandoffLivenessObserver | Observer | distinguish current/expired/inactive/unknown handoff | live observation | provider adapter |
| AB30 HumanResumeCoordinator | Reconciler | safely reclaim same effect after human verification | no new semantic Birth identity | provider adapter + Service lifecycle |
| AB31 TurnAdmissionCoordinator | Router | admit post-Birth continuation against BOUND resource | session admission | Agent Service Session |
| AB32 TurnEffectLedger | State | persist turn identity/receipt | turn effect truth | Session/provider adapter |
| AB33 ContinuationExecutor | Effect | one continuation SEND | provider turn effect | Session/provider executor |
| AB34 ConversationOutputObserver | Observer | exact-turn read-only output/read-back | observation | Session/provider observer |
| AB35 AutomationDoctor | Projection | summarize substrate/ledger health and backlog | none | operations |
| AB36 ReleaseCarrier | Adapter | stable node-local invocation of immutable release | delegated release truth | Workstation v2 + Harness release |

## 6. Identity algebra — never collapse these

```text
campaignId
    logical campaign label

campaignRef
    content-addressed registry identity for exact CampaignSpec bytes

agentId
    roster-local role identity

roleDigest
    digest of role-card bytes

taskPromptDigest
    digest(sharedPrompt + roleCard)

effectId
    sha256({campaignId, agentId, taskPromptDigest})
    = stable logical provider-effect identity for Birth

bootstrapPromptDigest
    digest of exact provider bootstrap bytes

preparationDigest
    digest(effectId + role/task/bootstrap digests)

materializationRequestDigest
    exact carrier-neutral request-content identity

Temporal workflowId
    first Birth: effectId
    PRE_EFFECT retry: fresh UUIDv7 execution identity, same effectId
    reconcile: fresh observation UUIDv7, same effectId
    human resume: handoffDigest, same effectId

endpointId + endpointIdentityDigest
    physical Browserless carrier identity

providerResource
    canonical ChatGPT conversation coordinate

handoffDigest
    human-verification handoff/resume identity

turnRequestId
    UUIDv7 identity for a post-Birth continuation effect
```

Required inequalities:

```text
agentId != future AgentInstanceId
agentId != effectId
effectId != providerResource
effectId != Browserless endpoint identity
effectId != retry/reconcile Temporal execution identity
carrier binding != provider conversation identity
turnRequestId != effectId
```

This is the main reason the future Agent Service must introduce `AgentInstanceId` rather than reusing current `agentId` or `effectId`.

## 7. Provider Boundary state — do not collapse provider admission into substrate health

Provider preflight now feeds a separate pure diagnosis node, `AB37 ProviderBoundaryDiagnosis`.

For a healthy carrier that observes `CHALLENGE_GATED`, the runtime classification is:

```text
SUBSTRATE_HEALTHY_PROVIDER_NOT_ADMISSIBLE
```

This means:

```text
carrier routing        PRESERVE_SELECTED_CARRIER
provider admission     NOT_ADMISSIBLE
human verification     eligible
automatic Browserless/Profile/Launcher/Network repair
                       forbidden
provider root cause    not established
```

Only narrow carrier/transport-local pre-SEND standings may fail over to another candidate. The Browser Security R9 result is carried only as `REFERENCE_ONLY_NOT_LIVE_ASSERTION`; preflight does not claim to re-run R1-R9 on every observation.

Detailed evidence and routing law: `knowledge/lessons/agent-birth-provider-boundary-r1.md`.

## 8. Birth effect state machine

The current carrier-neutral standing set is:

```text
UNRECORDED
    ↓ durable intent
PREPARED
    ↓ atomic effect claim
UNKNOWN
    ├─ proven no SEND ───────→ PRE_EFFECT_FAILED
    ├─ provider challenge ───→ HUMAN_REQUIRED
    ├─ SEND structurally seen → SUBMIT_OBSERVED
    └─ coordinate + evidence → BOUND
                                ↓ optional stronger proof
                           READY_CONFIRMED
```

The important transition laws are stronger than the state names:

```text
PRE_EFFECT_FAILED
    SEND proven not crossed
    => explicit bounded retry of SAME effectId is allowed

HUMAN_REQUIRED
    providerEffectAttempted=false is durably proven
    => resume only through handoff/liveness contract

UNKNOWN / SUBMIT_OBSERVED
    provider outcome may already exist
    => RECONCILE ONLY
    => blind resend forbidden

BOUND / READY_CONFIRMED
    terminal provider-effect truth
    => replay returns existing receipt
```

`effect_generation` counts admitted physical effect attempts under one stable request/effect identity. It is not a new semantic Agent generation.

## 9. Full campaign Birth flow

```text
MCP / CLI
   │
   ▼
AB03 validate CampaignSpec
   │
   ▼
AB04 freeze content-addressed spec
   │
   ▼
AB09 fan out roster
   │
   ├─ AB06 compile task prompt
   ├─ AB07 derive effectId
   └─ AB08 freeze bootstrap
   │
   ▼
AB05 read ledger census
   │
   ▼
AB10 admission gate
   │
   ▼
AB11 choose Temporal execution identity
   │
   ▼
AB12 admit Temporal workflow
   │
   ▼
AB13 durable BirthWorkflow
   │
   ▼
AB14 Activity worker
   │
   ▼
AB15 choose eligible carrier
   │
   ▼
AB16 exclusive carrier lease
   │
   ▼
AB17 read-only provider preflight
   │
   ▼
AB18 bind exact carrier identity
   │
   ▼
AB19 materialization request
   │
   ▼
AB20 persist PREPARED
   │
   ▼
AB21 atomically claim effect -> UNKNOWN
   │
   ▼
AB22 Browserless target adapter
   │
   ▼
AB23 Playwright ChatGPT SEND
   │
   ▼
AB24 interpret evidence
   │
   ├──────── pre-effect failure / human path
   │
   ▼
AB25 canonical providerResource when proven
   │
   ▼
AB20 persist observed standing/evidence
   │
   ▼
AB05 derived census
```

## 10. Ambiguous-effect recovery flow

```text
UNKNOWN / SUBMIT_OBSERVED
       │
       ▼
AB10 permits reconcile, forbids new Birth SEND
       │
       ▼
AB11 fresh observation execution id
       │
       ▼
Temporal ReconcileWorkflow
       │
       ▼
AB26 BirthReconciler
       │
       ├── require same current physical carrier binding
       │
       ▼
AB27 Browserless reconnect/read-back
       │
       ▼
observed BOUND ?
   │          │
  yes        no
   │          │
   ▼          ▼
update      preserve ambiguity
ledger      safeToResend=false
```

Loss of the old carrier destroys observation authority; it does **not** create resend authority.

## 11. Human verification flow

```text
provider challenge before SEND
      │
      ▼
AB28 durable handoff receipt
providerEffectAttempted=false
      │
      ▼
AB29 current liveness observation
      │
      ├─ CURRENT -> expose bounded operator handoff only
      │
      └─ proven inactive/eligible
              │
              ▼
AB30 HumanResumeCoordinator
              │
              ▼
atomic same-effect resume claim
              │
              ▼
provider revalidation / SEND
```

Human verification is therefore a **recovery branch of the same effect identity**, not creation of a new Agent.

## 12. Failure model

### Before Temporal admission

- invalid/legacy CampaignSpec -> reject;
- no healthy Browserless substrate for a genuinely unrecorded Birth -> HOLD;
- no provider effect has been authorized.

### Temporal admission ambiguity

If admission loses its response or returns malformed receipt:

```text
outcome = ambiguous
next action = observe exact deterministic workflow/effect identity
not = start a new guessed workflow
```

### Before SEND

Transport/carrier failures that prove no SEND may become `PRE_EFFECT_FAILED`. Only narrow transport/navigation classes auto-retry inside the Temporal Activity; explicit provider pressure/challenge does not.

### At/after SEND

The ledger transitions through the ambiguity fence before the external call. If the process disappears after claim, the standing remains `UNKNOWN`; replacements reconcile the same request.

### Carrier replacement

A stale endpoint identity cannot be silently rebound for an ambiguous effect. New carriers may be considered only on the pre-SEND side where absence of provider effect is established.

## 13. Current production boundaries

A major finding from source + live inspection:

```text
CURRENT PRODUCTION BIRTH PATH

CampaignSpec
 -> Agent Automation facade
 -> Temporal
 -> Browserless/Playwright
 -> ChatGPT Web
 -> Birth effect ledger
```

The following are **not currently on the production Birth effect path**:

```text
Host v2
Runtime
Agent Service Slice 1
```

They must not be described as current Birth dependencies merely because they exist elsewhere in Ordivon.

## 14. Migration into Agent Service

The clean migration is not "move all Agent Birth code into Agent Service".

### Move semantic preparation/lifecycle upward

```text
AB03 CampaignSpecValidator
AB05 CampaignCensusProjector (as Service/Board projection)
AB06 RolePromptCompiler
AB07 BirthIdentityCompiler
AB08 BootstrapCompiler
AB09 CampaignFanoutPlanner
AB10 BirthAdmissionGate
```

These become Agent Service responsibilities around `AgentRevision -> AgentInstance -> DesiredPlacement`.

### Keep durable workflow behind an adapter

```text
AB11 TemporalWorkflowIdentityPlanner
AB12 TemporalAdmissionAdapter
AB13 BirthWorkflow
AB14 BirthActivityWorker
```

Agent Service should call Temporal only when durable orchestration is actually needed; it should not copy Temporal's history/retry engine.

### Keep provider-specific effect safety near the provider

```text
AB15..AB30
```

Especially **do not move raw ChatGPT SEND into Agent Service**. The provider adapter knows the actual non-idempotent boundary and owns the strongest evidence for whether it was crossed.

Agent Service should store references to provider observations/receipts and derive semantic Agent lifecycle from them.

### Move continuation out of Birth

```text
AB31..AB34
    -> Agent Service Session / Message / communication layer
```

Provisioning and continued conversation are adjacent, but they are not the same lifecycle.

### Registry migration caution

`AB04 CampaignRegistry` may be subsumed later by Agent Service revision/input authority only if the replacement preserves:

- exact content-addressed identity;
- tamper detection;
- replay against immutable bytes;
- no transient `/tmp` path as durable workflow input.

Until then, keeping the tiny CAS is safer than prematurely merging it.

## 15. Minimal clean-room Birth kernel

If Agent Birth had to be rebuilt from zero while consuming mature substrates, the minimum faithful clone is only:

```text
1. BirthSpec + deterministic compiler
2. stable BirthEffectId
3. immutable input store/reference
4. BirthEffectLedger
5. atomic EffectAttemptClaim
6. ProviderAdapter.materialize()
7. ProviderAdapter.reconcile()
8. exact provider binding/evidence
9. durable orchestration adapter (Temporal optional for long-running production path)
10. explicit human-required branch
```

Everything else is shell, provider mechanics, or post-Birth Session behavior.

## 16. Minimal behavioral acceptance suite

A faithful reimplementation must prove at least:

1. Same CampaignSpec/Role produces exactly the same Birth effect identity.
2. Semantic prompt change changes effect identity.
3. Exact campaign registration is content-addressed and tamper fails closed.
4. First Birth persists intent before SEND is possible.
5. Two concurrent callers cannot both cross SEND for one prepared effect.
6. Exact Birth replay returns existing terminal effect instead of resending.
7. `PRE_EFFECT_FAILED` permits explicit same-effect retry and no new semantic Birth identity.
8. `UNKNOWN` and `SUBMIT_OBSERVED` never authorize blind resend.
9. Reconcile observes the same carrier/effect and can advance to BOUND without SEND.
10. Stale carrier identity cannot silently rebind an ambiguous effect.
11. Human handoff proves `providerEffectAttempted=false` before operator interaction is exposed.
12. Human resume preserves the same effect identity.
13. Campaign fan-out admits independent durable workflow identities without merging effects.
14. Temporal admission response loss is reported as ambiguity, not guessed failure.
15. Provider policy/challenge states do not trigger cross-carrier failover.
16. Only carrier/transport-local pre-SEND unavailability can rotate candidates.
17. BOUND includes canonical providerResource plus evidence digest.
18. Post-Birth continuation is impossible until the occurrence is provider-bound.
19. Replacing Browserless with another provider adapter does not change Birth identity/effect-ledger laws.
20. Replacing Temporal orchestration does not change Birth semantic/effect identities.

Most of these invariants already have direct regression tests in the current Harness suite; the decomposition turns those tests into explicit architectural contracts.

## 17. What to keep vs what not to copy

### KEEP / EXTRACT

- deterministic Birth identity algebra;
- durable pre-effect intent;
- atomic effect claim;
- ambiguity-preserving reconciliation;
- exact carrier identity binding;
- human-required proof/resume semantics;
- content-addressed frozen input;
- provider evidence references.

### ADAPT / CONSUME

- Temporal;
- Browserless;
- Playwright;
- Network v2;
- Workstation/systemd/Podman;
- SQLite as current small ledger substrate.

### MOVE

- semantic Agent lifecycle to Agent Service;
- continuation to Session/Message;
- campaign/team fan-out to Service planning/assignment semantics.

### DO NOT COPY INTO AGENT SERVICE

- Browserless browser lifecycle;
- Playwright UI mechanics;
- Temporal history/retry engine;
- raw ChatGPT Web SEND implementation;
- Network v2 routing/DNS/proxy machinery;
- provider-specific human-interaction transport;
- current MCP/CLI surface as semantic source of truth.

## 18. Final acceptance

```text
ONE-SENTENCE TEST:          PASS
MODULE-COMPLETENESS TEST:   PASS
MINIMAL-CLONE SPEC TEST:    PASS
BEHAVIORAL-ACCEPTANCE TEST: PASS (contracts extracted from existing tests)

NODE-GRAPH COVERAGE:        PASS
ATOMICITY GATE:             PASS at architectural level
EDGE-TYPING:                PASS
REASSEMBLY SUFFICIENCY:     PASS
```

The decomposition is now sufficient to rebuild Agent Birth from the leaf contracts without treating the current file/module layout as the architecture.
