# Agent Architecture LEGO Catalog R1

Date: 2026-09-18
Status: **ARCHITECTURE REFERENCE / EVIDENCE-SNAPSHOT R1**
Method: `project-kernel-decomposition` + LEGO node graph / Atomicity Gate
Scope: agent harnesses, durable sessions, execution runtimes, agent-service/control planes, artifacts/provenance, and extension systems.

## 0. Purpose

This catalog is a reusable coordinate system for decomposing agent systems. It is not a new framework and does not make Ordivon the owner of every listed concept.

For a new project, the analysis question becomes:

```text
Which LEGO does this project implement?
What authority does each implementation own?
What failure mode does it solve?
Is the implementation portable, client-native, or product-specific?
Does it introduce a genuinely new LEGO or only another provider behind an existing seam?
```

The catalog complements the existing `project-kernel-decomposition` method exposed through the Ordivon Skill plane when available. It does not require that Skill to be vendored into this repository revision, and it does not become a replacement decomposition authority.

## 1. Evidence snapshot

Public evidence checked on 2026-09-18:

- OpenAI4S: `docs/architecture.md`, `docs/backend-extension-guide.md`, `docs/webapp.md`, README and source-adjacent architecture notes.
- OpenAI Codex: public `thread-store`, rollout/compaction trace source, and the public OpenAI Plugins example repository.
- OpenClaw: agent runtime architecture, Agent Harness SDK, Task Flow, session-state awareness, plugin manifest/bundle docs.
- Hermes Agent: architecture, code execution, Skills, and Plugin docs.
- Anthropic Claude Science: public workbench announcement and documented product contract; private internals are treated as unknown.
- Agent Skills: public Agent Skills specification and Anthropic reference implementation.
- Agent Plugins: published Agent Plugins Specification 1.0.0. Portable v1 component types are exactly Agent Skills and MCP servers; richer client-native surfaces remain extensions.

Local evidence was intentionally split by lineage:

**Research-side evidence used during construction (`ordivon-next` source revision `595dfcbc50e82a7280025461f6db2ae8592f465c`):**

- the `project-kernel-decomposition` Skill and its LEGO node-graph contract;
- the detached Agent Service minimal-kernel / node-graph development records;
- Runtime/Host/Artifact/Harness domain evidence referenced from that development line.

**Current `main` integration evidence (`7648600e40eeec9912187d529c1f48653a8db565`):**

- `docs/AGENT_PLUGIN_CORE_R3.md`;
- `docs/ARCHITECTURE.md`;
- `knowledge/lessons/ordivon-agent-birth-lego-r1.md`.

Research-side records are evidence for the catalog but are **not** relabeled as current-main authorities until their own integration path lands.

## 2. Why R1 has 24 LEGO rather than the provisional 20

The preliminary list collapsed responsibilities that the source systems keep separate. Atomicity review forced four splits:

```text
Engine != Context Projection
Action != Completion Contract
Checkpoint != Branch != Recovery
Plugin envelope != Skill/Tool/MCP surfaces
```

The R1 leaf set therefore contains 24 architectural LEGO. This is a catalog vocabulary, not a mandate that every product implement all 24.

## 3. Canonical LEGO contract

Every LEGO entry is evaluated with the same fields:

```text
Id
Name
PrimaryKind
ResponsibilitySentence
Authority
Identity
State / Revision Semantics
Inputs
Outputs
Persistence Law
Concurrency / Replay Law
Failure Modes
Replacement Contract
Must-Not-Own
Acceptance Test
External Precedents
Ordivon Decision
```

An implementation may combine several LEGO in one process or repository, but the authority boundaries remain distinct.

## 4. Core-24 catalog

| id | LEGO | kind | one-sentence responsibility | natural authority | Ordivon decision |
|---|---|---|---|---|---|
| L01 | Agent Engine | DECISION_ROUTER | Repeatedly obtains model decisions and advances one cognitive run without owning physical execution. | harness | ADAPT existing/mature harness |
| L02 | Context Projection | TRANSFORM | Builds the bounded model-visible working set from durable/project state, instructions and current capabilities. | harness/context engine | ADAPT |
| L03 | Action Router | DECISION_ROUTER | Converts one model response into one explicit executable/control action channel. | harness | ADAPT |
| L04 | Completion Contract | VERIFIER_OBSERVER | Separates loop termination and domain completion claims from the evidence required to accept them. | harness + semantic owner | EXTRACT thin contract; never collapse authorities |
| L05 | Execution Attempt | STATE_AUTHORITY | Gives one admitted attempt a durable identity before physical execution begins. | Runtime | RETAIN/strengthen |
| L06 | Execution Coordinator | STATE_AUTHORITY | Serializes or schedules competing execution owners and exposes exact cancellation ownership. | Runtime | RETAIN/strengthen |
| L07 | Execution Lease | IDENTITY boundary | Proves that a lifecycle mutation targets the exact currently-owned execution generation. | Runtime | EXTRACT into exact-owner lifecycle where missing |
| L08 | Runtime Generation | STATE_AUTHORITY | Identifies one exact executor/worker/environment lifetime separately from its logical runtime label. | Runtime/provider | EXTRACT/ADAPT |
| L09 | Observation | VERIFIER_OBSERVER | Records what physically happened without promoting it to semantic success. | Runtime/Host/provider observer | RETAIN |
| L10 | Action/Thread Ledger | STATE_AUTHORITY | Stores canonical append-oriented execution/conversation facts from which projections can be rebuilt. | owning harness/session domain | ADAPT; no universal global ledger |
| L11 | History Projector / Cursor | PROJECTION_SINK | Projects branch/session/model views and incremental deltas from canonical state using explicit cursors/revisions. | session/service domain | EXTRACT small reusable contract |
| L12 | Session | STATE_AUTHORITY | Owns communication/interaction continuity independently of Task, Agent and Runtime execution identity. | Agent Service or harness-specific session owner | RETAIN separation |
| L13 | Task | STATE_AUTHORITY | Owns a semantic/service work unit that may map to zero, one or many executions. | Agent Service/domain | RETAIN |
| L14 | Task Flow | STATE_AUTHORITY | Persists multi-step orchestration state above individual tasks with revision-aware mutation. | workflow/service owner | ON_DEMAND; do not build generic engine by default |
| L15 | Checkpoint | STATE_AUTHORITY | Captures a durable reconstructable state boundary and explicit recovery coverage. | session/domain owner | ON_DEMAND, scoped |
| L16 | Branch | STATE_AUTHORITY | Defines an alternate logical lineage without erasing abandoned physical history. | session/domain owner | ON_DEMAND, scoped |
| L17 | Recovery | RECONCILER | Rebuilds from durable evidence, validates coverage, and atomically publishes only a verified candidate. | owning Runtime/session/service | EXTRACT law, implement per authority |
| L18 | Artifact Version | STATE_AUTHORITY | Identifies immutable content bytes independently of the event that produced or observed them. | Artifact domain | RETAIN/strengthen |
| L19 | Artifact Observation | STATE_AUTHORITY | Records one production/capture event and its producer/evidence lineage even when bytes equal an existing version. | Artifact domain | EXTRACT generic `ProducerRef` |
| L20 | Agent Plugin Envelope | ADAPTER_GATEWAY | Packages portable extension components under a standard identity/distribution envelope without owning their semantics. | published Agent Plugins standard/client | ADOPT upstream, no Ordivon rich format |
| L21 | Skill Surface | DATA/Instruction surface | Supplies on-demand procedural knowledge/resources through Agent Skills-compatible discovery and progressive disclosure. | Agent Skills/client | ADOPT upstream |
| L22 | Tool Surface | EFFECT interface | Exposes typed model-callable actions while keeping dispatch, policy and effect authority outside the schema. | harness/client | ADAPT client-native; do not force portable standard |
| L23 | MCP Surface | ADAPTER_GATEWAY | Connects external capabilities/resources/tools over the Model Context Protocol and client-managed authorization. | MCP client/server owners | ADOPT upstream |
| L24 | Agent Service | RECONCILER/control plane | Owns durable Agent/Goal/Task/Assignment/Session/fleet semantics above Host, Runtime and Harness. | Ordivon Agent Service | EXTRACT/build thin control plane |

## 5. Detailed contracts

### L01 — Agent Engine

```text
Identity: cognitive run / turn context supplied by owner
State: ephemeral loop state plus references to durable history
Inputs: prepared context, model, action surfaces, cancellation
Outputs: model response / action proposal / terminal loop outcome
Persistence: delegated to ledger/session owner
Replay: must not silently repeat side effects
Must-Not-Own: Runtime Job truth, domain Task truth, Artifact bytes, fleet lifecycle
Acceptance: replace the model/provider or executor adapter without rewriting the loop
```

Precedents: OpenAI4S `AgentEngine`; Codex core loop; Hermes `AIAgent`; OpenClaw agent-core/harness.

### L02 — Context Projection

```text
Identity: projection revision or source cursors when durability matters
State: disposable derived working set
Inputs: canonical history, project instructions, Skills metadata, tool availability, policy
Outputs: bounded model-visible messages/instructions/tool schemas
Persistence: source state persists; projection may be rebuilt
Must-Not-Own: canonical history or package truth
Acceptance: delete projection/cache and reconstruct equivalent context from authorities
```

Precedents: Codex project instructions/compaction; OpenClaw context engine/session wiring; Hermes progressive Skill disclosure; OpenAI4S context compaction.

### L03 — Action Router

```text
Identity: action proposal id or parent turn/action-group reference
State: deterministic routing result
Inputs: model response
Outputs: one explicit action channel
Failure: ambiguous mixed action forms
Must-Not-Own: effect execution or authorization
Acceptance: the same response routes deterministically under the same protocol profile
```

OpenAI4S demonstrates the strongest explicit rule: native structured calls take priority; otherwise one complete code Cell; finalization is a separate Engine-owned action.

### L04 — Completion Contract

```text
Identity: completion proposal / verification record
State: proposed -> verifying -> accepted|rejected|partial|blocked
Inputs: claim + evidence references
Outputs: loop terminal outcome and/or domain semantic verdict
Persistence: semantic completion persists with its natural domain owner
Must-Not-Own: evidence it cannot verify
Acceptance: process exit zero or an assistant saying 'done' cannot alone mark a domain Task successful
```

OpenAI4S makes finalization and `host.submit_output` explicit; Claude Science publicly describes reviewer checks; Ordivon Agent Service already separates Runtime evidence from `task.verify()` semantic completion.

### L05 — Execution Attempt

```text
Identity: AttemptId, immutable parent work reference
State: admitted -> started -> terminal/unknown
Persistence: allocate before touching the physical executor when durable recovery matters
Replay: retry creates another attempt, not another semantic Task
Failure: pre-start rejection, worker death, ambiguous external effect
Acceptance: a failed/prepared attempt remains visible history and cannot be reused as a new attempt
```

### L06 — Execution Coordinator

```text
Identity: ExecutionId/ticket + owner reference
State: queued -> active -> settled
Concurrency: defines one-writer or controlled parallelism law
Cancellation: targets exact execution ownership
Must-Not-Own: semantic Task scheduling unless Runtime is itself the domain owner
Acceptance: user REPL/lifecycle/recovery cannot accidentally interrupt another owner
```

OpenAI4S uses FIFO writer coordination; Ordivon Runtime already distinguishes durable Jobs/Attempts and exact projection/observation operations.

### L07 — Execution Lease

```text
Identity: frozen binding to exact execution/runtime generation
State: valid while current binding matches
Mutation law: kill/restart/interrupt only if lease is still current
Failure: stale-owner / ABA
Acceptance: an old watchdog cannot kill a newly replaced worker
```

OpenAI4S is the clearest precedent (`*_if_current(lease)`).

### L08 — Runtime Generation

```text
Identity: RuntimeGenerationId distinct from logical runtime/provider name
State: preparing -> ready -> active -> terminal
Relationships: parent/recovered-from generation references where useful
Persistence: record exact environment/provider identity required for later evidence
Acceptance: a restart creates a new generation; old identity is never silently reused
```

### L09 — Observation

```text
Identity: observation/evidence record
Inputs: physical/provider read-back
Outputs: bounded facts and evidence refs
Law: observed execution success != semantic requirement satisfied
Failure: unavailable/ambiguous observation remains ambiguity
Acceptance: missing read-back cannot be converted to success
```

### L10 — Action / Thread Ledger

```text
Identity: ordered event/item ids + owning aggregate/thread/session
State: append-oriented facts; materialized lifecycle rows may coexist
Persistence: canonical source is not a UI transcript
Replay: reducers/projectors reconstruct derived views
Must-Not-Own: facts whose authority belongs to another subsystem
Acceptance: conversation/activity projections can be rebuilt after cache deletion
```

OpenAI4S is action-ledger-first; Codex persists rollout/thread history; Hermes and OpenClaw persist sessions but with different canonical models.

### L11 — History Projector / Cursor

```text
Identity: cursor/revision/watermark
Inputs: canonical events/state + selected lineage
Outputs: model history, chat/notebook/board views, incremental delta
Failure: history gap is explicit, never inferred away
Acceptance: changesSince(cursor) either returns exact delta or signals a gap requiring full refresh
```

OpenClaw's `stateVersion`/`changesSince`/`historyGap` is a strong precedent; OpenAI4S uses one append-only history projection for provider/chat/notebook branch views.

### L12 — Session

```text
Identity: SessionId
State: open/active/closed plus owner-specific lifecycle
Purpose: communication/context continuity
Must-Not-Own: Task identity, Agent identity, Runtime Job identity
Acceptance: one Task may span sessions and one session may discuss multiple Tasks without identity collision
```

### L13 — Task

```text
Identity: TaskId independent of execution ids
State: semantic/service lifecycle
Relationship: Task -> Assignment -> zero/one/many Runtime Jobs/Attempts
Must-Not-Own: physical execution truth
Acceptance: Runtime retry does not create a new Task and process exit does not decide Task success
```

### L14 — Task Flow

```text
Identity: FlowId + monotonic revision
State: durable multi-step orchestration state
Mutation: expected-revision/CAS when concurrent writers exist
Recovery: controller reconciles child outcomes after restart; never blindly replays side effects
Must-Not-Own: child Task physical truth
Acceptance: stale writer conflicts instead of overwriting a newer flow revision
```

OpenClaw Task Flow is the clearest current public precedent. Ordivon should use this LEGO only where a real multi-step control-state gap remains after Task + mature workflow substrate reuse.

### L15 — Checkpoint

```text
Identity: CheckpointId + exact source cursor/revision
State: immutable captured boundary
Content: only reconstructable/durable state with explicit coverage
Law: checkpoint != arbitrary process-memory snapshot
Acceptance: recovery report names verified/unverified state classes
```

### L16 — Branch

```text
Identity: BranchId + ancestry/checkpoint reference
State: active/inactive lineage
History law: abandoned physical tail is retained for audit
Must-Not-Own: physical effect rollback it cannot actually perform
Acceptance: fork/revert changes logical projection without rewriting historical facts
```

### L17 — Recovery

```text
Identity: RecoveryAttemptId and candidate generation when needed
Pipeline: admit -> rebuild candidate -> validate -> reconcile external effects -> atomic publish
Outcome: active|partial|failed with coverage, not a boolean fiction
Law: unknown external outcome is reconciled, not blindly retried
Acceptance: invalid candidate cannot replace current runtime/state
```

OpenAI4S provides build-first candidate recovery; OpenClaw durable flows explicitly reload/reconcile rather than preserving a JS stack.

### L18 — Artifact Version

```text
Identity: content digest / immutable VersionId
State: immutable bytes + metadata
Law: same bytes may reuse one content version
Must-Not-Own: producer event identity
Acceptance: byte-equivalent outputs do not fabricate semantic version changes
```

### L19 — Artifact Observation

```text
Identity: ObservationId
Producer: generic ProducerRef(kind,id,attempt?,generation?)
Relationships: artifact/version, producer, environment, inputs, trace/evidence
Law: same ArtifactVersion may have multiple observations
Acceptance: two independent executions producing identical bytes yield two observations and one content version
```

OpenAI4S currently centers producing Cell identity. Ordivon should generalize producer kinds to Cell, Tool, Runtime execution, browser step, render, human edit, remote job and import.

### L20 — Agent Plugin Envelope

```text
Identity: plugin name/version/spec target/content/package identity
Portable components: exactly what the published Agent Plugins specification defines
Lifecycle: discovery/install/enable/trust/authorization/activation remain client concerns unless standardized
Law: package presence != authorization
Must-Not-Own: Runtime/Host/domain state, credentials, semantic Tool effects
Acceptance: valid independent components survive failure of an invalid sibling at the specified boundary
```

**Ordivon policy remains `docs/AGENT_PLUGIN_CORE_R3.md`: adopt the published portable standard and do not invent a rich Ordivon-native portable format.**

### L21 — Skill Surface

```text
Identity: Agent Skill package/name plus source/revision/digest as client needs
State: available -> selected -> instruction/resource loaded
Law: progressive disclosure; scripts/resources are not automatically model context
Must-Not-Own: tool execution authority
Acceptance: a client can discover metadata before loading full instructions/resources
```

### L22 — Tool Surface

```text
Identity: tool/capability id + invocation id
Content: typed schema/spec visible to model + dispatcher binding
Law: model request != authorization; schema != effect implementation
Must-Not-Own: Runtime execution state or portable Plugin semantics
Acceptance: alternate implementation can replace handler behind the same callable contract and policy boundary
```

### L23 — MCP Surface

```text
Identity: MCP server/session/request/tool/resource identities per protocol/client
Purpose: remote/local capability transport and discovery
Authorization: client/provider owned; plugin config is not a secret store
Law: transport/config failure of one server need not invalidate independent components
Acceptance: MCP provider can change without changing domain semantic ownership
```

### L24 — Agent Service

```text
Identity: AgentDefinition/Revision/Instance, Goal, Task, Assignment, Session, placement and service events
State: durable semantic/control-plane lifecycle
Inputs: service requests, desired fleet/work state, provider observations
Outputs: assignments, desired placements, governed routes and projections
Must-Not-Own: Runtime physical execution truth, Harness model loop, Board projection as canonical truth
Acceptance: Harness/Runtime provider can be replaced behind adapters without changing Task/Goal/Agent identity algebra
```

Detailed L24 Agent Service semantics were derived from the detached Agent Service development line rooted beyond `595dfcbc`; they remain research-side evidence here rather than a claim that the corresponding design document is already canonical on `main`.

## 6. Cross-harness matrix

Legend:

- `●` = explicit first-class public mechanism/contract found.
- `◐` = adjacent or partial mechanism; do not treat as the same contract.
- `◇` = public product contract exists but implementation details are private/insufficient for source-level equivalence.
- `○` = no comparable first-class public mechanism found in the evidence set; not proof of absence.

| LEGO | OpenAI4S | Codex | Claude Science | Hermes | OpenClaw |
|---|:---:|:---:|:---:|:---:|:---:|
| L01 Engine | ● | ● | ◇ | ● | ● |
| L02 Context Projection | ● | ● | ◇ | ● | ● |
| L03 Action Router | ● | ● | ◇ | ● | ● |
| L04 Completion Contract | ● | ◐ | ◇ | ◐ | ● |
| L05 Execution Attempt | ● | ◐ | ◇ | ◐ | ● |
| L06 Execution Coordinator | ● | ◐ | ◇ | ◐ | ● |
| L07 Exact Lease | ● | ○ | ○ | ○ | ◐ |
| L08 Runtime Generation | ● | ○ | ○ | ○ | ◐ |
| L09 Observation | ● | ● | ◇ | ● | ● |
| L10 Ledger / durable history | ● | ● | ◇ | ● | ● |
| L11 History Cursor/Projection | ● | ● | ◇ | ● | ● |
| L12 Session | ● | ● | ● | ● | ● |
| L13 Semantic Task | ◐ | ◐ | ◐ | ◐ | ● |
| L14 Durable Task Flow | ○ | ○ | ○ | ○ | ● |
| L15 Checkpoint | ● | ◐ | ◐ | ◐ | ◐ |
| L16 Branch | ● | ● | ● | ○ | ◐ |
| L17 Recovery | ● | ● | ◐ | ● | ● |
| L18 Artifact Version | ● | ○ | ◇ | ○ | ○ |
| L19 Artifact Observation | ● | ○ | ◇ | ○ | ○ |
| L20 Plugin Envelope | ◐ | ● | ◐ | ● | ● |
| L21 Skill Surface | ● | ● | ● | ● | ● |
| L22 Tool Surface | ● | ● | ◇ | ● | ● |
| L23 MCP Surface | ● | ● | ● | ● | ● |
| L24 Agent Service / fleet control | ○ | ○ | ○ | ◐ | ● |

This matrix is descriptive, not a scorecard. Different systems deliberately center different objects:

```text
OpenAI4S     -> scientific execution/provenance
Codex        -> durable coding thread and native coding loop
ClaudeScience-> scientific workbench product contract
Hermes       -> integrated autonomous assistant/gateway
OpenClaw     -> gateway/control plane + replaceable agent runtimes
Ordivon      -> composition layer with separate Agent Service / Runtime / Host / Harness authorities
```

## 7. Canonical assemblies

The catalog intentionally allows larger concepts to be compositions rather than leaf LEGO.

### Agent Harness assembly

```text
L01 Engine
+ L02 Context Projection
+ L03 Action Router
+ L04 loop-side completion
+ L21 Skill admission
+ L22 Tool admission
(+ L23 MCP client where supported)
```

Harness must not own L13 semantic Task truth or L05-L09 Runtime physical truth unless the product intentionally collapses those domains and documents the trade-off.

### Execution Runtime assembly

```text
L05 Attempt
+ L06 Coordinator
+ L07 Lease
+ L08 Generation
+ L09 Observation
```

Runtime is therefore an execution substrate, not an all-owning agent platform.

### Durable Session assembly

```text
L10 Ledger/history authority
+ L11 projector/cursor
+ L12 Session
+ optional L15 Checkpoint
+ optional L16 Branch
+ L17 Recovery
```

### Artifact provenance assembly

```text
L18 Artifact Version
+ L19 Artifact Observation
+ foreign refs to L05/L08/L09 or other producers
```

### Extension assembly

```text
L20 portable Agent Plugin envelope
├── L21 Agent Skills
└── L23 MCP servers

L22 client-native Tool surface remains a client/harness concern unless carried through MCP or another standardized component.
```

Agent Plugins v1.0.0 defines exactly two portable component types: Agent Skills and MCP servers. L22 Tool remains a client/harness action surface unless a capability is exposed through MCP or another standardized component.

### Agent Service assembly

```text
L24 Agent Service
+ L12 Session
+ L13 Task
+ optional L14 Task Flow
+ L11 revision/delta projection
+ adapters to Runtime/Harness/Host/identity/policy/protocol providers
```

## 8. Cross-system architecture laws frozen by R1

1. **Intent != authority.** A model or Agent request is not permission to execute an effect.
2. **Task != execution.** Semantic work identity survives retries, reassignment and multiple Runtime Jobs.
3. **Attempt-before-effect when durability matters.** Persist enough identity before touching an uncertain executor.
4. **Runtime mutation targets exact ownership.** Prefer execution/generation leases over session-global kill semantics.
5. **Failure is history.** Do not rewrite failed attempts/events to make retries look successful.
6. **Observation != semantic success.** External/provider/runtime evidence feeds a verifier; it is not automatically the verdict.
7. **Content identity != production-event identity.** Artifact Version and Artifact Observation remain separate.
8. **Checkpoint != heap snapshot.** Report recovery coverage explicitly.
9. **Recovery = rebuild + reconcile + validate + atomic publish.** Never blindly replay unknown external effects.
10. **Canonical truth != projection.** Chat, Notebook, Board, activity UI and model context must be rebuildable when their source authority allows it.
11. **Plugin package != authorization.** Installed/enabled/model-visible/authorized/active are separate states.
12. **Portable core stays small.** Agent Plugins v1 portable components are Agent Skills and MCP; rich harness/hooks/agents/providers remain client-native until standards converge.
13. **Progressive disclosure is an attention boundary.** Broad discovery must not imply broad context injection.
14. **Immutable candidate + validated activation** is preferred for executable generations, package updates and recoverable state transitions.
15. **Unknown external outcome is first-class.** Reconcile before retrying non-idempotent effects.

## 9. Ordivon adoption map

| LEGO group | local action |
|---|---|
| L01-L04 Harness | keep Harness narrow; reuse mature loops and client adapters rather than move them into Agent Service or Runtime |
| L05-L09 Runtime | continue exact Job/Attempt/evidence semantics; add exact lease/generation concepts only where they close a demonstrated lifecycle race |
| L10-L12 Continuity | preserve authority-specific history; standardize small cursor/delta semantics where multiple consumers need re-entry |
| L13 Task | Agent Service authority; Runtime Job remains foreign execution reference |
| L14 Task Flow | ON_DEMAND; prefer existing workflow/control substrates before building a generic Ordivon flow engine |
| L15-L17 Checkpoint/Branch/Recovery | implement only per domain that can define reconstructable state and honest recovery coverage |
| L18-L19 Artifact | retain Artifact domain; generalize observation producer beyond scientific Cell identity |
| L20 Plugin | ADOPT published Agent Plugins; keep `docs/AGENT_PLUGIN_CORE_R3.md` policy |
| L21 Skill | ADOPT Agent Skills; existing Skill MCP remains an adapter, not the semantic owner |
| L22 Tool | client/harness-native action surface; no new portable Ordivon Tool format |
| L23 MCP | standard transport/capability surface; authorization remains natural owner/client responsibility |
| L24 Agent Service | continue current harness-neutral durable control-plane slices; Board remains projection |

## 10. Explicit do-not-build boundaries

R1 does **not** justify building:

- a new Ordivon rich Plugin schema;
- a universal global Ledger that duplicates Runtime, Host, Harness and domain truth;
- a universal durable workflow engine;
- a universal process/heap checkpoint mechanism;
- a second model/tool loop inside Agent Service;
- a second physical-execution ledger inside Agent Service;
- Board/UI storage as canonical Task/Agent truth;
- portable hooks/agents/providers/commands invented locally ahead of upstream standards;
- one universal ID used for Task, Session, Agent and execution.

## 11. Minimal implementation / migration order

### R1-A — Catalog only

- preserve this catalog and machine-readable graph;
- when `project-kernel-decomposition` is available through the current Skill plane, let adapters/references consult this catalog without requiring a repo-local copy of that Skill;
- do not migrate production code merely to match vocabulary.

### R1-B — Identity alignment

When modifying Runtime/Host/Agent Service/Artifact code, map existing identities to:

```text
TaskId
AssignmentId
RuntimeJobId
AttemptId
ExecutionId
RuntimeGenerationId (only if required)
ArtifactVersionId
ArtifactObservationId
SessionId
HistoryCursor/Revision
```

Do not rename mature existing identities without a real ambiguity or bug.

### R1-C — ProducerRef for Artifact

Evaluate the smallest cross-domain producer reference:

```text
ProducerRef {
  kind
  id
  attemptId?
  generationId?
  traceId?
}
```

Adopt only after the Artifact package's own decomposition/acceptance shows it fits current version/observation ownership.

### R1-D — Cursor/delta seam

Unify only the generic pattern:

```text
state_version
changes_since(version)
history_gap
```

where Agent Service/Host consumers actually need incremental reconciliation. Do not make all stores event-sourced merely for symmetry.

### R1-E — Exact lifecycle lease

Where a real stale-owner race exists, introduce exact lease binding around restart/interrupt/retire. Do not add Lease objects to systems with no competing lifecycle actors.

## 12. Rules for decomposing future projects

For every new agent project:

1. run the normal evidence-first project-kernel decomposition method first (using the current Skill catalog binding when available);
2. map candidate responsibilities to Core-24 only after source evidence exists;
3. a project-specific feature that matches an existing LEGO is a provider/implementation, not a new universal node;
4. create a new LEGO only when an important authority/failure mode cannot be represented without violating Atomicity Gate;
5. mark private-service internals `UNKNOWN`; public product contracts do not justify invented implementation details;
6. update the cross-harness matrix only from current source/official docs;
7. prefer upstream standards and thin adapters over local portable formats.

## 13. Acceptance

```text
ONE-SENTENCE TEST: PASS
MODULE-COMPLETENESS TEST: PASS
NODE-GRAPH COVERAGE: PASS
ATOMICITY GATE: PASS_FOR_R1_CATALOG_LEVEL
EDGE-TYPING: PASS
REASSEMBLY SUFFICIENCY: PASS
MINIMAL-CLONE SPEC TEST: PASS_AS_ASSEMBLY_CONTRACTS
BEHAVIORAL-ACCEPTANCE TEST: PASS_SPECIFIED_NOT_GLOBAL_IMPLEMENTATION
```

Interpretation: R1 is sufficient to classify and compare future agent architectures without reopening broad ontology design. It does **not** claim all 24 LEGO are implemented locally, nor that all systems should implement them.

## 14. External source snapshot

- https://github.com/PKU-YuanGroup/OpenAI4S/blob/main/docs/architecture.md
- https://github.com/PKU-YuanGroup/OpenAI4S/blob/main/docs/backend-extension-guide.md
- https://github.com/PKU-YuanGroup/OpenAI4S/blob/main/docs/webapp.md
- https://github.com/openai/codex/tree/main/codex-rs/thread-store
- https://github.com/openai/codex/tree/main/codex-rs/rollout-trace
- https://github.com/openai/plugins
- https://github.com/openclaw/openclaw/blob/main/docs/agent-runtime-architecture.md
- https://github.com/openclaw/openclaw/blob/main/docs/plugins/sdk-agent-harness.md
- https://github.com/openclaw/openclaw/blob/main/docs/automation/taskflow.md
- https://github.com/openclaw/openclaw/blob/main/docs/concepts/session-state.md
- https://github.com/openclaw/openclaw/blob/main/docs/plugins/manifest.md
- https://github.com/NousResearch/hermes-agent/blob/main/website/docs/developer-guide/architecture.md
- https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/code-execution.md
- https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/plugins.md
- https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/skills.md
- https://www.anthropic.com/news/claude-science-ai-workbench
- https://github.com/anthropics/skills
- https://agent-plugins.org/specification

## Verdict

**FREEZE AGENT ARCHITECTURE LEGO CATALOG R1 AS A REFERENCE VOCABULARY, NOT A NEW ALL-OWNING PLATFORM: preserve separate semantic authorities, use the 24 LEGO to compare implementations and expose failure boundaries, adopt Agent Skills/Agent Plugins/MCP where standardized, and evolve the catalog only when evidence demonstrates a new atomic responsibility.**
