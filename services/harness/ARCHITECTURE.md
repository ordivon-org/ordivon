---
schema_version: 1
id: harness.architecture
title: Ordivon Harness architecture
type: architecture
profile: engineering
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-harness
audience:
  - builder
  - operator
  - agent
updated: 2026-11-16
summary: Canonical world model for Harness as the durable cognitive execution substrate of an Agent, including cognition, control, effects, continuity and caller/Runtime/Host boundaries.
evidence_status: verified
readiness: READY
applies_to:
  - ordivon-harness
related:
  - harness.start
  - harness.authority
---
# Ordivon Harness Architecture

## Purpose

Ordivon Harness is the **durable cognitive execution substrate of an Agent** and the independent authority for one bounded Agent Run. A caller supplies immutable semantic/execution authority in a `HarnessRunContract`; the Agent owns semantic reasoning, cognition selection and action choice; Harness turns those choices into exact, provenance-bound, recoverable state transitions and effect intents.

Harness does not build the Agent's world model for it. It preserves the structural truth required for an Agent to build, revise, inspect and act from its own world model without conflating history, cognition, observation, control or physical effects.

## Harness world model

The current architecture is not a `messages[]` transcript machine. It has six distinct state domains:

| Domain | Question it answers | Current owner/mechanism |
| --- | --- | --- |
| **Canonical History** | What actually happened? | append-only Harness Journal/CAS, Provider/Tool/WorkingSet events and receipts |
| **Durable Cognition** | What has the Agent explicitly selected as current long-lived cognition? | committed `HarnessWorkingSetSpec` over exact `HarnessWorkingViewSource` pins |
| **Interaction Cognition** | What is the caller currently saying to the Agent? | exact plain caller ingress after the latest `needs_input` boundary |
| **Attempt Cognition** | What has the Agent just observed during this cognition attempt? | Provider-authored Tool-call/result exchange reconstructed from durable evidence |
| **Execution Control** | What may the Agent lawfully do now, and which authority objects may it address? | admitted Tools/cognition controls, budgets, caller provenance and current WorkingSet addressability |
| **Effects** | What action was admitted and what physically happened? | durable Tool/Provider intent/fence/receipt chains plus Runtime/external authority |

These domains compose into one effective Agent turn without collapsing into one authority:

```text
                         Canonical History
                               │
            ┌──────────────────┼──────────────────┐
            ▼                  ▼                  ▼
   Durable Cognition   Interaction Cognition   Attempt Cognition
      WorkingSet            caller ingress        Tool exchange
            └──────────────────┬──────────────────┘
                               ▼
                      Effective Model View
                               │
                     + Execution Control
                               │
                               ▼
                             Agent
                 ┌─────────────┼─────────────┐
                 ▼             ▼             ▼
           cognition       external       conclusion
           transition       action
                 │             │
                 ▼             ▼
            WorkingSet      Runtime / World
                 └──────┬──────┘
                        ▼
                   new History
```

The core inequalities are architectural laws, not documentation slogans:

```text
History ≠ Cognition
Storage ≠ Selection
Observation ≠ Retention
Caller Input ≠ Durable Cognition
Attempt Change ≠ Cognition Change
Cognition Change ≠ Progress
Progress ≠ External Effect
Tool Intent ≠ Physical Effect
Physical Effect ≠ Semantic Success
Source Identity ≠ Source Truth
Provenance ≠ Semantic Validity
Exact Replay ≠ Redispatch
```

Harness therefore owns **structural cognition and execution truth** while the Agent owns **semantic cognition and choice**. Harness may validate, materialize, persist, recover, fence and make authority addressable; it must not rank relevance, choose memories, infer semantic correction, silently summarize sources or conclude world truth on the Agent's behalf.

### Cognition sovereignty laws

1. **History is not cognition.** Past Run events remain durable without being replayed automatically into the model view.
2. **Observation is not retention.** Tool results, caller messages and discovered/materialized sources do not become durable cognition merely because they exist or were observed.
3. **Durable cognition selection belongs to the Agent.** A source becomes current durable cognition only through an Agent-owned WorkingSet selection/promotion path.
4. **Semantic meaning belongs to the Agent; structural truth belongs to Harness.** Harness proves exact identity/provenance/transitions, not relevance, truth or semantic supersession.
5. **Authority required for lawful Agent choice must be visible and addressable.** Hidden current authority that an action must reference is an Agent-usability defect; execution control therefore exposes currently promotable caller indexes, admitted capabilities and exact current WorkingSet identities when those actions are granted.
6. **Cognition, interaction, control and effects remain distinct state domains.** They may be composed for one turn but cannot be treated as interchangeable facts.
7. **Recovery restores proven state, never invented continuity.** Lost Provider/Runtime responses are replayed/reconciled from durable authority; uncertain effects are not blindly redispatched.
8. **New Harness mechanisms require an otherwise inexpressible Agent state transition.** Generic Memory, RAG, ranking, summarization or supersession subsystems are not architectural defaults.

## Ownership

```text
caller / domain / optional Host
        │
        │ HarnessRunContract
        ▼
┌────────────────────────────┐
│ Ordivon Harness            │
│                            │
│ independent Journal / CAS  │
│ Provider Call continuity   │
│ model ↔ Tool loop          │
│ Run budgets                │
│ pause / resume / recovery  │
│ Trace / Run Receipt        │
│ CompletionProposal         │
└─────────────┬──────────────┘
              │ Tool-bearing Runs only
              ▼
       HarnessRuntimeClient
              │
              ▼
           Runtime
```

Harness does not own caller Task state, domain commitments, final acceptance, or Runtime Workspace/Job truth. Runtime does not know the Harness state machine. Host is an optional caller rather than a persistence prerequisite.

> **Run terminality is not epistemic closure.** `candidate_completed` means the bounded Run formed a candidate result; it may retain explicit unresolved unknowns for caller/domain judgment.

## Source layout and retention boundaries

The following describes the current *source responsibilities*, not a certificate
that every optional service or model is installed or running. Historical documents
and evaluation fixtures are not authoritative execution entrypoints.

| Path | Natural responsibility | Source-level treatment |
| --- | --- | --- |
| `src/ordivon_harness/` | Public Run API, Store port, PG implementation, external Tool/Gateway boundaries | Keep one public contract per responsibility; PG-only CLI, no implicit SQLite writer fallback |
| `src/ordivon_harness/ordivon/` | Agent Loop, working-set projection, Provider/Tool continuity and bridges | Keep backend-neutral Run/Bridge classes; do not reconstruct an alternate agent framework |
| `scripts/` | Provider adapters, Browserless, Agent Automation, PG cutover and operational tools | Keep real caller-bound scripts; move truly shared identity checks to `wake_turn_contract.py`; retire migration scripts only after consumer cutover |
| `formal/` | Scoped TLA+/TLC models and counterexample probes | Model results do not imply Python/SQL refinement or installed effect success |
| `tests/`, `evals/`, `fixtures/` | Native implementation consumers, evaluation and fixed input data | Retain tests for real boundaries; remove self-referential tests with retired implementations |
| `planning/`, `schemas/`, `config/` | Existing LEGO graph, machine-readable input contracts and deployment/benchmark configuration | Update evidence paths and exact consumer contracts with source retirement, never create a second registry |
| `docs/`, `research/`, `evidence/` | Current owner guidance, prior experiments and provenance | Keep the source-of-truth distinction explicit: historical results are not automatically current deployment claims |
| `systemd/`, `containers/`, `.github/` | Service units, containers, native release automation | Verify installed revision and live consumer independently of a Git or CI result |

### Thought → Logic → Capability: current source map

Thought LEGO are reusable methods, not owners or a runtime permission layer:
construct forward from the caller's objective; work backward from loss,
duplicate effect, stale authority, ambiguous output, and incorrect completion.
A logic LEGO expresses each problem as state, preconditions, invariants, failure
partitions and falsification obligations. A capability LEGO is the source
implementation behind the existing Store, Provider, Tool and Runtime ports.

| Logical problem | Current capability-bearing source | Non-negotiable boundary |
| --- | --- | --- |
| Contract/Run composition | `core_contracts.py`, `agent_run.py`, `run_authority.py` | One immutable Contract; Run composition must not select external task outcomes |
| Current cognition vs history | `working_view.py`, `ordivon/turn_projection.py`, `ordivon/run_continuity.py` | Retained evidence is not automatic model-visible relevance |
| Provider turn and retry | `ordivon/loop.py`, `ordivon/provider_lifecycle.py` | Provider reply/transport result is not domain completion |
| Durable continuity | `postgres_store.py`, `ordivon/run_continuity.py`, `crates/harness-pg/` | Existing Harness PG writer is the only Run journal authority |
| Tool effect and current permission | `gateway_execution_policy.py`, `plugin_gateway_effect.py`, `ordivon/runtime_bridge.py`, `runtime_port.py` | Caller grant, native admission and physical receipt are different facts |
| Workspace lifecycle | `workspace_claim.py`, `run_authority.py`, `agent_run.py` | Run ACTIVE without active Jobs must still protect its Workspace |
| Recovery/finalization | `ordivon/run_continuity.py`, `ordivon/runtime_bridge.py`, `agent_run.py` | UNKNOWN is partitioned by issuer/OS/recipient observations; release requires independent acceptance |
| Formal verification | `formal/`, `tests/`, `crates/harness-core/` | Source proof, PostgreSQL test, installed native effect, domain receipt are separate claims |

The Gateway permission kernel `gateway_execution_policy.py` is independent of
Run composition; `plugin_gateway_effect.py` imports it directly, while
`run_authority.py` re-exports historical names without owning duplicate
policies. This is a source-only modularization; it does not install a new
Harness or grant Runtime issuer privileges.

**Source-certified decomposition of the existing boundaries (2026-11-19):**

| Existing facade | Delegated module | Exact single responsibility |
| --- | --- | --- |
| `ordivon/run_continuity.py` | `ordivon/run_source_inspection.py` | Revision-fenced original Tool-source identities and Run finalization source assessment; a query is never a release certificate |
| `ordivon/runtime_bridge.py` | `ordivon/runtime_effect_policy.py` | Pure original Intent/Fence-to-physical-request validation and Runtime delivery-state interpretation |
| `ordivon/runtime_bridge.py` | `ordivon/runtime_job_lookup.py` | Bounded Runtime read-only Job recovery lookup by exact original request and Workspace, with strict cursor and returned-identity validation |
| `ordivon/loop.py` | existing `ordivon/run_contract.py` | Reconcile Provider token-count projections within the existing RunBudget contract, without a second counter model |

All public `EventSourcedRunContinuity` methods continue on the one original
Run API through an inspection mixin. The Runtime Bridge continues exposing
its historical functions as aliases to the extracted modules; there is only
one implementation. No new PostgreSQL Writer, Runtime schedule, effect issuer,
tool registry or extra state authority was introduced.

**Original Run birth and legacy adoption are distinct operations.**
For NEW Workspace-bearing Runs, the supported `HarnessAgentRun.create`
first obtains the native HELD Workspace Claim, then commits the original Run
birth to the existing Harness PostgreSQL Journal. An unconfirmed native
reservation means **no newly born PG Run**; a lost reserve reply that did
commit is recovered by the exact stable native request key before PG birth.
An orphan HELD Claim after a later PG failure is protected and requires
explicit original-owner reconciliation; it is not auto-released by a TTL.

For EXISTING PostgreSQL Runs, both `HarnessAgentRun.open` and idempotent
`create` must read the same original Native Claim and prove HELD before
any Provider/Tool execution. They **never** reserve a new Workspace Claim
using the current caller's mutable Workspace reference. No-tool Runs are
unaffected. Native NOT_COMMITTED claim absence is distinguished from
transport UNKNOWN; neither allows dispatch or automatic re-pinning.

The real-PG18 `tests/test_workspace_claim_run_birth.py` and
`tests/test_legacy_workspace_claim_reentry_pg.py` prove the two
operations, lost reply, error and race-recovery boundaries with a Fake
Native transport. They are source/isolated PG evidence, **not** physical
proof for old production Runs. A caller-supplied WorkspaceRef, original
RunContract/sourceRef hash or successful PG reopen cannot establish an
unclaimed historical Run's physical Workspace provenance. A natural
authenticated Runtime Owner must first verify original physical identity,
source and effect history, then pin it in Runtime under the original
Run identity; only afterwards can normal `open` resume it. A deleted
original Workspace cannot be repaired by claiming another one. Do not
auto-migrate old Runs or enable global Workspace GC.

**R29 Native Claim-only client; source, delivery and deletion remain separate.**
Current Rust Runtime's `ClaimFinalizerOnly` profile uses a separate authenticated
`/harness/mcp` Principal and exposes only `workspace.get`,
`workspace.claim.reserve/get/release`. It does NOT require the original
Harness JobIssuer SQL function in the Runtime database. Harness PG and Runtime
PG may remain distinct databases; an original Run can obtain and retain the
exact native HELD Claim across those databases without moving any Harness
table, Registry or scheduling controller.

The independent CLI for a NEW Workspace-bearing Run accepts only an explicit
dedicated `--runtime-claim-url http://127.0.0.1:<port>/harness/mcp`
(and private `--runtime-claim-bearer-token-file`). It does not downgrade
to ordinary `/mcp`; that route cannot release its own Claims once the
ordinary native release-denial source is installed. Existing normal Gateway
execution continues using ordinary `/mcp` and a different Bearer. No Run,
User message or Tool grant contains the Native Claim credential.

**Not a certified Finalizer yet.** A separate token and a strong normal-route
DENY prevent accidental ordinary release; they do not prevent the *privileged*
Claim-only caller from issuing `workspace.claim.release` while original
Harness PG still reports CREATED, no recipient byte has been accepted and
normal nonforce Close must still be protected. R29 reproduced that physical
RED with a disposable original Run against the exact native Claim-only
Runtime candidate; it does not affect a real user Workspace. The existing
`release_workspace_after_delivery` checks Run status, PG source-settled and
a supplied recipient ACK plus verifier callback, but those supplied values
are NOT independent authenticated domain or OS attestations.

Qualify a true Finalizer only after its current authenticated original Run,
recipient's original output bytes/receipt, all actually issued native Attempts
and no-future-spawn/drain have been independently verified, and its Bearer is
inaccessible to ordinary executors. A root `trusted_local` execution that
can read the same protected file is not isolated by chmod 0600 alone.
Do not install Claim-only credentials, release historical claims or enable
global GC based only on source tests or simulated ACKs.

**Next structural cuts are consumer-driven, not directory-driven.**
The remaining `ordivon/run_continuity.py` still couples working-set mutation,
Provider dispatch, and Tool receipts; they must retain one PG writer and
atomic Run CAS when extracted. The `ordivon/loop.py` function `_run`
contains nested `execute_tool_calls`, `evaluate_turn_progress`, and
`restore_projected_cognition_overlay` with shared mutable locals: do not
move those closures behind an invented second state machine. Extract a
single explicit per-attempt state contract only after proving restore/replay
parity, exact budgets and cancellation. Runtime Bridge's remaining physical
`_execute` and reconciliation methods must retain frozen request identity,
original Tool Intent, externally owned Job truth and reachable UNKNOWN.

**Falsification checklist:** negative cross-Workspace Job, reused cursor,
boolean/u64 cursor, changed clientRequestId, stale Run revision, unresolved
physical Tool, incomplete external recipient ACK and loss between Owner
admission and reply. Negative checks verify local code boundaries; neither
source verification nor a terminal Job proves physically fenced future spawn
or domain completion.


`sqlite_store.py` and `scripts/sqlite_*` are still separately reachable legacy
implementations or migration inputs; their existence does not authorize them as
the active PostgreSQL write authority. The old `store_ops.py` SQLite-only backup
implementation had no non-test current source consumer and is retired rather than
kept as a misleading generic Store interface. Native PG backup/recovery belongs
to the PostgreSQL owner and its installed operational workflow.

**Human operators:** begin with `ordivon-harness doctor` and the existing
`mise` Owner commands. Use a specifically disposable PostgreSQL test database
for destructive DB admission/recovery tests. Determine service readiness from
installed SourceCut and actual Runtime/Provider readback, not local package files.

**Agents:** bind the exact Git SourceCut, `HarnessRunContract`, Store/Tool ports,
affected consumers, and one scoped R2.1 proof obligation. Choose the existing
Owner-native verifier, report model/source/real-PG/installed evidence separately,
and retire code only after reaching the final consumers. UNKNOWN is not PASS.


## Run authority and external orchestration

Harness begins at one exact caller-authored `HarnessRunContract`:

```text
caller / domain / workflow / resource allocator
        │
        │ chooses objective/context/provider/model/Tools/budget/privacy/deadline
        │ and binds one exact system-manifest digest
        ▼
   HarnessRunContract
   immutable Run authority
        │
        ▼
    HarnessAgentRun → Receipt / CompletionProposal
```

Higher-level multi-Run planning, aggregate resource envelopes, profile discovery, Strategy rationale, prior-attempt accounting, successor selection, and retry policy are outside Harness. The former `HarnessExecutionMandate`, `HarnessExecutionProfile`, `HarnessExecutionStrategy`, `HarnessMandateConsumption`, `CompiledHarnessAttempt`, and `compile_harness_attempt()` layer is retired rather than preserved as a second orchestration/resource-allocation ontology.

Harness now executes one current Agent-loop scheduling kernel. The experimental LoopDriver/morphology identity layer is retired because current authoritative state contains no bound LoopDriver records and no independent consumer selects an alternate mode. Explicit deliberate-then-tool behavior is caller/domain composition: perform a no-Tool Agent turn under owner authority, retain whatever cognition evidence that owner chooses, then enter `DomainToolLoopRunner` with the exact Tool grant. Harness does not own a generic two-phase lifecycle or strategy policy.

## Self-change evidence and promotion authority

RSI P2 validated one bounded source-improvement loop without moving source-generation, evaluation, or promotion policy into Harness:

```text
exact baseline failure evidence
        ↓
source-change Agent
        │ semantic candidate edits
        ▼
Runtime materialization
        │ exact source bytes only
        ▼
independent evaluator
        │ baseline ↔ candidate evidence
        ▼
independent promotion decision
        │ promote / revise / reject
        ▼
guarded canonical Git promotion
```

The authorities remain deliberately separate. The source-change Agent may choose what to alter and author the replacement bytes; it does not certify that its own candidate is better. Runtime proves only whether the requested exact source edit can be materialized and executed. The evaluator owns the comparison evidence, not the candidate. Promotion is a separate semantic decision over exact proposal, diff and evaluation evidence, and canonical Git movement remains guarded by repository ancestry/concurrency checks.

The experiment also exposed an action-encoding boundary. Two independent Agent attempts selected the same correct source-level law but emitted malformed unified diffs. Those diffs were rejected unchanged; no human repaired their hunk arithmetic. A later attempt consumed those failures and expressed the same semantic change as exact `oldText → newText` replacements. Runtime admitted each replacement only when the old bytes occurred exactly once. This preserves Agent authorship while moving line-number/hunk-count mechanics out of the model's semantic burden. It does **not** establish a generic source-edit service or require Harness to own self-modification orchestration.

The accepted source candidate also strengthens one existing authority law: caller-authored JSON object keys at Mandate and structured-completion projection boundaries must already be strings. Harness now fails closed instead of silently converting a non-string key into different valid bytes via `str(key)`. Valid legacy all-string-key objects preserve their existing canonical representation.

RSI P3 extends this with a bounded improvement-of-improvement result. The promoted P2 system was not handed a source defect and patch: a target-discovery Agent received the durable P2 receipt plus current source evidence, rejected weak or unreachable candidates, selected the delegated sha256-digest validation gap itself, and authored the falsifier used for baseline admission. A malformed first falsifier did not count as a red baseline merely because it exited non-zero; the experiment distinguished action failure from invariant falsification and introduced static falsifier admission before evaluation.

That failure also reproduced the same stale-world-model pressure seen in ordinary Agent cognition: replaying exact malformed action or diagnostic bytes into the next model request repeatedly anchored the old invalid action even when the failure evidence said it was wrong. P3 therefore applied the existing cognition law to self-change evidence: **canonical failed-action history is not the next Working View**. Exact historical evidence remains digest-bound and recoverable, while the current model view may carry only the selected target, failure class, action digest and current repair constraint. Removing obsolete failed-action/diagnostic bytes from the active view allowed the next Agent attempt to produce an admissible falsifier without deleting the underlying history.

P3 also removed experiment-local mechanical glue. The source Agent still authored exact `oldText → newText`, but materialization used Runtime's native exact replacement authority rather than a custom patch/materializer program. Thus the improvement loop itself became smaller: P2 used separate source-generation and promotion scripts plus custom materialization; P3 used one experiment runner for target selection, source edit and promotion decision, while existing Runtime primitives handled exact mutation. None of this changes Harness ownership: target discovery policy, evaluator construction and canonical promotion triggering remain external, and no Scheduler, generic Evaluator Service, Memory/RAG system or RSI Controller is implied.

The P3 source candidate closes the delegated-digest authority gap selected by the Agent: Mandate-layer digest values must now be exactly `sha256:` followed by 64 lowercase hexadecimal characters, matching the strict digest form already used by core Contracts. The shared Mandate `_digest` boundary therefore rejects non-hex payloads consistently for Mandate consumption, execution Profiles, Strategies and compiled-attempt evidence while preserving all valid lowercase sha256 identities.

RSI P4 tests whether the Agent can compose the *discovery side* of the next improvement cycle rather than receiving a caller-prepared source view. It receives a bounded capability catalog and exact prior evidence, then chooses concrete repository observations itself. In the accepted run it selected 203 observations across path listing, text search, exact file reads, named/unit checks, exact prior-observation recall and bounded probes; 50 of 51 tracked Harness source files were read exactly. The caller did not preselect source slices or evaluator gates.

The run also establishes an asymmetric authority law for recursive improvement. Two Agent-finalized target hypotheses were mechanically rejected because their declared falsifiers exited zero: a plausible target, broad search coverage or model confidence does not earn mutation authority. But requiring the Agent to either keep observing or invent a source target is also incorrect. The initial P4 experiment contract had only `observe | finalize`, so after 203 rounds it entered a low-information search tail and finally hit a no-progress admission. A deterministic meta-falsifier captured this protocol defect. The experiment-only contract was then extended with a bounded `abstain` result that means only **no causal baseline-red target was demonstrated under the observed evidence**. It does not mean Harness is defect-free.

With that outcome available, the Agent immediately abstained on round 204. Because no target survived admission, source generation, materialization, candidate evaluation, source-promotion decision and canonical Git source promotion were intentionally not invoked. This is a stronger authority separation than fabricating a candidate merely to exercise the pipeline. P4 therefore treats no-change as a first-class improvement-cycle outcome: **mutation requires causal red evidence; no-change requires exact provenance plus an explicit epistemic boundary.** The one-off discovery/abstention runner was deleted after its evidence digests were frozen; no RSI controller, Evaluator Service, Scheduler or public self-modification API was added. Discovery efficiency remains an open problem—the accepted semantics required near-complete source coverage—so P4 proves bounded composition/abstention authority, not efficient autonomous repository research.

RSI P5 attacks that discovery-efficiency boundary. Its first negative control intentionally optimised only observation count; the Agent immediately abstained after seeing one mechanical repository index, demonstrating that `fewest observations` is not a valid objective because it rewards ignorance. The corrected experiment instead adds one exact independent external failure observation as world evidence while leaving source targeting, observation choice and evaluator design unselected. The Agent then chooses the next repository observation according to decision value rather than coverage.

The accepted trajectory required 8 admitted observations over 12 Agent decisions: one full mechanical repository index, one exact Host/World failure record, four exact symbol reads, one literal search and one reference search. This is 25.375× fewer observations than P4's 203. The Agent localized the reported no-Tool failure to a deliberate `HarnessAgentBridge` guard, but it did not prove that a real no-Tool control path reaches the guard with non-empty observations or Tool Call identities. It therefore abstained rather than converting adjacency into a causal source claim. A later historical P6 did prove and repair that path, a subsequent contraction reopened the current failure while removing its dedicated falsifiers, and current repair 145 now re-establishes the conclusion/control-vs-Tool-authority separation with seven permanent post-contraction regression tests without restoring generic Provider continuation machinery.

P5 also reduces the information repeatedly projected into the model. A 53,618-byte full AST repository index remains exact durable experiment history, while the model-visible map keeps only source/test addressability and symbol names. Exact rejected actions remain in the checkpoint but their malformed arguments are omitted from later Working Views; only capability, decision digest and failure class are projected. Reducing recent exact observations from three to one plus compacting the index lowered one previously rejected request upper bound from 92,595 to 75,592 and restored Provider dispatch without expanding the 90,000-token experiment envelope. A large nested discovery-result schema also proved mechanically fragile, so the Provider-facing structured result was reduced to one `decisionJson` string and strict semantic JSON admission moved caller-side. This mirrors the P2 exact-edit lesson: models own semantic content; infrastructure should not make them perform unnecessary mechanical encoding.

P5 is therefore a bounded R12 result about **evidence-driven high-information discovery**, not general efficiency. The accepted semantic discovery path still used 12 fresh Provider calls and 239,953 total tokens, so observation traversal became dramatically smaller while model-call/token cost remains high. That Agent discovery branch authorized no source change; generator, materializer, candidate evaluator, source promotion decision and canonical source promotion remained intentionally unused. A later independent release-acceptance path did find a separate causal Provider concurrency defect; its source repair has distinct provenance and is not attributed to the discovery Agent.

## Run Contract

`HarnessRunContract` binds one **attempt** to caller identity/reference, Objective and Context refs, Provider/Adapter/model identity, Tool catalog and grant digests, execution budget, completion contract, system manifest, privacy policy, deadline and correlation links. The Contract digest is execution authority for that attempt: a Run may not silently execute against different values. When compiled from a Mandate, its system manifest binds the Mandate, selected profile, Strategy, attempt index, and adopted prior Context evidence.

Harness does not synthesize a higher-level Task from CLI flags. The caller authors the Contract; the CLI only supplies Run-local input messages.

## Persistence and continuity

The independent Store is the only current Harness writer. It owns:

- Run creation, caller binding and terminal projection;
- immutable CAS objects and contiguous Run events;
- leases and revision fencing;
- Provider Call claim, dispatch, completion, failure and UNKNOWN state, with exact request/result content only when authorized;
- Tool-step intent, dispatch fence and receipt chains, plus exact Tool observations only when authorized;
- privacy-projected pause/resume snapshots;
- recovery assessments;
- privacy-projected Trace and terminal Run evidence, with exact conclusion/CompletionProposal content only when authorized.

There is no Host-backed Store, Assignment writer, dual write or cutover selector.

### Privacy authority inside continuity

The Run Contract privacy policy is execution authority, not a diagnostic preference. Default `metadata-only` continuity retains identities, digests, causal/effect receipts and budgets while omitting exact model/Tool content from Harness-managed durable objects. `bounded-private-content` may separately authorize model and Tool content; mixed objects use the stricter applicable authority so Tool calls, Tool-role messages and Tool observations cannot become a model-content persistence bypass.

Privacy does not weaken effect fencing. A digest-only completed Provider Call still prevents physical redispatch after response loss. If exact result/transcript/Tool content was not authorized for retention, recovery fails closed and requires caller-authorized rehydration rather than reconstructing content from another hidden Harness copy.

These are structural content laws, not semantic taint tracking: ordinary model text can semantically repeat Tool-derived information, and Harness does not currently prove otherwise.

Store integrity checks are backend-specific: the supported PostgreSQL Store validates its configured schema and verifies the digest and canonical content of persisted CAS objects when read; SQLite `PRAGMA quick_check` belongs only to the separately reachable legacy SQLite Store, not the PostgreSQL CLI. Ordinary Store admission does **not** replay every unrelated Run. Opening a Run continuity boundary validates that Run's complete semantic history before execution; explicit full Doctor remains the authority-wide history replay. This keeps fail-closed semantics local to the Run being executed instead of making every worker pay an all-Runs startup cost.

Durable event and request identities remain deterministic for idempotent replay. Execution ownership does not: Continuity Stores, Agent Bridges, and terminal recorders use process-instance owner identities for leases and Provider claims so two workers cannot consume one durable dispatch admission as two physical executions.

## Model-visible Working View

The mature `OrdivonAgentLoop` no longer requires the Provider request to be identical to the complete canonical Run-local message history. An optional internal `WorkingViewProjector` seam may supply the exact model-visible messages for each Provider turn while the Loop continues to retain canonical execution history for progress accounting, recovery and Tool correlation.

The current `WorkingSetViewProjector` is deliberately narrow: it loads the current **committed** `HarnessWorkingSetSpec` and deterministically compiles its pinned exact sources into one `HarnessWorkingView`. It performs no Context discovery, ranking, RAG, Memory, summarization or automatic source selection.

Discovery and selection are separate authorities. A domain, World integration or Runtime Tool may discover raw paths, URLs, records or already-materialized source identities. Harness does not interpret those results as relevant Context. Raw content must first cross the Run's privacy-aware source-materialization boundary before it can become an exact `HarnessWorkingSetPin`; the resulting CAS object identity, not a caller-guessed semantic digest, is the pin authority.

The model-visible suffix now has two explicit non-WorkingSet authorities. **Caller interaction ingress** consists only of exact plain `user` messages appended on resume after the latest `needs_input` Snapshot; it is caller-owned model cognition, not Agent-selected durable Context. It remains visible across Agent WorkingSet transitions during that interaction and is consumed when the next `needs_input` Snapshot becomes the new interaction boundary. **Transient Tool evidence** remains attempt-local cognition: the exact Provider-authored assistant message containing `toolCalls` followed by the exact bound Tool Observation messages. Journal sequence orders Tool exchanges before and after the caller boundary, so recovery can reconstruct `pre-caller Tool exchange → caller ingress → post-caller Tool exchange` without inventing chronology. The committed Working View remains the exact prefix. Unbound user text, `system`/`assistant`/Tool-shaped caller injection, isolated Tool observations and replacement projections are rejected before physical Provider dispatch. Continuity Doctor independently recomputes the permitted suffix from Snapshot/RunState, WorkingSet, Provider and Tool evidence.

A projected Run may also grant an **Agent-owned caller-ingress promotion** cognition action. The Agent does not restate hidden WorkingSet pins and cannot provide or rewrite source bytes. It names only a new successor slot, a new attempt identity, and exact indexes into the caller ingress that the Provider request explicitly marked as promotable. Harness then mechanically derives those exact caller bytes from durable Snapshot/RunState and Provider evidence, materializes one deterministic `HarnessWorkingViewSource`, and atomically extends the current selected WorkingSet with the new pin. Existing selected pins are preserved mechanically; choosing which caller indexes deserve persistence remains an Agent decision. Promotion is cognition state, not a Runtime Tool effect, and consumes no external Tool-call budget.

Promotion provenance is visible rather than hidden. `AgentTurnRequest` may carry exact caller-ingress references mapping the interaction-local caller index to the corresponding Provider-request message position. Provider adapters can project those references as Harness execution-control metadata. DeepSeek exposes `promote_caller_ingress` only while at least one exact caller index is currently promotable, and constrains its schema to those indexes; once none remain, the cognition capability is withdrawn from the Provider surface. This is capability truth, not a Harness judgment about whether the caller fact is semantically worth keeping.

Caller and durable authority remain separate even after promotion. While the promoted source remains in the current WorkingSet, the exact promoted caller indexes are suppressed only from the caller-overlay projection so the model does not receive duplicate bytes. This is provenance-aware suppression, not text deduplication: if the Agent later drops that promoted pin during the same interaction, the still-valid caller ingress reappears. The next `needs_input` Snapshot ends the caller authority either way; a promoted source survives because its WorkingSet pin, not the old interaction overlay, now owns its durable cognition. Re-promoting an index that is already durable in the current WorkingSet is rejected.

An execution may explicitly grant an Agent-owned cognition transition surface. In that mode, one Provider turn can return an `AgentWorkingSetTransitionProposal` containing exact successor pins plus a bounded basis. This is a third Agent action category beside external Tool calls and a Run conclusion; it is not charged to the Tool budget and it cannot be mixed with either action in the same normalized turn. DeepSeek may encode the proposal as a function call on the wire, but the Adapter normalizes it as cognition state rather than an `AgentToolCall`.

A transition-capable projected turn may also carry **current WorkingSet addressability**. The projector mechanically aligns every current exact pin with the half-open message range `[start,end)` produced by that source in the effective request prefix. `AgentTurnRequest.workingSetRefs` retains this internal provenance, and DeepSeek exposes it as `workingSetSelection` execution-control metadata only when the WorkingSet-transition surface is granted. This is not new task evidence and does not rank or interpret sources: it makes the durable cognition the Agent is already seeing exactly addressable, so retain/drop decisions can use existing `propose_working_set_transition` without guessing hidden logical references, generations, slots or digests. Continuity recomputes the pin/range mapping from the current committed WorkingSet and exact source objects before Provider dispatch; forged identities or message ranges fail closed.

Durable correction therefore requires no separate supersession or memory-update primitive. If caller interaction supplies a correction, the Agent may first use caller-ingress promotion to materialize the exact corrected bytes, then use the ordinary WorkingSet transition to omit the stale pin while retaining the task and corrected pins. The stale source leaves **current cognition** but remains an earlier committed WorkingSet fact and may still be inspected or recalled through the existing historical-cognition boundary. Harness does not infer that a newer-looking statement supersedes an older one; semantic correction ownership remains with the Agent.

Continuity applies one accepted proposal as an atomic `replan → select exact pins → commit` Journal transaction under one Run lease. Provider-authored transitions bind two different facts: `sourceWorkingSetDigest` identifies the durable selected Context that remained current, while `sourceModelViewDigest` identifies the exact effective view the Agent actually saw, including admitted caller interaction ingress and transient Tool exchanges. The exact retained Provider request/result prove that the proposal came from that model view. Competing proposals have one winner, exact replay is idempotent, and Continuity Doctor verifies the proposal/source/Provider evidence rather than trusting a mechanically valid WorkingSet chain alone. Base-only direct transition receipts remain readable under the earlier single-view evidence form.

Transient Tool exchanges are **attempt-local cognition**, not durable selected knowledge. When exact model and Tool content are authorized, any fresh-process resume reconstructs the current attempt's complete Provider-authored Tool exchanges from Journal/CAS authority: the current committed WorkingSet event defines the attempt boundary, later completed Provider Tool turns identify the assistant `toolCalls` messages, terminal Tool intent/receipt/Observation evidence proves physical observations, and an active effect is reconciled without redispatch before any still-pending calls execute. This applies to both hard recovery and an ordinary clean pause/resume. When a successor WorkingSet commits, all predecessor-attempt transient exchanges disappear automatically.

Durable cognition still needs no generic Memory subsystem. For an already-materialized source, promotion remains ordinary Agent WorkingSet selection: the source becomes durable current cognition only when the Agent explicitly includes its exact pin in a successor committed WorkingSet. Caller ingress is a narrower special case because no exact source pin exists yet. Its promotion action therefore combines two mechanical steps—materialize the exact Agent-selected caller bytes, then add the resulting pin to the current selection—under one provenance-bound transaction. In both cases Harness does not decide which facts deserve persistence, synthesize memories, summarize caller text, rank retained sources or inject materialized-but-unselected objects into future model views. `source bytes exist`, `source is current cognition`, `source remains selected later`, and `caller bytes were interaction cognition` remain different facts.

Historical recall is the inverse mechanical boundary, not a semantic Memory search. An execution may explicitly grant `inspect_working_set_history`, which returns a bounded reverse-chronological catalog of **earlier committed WorkingSet identities and exact pins only**. Materialized-but-never-selected CAS objects are absent; historical source content, semantic similarity, relevance scores and automatic source injection are absent. The Agent decides when to inspect the catalog and may use the existing WorkingSet transition control to re-select an exact historical pin. History inspection performs no Runtime dispatch and consumes no external Tool-call budget, but its Provider-faithful function result is bounded by observation bytes and participates in observation/no-progress accounting. Continuity recomputes the result from Journal history relative to the exact WorkingSet that authored the Provider turn, so a forged local history reader cannot authorize invented recall evidence. Exact clean-pause replay of the function-call/result transcript still requires both model- and Tool-content authority because the Provider wire uses a structural Tool channel.

Execution control is distinct from task Context. The exact **per-turn action authority** is now request-bound: `AgentTurnRequest.tools` contains the Runtime/World Tool actions currently admitted for that turn, while provider-neutral `AgentTurnRequest.capabilities` contains the Harness-native actions currently admitted (`submit_run_conclusion`, WorkingSet transition, caller-ingress promotion and bounded WorkingSet-history inspection). Installed mechanisms are not themselves current capability. The Loop derives this action surface from the mechanisms actually wired for the Run plus dynamic turn facts such as current caller-ingress addressability and external-observation gates; the resulting request participates in `dispatchDigest`, Provider claim identity and optional retained request evidence. A Provider adapter may render this exact action authority, but it cannot independently add or remove Harness actions through adapter-local feature flags.

For DeepSeek, the Harness-authored system control envelope names the exact `harnessActions`, Runtime Tools and remaining bounded budget admitted by that `AgentTurnRequest`, plus the exact caller message indexes/Provider positions still eligible for promotion and exact selected durable pins/ranges when the corresponding request-bound capability is present. Caller promotion is true only while at least one exact promotable caller reference exists; after promotion suppresses that ingress from the interaction overlay, the next turn carries promotion=false even though the Run still has a promotion mechanism installed. Capabilities that are no longer executable are therefore absent from both the exact request truth and the Provider surface. The transition control still states that reselecting identical pins is an intentional cognition-attempt reset rather than progress or a substitute for a `needs_input` conclusion.

No-progress and observation-only limits are effect gates, not epistemic verdicts. Their durable authority is the retained progress counters; the process-local gate reason is only a projection and is recomputed after fresh-process resume. Reaching one closes new external observation capability and gives the Agent a subsequent cognition/closure turn over the evidence it has already seen. A successor WorkingSet attempt may still be legal with exactly the same pins because attempt identity owns transient cognition lifetime: such an attempt reset discards predecessor Tool exchanges but is **not** structural progress, does not reset the counters, and does not reopen a closed soft effect gate. A transition whose exact selected pins change is a structural cognition mutation and may reset the soft progress counters/gate. A newly admitted caller interaction ingress is also genuine progress because those exact caller bytes now enter the effective model view; it may reset the soft counters without changing Agent-owned WorkingSet selection. Hard Tool-call budget remains global and cannot be revived by either cognition
transition or caller ingress. A Provider that still refers to a now-unavailable
historical Runtime Tool receives a bounded local, model-correctable rejection with
`physicalDispatch=false`; this consumes the Tool-correction budget but cannot
exceed the external Tool budget. Caller/domain rejection of a Run conclusion is a
separate mechanic: it consumes `maxConclusionCorrections`, not
`maxToolCorrections`, and Harness forwards the owner rejection reason without
assuming that evidence is missing. Harness therefore bounds effects while the Agent
still owns whether to conclude `candidate_completed`, report concrete
`needs_input`, or perform an admitted cognition transition. A Harness-owned
`no_progress` execution stop is not an Agent semantic conclusion: its reason
remains in Run stop detail/Trace and Harness does not synthesize an
`AgentRunConclusion` for that disposition.

The cognition mechanisms now have one **experimental product composition proof** in `StandaloneHarnessRunner`. A `HarnessCognitionProfile` selects which already-proven cognition mechanisms are wired for the Run, and the Runner constructs the `WorkingSetViewProjector` plus exact Continuity handlers mechanically rather than requiring an application to hand-wire four seams. `HarnessCognitionSeed` is an explicit caller-authored bootstrap only: it contains exact slot/source pairs and a basis, which the Runner materializes and commits through the existing WorkingSet authority. It performs no discovery, ranking, summarization or memory extraction. Re-entry after a response loss between the initial and committed WorkingSet records is idempotent against the exact seed.

`HarnessCognitionProfile` now means only **installed cognition mechanisms**. It is deliberately not Provider capability truth. Each concrete turn derives one `AgentTurnCapabilities` value from the mechanisms actually wired plus current addressable authority, and DeepSeek no longer has independent cognition feature booleans. History composition still requires the privacy/Tool-channel authority already established by P-C1.8; capability truth describes what is admitted now, not permission to violate the Run Contract's content authority.

R2 begins physical recomposition only where R0/R1 exposed a proven seam. `AgentTurnProjector` now owns read-side construction of the exact Agent-visible turn: current WorkingView projection, caller-ingress addressability, attempt-local pre/caller/post overlay ordering, stale predecessor-attempt Tool-exchange withdrawal, Runtime Tool surface inclusion and request-bound Harness capabilities. `CognitionAdmissionKernel` owns only the common structural admission law for Agent-authored durable cognition mutations: reload the current WorkingSet, require the exact source digest to remain current, then invoke the action-specific promotion or transition handler. Promotion and ordinary transition remain distinct actions; their progress/evidence semantics stay in the Run coordinator.

This extraction deliberately preserves **construction ≠ verification**. `AgentTurnProjector` constructs a request from the read-side authorities available to the Loop, while `EventSourcedRunContinuity` continues to reconstruct the permitted WorkingView prefix, caller provenance, Tool exchange chronology and exact current pin ranges independently from Journal/CAS before Provider admission. R2 therefore does not DRY those two algorithms into one shared authority.

A third seam is now proven by Provider response-loss/retry/UNKNOWN friction. `ProviderCallLifecycle` freezes the optional durable Provider-continuity surface at Loop composition time, validates exact `provider_request_digest` identity for durable calls, and normalizes bridge `begin/admit/fail/retry/complete` addressing. It deliberately does **not** own retry/backoff policy, Run stop codes, token accounting, model-result semantics or physical Provider transport; those remain in the Loop/Adapter, while durable Provider truth remains in Continuity. Current source and tests contain no supported dynamic replacement of these hooks after Loop construction, so repeated per-turn `getattr` discovery is not an authority requirement.

Across the complete current R2 lineage, `_run()` falls from 2,083 lines before kernel extraction to 1,876 after the three proven seams; the Provider-lifecycle extraction alone reduces the current no-progress/two-kernel coordinator from 1,974 to 1,876. The remaining Tool-effect coordination and progress/control code stays in the sequential Run coordinator until an equivalent real friction case demonstrates a stronger boundary. Large function size alone remains insufficient evidence for extraction. No SQLite schema, generic Memory/Capability service or public API is added.

R3 promotes a supported caller-facing Agent Run surface without promoting the R2 kernels themselves. `HarnessAgentRun` owns only mechanical product composition: state-root Store opening, exact Continuity reconstruction, Contract-budget reconstruction, selection of the built-in no-Tool versus independently bound Runtime-search bridge from exact Contract digests, and Snapshot-bound Provider-source rebinding on resume. It receives a caller-supplied Adapter factory and invokes that factory only after structural composition is admissible; therefore Harness can bind the exact persisted Contract without choosing a Provider or constructing one for an invalid surface. Runtime Tool execution still requires caller-supplied `HarnessExecutionBinding` and `HarnessRuntimeClient`; workspace identity, runtime-binding digest and foreign references are not inferred.

R3.2 strengthens `HarnessAgentRun.create()` into the supported surface's **static composition admission boundary**. Every impossibility provable from the exact Contract plus caller-supplied composition inputs is rejected before durable Run creation. Cognition privacy/history authority and exact independent Runtime-binding identity are checked before the Adapter factory is called; Adapter/model and structured-completion binding are checked immediately after the caller-owned factory returns and still before state creation. This is intentionally not Provider or Runtime liveness probing: availability, physical effects and semantic correctness remain outside static admission. Lower layers keep their own validation as defense-in-depth rather than becoming the caller-facing product boundary.

Caller-facing `HarnessCognitionProfile`, `HarnessCognitionSeed`, `HarnessCognitionSeedSource` and canonical `HarnessWorkingViewSource` are part of the supported surface because exact initial cognition selection is caller authority. The former `HarnessCognitionSource` name was only an alias of `HarnessWorkingViewSource` and is retired; current callers use the canonical type directly. `AgentTurnProjector`, `CognitionAdmissionKernel` and `ProviderCallLifecycle` remain internal kernels and are not promoted. Harness still has no generic Capability Service, CandidateSet, Context Service, Memory service or semantic search/relevance policy.

## Provider lifecycle

A Provider Call is durable before uncertain physical delivery. Live claims exclude competing holders; response loss is reconciled from retained Provider state rather than treated as permission to redispatch. Dispatching with no safe proof of outcome becomes UNKNOWN. Retry is admitted only when the retained failure semantics prove redispatch safe and budget remains.

P5 release acceptance adds one narrower post-dispatch law. Once an execution has durably advanced the exact Provider Call to `DISPATCHING` and owns the physical Provider outcome, a competing replay that can already see that same `DISPATCHING` record must not take the generic Run lease merely to discover that redispatch is forbidden. If short mechanical Run-lease contention still exists when the physical result returns, the exact outcome owner may wait for at most one second in bounded local-monotonic intervals, but only while the durable Provider Call record remains byte-identical/current. A changed record fails as superseded; exhausted waiting becomes explicit Provider recovery. This is bounded known-outcome commit authority, not a generic lock-retry policy.

Provider identity belongs to Harness execution. A higher-level caller does not need to model Provider sessions or retry state.

DeepSeek physical egress may be supplied by an external workstation transport without turning Harness into a network router. The cancellable pinned-HTTPX transport keeps exact Harness-built request bytes, one physical request, undecoded bounded response bytes and Harness-owned failure interpretation while delegating HTTP/TLS mechanics to an async task. It disables inherited environment routing, redirects and HTTP/2. When no HTTPS proxy is projected the request goes directly to the target. If `HTTPS_PROXY`/`https_proxy` is present, Harness accepts only one unauthenticated `http://127.0.0.1:<port>` CONNECT endpoint; HTTPX tunnels the fixed official DeepSeek HTTPS origin and performs TLS end-to-end to DeepSeek. Remote proxies, proxy credentials, non-loopback hosts, conflicting proxy variables and proxy URL paths fail before Provider dispatch. The physical transport is deliberately not part of Provider request identity: changing a safe pre-dispatch route is analogous to changing an IP path, while an ambiguous Provider delivery remains fenced by the existing Provider Call lifecycle and is never permission for automatic mid-call migration.

A Provider turn that simultaneously requests ordinary Tools and submits a Run conclusion is treated as a **model-correctable action conflict**, not as permission to choose on the model's behalf and not as a Harness failure. Harness dispatches none of those ordinary Tools and admits no conclusion from that mixed turn; the next model turn must choose whether to continue acting or conclude.

## Tool lifecycle

### Current consumer-critical path and owner boundaries

The source-owned, default no-Tool CLI remains intact. A caller who explicitly
selects Gateway execution can first inspect the original MCP Tool schemas
with `gateway-profile` **without creating a Run or opening PostgreSQL**.
The returned catalog/grant digests must match the caller's immutable
`HarnessRunContract` before dispatch.

| Logical LEGO | Current capability | Physical/semantic truth owner |
| --- | --- | --- |
| L1 Run admission | `core_contracts.py`, `agent_run.py`, `independent_cli.py` | Harness PostgreSQL Run |
| L2–L4 cognition, loop, Provider | `working_view.py`, `ordivon/loop.py`, `ordivon/deepseek.py` | Harness for Run/Provider only |
| L5 effect proposal and fence | `plugin_gateway_effect.py`, `ordivon/runtime_bridge.py` | Harness Intent; Runtime admission is separate |
| L6/L8 journal and uncertainty | `postgres_store.py`, `ordivon/run_continuity.py` | One existing Harness PG writer; UNKNOWN is not safe retry |
| L7 physical observations | Gateway MCP `execution.get`, `artifact.read` and native Runtime Artifact | Runtime/Gateway owner receipts; byte-bounded model projection |
| L9 task success | original independent `evals/harness-edit-addressing-002/qa.py` and domain callers | Domain verifier, not model `candidate_completed` |

A native process exit code, a committed Tool Receipt, and a model's
`candidate_completed` are insufficient on their own to prove a coding TaskSolved.
The domain-hidden verifier remains outside the model-visible Workspace.

**R45 source-only continuity boundary:** if and only if the original ToolStep
has a durable UNKNOWN Receipt and `effect-dispatch-pending` Pause, a fresh
`resume` can reconcile that exact Owner operation and continue the same Run.
The original Tool intent and dispatched physical operation must not be
resubmitted. Other `runtime_unknown` outcomes remain stopped. This source
PG18 regression is not a certificate of production-installed Gateway/Runtime
behavior or a guarantee of domain TaskSolved. Rust native `DurableJournal`
production binding and issuer-current physical spawn remain independent
qualifications; do not build a second Journal or Tool execution engine.
Tool-bearing Runs bind a complete Tool catalog digest and Tool grant digest. Before physical delivery, Harness records a Tool intent and dispatch fence. Runtime requests carry Harness authority references. Observation-only failures can be corrected by the Agent; ambiguous external effects require reconciliation and may terminate recovery as UNKNOWN.

The primary CLI defaults to the canonical no-Tool DeepSeek profile. The opt-in `gateway-profile`/Gateway Run path consumes a caller-selected authenticated MCP endpoint, existing Workspace, explicit executable grant and the original PostgreSQL Journal; it does not discover or mint Runtime authority. Other Tool-bearing applications continue to use `ordivon_harness.api` with an application-supplied `HarnessRuntimeClient`.

### R8 cross-database Workspace consumer lifetime (open production gap)

**Observed on 2026-11-16, not yet a deployed fix.** An independent Runtime
consumer reproduced a Harness PostgreSQL Run paused for `needs_input` with a
frozen Gateway Tool grant pointing to a native Git Workspace. Even with zero
Tool calls and no active Runtime Job, a non-force native Workspace close with
`consumerReleased=true` removed that Workspace. The original Harness Run still
reopened as `PAUSED`, but its frozen physical Workspace no longer existed.
The disposable reproduction is recorded as Runtime Job
`job-01a1e41a-ca97-775b-ab8d-48c231b6455a` and Host #28453.
This is a confirmed physical *counterexample*, not proof that production
customer source was lost. Runtime's caller release assertion is not the
Harness Run's authenticated consumer release certificate.

The minimal **target contract** below is accepted for R8 architecture review;
it is not a claim that the current Runtime or installed Harness enforces it:

| Phase | Owner and required fact | Can the original Workspace be closed? |
| --- | --- | --- |
| PROVISIONAL | Harness PG creates/opens an immutable Run and frozen grant without claiming physical Workspace readiness | Not proven safe by Harness status alone |
| HELD | A trusted Harness issuer binds the Run, frozen grant epoch and stable native Workspace incarnation; Runtime PG commits a per-Run consumer claim under its own native-close admission fence and certifies exact-key readback | No while any matching native claim remains held |
| ACTIVE or PAUSED | A Workspace-backed Run obtains HELD **before its first model turn that can pause**, and the physical submission path checks the current native grant/claim epoch again | No; PAUSED is not terminal |
| SEALED | Original Harness PG authority forbids new Tool intents; Provider/Tool UNKNOWN effects are reconciled; the Run is terminal or has an explicit safe successor; Git/Artifact/domain delivery is attested by its natural consumer | Not yet, until the per-Run native release commits |
| RELEASED | A trusted issuer submits a source-qualified finalizer for the exact claim and epoch; Runtime PG verifies the claim release under the same native lock, and each other Run sharing the Workspace releases separately | Only after every native Job, Git/source and external consumer qualification permits native close |

**Identity and concurrency.** A native Workspace incarnation is immutable
over ordinary source editing; mutable `sourceStateDigest` belongs to the
*current* Workspace-close source CAS and must not invalidate a long-lived
claim after a legitimate Agent edit. Harness and Runtime PostgreSQL schemas
may live in different databases: identical advisory-lock integers across
different databases do **not** protect one shared physical Workspace.
Short native Runtime PG transactions fence claim reserve, actual effect
admission and close; a persistent HELD claim protects long user waits without
holding a database transaction open. Lost reserve/release responses require
same-key native readback; UNKNOWN must not be interpreted as permission to
submit another effect or release a claim.

**Effect paths and exceptions.** The existing `HarnessAgentRun.run/resume`
composition and both `PluginGatewayExecutionBridgeFactory` /
`GatewayMcpRuntimeAdapter._submit` and built-in `HarnessRuntimeBridge`
must consume one thin authenticated Workspace-eligibility contract.
A custom Tool bridge needs it only if it truly uses a Runtime-owned
Workspace. No-Tool Runs and tools unrelated to Runtime Workspaces require no
such claim. An old PAUSED Run that predates the claim contract must be
inspected and explicitly repaired or superseded; neither a new Workspace
with the same display name nor a bare Harness PG Run status authorizes
silent physical recovery.

**Other outstanding risk.** The already demonstrated revocation window
between a Runtime job's admission and physical OS spawn is an *independent*
issuer-currentness problem. A successful Workspace claim alone does not
prove that a revoked high-risk effect cannot start. Native effect startup,
issuer credentials and risk-tiered revocation semantics belong to Runtime
and Gateway natural owners; Harness does not create a second executor,
credential authority, queue or distributed transaction coordinator.

The existing Harness PostgreSQL Journal, `ToolStep` Intent/Receipt,
`runtime_port.py` and owner-native Runtime Claim prototype remain the
preferred composition points. Actual acceptance must reproduce the failing
cross-PG native close, then prove its safe rejection, safe legal release,
multi-Run sharing, editing during HELD, and independent domain TaskSolved.
See `docs/VERIFICATION.md` and `docs/OPERATIONS.md`.

### Run authority as a separate module (source candidate, R22)

The file-by-file audit separates **permission decisions** from **business work**.
This is a source boundary; merged code and physical installation are different
facts. It does not introduce a new permission registry, owner approval chain,
shared transaction across Harness/Runtime databases, or replacement MCP API.

| Actual file | Sole responsibility after extraction | Forbidden responsibility |
| --- | --- | --- |
| `src/ordivon_harness/run_authority.py` | Validate Run composition, caller Tool grant/executable/env/timeout, exact Workspace selection, immutable Gateway effect sources, current Runtime issuer Port and post-delivery release prerequisites | Execute physical Jobs, persist a second Run/Claim registry, infer user/domain success from Job completion |
| `src/ordivon_harness/agent_run.py` | Run creation/reopen, PG Journal/Continuity, turn scheduling, reporting output; call authority decisions, not implement them | Invent policy/identity booleans, infer native HELD from an active Run |
| `src/ordivon_harness/workspace_claim.py` | Idempotent native Runtime `workspace.claim.reserve/get/release` using one original Run/contract request key, physical HELD readback, lost-response reconciliation | Decide permissions or grant Tool invocation based on a claim alone |
| `src/ordivon_harness/plugin_gateway_effect.py` | Gateway execution lowering/dispatch/resolve/receipt, consume the authority decision before first send and original-effect replay | Reimplement allowlist or issuer checks in each execution branch |
| `src/ordivon_harness/runtime_port.py` | Existing structural Protocols, typed Runtime errors | Duplicate a physical Runtime Claim backend |
| `src/ordivon_harness/execution_binding.py` | Immutable Run/Workspace/foreign reference identities and request ID construction | Authorize effects or own their physical state |
| `src/ordivon_harness/mcp_http_client.py` | Existing authenticated SDK transport and private bearer-file validation | Choose Run lifecycle or domain delivery |
| `src/ordivon_harness/cli.py` and `independent_cli.py` | Compose configured Gateway/native clients and Run commands; no silent unprotected fallback for Workspace Run | Interpret transport identity as Runtime issuer privilege |

No-Tool Runs and custom Tools without a Runtime Workspace do **not** pay a
native Claim requirement. Any workspace-bearing original Run must receive
native HELD readback before its handle can run; a lost Runtime reserve response
is reconciled with the exact same request key. `CREATED` in Harness PG after
native timeout is not an executable Run. A terminal Run must not trigger
automatic physical release: verified recipient delivery and native drain are
separate inputs, and actual Runtime close still applies its own source/Job
checks. Dedicated high-risk NoFutureSpawn guarantees remain unqualified until
native OS/issuer owner evidence exists. The file-level test double only proves
policy wiring; native physical close acceptance requires a separate real Runtime
PG/Git/Job test and installed readback.

## Pause, resume and recovery

Pause snapshots retain Provider source identity plus the Run state content or content digests authorized by the Contract. Exact-content resume starts from an authorized snapshot and may append caller messages. In the non-projected path those messages remain part of the canonical Provider-visible transcript. In a projected WorkingView Run, plain caller `user` messages following a `needs_input` Snapshot are now a separate caller-owned cognition ingress: they are projected after any current-attempt Tool exchanges that happened before that pause, survive WorkingSet transitions, precede Tool exchanges produced after the caller reply, and expire when the next `needs_input` Snapshot starts a new interaction. Their exact bytes are recovered from the authorized Snapshot/RunState continuation and revalidated before Provider dispatch; a forged bridge cannot invent them. Because this is model content rather than a Tool channel, exact caller ingress requires model-content authority but not Tool-content authority. Digest-only recovery remains conservative and cannot reconstruct omitted caller bytes.

## Completion

Harness can conclude that an Agent Run produced a candidate-completed result and can record a `CompletionProposal`. That is not the same as caller/domain completion. Final verification and commitment remain outside Harness.

### R8 Domain QA, durable delivery and finalization are different facts

A real Coding Run can pass independent hidden QA and still leave its
edited candidate inaccessible to its intended user. The historical R4
HARNESS-EDIT-ADDRESSING-002 evidence supports `DomainQA_PASS`, but the
task required no delivered artifacts, its merged test/evidence PR did not
contain the model-edited candidate, and its ephemeral native Workspace
is now closed. The strongest supported delivery status is therefore
`DELIVERY_TO_CONSUMER_UNVERIFIED`; permanent loss has not been proven.
New Coding task acceptance requires the exact output Git commit/patch
or Runtime Artifact to be durable and byte-read-back by the downstream
consumer before releasing its Workspace claim.

Run terminality is also insufficient as a certified-release condition:
`STOPPED` is terminal under source semantics even for certain UNKNOWN
reasons, and only the latest Tool event may appear in a current-head
projection. A finalizer must review the original PostgreSQL ordered Run
event chain for *every* Provider/Tool effect, verify no unresolved
UNKNOWN/Prepared effects, and pair that source fact with independent
Git/Artifact/domain delivery evidence. Never infer safe release from
`terminal=true`, latest Tool head or native Job exit code alone.

## Integration boundary

Higher-level orchestrators integrate through the caller-neutral Harness Python API or CLI. The package no longer ships a Host-specific external-executor adapter; orchestration lifecycle remains outside Harness while Harness retains its own execution, snapshot, Provider, Tool, trace, and terminal evidence.

## Removed pre-H3 architecture

H3 intentionally removed the former `HarnessHost`, Host Assignment/TaskContract model, `HostHarnessRunStore`, Host CLI namespace, cutover machinery, Host dependency extra, and Host-coupled Codex/Hermes drivers. Historical evidence may describe those experiments, but current source does not decode or advertise them.
