---
schema_version: 1
id: game.research.cross-project-self-loop-study
title: Cross-Project Self-Loop Study
type: research-synthesis
profile: research
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-game
audience:
  - designer
  - builder
  - agent
  - researcher
updated: 2026-08-15
summary: Revision-bound study of Ordivon Runtime, Host, Harness, World, Computing, Web, Studio, Security, Finance, Workstation, Human, and Game. Extracts independently recurring responsibility boundaries and self-correction patterns, then derives bounded contraction hypotheses for Game without creating a new cross-project authority.
evidence_status: derived
readiness: READY
applies_to:
  - ordivon-game
related:
  - game.development-model
  - game.authority
  - game.product.station-zero-v3
---
# Cross-Project Self-Loop Study

## Status and boundary

This study intentionally pauses Station Zero G5 content expansion and asks a higher-level question:

```text
What have Ordivon's projects independently learned about
how an Agent-first system should observe, decide, commit,
recover, express, evaluate, and improve itself?
```

It is a **Game research synthesis**, not a new Ordivon architecture, service, protocol, controller, or source of truth.

It does not own Runtime Jobs, Host Tasks, Harness cognition, World trajectories, Security authority, Finance capital truth, Studio production, Web publication, Workstation capability, Human evidence, or any other project's current state. Every statement below is a revision-bound observation of another owner.

The intended consequence is narrower:

```text
cross-project observation
→ identify recurring pressure
→ derive Game hypotheses
→ test them owner-locally in Game
→ retain / shrink / delete based on Game evidence
```

Do not convert the common patterns in this document into a universal Ordivon framework merely because they recur.

---

# Why this study exists

Station Zero v3 had just exited G4 and entered bounded G5 Production. The next obvious move was to produce a second encounter and continue product detail work.

That was deliberately paused.

The reason is methodological: Ordivon has several projects that have already undergone repeated expansion, falsification, contraction, responsibility reassignment, and semantic-surface compression. Continuing to optimize Game only from Game's own recent evidence risks a closed self-loop in which local architecture increasingly justifies itself.

The research question therefore became:

```text
Before expanding Game again,
what stable structures survived pressure elsewhere?
```

The important unit is not the project name. It is the **problem that forced a structure to survive**.

---

# Method

Each repository was inspected in its own Runtime Workspace rather than through one unrestricted cross-repository shell. This was not only a security constraint; it preserved the same epistemic discipline the projects themselves use:

```text
historical observation ≠ current owner truth
```

For each project the study asked:

1. What problem does this project actually solve?
2. What is its smallest recurring loop?
3. What does it own?
4. What does it explicitly refuse to own?
5. Which state is durable, and why can it not be safely recomputed?
6. How are uncertainty and recovery represented?
7. What is the Agent-facing semantic surface?
8. Which abstractions were expanded and later deleted or contracted?
9. Which result has survived a later independent workload rather than only its original experiment?

Source, tests, exact contracts, and authority documents outrank project summaries.

---

# Revision-bound audit table

These are the revisions observed for this study, not claims about future currentness.

| Project | Observed revision | Primary role in this study |
| --- | --- | --- |
| Runtime | `761bfe8dd7ca7c5e3e514891657c986eecb204e5` | physical execution commitment, evidence, uncertainty, recovery |
| Host | `507589eb1ae602f788913c7a8fdfd7bad355fe6c` | semantic Task continuity across replaceable cognition/execution |
| Harness | `bb9f636cc4b533895254c0caf3e90eb083ca9e50` | bounded Agent Run, cognition/history separation, Tool/effect loop |
| World | `d36fa9e8764c89dd9c51dbef2727ebb13e7a9e27` | owner-native external relations and consequence continuity |
| Computing | `c96ba2cc73b651097443a38ff7a2431801efd217` | cross-project world-model compression and responsibility placement |
| Web | `c640e5af80727c7f7f35919257642776a8cdce10` | source-bound public judgment, rendered encounter, publication evidence |
| Studio | `ad313efe289d36660e6643934ed5e3a586e5fab3` | editable expression, media production, review, scoped learning |
| Security | `2aba805e6ffe6c64ce0e0ebafce4240b61ef26a3` | adversarial authority/evidence separation and recovery under deception |
| Finance | `f3a3ff13077961620c8fb965506557e8947a6ecb` | capital semantics, effect admission/reconciliation, semantic compression |
| Workstation | `8dde4a411c71b062a0b5765dc6534d445a9ed6db` | node capability, transport/currentness, scoped equipment/admission |
| Human | `f7725dfc9b391c3e9a0c509d49795994931c9d63` | decision-relevant research and Human↔Agent capability allocation |
| Game | `430ed2f77a18d925963de8a8cb1e6f32142655d7` | authoritative interactive World and current Station Zero product |

Harness and World advanced while this study was already running. The earlier Harness observation was `6639cf5...` and World observation `da4eb2c...`. Both were explicitly revalidated against their new heads before synthesis.

That currentness correction is part of the result rather than bookkeeping noise.

---

# 1. Runtime — physical commitment, not semantic completion

## Problem

An Agent may ask for a physical operation, but admitting that operation is not the same thing as knowing whether it ran, whether an external consequence happened, or whether the user's semantic goal is complete.

Runtime solves the physical middle:

```text
Operation proposal
→ durable admission
→ Job / Attempt
→ owned process tree
→ bounded evidence
→ reconciliation
```

## Stable separations

```text
Proposal ≠ Commitment
Execution Result ≠ External Effect Receipt
External Effect Receipt ≠ Semantic Completion
Unknown ≠ Failed
```

The practical meaning is visible in its recovery rules: an ambiguous dispatch becomes `lost`/`orphaned`/unknown evidence, not an excuse for a silent fresh redispatch.

Effect classes are recovery contracts, not caller optimism:

```text
READ_ONLY
IDEMPOTENT
RECONCILABLE
OPAQUE
```

The generic execution surface remains OPAQUE rather than allowing callers to declare themselves safe.

## Why this matters

Runtime's strength is not that it can execute many things. It is that it refuses to convert missing evidence into invented certainty.

Its architecture is primarily a set of **non-equivalences** maintained across interruption.

---

# 2. Host — semantic continuity, not another executor

## Problem

Agent sessions, model calls and executor processes may disappear while the meaning of an unfinished Task must survive.

Host preserves:

```text
objective
Task identity
current semantic frontier
retained commitments
unresolved uncertainty
next possible continuation
```

It does not preserve the illusion that one Agent session is the Task.

## Core loop

```text
purpose
→ durable Task identity
→ bounded semantic frontier
→ external work / cognition
→ evidence
→ verification or unresolved state
→ next frontier / outcome
```

## Stable boundary

```text
Runtime = physical execution truth
Harness = bounded Agent Run / cognition machinery
Host    = semantic Task continuity
Domain  = authoritative domain truth
```

A WorkingCheckpoint is explicitly a semantic working claim, not Runtime/Git/domain truth. Its external references are navigation hints that must be revalidated.

## What Host refuses to become

Host explicitly avoids becoming:

- a chat transcript database;
- Provider/session manager;
- Agent planner;
- general scheduler;
- second Runtime;
- generic domain database.

This refusal is a source of strength.

---

# 3. Harness — cognition is not history

## Problem

Traditional Agent loops often collapse everything into a single message list. That makes it difficult to distinguish what happened, what the Agent currently retains, what the caller just supplied, and what Tool effects are still unresolved.

Harness separates:

```text
Canonical History
Durable Cognition
Interaction Cognition
Attempt Cognition
Execution Control
Effects
```

## Core loop

```text
Canonical History
  + Agent-owned Working Set
  + caller ingress
  + recent Attempt cognition
→ Effective Model View
→ Agent Decision
→ cognition transition | Tool intent | conclusion
→ new retained History / evidence
```

## Stable separations

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
```

The Agent owns semantic retention; Harness proves structure and provenance without pretending to know what is semantically worth remembering.

## Current morphology result

During this study Harness itself supplied a fresh example of the self-loop.

An AM1 prototype first admitted an executable caller-supplied Loop factory. AM2 then found two falsifiers:

```text
declared driver digest ≠ executed implementation-byte proof
Python subclass/type ancestry ≠ semantic-kernel compatibility proof
```

The executable substitution seam was deleted. What survived is only:

```text
Attempt-bound LoopDriver identity
```

It can name morphology but cannot load, execute, replace, discover or promote arbitrary code.

This is an important pattern:

```text
expand hypothesis
→ attack proof boundary
→ contract to smallest supported result
```

---

# 4. World — relation continuity outlives controller morphology

## Problem

External environments and destination owners have their own truth. A World connector must not make Host, Harness or an Agent the owner of those external consequences.

World's recurring forms are:

```text
External provider:
Bind → Observe → Act → Reconcile

Resource:
Source Egress → Bind → Destination Ingress → Reconcile

Message:
Source Issuance → Bind → Destination Admission → Reconcile

Entity:
Source Departure → Bind Continuity → Destination Materialization → Reconcile
```

## Stable separations

```text
Observation ≠ Currentness
Currentness ≠ Action Authority
Provider Success ≠ Task Completion
Historical Occurrence ≠ Current Presence
Delivery ≠ Cognition
Task Identity ≠ World trajectory identity
```

## Durability fence

World repeatedly converged on:

```text
Observe / Query / Select
→ usually recomputable

Prepare / Bind / Dispatch consequence
→ durable exact identity required
```

Durability belongs at the **consequence boundary**, not automatically at every planning step.

## Current morphology result

The current World head added no new production mechanism; it added tests showing:

```text
controller / loop / process replacement
≠ World consequence replacement
```

If response loss leaves an owner-native consequence `UNKNOWN`, replacing the Agent morphology does not make retry safe.

```text
UNKNOWN + new morphology ≠ safe retry
UNKNOWN + exact owner-native not_committed proof
→ original retry may become admissible
```

World also rejected a new global quiescence database. A derived caller projection over owner-native commitments is enough to answer whether unresolved reconciliation would be orphaned.

Finally, internal critic/planner/verifier topology remains Harness cognition morphology until an actor actually needs independent durable identity + continuity + independently addressable World relation/authority. A Message is not an Entity merely because it crosses a boundary.

---

# 5. Computing — the self-loop is responsibility reassignment

## Problem

As models and classical substrates improve, an architectural responsibility that once needed a project/package may become cheaper to localize, delete, or push downward.

Computing studies the **residual responsibility**, not the survival of component names.

## Three bands

```text
1. flexible cognition / product policy
2. thin durable responsibility boundaries
3. mature classical substrate / owner-native domains
```

The middle band must justify itself continuously.

## World-model loop

```text
shared world model
→ project/research structures
→ real project practice
→ owner-native evidence
→ project delta / model pressure
→ cross-project comparison
→ retain / narrow / split / revise claims
→ project-specific reform question
→ independent project re-test
↺
```

The return edge is mandatory. A reform that is never consumed later is not demonstrated recursive improvement.

## Persistent Adaptive Loop result

Computing's strongest correction is:

```text
stored state != useful persistence
available capability != expanded useful work
behavior change != held-out objective transfer
deterministic projection != deterministic cognition
rendered encounter evidence != human response
Persistent Change != Recursive Improvement Evidence
```

The only scoped L4 result in that PAL round was Web/Studio render-review: a later fresh surface consumed the prior and found a real source/build-invisible defect.

Host persistence, Workstation scoped paths, Game responsibility feedback and Security evidence reduction all produced useful local changes but did **not** automatically earn recursive-improvement credit.

## L4 admission

A persistent change earns stronger recursive-improvement evidence only when a later independent workload consumes it and owner-native outcome improves, with scope/cost/negative evidence retained.

This is stricter than “we changed code and the test passed.”

---

# 6. Web — public expression is another consequence boundary

## Problem

A source owner changing does not determine what the public site should say, and a page rendering correctly does not establish what a human understood.

Web's loop is:

```text
owner-native source
→ public consequence judgment
→ expression candidate
→ rendered encounter
→ verification
→ publish / correct / rebind / no-op
```

## Stable separations

```text
Owner changed ≠ public page must change
Source fact ≠ public judgment
Public source ≠ rendered encounter
Exposure ≠ Comprehension
Rendered encounter ≠ human response
```

A source change creates a review obligation, not an automatic publication mutation.

## Evidence hierarchy

Web separates mechanical browser evidence, task/UX evidence, creative judgment, calibrated Agent review and human preference rather than collapsing them into one score.

A deterministic screenshot proves what pixels were rendered. It does not prove that the visual hierarchy is meaningful to a reader.

## Important product lesson

Expression itself is consequential. Correct World state and correct execution can still produce a wrong public/player encounter.

---

# 7. Studio — production learning must survive transfer

## Problem

Studio turns source-owned reality into editable medium-specific expression without making the artwork, review system or Output a second source of truth.

## Core protocol

```text
FRAME
→ BIND
→ EXPRESS
→ RENDER
→ AUDIT
→ DECIDE
→ scoped LEARNING
```

The value is not the stage names. It is the boundary discipline between them.

## Stable separations

```text
authoring representation ≠ rendered perceptual fact
selected Asset identity ≠ exact Blob bytes
production finished ≠ reusable principle earned
mechanical temporal observation ≠ semantic visual judgment
creative Output ≠ source-owner truth
```

Critique is transient by default. The retained consequences are usually:

```text
source diff
new artifact / review evidence
bounded current production cognition if still needed
```

Not a universal critique database or hidden chain-of-thought archive.

## Learning promotion

```text
artifact-local result
→ repeated one-medium result
→ medium profile
→ survives materially different media
→ cross-medium core
```

A production trick does not become a general Studio law because one artifact shipped.

---

# 8. Security — adversarial pressure makes epistemic boundaries sharper

## Problem

Security must reason when actors may deceive, observations may conflict, controllers may be compromised, and real effects may survive the process that caused them.

## Consequence chain

```text
Actor intent
≠ authority admission
≠ executor ran
≠ receipt
≠ world consequence
≠ verified consequence
```

## Evidence planes

```text
Actor observation
communicated claim
sensor telemetry
management observation
independent world truth
```

These are deliberately not collapsed.

## Law versus profile

Security makes one distinction unusually explicit:

```text
constitutional law
≠ authority/resource grant
≠ experiment profile/fixture
≠ evaluator judgment
```

A current experiment forbidding something does not make it a universal constitutional prohibition.

## Recovery insight: the world can be the progress state

C1-D showed that a fresh controller could continue a partial physical effect from:

```text
semantic effect identity
+ resource identity
+ current world placement
→ infer missing suffix
→ execute suffix
→ independently verify target world
```

It did **not** need the old Python object graph, old RangeSession or a newly invented durable substep workflow.

This is a direct warning against persisting every process state merely because the process is complicated.

## Information-theoretic UNKNOWN

C1-I constructed two different histories that collapsed to the same recoverable sender view. Since the observer could no longer distinguish “effect happened” from “effect did not happen,” the only sound result was:

```text
UNKNOWN
blindResendAuthorized = false
completionPublicationAuthorized = false
```

This is not conservative taste. It is logically forced by lost information.

---

# 9. Finance — complexity may survive below a semantic waist

## Problem

Finance must preserve real capital meaning while dealing with research, decisions, venue execution, partial observations, bills/fills, reconciliation and owner performance.

The latest reform did not delete all lower-level complexity. It pushed it below a smaller Agent-facing semantic surface:

```text
finance.observe
finance.research
finance.decide
finance.execute
finance.reconcile
finance.performance
finance.owner
```

## Canonical loop

```text
OBSERVE
→ RESEARCH
→ DECIDE
→ EXECUTE
→ RECONCILE
→ PERFORMANCE / LEARN
→ OBSERVE
```

## Semantic waist test

A concept belongs above the waist if it changes capital meaning:

- owner capital;
- evidence;
- belief/decision;
- portfolio transition;
- risk/survival;
- effect/reconciliation;
- attributable outcome.

If it exists only because software must transport, sign, route, retry, store or deploy bytes, it should stay below the Agent semantic surface.

## Stable separations

```text
Proposal ≠ execution authority
Fill ≠ cash ledger entry
failed collection ≠ empty observation
incomplete [] ≠ zero fills/bills
nominal return ≠ real return without inflation evidence
residual equity change ≠ Agent alpha
Performance feedback ≠ execution gate
```

Performance is an input to the next world model, not permission to rewrite past causality.

---

# 10. Workstation — installed capability is not usable authority

## Problem

A machine may contain many tools, paths, proxies and transports. Their existence does not mean an Agent may use them, that they are currently healthy, or that they add useful work.

## Stable separations

```text
installed capability ≠ ambient authority
reachable path ≠ admitted path
historical path success ≠ current reachability
service alive ≠ selected transport healthy
many routes ≠ independent failure domains
ranking ≠ selection
selection ≠ admission
```

## Semantic surface

The semantic MCP is intentionally small:

```text
path.observe
path.revalidate
anchor.admit
anchor.observe
egress.observe
egress.ensure
```

Raw route/proxy mechanics stay below the surface.

## PAL-P2 negative result

Scoped network paths were useful engineering capabilities, and some reduced latency, but ambient paths already completed every tested useful workload. Therefore:

```text
available capability ≠ expanded useful work
```

The paths did not earn L4 recursive-improvement status merely because the capability count increased.

This is an important falsifier for tool accumulation in any Ordivon project.

---

# 11. Human — the scarce resource is decision-quality synchronization

## Problem

Agent iteration speed can exceed a person's ability to internalize every technical change. The solution is not “the human must catch up” and not “delegate everything.”

The question is capability allocation:

```text
What must the human internalize?
What only needs conceptual understanding?
What can be externalized safely?
What should be delegated entirely?
```

## Research contraction

Current Human work has moved toward:

```text
mature external evidence
→ moderator / transport analysis
→ Ordivon-specific structural residual
→ natural dogfood
→ personal experiment only if unresolved claim still changes a real decision
```

## Research Task as search state

A useful Task is not “the original list of phases.” It is:

```text
stable problem
+ current evidence
+ candidate solutions
+ rejected regions
+ unresolved regions
+ next information-gain action
```

A plan is a search aid. Completing every initially imagined phase is not the goal.

## Model deletion

If a research model no longer changes decisions, predicts no new evidence and only adds explanatory machinery, contraction/deletion is positive progress.

---

# 12. Cross-project convergence

The projects do not share one implementation architecture. They do share repeated pressure patterns.

## 12.1 Strong architecture is subtractive

The strongest projects repeatedly gain power by narrowing responsibility:

- Runtime refuses semantic completion;
- Host refuses execution/domain ownership;
- Harness refuses semantic truth selection for cognition;
- World refuses a global World/Presence/capability registry;
- Security rejects generic causal/trust/evidence services;
- Finance pushes plumbing below the semantic waist;
- Studio refuses critique/history databases by default;
- Workstation refuses to equate installation with authority;
- Computing deletes responsibilities when lower owners can carry them.

The recurring question is not:

```text
What else can this project represent?
```

It is:

```text
What responsibility would become unsafe or impossible if this structure disappeared?
```

## 12.2 The architecture is largely a set of non-equivalences

Across projects, failures often begin by collapsing two things that are merely correlated.

Recurring examples:

```text
intent ≠ commitment
execution ≠ external occurrence
occurrence ≠ semantic completion
history ≠ cognition
observation ≠ retention
observation ≠ currentness
currentness ≠ authority
source fact ≠ public judgment
render ≠ human response
proposal ≠ execution authority
fill ≠ cashflow
available capability ≠ useful work
persistent change ≠ recursive improvement
```

This suggests a useful design practice:

> When a project grows complex, first identify which non-equivalence the complexity is protecting. If no one can name it, the structure is suspect.

## 12.3 Uncertainty is a first-class state

Healthy projects preserve:

```text
UNKNOWN
stale / uncurrent
partial / incomplete
lost / orphaned
unresolved reconciliation
unproven human response
```

They do not translate uncertainty into failure, success or safe retry merely to simplify control flow.

## 12.4 Owner-native truth outranks convenient projection

Derived projections are useful everywhere, but they remain subordinate:

```text
Runtime registry projection
Host checkpoint
Harness Effective Model View
World inspector
Web source snapshot
Studio review packet
Security evidence projection
Finance context
Workstation ranking
Game Mission Control
```

A projection becomes dangerous when it silently turns into a second truth owner.

## 12.5 Durability belongs at irreducible boundaries

Persist when information would otherwise be impossible or unsafe to reconstruct:

- semantic work identity across cognition replacement;
- an admitted external consequence identity;
- evidence required to distinguish retry from duplicate effect;
- player-visible live-model output that may later be committed exactly;
- authoritative World history needed for replay/accountability.

Prefer recomputation for:

- discovery/query/ranking where owner state can be re-observed;
- derived analysis/review projections;
- transient critique;
- process-local substeps already encoded in current world placement;
- implementation detail that has no independent semantic consequence.

## 12.6 A semantic waist is often better than deleting valid complexity

Some complexity is real and cannot simply disappear. The mature pattern is:

```text
small semantic surface
----------------------
correct lower-level contracts / mechanics
```

Finance makes this explicit, but the same structure exists in Workstation, Harness, World, Web and Studio.

For Agent-first systems this is particularly important: the Agent should reason in owner-native semantics rather than spending cognition on transport/retry/storage/plumbing concepts that do not change the task's meaning.

## 12.7 Law, authority, profile and evaluator must stay distinct

Security makes this clearest:

```text
constitutional law
≠ authority grant
≠ profile / encounter configuration
≠ evaluator judgment
```

The distinction generalizes. A current fixture or benchmark threshold must not quietly harden into a universal invariant.

## 12.8 World/real state can replace workflow state

Before inventing a durable workflow state machine, ask whether exact identity + current owner/world state already contains enough information to continue safely.

Security C1-D is the strongest current proof.

This does not mean “never persist workflow.” It means persistence must prove information not recoverable from current reality.

## 12.9 Tool availability is not value

Workstation PAL-P2 is a useful negative example:

```text
more scoped routes
+ lower latency
≠ more useful workloads completed
```

The same standard should apply to models, providers, game mechanics, editors, media tools and research infrastructure.

## 12.10 Generalization requires materially different consumers

World and Computing converge strongly here.

A second label is not a second consumer. Shared structure should normally require:

```text
materially different workload A
+ materially different workload B
+ reproduced common failure
+ clear lower-cost shared responsibility
```

Game should therefore remain Station Zero-specific until another genuinely different game reproduces the same need.

## 12.11 Human↔Agent synchronization is selective

A human should not internalize every implementation change simply because Agents can produce them faster.

The synchronization target is decision quality. Human attention should be spent on abstractions, consequences and tradeoffs that change real choices; mechanical detail can remain externalized where trustworthy evidence and tooling preserve it.

## 12.12 The next action should maximize information gain, not plan completion

Human and Computing independently converge on this.

A research series is search through a problem space. Once an experiment kills a branch, continuing its originally listed phases can become process theater.

---

# 13. The cross-project self-loop

The common structure can be described without creating a common service:

```text
1. OBSERVE
   read owner-native current reality

2. FRAME
   choose one bounded decision-relevant problem / claim

3. SELECT
   choose the smallest owner-local action or experiment
   with highest expected information gain

4. ADMIT
   cross an explicit authority boundary only when
   a real consequence is about to become possible

5. ACT / PRODUCE
   execute the effect, produce the artifact, or change the owner state

6. RE-OBSERVE
   obtain independent consequence evidence

7. RECONCILE
   compare prediction / baseline / intended meaning with reality
   while preserving UNKNOWN and contradictory evidence

8. CONTRACT
   retain, shrink, split, localize, or delete the treatment

9. PROMOTE ONLY AFTER TRANSFER
   stronger shared learning is earned when a later independent
   workload consumes the retained change and improves owner-native outcome

↺ return to OBSERVE
```

A shorter mnemonic is:

```text
OBSERVE
→ DECIDE
→ COMMIT
→ CONSEQUENCE
→ RECONCILE
→ CONTRACT
→ TRANSFER
→ OBSERVE
```

Again: this is a **meta-pattern**, not a new lifecycle authority. Each owner keeps its own domain-specific loop.

---

# 14. What Game already gets right

Station Zero v3 already reflects many of the strongest cross-project laws:

```text
World ≠ Provider
Faction Knowledge ≠ hidden World truth
Agent Decision ≠ direct mutation
Preview ≠ Commit
Commit ≠ successful Intent
resolved unsuccessful Intent ≠ execution failure
World Event / Turn Record ≠ player projection
uncertain committed Turn ≠ blind fresh retry
rendered browser journey ≠ proof of fun
```

These are not the problem.

The more important current question is:

> Has Game retained too much research-era machinery around these correct boundaries after the product itself became stable enough to enter G5?

---

# 15. Game structural thickness

At the observed Game revision, Station Zero v3 alone contains approximately:

```text
115 exported interfaces
37 exported type aliases
20 exported classes
```

Large files include:

```text
persistence.ts           1764 lines
agent-planning.ts        1574
reducer.ts               1557
genesis.ts                699
deepseek-credentials.ts   580
deepseek-provider.ts      553
p3-model.ts               502
model.ts                  502
content.ts                496
planning-store.ts         490
```

Object count is **not** evidence of over-design by itself.

Deletion pressure must ask whether an object protects irrecoverable player/World meaning.

---

# 16. Game durability classification

## KEEP — currently justified irreducible state

### Selected Plan Preview

A Preview produced by a live model cannot be assumed reproducible. Once the player has seen it and may later Commit it, exact identity matters.

```text
recompute model output
≠ recover the plan the player actually reviewed
```

Persisting selected Preview is justified.

### Commander Order revision ↔ Preview binding

This is part of the player's commitment semantics. Editing the Order must invalidate the old Preview without changing World state.

### Faction Plans / Turn Batch / World Event / Turn Record

These bind authoritative consequence, deterministic replay, response-loss recovery and exact Aftermath evidence. They are not merely UI history.

## KEEP AS DERIVED — correctly recomputed, not separately persisted

The following are derived from retained truth:

```text
Mission Control view
Plan Impact
Aftermath
Plan Review
Operation Debrief
Temporal Expression
bounded spatial projection
```

This is healthy and already matches the mature Web/Studio/Finance pattern.

---

# 17. Game contraction hypotheses

These are **research hypotheses**, not deletion authorization.

Use four labels:

```text
PROVEN RESIDUE
  current product has no production consumer

DELETION EXPERIMENT REQUIRED
  likely duplicate responsibility, but equivalence must be proven

OWNERSHIP PRESSURE
  responsibility may belong below another semantic waist,
  but migration cost/second-consumer pressure is not yet proven

KEEP
  current evidence demonstrates irreducible product/authority value
```

## 17.1 Optional Agent Action Admission — PROVEN RESIDUE

Current code contains an optional stronger binding from external cognition evidence to exact Game Intent admission.

But outside its implementation/tests there is no production caller of:

```text
enableAgentActionAdmission(...)
```

Observed maintenance surface:

```text
agent-action-admission.ts       103 lines
dedicated test                 312 lines
```

This does not mean the research result was useless. It proved an important boundary. It does mean the current Station Zero product does not consume the capability.

**Next experiment:** remove/externally isolate it in a branch and prove current v3 product, live Provider boundary, recovery and E2E remain unchanged. If so, retain the lesson in Git/docs rather than the dormant product path.

## 17.2 Resource Egress / Message Issuance / Entity Departure — PROVEN RESIDUE

These three Game-local cross-owner protocol implementations have no current `src`, `scripts`, or `web-v3` production consumer beyond their own contract code/tests.

Observed implementation size:

```text
resource-egress.ts     275
message-issuance.ts    315
entity-departure.ts    344
```

They are valuable evidence from World/Game boundary research, but they are not currently part of Station Zero play.

**Next experiment:** prove that removing them from current Game product exports/build leaves every registered/v3 product behavior unchanged. Preserve cross-owner laws in World/Computing evidence rather than carrying dormant domain machinery indefinitely.

## 17.3 Embedded Host for every v3 Turn — DELETION EXPERIMENT REQUIRED

Current v3 Turn execution wraps Game-owned Planning/Turn evidence in another local semantic chain:

```text
TaskDescriptor
→ Effect / request
→ Dispatch
→ World executor
→ Observation
→ VerificationReceipt
→ TaskOutcome
```

But all substantive verification evidence is derived from:

```text
PreparedTurn
TurnBatch identity
World Event
Turn Record
Intent Resolutions
```

Response-loss recovery and duplicate-effect prevention are already anchored to exact Game Turn identity and retained World receipt.

`hostExecution` appears in the Mission Control data model, but the current `/v3` browser does not render Host/Dispatch/Verification semantics to the player. The Host chain mainly provides internal gating, audit structure and tests.

This makes it a serious deletion candidate, not an established defect.

**Required falsifier:** build a branch where v3 uses only Game-owned Planning + PreparedTurn + Turn Receipt for:

- next-Planning admission;
- response-loss reconciliation;
- exact no-redelivery behavior;
- restart recovery;
- verification;
- browser behavior.

If every current consequence/recovery property survives with a smaller state model, Embedded Host is duplicate ceremony for this local deterministic consumer. If one irreducible semantic continuity property disappears, keep the smallest Host responsibility that protects it.

## 17.4 DeepSeek credential/pool plumbing — OWNERSHIP PRESSURE

Game's actual semantic Provider interface is small:

```text
StationZeroV3AgentProvider.decide(context)
→ one Candidate identity already admitted by Game
```

Yet Game also owns roughly:

```text
deepseek-credentials.ts  580 lines
deepseek-provider.ts     553 lines
```

with tests for:

- secret-file permissions;
- directory hot-load;
- weighted scheduling;
- per-key semaphore;
- 429 cooldown;
- 401 quarantine;
- transport/server retry;
- usage accounting;
- pool health.

These are correct mechanics but mostly do not change Game meaning.

The Finance/Workstation/Harness pattern suggests a thinner semantic waist:

```text
Game owns:
  Agent Context
  legal Candidates
  Decision admission
  game-semantic feedback

provider/equipment layer owns:
  credentials
  transport
  pool scheduling
  retry/cooldown
  secret-file mechanics
```

However, moving code merely for architectural elegance is not justified. A migration should wait for an actual shared provider/equipment owner that reduces maintenance or serves a second consumer without weakening Game isolation.

## 17.5 `agent-planning.ts` — OWNERSHIP / COHESION PRESSURE

One 1,574-line file currently contains several distinct semantic responsibilities:

```text
legal Candidate generation
Rescue responsibility assignment
objective/responsibility semantic tagging
Agent Context compilation
Agent Decision admission
Fixture scoring
Pirate/Swarm baseline policy
Commander Order defaults/validation
player catalog copy
Commander action expansion
Faction Plan assembly
```

Not all of these should necessarily become separate files or packages. Physical splitting is not the goal.

The question is change coupling:

> Does changing one responsibility force unrelated policy/product/admission code to move or retest together?

A later refactor is justified only if measured G5 work demonstrates that this coupling creates repeated friction or ownership confusion.

## 17.6 Stage-era documentation — FUTURE CONTRACTION, NOT NOW

Current v3 documentation remains large:

```text
P0               314 lines
P1               420
P2               459
P3               544
Product           517
Vertical Slice    437
Product Value     790
Development       697
```

Much of this is useful because v3 is still an unregistered replacement target and its historical gates explain why current boundaries exist.

But `DEVELOPMENT_MODEL.md` already warns that P0/P1/P2/P3/GX/R-series work decomposition must not become the permanent product architecture.

If v3 becomes the registered Station Zero product, the surviving current contract should be compressed into:

```text
Product
Architecture
Authority
source/tests
```

and completed stage documents should be archived/deleted where Git history is sufficient.

Do not perform this contraction before the v2↔v3 replacement decision.

## 17.7 v2 + v3 dual product paths — TEMPORARILY JUSTIFIED

The dual path is currently real authority, not dead sentiment:

```text
v2 = registered product
v3 = unregistered G5 target
```

After the bounded G5 production proof, direct v2↔v3 comparison should become high priority. If v3 earns registration, delete the old v2 approval/product path rather than keeping indefinite dual architecture.

---

# 18. What Game should not copy from other projects

Cross-project learning is not feature shopping.

Do **not** import:

- Runtime Job/Attempt machinery into gameplay merely because execution is consequential;
- Host Task semantics for every Game object;
- Harness WorkingSet as universal NPC memory;
- World Resource/Message/Entity protocols unless an actual external trajectory exists;
- Security evidence planes as a generic trust/reputation system;
- Finance's seven-domain surface as a Game menu taxonomy;
- Workstation capability registries as gameplay equipment architecture;
- Studio review packets as Game World state;
- Computing's research loop as a production service/controller;
- Human research templates as mandatory playtest bureaucracy.

Transfer the **problem-solving law**, not the historical implementation.

---

# 19. What Game can consume immediately without code expansion

Several results change how future Game work should be judged now.

## 19.1 Every new system must name the inequality it protects

Examples:

```text
Preview persistence protects:
  player-reviewed plan ≠ recomputed model plan

Faction Knowledge protects:
  World truth ≠ what this faction knows

Turn Record protects:
  committed intention ≠ authoritative resolution
```

If a proposed object has no such irreducible distinction, deletion pressure should be immediate.

## 19.2 Every research change gets a transfer test

A Game reform should not be called recursive improvement because its own test passes.

Ask:

```text
Did a later independent encounter / provider / product task consume it?
Did owner-native Game outcome improve?
Did the benefit survive without answer compilation or evaluator leakage?
```

## 19.3 Prefer owner/world re-observation over durable process state

Before adding another planning/progress object:

```text
Can exact identity + current Game World + retained consequence evidence
reconstruct what remains to do?
```

If yes, persistence needs a stronger argument.

## 19.4 Compress Agent-facing semantics before adding cognition

The model should reason about:

```text
mission intent
known situation
legal options
risk/tradeoffs
responsibility
feedback
```

not credential pools, Host transcript stages, SQLite rows or transport mechanics.

## 19.5 Human attention follows decision relevance

The player/human owner should not have to understand every internal improvement. Surface the abstraction when it changes a real command/product decision; externalize implementation detail when evidence remains trustworthy.

---

# 19.6 First consumption result — GC1 dormant-surface contraction

The first owner-local consumption experiment was run after this synthesis instead of treating the hypotheses above as refactor authorization.

GC1 removed four dormant research surfaces from the experimental Game branch:

```text
Resource Egress
Message Issuance
Entity Departure
Optional exact Agent Action Admission
```

The first three had no current product caller outside their own implementation/tests. Agent Action Admission was more deeply embedded—two SQLite tables plus conditional commit/reopen verification—but `enableAgentActionAdmission()` had no production caller, so the hot-path check was always a no-op in the actual v3 product.

Combined contraction:

```text
source / persistence / dedicated-test maintenance removed: 2132 lines
remaining repository tests:                              297 / 297 PASS
v3 20-Turn browser E2E:                                 PASS
browser errors:                                          []
```

The earlier Resource/Message/Entity research remains useful evidence about cross-owner consequence boundaries, and the Agent Action work remains useful evidence that Provider choice is not Game action authority. What failed the deletion test was **continued product ownership of the dormant implementations**, not the historical research result.

Therefore GC1 upgrades those four candidates from `PROVEN RESIDUE` to:

```text
CONTRACTION ACCEPTED in the experimental Game branch
```

Canonical integration remains revision-fenced and is still separate from this research document's original observation table.

---

# 20. Recommended next Game sequence

This study changes the order of work.

Do **not** resume G5 content production immediately.

First run a bounded **Game Contraction / Responsibility Audit**:

```text
GC0  establish current product/recovery baseline

GC1  dormant capability deletion probes        DONE experimentally
     - Agent Action Admission
     - Resource Egress
     - Message Issuance
     - Entity Departure

GC2  Embedded Host ablation
     compare full current v3 Turn path
     vs Game-owned Planning/Turn evidence only

GC3  semantic-waist audit
     determine whether DeepSeek credential/pool mechanics
     can remain below a provider/equipment boundary without migration theater

GC4  planning cohesion audit
     measure change/test coupling before any file split

GC5  rerun product/recovery/live gates
     retain only contractions that preserve or improve owner-native outcomes
```

Only after GC0–GC5 should Game return to the bounded G5 Content Grammar proof.

The priority is not LOC reduction. It is to enter production with the smallest architecture that still preserves:

```text
authoritative consequence
bounded knowledge
player commitment
recovery under uncertainty
Agent accountability
product legibility
```

---

# 21. Explicit non-goals

This study does not authorize:

- a new cross-project self-improvement controller;
- a universal Ordivon state machine;
- a shared global Evidence/Trust/Memory service;
- deleting Runtime/Host/Harness/World boundaries from their owning projects;
- migrating Game Provider code without a real owner/consumer pressure;
- deleting v3 durability objects solely because there are many of them;
- replacing Product Value work with architecture cleanup indefinitely;
- treating code reduction as product value;
- delaying all G5 content until every architectural question is philosophically resolved.

The correct stopping rule for contraction is the same as elsewhere:

> Stop when the remaining structure has a named responsibility, survived a relevant falsifier, and further removal would lose owner-native value or cost more than it clarifies.

---

# 22. Current synthesis

The strongest Ordivon pattern is surprisingly simple:

```text
reality
→ bounded observation
→ bounded decision
→ explicit consequence boundary
→ owner-native consequence
→ independent reconciliation
→ contraction
→ later transfer test
→ reality again
```

The sophistication is not in having many stages. It is in refusing the easy collapses between them.

For Game, the current lesson is therefore not “add more self-improvement machinery.” It is almost the opposite:

> Station Zero already contains many of Ordivon's mature laws. The next useful self-loop is to ask which research-era mechanisms no longer need to remain inside the product now that those laws are understood.

That is the bridge from a research-rich prototype to a production-capable game.
