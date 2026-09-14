# Harness Port Composition Execution R1

Date: 2026-09-14  
Status: **REGISTERED / EXECUTION PLAN**

## Decision

Ordivon retains **Host, Harness and Runtime** as the three semantic cores. Harness is not replaced by one external agent framework. It becomes a small durable semantic core surrounded by replaceable capability/provider implementations.

The operating pattern is learned from n8n without cloning n8n:

```text
stable execution/authority semantics
        +
replaceable provider descriptions/adapters
        +
composition-time registration
        +
exact per-execution authority snapshot
```

For Harness this means:

```text
Harness Core
  Run identity / Journal / cognition / authority / effect continuity / recovery / completion
        |
        +-- stable ports
        |
        +-- provider implementations selected per composition
```

No OMP/Codex/OpenHands/Claude implementation becomes a new semantic owner.

## The n8n lesson translated precisely

n8n succeeds because a node implementation can change while the engine keeps stable notions of node description, credential binding, workflow execution and execution result. Harness needs the same separation:

| n8n concept | Harness translation |
| --- | --- |
| node description | capability/action descriptor |
| node implementation | provider adapter |
| credential | owner/provider authority binding |
| workflow | bounded ToolProgram / external orchestrator composition |
| workflow execution | Harness Run |
| node result | Tool/Provider observation |
| execution history | Harness Journal |
| subworkflow | Child Harness Run |
| binary/resource object | ResourceRef / Artifact reference |
| external target truth | Runtime / provider / World truth |

The translation stops here. Harness does **not** become a workflow engine, credential database, integration marketplace, scheduler or global event platform.

## Non-negotiable laws

The refactor must preserve:

```text
History != Cognition
Observation != Retention
Installed capability != Run authority != Turn authority
Tool intent != Physical effect
Physical effect != Semantic success
Exact replay != Redispatch
Run terminality != Host/Domain completion
```

No provider port may weaken these inequalities.

## Important negative constraint: no resurrected global Capability Service

Current Harness correctly retired generic capability discovery/ranking/catalog ontologies after they had no independent authority/consumer.

Therefore R1 uses:

```text
composition-time provider registry (ephemeral)
        -> exact selected descriptors/grants
        -> frozen Run authority
        -> exact turn surface
```

The registry is not durable semantic truth, does not rank relevance, and does not decide authority.

Dynamic provider discovery such as MCP updates **availability** only. A new capability becomes turn-visible only when existing Run authority already permits it or a caller-authorized successor Run/binding explicitly admits it.

# Current Harness seams to retain

Current source already has useful boundaries:

- `HarnessRunContract` — immutable Run authority;
- `AgentTurnAdapter` / `AgentTurnRequest` / `AgentTurnResult` — Provider seam;
- `DomainToolBridge` — current Tool execution seam;
- `HarnessRuntimeClient` + `HarnessExecutionBinding` — Runtime seam;
- `WorkingViewProjector` — cognition projection seam;
- `HarnessToolProgram` — bounded deterministic programmatic composition;
- Journal/CAS + Provider/Tool lifecycle — continuity core.

R1 should regularize these seams instead of creating parallel abstractions.

# Target ports

These are logical ports, not a demand to create eight empty framework classes on day one.

## P1 Provider Port

Current donor: `AgentTurnAdapter`.

Stable responsibility:

```text
exact AgentTurnRequest
  -> Provider/model physical interaction
  -> normalized AgentTurnResult / typed failure
```

Must not own Tool authority, WorkingSet selection, Runtime effects or semantic completion.

First implementation remains DeepSeek; later Codex/OpenAI/Claude/etc. prove portability.

## P2 Action / Capability Provider Port

Stable responsibility:

```text
action descriptor + exact request
  -> provider-specific mechanism
  -> structured observation/proposal
```

Used for Edit, LSP, DAP, Browser, Eval, MCP-backed Tools, n8n-backed deterministic automation and similar capabilities.

Do not persist a universal Harness capability database. Provider descriptors are composition inputs.

## P3 Resource Resolver Port

Stable responsibility:

```text
ResourceRef -> bounded content/metadata projection
```

Candidate schemes:

- `workspace://`
- `artifact://`
- `agent://`
- `history://`

Possessing a reference never grants an action.

## P4 Cognition Projection Port

Current donor: `WorkingViewProjector` and turn projection.

Stable responsibility:

```text
canonical history + selected durable cognition + interaction cognition + attempt cognition + control
  -> exact model-visible turn projection
```

OMP compaction, fresh-context handoff or other strategies may be implementations. History/cognition ownership remains Harness.

## P5 Effect Executor Port

Current donors: `DomainToolBridge`, Runtime bridge.

Stable responsibility:

```text
admitted Harness action/effect intent
  -> exact provider/Runtime dispatch
  -> receipt/observation/UNKNOWN/reconciliation
```

Provider transport success never becomes domain success.

## P6 Child Run Port

Stable responsibility:

```text
ChildRunRequest
  -> independently identified Harness Run
  -> ChildYield / evidence refs
```

OMP `task` / Agent Hub are implementation donors. Child work that mutates code may bind a Runtime Workspace.

## P7 Programmatic Composition Port

Current donor: `HarnessToolProgram`.

Keep two complementary bounded forms:

- declarative short Tool dataflow: `HarnessToolProgram`;
- imperative computation/tool composition: Persistent Eval.

Do not add cron, webhooks, distributed workflow state or business process semantics. Route those to n8n/Temporal/Host as appropriate.

## P8 Interceptor Port

Experimental only. Candidate hooks:

- before turn;
- before Provider call;
- Provider stream observation;
- after Provider result;
- before action admission;
- after observation;
- before completion proposal.

TTSR and Advisor are candidate implementations. Interceptors receive no hidden authority.

# Execution sequence

## R0 — Freeze semantic baseline

Goal: prove the refactor starts from a healthy exact current Harness.

Actions:

1. run current portable deterministic suite;
2. record current public API and durable schema inventory;
3. record existing cross-repository consumers of `AgentTurnAdapter`, `DomainToolBridge`, `HarnessRuntimeClient`, `WorkingViewProjector`, `HarnessToolProgram`;
4. classify each public type as semantic core, current port, provider implementation or migration residue;
5. add characterization tests only where a real current seam lacks one.

Exit:

- no production behavior change;
- exact baseline test/evidence recorded;
- migration map names every current seam owner.

## R1 — Formalize existing ports without new capability behavior

Do the smallest extraction possible:

1. retain `AgentTurnAdapter` as Provider Port rather than renaming merely for aesthetics;
2. retain `WorkingViewProjector` as Cognition Projection Port;
3. define one common provider/action descriptor shape only where first external capability needs it;
4. define ResourceRef/resolver only when the first large deferred resource path is wired;
5. keep `HarnessRuntimeClient` as the Runtime-specific Effect Executor adapter;
6. add conformance tests that implementations cannot add turn authority absent from the exact `AgentTurnRequest`/grant.

Exit:

- existing DeepSeek/no-Tool/Runtime behavior byte- or semantically-equivalent where compatibility requires;
- no new global registry or persisted state;
- first stable-port tests pass.

## R2 — First real donor: Adaptive Edit Gateway

Use the OMP-derived Edit ABI as the first proof that the architecture is genuinely replaceable.

Implement:

```text
EditCodec
  anchored/hashline-like
  exact replacement
  conventional patch where useful
        |
        v
CanonicalEditPlan
        |
        v
Runtime workspace.patch / patch.get
```

Why first:

- historical Harness P2/P3 independently exposed malformed unified-diff failures;
- current Runtime already has strong exact Patch/reconciliation semantics;
- OMP supplies mature ACI lessons;
- it tests a provider mechanism without changing Harness Run laws.

Exit:

- same semantic edits benchmarked across at least replacement + anchored + patch;
- stale source and lost-response falsifiers pass;
- no edit codec writes files outside Runtime Patch authority.

## R3 — Programmatic composition upgrade

Keep existing `HarnessToolProgram` as declarative bounded dataflow.

Add Persistent Eval as a sibling implementation:

```text
ProgrammaticComposition
   |- ToolProgram (declarative)
   `- Eval kernel (imperative Python first)
```

All tool re-entry passes through the exact current Harness Tool admission and normal Tool effect lifecycle.

Exit:

- retained Python state across cells;
- denied Tool cannot be called from Eval;
- computation workload demonstrates lower model round trips/context than shell-loop baseline;
- no duplicate Tool authority plane.

## R4 — Resource references

Introduce the smallest Resource Resolver proven by R3/child-output pressure.

Start with existing natural authorities:

```text
workspace:// -> Runtime Workspace read projection
artifact://  -> Runtime/Harness Artifact owner
```

Add `agent://` only when Child Runs land.

Exit:

- large content stays out of model context by default;
- references retain provenance;
- resource possession grants no new action.

## R5 — Child Harness Runs

Translate OMP subagent mechanics onto existing Harness semantics:

```text
parent Run
  -> exact ChildRunRequest + explicit Tool subset
  -> child Harness Run
  -> optional isolated Runtime Workspace
  -> schema-validated ChildYield
```

Add projection/control operations only after child identity is durable:

- list/inspect;
- message/steer;
- cancel;
- wait;
- later park/revive.

Exit:

- response loss cannot duplicate spawn;
- parent restart can reattach;
- child Workspace cannot mutate parent source implicitly;
- typed yield does not require injecting entire child transcript.

## R6 — Live provider availability / MCP

Now introduce an ephemeral live availability registry because a real consumer exists.

Pipeline:

```text
provider discovery/connect
  -> available descriptors
  -> intersect immutable Run admission
  -> derive next-turn surface
```

No dynamic discovery directly modifies Run authority.

Exit:

- late MCP provider can appear without Run restart;
- unauthorized late Tool remains invisible;
- schema revisions have stable identities;
- provider disappearance preserves historical receipts.

## R7 — LSP + DAP standard providers

Adopt protocol clients; do not create Ordivon protocol clones.

LSP mutation path:

```text
LSP WorkspaceEdit
  -> Adaptive Edit Gateway
  -> exact Runtime Patch
```

DAP execution should bind Runtime-owned target processes when practical; otherwise clearly record DAP provider as physical process owner.

Exit: one real code task proves semantic navigation/refactor/debug behavior and downstream tests.

## R8 — Experimental cognition interceptors

Only after the stable ports are proven:

- TTSR-like stream intervention;
- Advisor/watchdog;
- alternative context/compaction strategies.

Every mechanism needs an ablation against baseline. Do not promote merely because OMP implements it.

# Provider package shape

Do not force one language/package format prematurely. The logical package contract should be approximately:

```text
provider identity/version
supported port/action families
input/output schemas
session scope
consequence/effect classification
health/readiness projection
configuration references
natural credential owner
optional resource resolvers
verification/conformance tests
```

Credentials stay with the natural provider where possible, following the n8n rule `capability != credential`.

# Composition API direction

Target composition should become simple enough that an application can say, conceptually:

```python
run = HarnessAgentRun.create(
    contract=contract,
    provider=openai_or_deepseek,
    cognition=working_view_projector,
    actions=[edit, lsp, runtime_tools, n8n],
    resources=[workspace_resources, artifact_resources],
    execution=runtime_effects,
)
```

The exact Python API need not use these names. The law is that composition binds implementations while the `HarnessRunContract` and per-turn request bind authority.

# Routing rules

To avoid duplicating mature systems:

```text
short deterministic Tool dataflow -> HarnessToolProgram
algorithmic in-turn computation -> Persistent Eval
SaaS/API integration workflow -> n8n
long-running durable workflow -> Temporal / mature workflow engine
business/domain work continuity and acceptance -> Host/domain owner
physical machine execution/evidence -> Runtime
uncertain Agent reasoning/action loop -> Harness
```

# Migration safety rules

1. **No big bang.** One port/donor at a time.
2. **No rename-only architecture.** Do not create replacement types unless behavior/consumer pressure proves a separate contract.
3. **Existing seams first.** Normalize `AgentTurnAdapter`, `WorkingViewProjector`, `DomainToolBridge`, `HarnessRuntimeClient` before inventing new abstractions.
4. **No second Store.** Provider/plugin registries are ephemeral unless a real state owner requires persistence.
5. **No second Tool authority.** Eval, subagents, MCP and Skills all consume existing Run/turn authority.
6. **No second Runtime.** Edit/LSP/DAP/browser adapters lower physical work to natural providers/Runtime instead of owning generic execution.
7. **No framework lock-in.** OMP/Codex/OpenHands/Claude/Aider mechanisms enter through ports and remain removable.
8. **A/B or conformance proof before cutover.** Keep old path until replacement passes the same current workload.
9. **Delete obsolete path after proof.** Do not keep two long-lived mechanisms “just in case.”

# First implementation slice

The next concrete engineering slice should be **R0 + R2 preparation**, not all ports at once:

1. freeze current Harness baseline;
2. make a current seam/consumer inventory;
3. define an internal `EditCodec -> CanonicalEditPlan` contract;
4. implement exact-replace codec using the already-proven path;
5. implement anchored/hashline-like codec;
6. lower both to current Runtime Patch;
7. add protocol-selection benchmark fixtures;
8. run stale-source, ambiguity and response-loss falsifiers;
9. only then decide whether the generic Action/Capability Provider descriptor earned promotion into supported API.

This sequence deliberately lets a real donor implementation *earn* the generic port instead of creating an abstract plugin system first.

## Acceptance

R1 architecture passes only if all are true:

- current Harness semantic laws remain unchanged;
- one mature donor mechanism can be replaced without editing the Run state machine;
- provider availability and authority remain distinct;
- Runtime remains physical truth owner;
- Host/domain remains semantic completion owner;
- old implementation can be deleted after equivalent/better verified behavior;
- no new global capability/workflow/credential ontology is introduced.

## Final rule

**Stable semantics at the waist; replaceable mechanisms at the edges.**

Harness should become easier to automate in the same sense that n8n is easy to extend: new implementations register against narrow contracts, while execution authority and state ownership remain stable and explicit.

# Current realization — 2026-09-14 R0/R2

The first implementation slice is now materially realized in canonical `ordivon-harness`.

Harness baseline before the donor change:

```text
72d47c5
417 deterministic tests PASS
```

Canonical implementation commits:

```text
0468dcf harness: prototype adaptive edit gateway
94cce41 harness: wire durable workspace patch recovery
```

Realized mechanisms:

- internal `EditCodec -> CanonicalEditPlan` seam;
- `exact-replacement-v1` codec;
- `anchored-line-v1` Hashline-like codec bound to exact source snapshots;
- measured/profile-driven codec-selection hook rather than universal Hashline preference;
- common lowering to existing `HarnessExecutionBinding.patch_request_id()` and Runtime `workspace.patch`;
- durable Harness Tool lifecycle support for `workspace.patch` only under explicit `WORKSPACE_CHANGE_POSSIBLE` consequence;
- response-loss reconciliation through `workspace.patch.get` with no physical Patch redispatch;
- distinct `committed`, `prepared/not-committed`, and `unknown` recovery standing;
- default observation-only bridge remains unable to Patch even if supplied a patch-shaped Tool definition.

Current regression standing after durable Patch integration:

```text
434 deterministic tests PASS
Ruff PASS
documentation contract PASS
dependency contract PASS
git diff --check PASS
```

The public default Agent Tool surface is unchanged. No global Capability Service, plugin database, second Tool authority, second Store, or second Runtime was introduced.

R2 is therefore **PARTIALLY REALIZED**: the codec and durable physical-effect backend are proven, while the model-facing `edit_workspace` action, exact prior-read snapshot binding, codec benchmark/selection evidence, and LSP WorkspaceEdit expansion remain forward work.

## R2 update — Agent-facing internal path realized

Canonical Harness advanced with:

```text
33ac4a8 harness: wire agent-facing adaptive edit path
```

R2 now additionally realizes:

- explicit internal `AdaptiveEditRuntimeBridge` composition with `read_workspace` + `edit_workspace`;
- editable reads return exact Runtime source digest plus Harness-generated line anchors;
- `edit_workspace` requires the prior source digest and performs a fresh full Runtime read before Patch admission;
- stale source digest fails model-correctably before any physical Patch intent;
- the logical Harness Tool identity remains `edit_workspace` while the physical operation lowers to `workspace.patch`;
- exact-replacement and anchored-line both use the same durable Patch/reconciliation backend;
- one complete scripted Agent loop passes `read_workspace -> edit_workspace -> candidate_completed`;
- deterministic mechanical benchmark `scripts/check_adaptive_edit_r2_benchmark.py` is now part of the Harness regression suite.

Mechanical benchmark findings are deliberately narrow:

```text
HARNESS-REPO-REPAIR-001:
  exact-replacement-v1 -> oracle PASS
  anchored-line-v1     -> oracle PASS
  lowered Runtime patch -> identical

Repeated identical target text:
  exact replacement -> fail closed as ambiguous
  anchored line      -> exact intended-line PASS

Stale anchor:
  anchored line      -> fail closed
```

This establishes a real adaptive-selection reason without claiming model-quality improvement: exact replacement is simpler when text identity is unique; anchored addressing is mechanically stronger when repeated text makes replacement ambiguous.

Current Harness regression standing:

```text
445 deterministic tests PASS
Ruff PASS
documentation contract PASS
dependency contract PASS
git diff --check PASS
```

The default public Agent Tool surface remains unchanged. The remaining R2 work is now narrower: live Provider/model A/B trials, measured per-model codec profiles, a mature conventional-patch donor if justified, and later LSP `WorkspaceEdit` lowering through the same canonical edit boundary.

## R2 update — first live model/task profile recorded

Canonical Harness advanced again:

```text
6126ad2 harness: record adaptive edit live profile
```

The internal edit mechanism is now past deterministic-only validation. Harness records one revision-bound live profile for:

```text
provider/model:      deepseek / deepseek-flash
task:                HARNESS-REPO-REPAIR-001
max model calls:     6
max tool calls:      8
max total tokens:    64,000
replicates/codec:    5
```

Corrected equal-authority outcomes:

```text
exact-replacement-v1:
  hidden verifier       5/5
  candidate_completed   5/5
  rejected observations 0
  total model calls     22
  total tool calls      27
  total tokens          89,864

anchored-line-v1:
  hidden verifier       4/5
  candidate_completed   3/5
  rejected observations 1
  total model calls     26
  total tool calls      33
  total tokens          114,992
```

Therefore the current profile standing is intentionally narrow:

```text
deepseek-flash + HARNESS-REPO-REPAIR-001 + 2026-09-14
    -> provisional preferred codec: exact-replacement-v1
```

This does **not** authorize a global exact-replacement default. The deterministic repeated-text falsifier remains decisive evidence for retaining anchored addressing: exact replacement must fail closed when the target text is ambiguous, while anchored addressing can identify the intended repeated line.

The primary live evidence is registered in canonical Harness as a verified receipt bound to implementation revision `33ac4a891441c565371767f02905361dd1d5fe55`:

```text
evidence/adaptive-edit-r2-live-ab-deepseek-flash-20260914.json
payload digest:
sha256:e36864e2487a555289cfb0df0481b3c8c00ad9d4a7cf7593ca298f20082ea0ec
```

A preceding 24k-token pilot is explicitly non-primary because Harness's conservative Provider request-token upper-bound gate prevented the fourth Provider turn for both treatments. The corrected 64k run set is the treatment evidence.

One isolated DeepSeek finish-reason inconsistency was retained as an anomaly without weakening the Adapter invariant; subsequent wire-shape and formal Adapter probes were normal.

Current Harness regression standing after the live-profile landing:

```text
448 deterministic tests PASS
Ruff PASS
documentation contract PASS
dependency contract PASS
evidence contract PASS (80 historical / 1 verified)
git diff --check PASS
```

R2 is now **REALIZED FOR THE FIRST INTERNAL AGENT-FACING EDIT DONOR AND ONE LIVE MODEL/TASK PROFILE**, but not graduated as a universal edit-selection layer. Remaining evidence pressure is:

1. additional task families, especially repeated-target and multi-region edits;
2. additional model/provider profiles;
3. mature conventional-patch donor evaluation only if it earns the same canonical boundary;
4. LSP `WorkspaceEdit -> CanonicalEditPlan -> Runtime Patch` lowering;
5. automatic codec selection only after profile evidence plus structural applicability checks justify it.

## R2 update — second live profile corrects global-preference overreach

Canonical Harness advanced to:

```text
9d936e9 harness: add second adaptive edit live profile
```

A second task family now pressures repeated textual targets rather than broad repository repair:

```text
HARNESS-EDIT-ADDRESSING-002
```

The model-visible source contains two identical `return False` lines, while only `beta_enabled()` may become true and `alpha_enabled()` must remain false. The hidden verifier protects the untouched alpha behavior and public function surface. Exact replacement remains expressible by widening `oldText` to unique surrounding context; the task therefore measures model/ACI behavior rather than making one codec impossible by construction.

DeepSeek Flash, under the same 64k / 6-model-call / 8-tool-call authority, produced:

```text
exact-replacement-v1:
  hidden verifier       5/5
  candidate_completed   5/5
  rejected observations 0
  total model calls     20
  total tool calls      25
  total tokens          51,266

anchored-line-v1:
  hidden verifier       5/5
  candidate_completed   5/5
  rejected observations 0
  total model calls     20
  total tool calls      25
  total tokens          52,336
```

The 2.05% token difference is not treated as a meaningful winner. Standing:

```text
deepseek-flash + HARNESS-EDIT-ADDRESSING-002 + 2026-09-14
    -> NO_CLEAR_WINNER_BOTH_VIABLE
```

This invalidates any attempted extrapolation from the first task to a global DeepSeek-Flash preference for exact replacement. Current selection law is now explicitly:

```text
structural applicability
        +
model/task profile evidence
        -> codec preference, if any
```

If no meaningful profile advantage exists, both mechanically valid codecs remain available; Harness must not fabricate a performance preference.

The second verified receipt is:

```text
evidence/adaptive-edit-r2-live-ab-deepseek-flash-addressing-20260914.json
payload digest:
sha256:fb3c3ff88821c0300ee87110e06a9abadfd3a065c2bc4cc1a46777ec647613cc
```

The live A/B runner was also generalized from one hard-coded task to a small multi-task specification boundary. During this work, a reporting defect was found and fixed: float-valued summary means violated Harness canonical JSON. Live reports now use integer totals plus `meansTimes10`, with offline canonical-encoding coverage before Provider use.

Current Harness acceptance after the second profile:

```text
452 deterministic tests PASS
Ruff PASS
documentation contract PASS
dependency contract PASS
evidence contract PASS (80 historical / 2 verified)
profile evidence integrity PASS
git diff --check PASS
```

The next high-information R2 pressure point is **multi-region editing**. Current `CanonicalEditPlan` intentionally allows only one semantic edit per file per compiled plan. The next experiment should determine whether that restriction remains a useful narrow waist, whether multiple Agent-visible edit calls are sufficient, or whether evidence now justifies a bounded multi-edit plan while preserving exact snapshot fencing and one Runtime Patch authority boundary.

## R2 update — multi-region pressure closes without a wider Agent wire

Canonical Harness advanced to:

```text
d1667ba harness: validate multi-region edit boundary
```

`HARNESS-EDIT-MULTIREGION-003` requires two separated changes in one file while preserving an unrelated middle region. The Agent-facing ACI remains unchanged: one semantic edit per `edit_workspace` call against one exact source digest.

DeepSeek Flash results under the unchanged 64k / 6-model-call / 8-tool-call authority:

```text
exact-replacement-v1:
  hidden verifier       5/5
  candidate_completed   5/5
  rejected observations 0
  total model calls     27
  total tool calls      32
  total tokens          79,667

anchored-line-v1:
  hidden verifier       5/5
  candidate_completed   5/5
  rejected observations 0
  total model calls     24
  total tool calls      28
  total tokens          68,931
```

Anchored-line used 13.48% fewer aggregate tokens, three fewer model calls and four fewer Tool calls, but both codecs remained fully reliable. Therefore:

```text
current one-edit-per-call boundary
    -> SURVIVES_CURRENT_TASK

atomic multi-edit Agent wire
    -> NOT_JUSTIFIED_BY_CURRENT_EVIDENCE
```

This is a deliberate negative architecture decision. `CanonicalFilePatch` and Runtime `workspace.patch` already support multiple `edits[]`, but implementation capability is not sufficient reason to widen the model-facing contract. The current narrow waist remains until a broader workload demonstrates a concrete reliability or cost failure that cannot be handled by codec choice, bounded wider replacement, or sequential digest-fenced edits.

Third verified receipt:

```text
evidence/adaptive-edit-r2-live-ab-deepseek-flash-multiregion-20260914.json
payload digest:
sha256:993750fdc5911eee8bfba00b8917cf1be2313d4712da13b5ba7a13d86b6388bb
```

Current Harness acceptance:

```text
456 deterministic tests PASS
Ruff PASS
documentation contract PASS
dependency contract PASS
evidence contract PASS (80 historical / 3 verified)
profile evidence integrity PASS
git diff --check PASS
```

Adaptive Edit R2 is now sufficiently evidenced for the current slice. The next composition target should move to mature protocol integration rather than inventing more edit syntax: first evaluate `LSP WorkspaceEdit -> CanonicalEditPlan -> Runtime Patch` using existing local LSP/client components where possible.

## R7 update — LSP WorkspaceEdit proposal path reaches real Runtime Patch

Canonical Harness advanced through two LSP R7 commits:

```text
9c774b3 harness: add LSP WorkspaceEdit adapter
d75617d harness: verify LSP rename through Runtime
```

R7 deliberately composes mature LSP semantics without granting the language server mutation authority:

```text
Language Server
    -> LSP client transport
    -> WorkspaceEdit proposal
    -> Harness URI/version/snapshot/position validation
    -> CanonicalEditPlan
    -> Runtime workspace.patch
```

The pure Harness adapter accepts standard `WorkspaceEdit.changes` and TextDocumentEdit-only `documentChanges`, explicit URI-to-authorized-snapshot bindings, and negotiated `utf-8` / `utf-16` / `utf-32` position encodings. It fails closed on unbound URIs, version mismatch, unsupported resource operations, overlapping edits, encoding-unit splits, out-of-range positions, conflicting URI aliases, and no-op edits.

A `file://` URI is explicitly not authority identity:

```text
server URI != workspace authority != exact source identity
```

URI aliases are deduplicated only when they bind the same exact snapshot and propose identical edits.

Local provider validation used the already-installed `clangd 22.1.8` and temporary `pygls 2.1.1` LanguageClient donor. `pygls` was not added to Harness production dependencies. A revision-bound rename flow from `9c774b3` proved:

```text
clangd textDocument/rename: square -> quad
    -> WorkspaceEdit.changes
    -> negotiated positionEncoding=utf-8
    -> Harness CanonicalEditPlan: 1 file / 2 exact edits
    -> Runtime workspace.patch
    -> committed
```

Runtime receipt:

```text
clientRequestId:
request:harness-patch:d8b7b215b74d50b31c0c6dbb5fbe1b5a

before:
sha256:59f92d40809853654b25d0ba5c3c9692021b2820d6f927818b1a952d8f33b286

after:
sha256:0bbf5c459448b66e3a4b7624820c81c8f594d49e9fca55ae7c99a9769c931fac
```

The source was unchanged until Runtime Patch admission; therefore clangd/pygls remained proposal-only and Runtime retained physical-effect ownership.

Fourth verified receipt:

```text
evidence/lsp-r7-clangd-runtime-patch-20260914.json
payload digest:
sha256:f16757f66ebfae75a815b5002c50a97e7aee50574639be1841bb5a55c949328d
```

This integration exposed a separate evidence-governance issue: repository-wide `src/` invalidation incorrectly made all three Adaptive Edit receipts stale when the unrelated LSP adapter was added. Harness evidence currentness now supports explicit `implementationPaths` scopes. The legacy repository-wide invalidation remains the default; scoped verified receipts must bind at least one implementation path plus `pyproject.toml` and `uv.lock`, and any change inside the declared slice still invalidates the receipt.

Current Harness acceptance:

```text
467 deterministic tests PASS
Ruff PASS
documentation contract PASS
dependency contract PASS
evidence contract PASS (80 historical / 4 verified)
LSP evidence integrity PASS
git diff --check PASS
```

R7 standing is therefore **VERIFIED FOR ONE LOCAL CLANGD PROVIDER PATH**, not graduated as a universal LSP provider. `pygls` remains an experimental transport donor. The next evidence target is a second language-server/provider path plus lifecycle/diagnostic behavior before fixing any default transport stack or exposing LSP as a public Agent Tool.

## R7 update — second language server confirms adapter portability

Canonical Harness advanced to:

```text
33a6066 harness: verify second LSP provider path
```

The already-installed `taplo 0.10.0` server was used as a second provider rather than installing another stack. Taplo advertises rename support and returned a standard `WorkspaceEdit.changes` for TOML key rename:

```text
name -> title
```

Taplo did not advertise `positionEncoding`, so the provider path correctly used the LSP default `utf-16` semantics. The same `workspace_edit_to_canonical_plan()` adapter compiled the proposal into one exact canonical edit; Runtime alone committed the physical mutation:

```text
before:
sha256:291c2536d2d7fff1c726f0f11b9b286d717eca3b6da650330ed9187a6eade5cd

after:
sha256:b51243ac16c473ecec65f0718264c65e36d9a5802e5e4ec58910f0b7ec769452
```

Fifth verified receipt:

```text
evidence/lsp-r7-taplo-runtime-patch-20260914.json
payload digest:
sha256:e8c6fb0040dac7c691373c24b3400d0e843bea7d1da345ce2fe22bc79f19e4b0
```

R7 provider diversity standing is now:

```text
clangd 22.1.8 / C++ rename -> VERIFIED
taplo 0.10.0 / TOML rename -> VERIFIED
same Harness WorkspaceEdit adapter -> VERIFIED
same Runtime physical-mutation boundary -> VERIFIED
```

This closes the question of whether the adapter is clangd-specific.

However the transport question remains deliberately open. During the bare pygls/Taplo probe, Taplo issued `workspace/configuration` and diagnostics traffic that the bare `pygls` LanguageClient probe did not handle. Rename still succeeded, but this is direct evidence that pygls is not lifecycle-complete enough **as used here** to become the default Harness LSP provider stack without a wrapper or comparison against a more complete mature client.

Current Harness acceptance remains:

```text
467 deterministic tests PASS
Ruff PASS
documentation contract PASS
dependency contract PASS
evidence contract PASS (80 historical / 5 verified)
2-provider LSP evidence integrity PASS
git diff --check PASS
```

R7 should therefore stop adding language servers. The next work item is provider lifecycle ownership: initialization/configuration, diagnostics, server requests, cancellation/shutdown, and Run/Tool Grant binding. Only after that should Harness choose or admit a production LSP transport/provider dependency.

## R7 update — lifecycle ownership narrowed to a replaceable provider port

Canonical Harness advanced through:

```text
c7df6ef harness: add proposal-only LSP provider port
cd45070 harness: verify LSP lifecycle provider candidate
```

The stable Harness waist is now provider-neutral:

```text
Harness Run / Tool authority
    -> HarnessLspProviderPort
        initialize
        rename -> WorkspaceEdit proposal
        drain diagnostics
        shutdown
    -> WorkspaceEdit authority binding
    -> CanonicalEditPlan
    -> Runtime workspace.patch
```

The port deliberately has no apply/write/workspace-patch method. A provider declaring direct workspace mutation is rejected by the Harness-side capability model. Harness-facing positions use one-based lines plus zero-based Unicode-character columns; provider wrappers convert them to negotiated UTF-8/UTF-16/UTF-32 LSP position units.

The port itself has no third-party dependency. This preserves the existing Harness repository boundary, which intentionally excludes optional dependency groups.

A fresh revision-bound lifecycle occurrence evaluated `lsp-client 0.3.9` with local `taplo 0.10.0`. The custom provider composition included rename, configuration-request handling, diagnostics, and log notifications while deliberately omitting the library's apply-edit mixin. Observed result:

```text
workspace/configuration handled = 1
publishDiagnostics notifications = 4
WorkspaceEdit proposal returned = yes
provider applyEdit mixin = absent
disk changed during lifecycle = no
disk changed after shutdown = no
typed WorkspaceEdit -> Harness JSON adapter = pass
```

The package's own mutating convenience APIs remain outside the Harness provider port. Its wheel metadata carries the MIT OSI classifier, but it has **not** been added to Harness production dependencies.

Sixth verified receipt:

```text
evidence/lsp-r7-lsp-client-lifecycle-20260914.json
payload digest:
sha256:6981aec36c5b90c8063894fbd0d94bf88e1130bb729e81c8bad22c7e663effc7
```

Current Harness acceptance:

```text
474 deterministic tests PASS
Ruff PASS
documentation contract PASS
dependency contract PASS
evidence contract PASS (80 historical / 6 verified)
LSP lifecycle evidence integrity PASS
git diff --check PASS
```

Current standing is therefore:

```text
WorkspaceEdit authority boundary          VERIFIED
provider portability (clangd + Taplo)    VERIFIED
provider-neutral lifecycle port          IMPLEMENTED + REGRESSED
lsp-client lifecycle candidate           SUPPORTED
lsp-client Harness core dependency       NOT_ADMITTED
default LSP provider                     NOT_FINAL
```

The remaining R7 work is negative/fault evidence rather than feature expansion: cancellation, abnormal language-server exit, and finally Run/Tool Grant binding before any public Agent Tool surface is exposed.
