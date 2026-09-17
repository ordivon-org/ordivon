---
schema_version: 1
id: game.domain-package-graph.r1
title: Ordivon Game Domain Package Graph R1
type: architecture-projection
profile: engineering
lifecycle: active
source_role: derived-navigation
visibility: public
owners:
  - ordivon-game
updated: 2026-09-17
summary: Machine-readable Lego decomposition of stable Game-domain semantics, responsibilities, mechanics, compositions, tools, Skills, horizontal dependencies, and first-class constraints without becoming a second task or product authority.
evidence_status: verified
readiness: READY
---
# Ordivon Game Domain Package Graph R1

## 1. Purpose

This document is the human-readable companion to [`../standards/game_domain_package_graph_r1.json`](../standards/game_domain_package_graph_r1.json).

The graph makes the current Game domain package decomposable like Lego:

```text
semantic kernel
  -> foundations
  -> development responsibility views
  -> product-stage commitments
  -> mechanics
  -> compositions
  -> concrete products / experiments
  -> Skills + thin Game adapters
  -> horizontal service owners
```

It is a **projection of existing authority**, not a new authority system. It does not select a product, admit a G-stage, rank work, assign priority, replace Host, or claim current provider/tool health.

Dynamic Task/Goal/checkpoint/Board standing remains owned by **Host plus the relevant domain owner** and must be re-entered when action depends on it. Current code/tool/provider standing likewise requires owner-native re-entry rather than reading this graph as a live registry.

## 2. Lego record shape

Every stable node should be understandable through the same minimal questions:

| Field | Question |
|---|---|
| `id` | What exact Lego block is this? |
| `kind` | Kernel, foundation, responsibility, stage, mechanic, composition, product/experiment, Skill, Game tool, or horizontal service? |
| `owner` | Who has semantic or service authority? |
| `authority` | What may this block actually decide, when non-obvious? |
| `refs` | Which source-owned records define or evidence it? |

Relations answer a different question and remain explicit: `constrains`, `routes-to`, `depends-on`, `composes`, `realizes`, `evidences`, `advises`, `executes-through`, `projects`, and `validates-with`.

A dependency edge therefore does **not** imply semantic ownership. For example, Game may execute through Runtime while retaining Game consequence semantics, or route D4 player evidence to Research without Research selecting the product.

## 3. Core layers

### 3.1 Semantic Kernel

Only four shared Game primitives are treated as kernel nodes:

```text
WORLD / STATE
    -> OBSERVATION
    -> ACTION
    -> TRANSITION / CONSEQUENCE
    -> WORLD' / STATE'
```

Inventory, combat, quests, economy, crafting, dialogue, NPC AI, physics, reputation, skill trees, maps, cards and narrative structures are composition-layer state/action/transition structures unless a concrete reopen case proves otherwise.

### 3.2 Foundations

The graph currently exposes four frozen foundation packages directly:

- Play / Game Deep Foundations;
- Action / Control / Skill Foundations;
- Challenge / Failure / Mastery Foundations;
- Authoritative Case Determination Foundations.

They are semantic foundations, not MCP servers or runtime frameworks.

### 3.3 D1-D8 development responsibilities

D1-D8 is a concurrent routing/evidence view:

```text
D1 Intent / Audience Context
D2 Play Causality
D3 Player Learning / Legibility
D4 Evidence / Prototyping
D5 Content / Progression Architecture
D6 Expression / Feel
D7 Production Realization
D8 Product Ecology / Evolution
```

### 3.4 G0-G8 commitment stages

G0-G8 remains the separate Game-specific commitment projection from Define through Release/Operate/Learn. A project can be at one stage while different D-axes have very different evidence strength. Stage standing must not wash out those differences.

### 3.5 Reusable mechanics and compositions

The first explicit reusable mechanic nodes are E01 Counterfactual Probe, E02 Transfer Route and E03 Commitment Lag. Their current graph-level claim ceiling is mechanical only.

PC01 Causal Works, PC02 Persistent Workshop and PC03 Loop Cartographer are composition nodes over the shared kernel. A mechanic may be composed into a candidate, discovered to be already subsumed, or rejected as a bad fit; surviving a mechanic falsifier does not force mechanic pile-up.

## 4. Constraint Taxonomy

Constraints are first-class records rather than prose comments attached to arbitrary nodes. Each constraint has an identity, type, explicit scope, substantive statement, source refs, and a failure disposition.

### 4.1 Authority

**Question:** who may decide or mint this truth?

Examples:

- Game owns Game-local state/action/consequence meaning;
- Provider cognition may propose but not mutate World directly;
- Host owns durable work continuity, not Game truth;
- Research owns method/evidence admissibility in its scope, not product selection.

### 4.2 Invariant

**Question:** what must remain true across replacement or refactoring?

Examples:

- the shared Game kernel remains four primitives;
- model prose cannot bypass action admission;
- D1-D8 responsibility standing cannot be collapsed into G-stage labels.

### 4.3 Admission

**Question:** what must be demonstrated before adding or promoting something?

Examples:

- product mechanics do not become Big Game shared code just because several files need a home;
- generic infrastructure requires an exact external-substitution failure plus a named lost Game invariant;
- changing shared Game Core has a much higher bar than trying a local mechanic.

### 4.4 Evidence

**Question:** what kind of evidence can support which target variable?

Automated mechanics, simulation, synthetic subjects and model trajectories can prove bounded mechanical properties. They cannot be relabeled as Human enjoyment, preference, interpretation, retention or market response.

### 4.5 Claim Ceiling

**Question:** what is the strongest statement the current evidence permits?

Examples:

- E01-E03 KEEP is mechanical-scope only;
- PC01-PC03 evidence does not by itself select a product or enter G0;
- an Artifact or beautiful render does not establish Player Value.

### 4.6 Currentness

**Question:** when must a source or owner be re-entered before acting?

This graph is deliberately **not** a live health/status registry. Historical refs preserve provenance, but current code head, provider admission, Task standing, tool health and accepted experimental standing require exact owner-native re-entry when materially used.

### 4.7 Forbidden Substitution

**Question:** what tempting proxy must never be silently treated as another authority or evidence class?

Examples:

- credential != effect authority;
- synthetic subject != Human participant;
- Host/Board persistence != domain truth;
- render/file existence/provider completion != semantic correctness.

### 4.8 Reopen Condition

**Question:** what concrete observation is strong enough to reopen a frozen foundation or ownership boundary?

A new engine, controller, genre, model, accessibility feature or Agent architecture is not enough by itself. Reopen requires a counterexample that defeats the frozen responsibility boundary or shows a real Game consumer cannot preserve a required invariant through the current owner/profile/adapter.

### 4.9 Replaceability

**Question:** what may change without redefining Game semantics?

Engines, model providers and advisory Skills are explicitly replaceable. Replacement must preserve the Game-facing contract and evidence boundary; it does not earn the right to redefine Game Core.

## 5. Constraint stack around a Lego block

A useful block is not just `Node(id, owner)`. Operationally it is:

```text
Block
  + authority boundary
  + invariants
  + admission preconditions
  + evidence contract
  + claim ceiling
  + currentness requirement
  + forbidden substitutions
  + reopen conditions
  + replaceability boundary
```

For example, `mechanic.e03` is not merely “Commitment Lag”. It is also constrained by:

```text
mechanical evidence only
no automatic Human-value claim
no forced composition into every product
no Game-Core expansion unless the local mechanic representation fails
exact tested semantics remain provenance-bound
```

This is the main reason constraints are stored independently: the same constraint can scope multiple blocks without duplicating or drifting prose.

## 6. Horizontal service boundary

The graph treats the following as external service owners rather than Game submodules:

```text
Research      -> scientific / Human evidence composition
Runtime       -> physical execution truth
Host          -> durable work continuity
Harness       -> Agent cognition / Provider continuity
Workstation   -> equipment / desired state / node operations
Artifact      -> artifact build / validation / delivery evidence
Media/Studio  -> representation / authoring / production
Distribution  -> external effect / release boundary
Network       -> connectivity / egress
Security      -> security evidence / admission context
Next          -> external authority / policy / capability knowledge
```

These are architecture/service relations, not npm-import requirements.

## 7. Skills and tools

The Skill plane is represented as advisory procedure. Skill installation, admission, visibility or invocation does not transfer Game semantic authority.

Game-owned root tools stay deliberately thin:

- `external-json-model.ts` — Game-facing JSON decision adapter;
- `browser-equipment.ts` — Workstation equipment binding;
- `canonical-digest.ts` — repository-mechanical identity helper.

The absence of a Game-owned scheduler, provider pool, engine installer, universal persistence framework or release manager is intentional.

## 8. How to extend the graph

Before adding a node, ask:

1. Is this actually a new stable responsibility or only an instance/configuration of an existing block?
2. Who is the natural owner?
3. Which existing node cannot represent the required semantics?
4. Which constraint applies, and does it already forbid/promote this move?
5. What source-owned record supports the node?
6. Is the information stable architecture, or should it stay in Host/current owner standing instead?

Before adding a new shared Game node, prefer `composition` over `kernel`, and prefer an external service/profile/adapter over new generic Game infrastructure.

## 9. Non-goals

R1 does not create:

- a universal Ordivon ontology;
- a second Task/Goal/Board database;
- a product selector;
- a G-stage state machine;
- a live dependency health registry;
- a Skill registry replacement;
- a tool/plugin package format;
- a generic game engine framework.

Its job is narrower: make the current Game domain package **decomposable, queryable and constraint-aware** while preserving the authority boundaries already earned elsewhere.


## 10. Constraint Interaction Graph

The machine graph now separates three things that were previously easy to conflate:

```text
constraint identity
    + enforcement profile
    + relation to other constraints
```

This makes it possible to ask not only “which constraint applies?” but also “what kind of constraint is it, what happens when its truth is unknown, what evidence can affect it, and which authority must still decide after that evidence exists?”

### 10.1 Enforcement profiles

Every constraint has exactly one enforcement profile:

| Profile | Meaning | Default when unresolved |
|---|---|---|
| **Hard Invariant** | Must remain true until an explicit reopen path succeeds. | Preserve the invariant. |
| **Authority Boundary** | Defines who may mint or decide a truth/effect. | Block authority transfer. |
| **Admission Gate** | Preconditions that must be satisfied before promotion/change. | Block admission. |
| **Evidence Gate** | Requires target-matched evidence before a claim can be raised. | Keep unknown or lower the claim. |
| **Claim Fence** | Caps what current evidence is allowed to imply. | Keep the lower claim. |
| **Currentness Fence** | Requires exact owner-native re-entry before action-changing use. | Re-enter the owner. |
| **Substitution Ban** | Rejects proxy equivalence such as credential=authority. | Reject the substitution. |
| **Reopen Trigger** | Defines what can justify reviewing a frozen boundary. | Keep the boundary frozen. |
| **Replaceability Boundary** | Allows implementation/provider replacement behind a preserved contract. | Keep the current proven owner contract. |

These profiles are not a priority ranking. A `Claim Fence` is not “weaker” than a `Hard Invariant`; it governs a different question.

### 10.2 Constraint-to-constraint edges

The graph uses typed directional relations:

```text
preconditions
strengthens
narrows
triggers
blocks
reopen-enables
potential-conflict
requires-adjudication-after
```

For example:

```text
synthetic-not-human
    --strengthens-->
mechanical-not-human
    --narrows-->
mechanic-wave claim ceiling

core-primitive-high-bar
    --preconditions-->
foundation reopen
    --reopen-enables-->
kernel-minimality review
```

`reopen-enables` deliberately means **review becomes admissible**, not “the old invariant is now false.”

Likewise, `potential-conflict` names a conditional design tension, not a contradiction in repository truth. For example, engine replaceability and prototype-medium adequacy can pull in different directions if the cheapest valid evidence carrier is not the currently proven production engine. That case requires a bounded decision, not an automatic winner.

### 10.3 Evidence Discharge

Evidence discharge is intentionally narrow. The graph recognizes reusable evidence classes such as mechanical-causal evidence, Human participant evidence, owner-currentness evidence, external-substitution mismatch, cross-product consumers, semantic counterexamples, native-consumer verification, and explicit effect authority.

Evidence may have only one of these graph-level effects:

```text
satisfies-gate
permits-reentry
permits-reopen-review
narrows-claim
supports-adjudication
does-not-discharge
```

A crucial invariant is:

> **Evidence does not become Authority.**

A test result, Human session, external mismatch, second product consumer, native render, or authenticated credential may change what review is admissible or what claim is supportable. It does not by itself mint product authority, ownership transfer, release authority, World mutation authority, or a new Game Core.

Hard Invariant constraints are therefore never silently discharged by ordinary evidence. Counterexample evidence may permit an explicit reopen review; the relevant authority must still commit a new decision before the old invariant stops governing.

The same distinction applies to effect authority: explicit Distribution/user effect authority can authorize a concrete effect, but that does not make a provider credential equivalent to effect authority. The substitution ban stays true.

### 10.4 Authority Adjudication

Some interactions end in an explicit authority decision rather than a purely mechanical rule. R1 records bounded adjudication contracts for four recurring cases:

```text
external-owner extension / ownership-boundary reopen
prototype medium vs current engine substrate
cross-game shared-code promotion
provider replacement vs Game action authority
```

Each adjudication rule declares:

```text
interacting constraints
named authority owner(s)
bounded decision question
fail-safe default if unresolved
source authority refs
```

The fail-safe defaults are deliberately conservative: keep the external owner, keep the current proven substrate while lowering the claim, keep product-specific code local, or reject a provider replacement path that would bypass Game action/consequence authority.

This does not create a generic arbitration service. The graph only states **where the decision belongs** and what must remain true while it is unresolved.

### 10.5 Why this matters for the Lego model

The Game domain can now express composition legality as a graph rather than relying on maintainer intuition:

```text
Node / Lego block
    ↓
applicable constraints
    ↓
constraint profiles
    ↓
constraint relations
    ↓
required evidence / currentness
    ↓
optional reopen or adjudication
    ↓
admitted composition / lower claim / blocked path
```

That is still not a rule engine. R1 deliberately stops before automatic semantic adjudication. The graph is a machine-readable **decision-support and falsification structure**; actual semantic commitment remains with the authority-owning Game/Research/Host/Runtime/Workstation/Artifact/Distribution surface named by the relevant record.


## 11. Composition Legality / Decision Trace evaluator

The repository exposes a thin evaluator at [`../scripts/composition-legality.ts`](../scripts/composition-legality.ts). Its job is to execute the graph projection, not to become a new semantic authority.

Example:

```bash
pnpm decision:composition -- \
  --operation compose \
  --nodes mechanic.e03,composition.pc02 \
  --evidence evidence.mechanical-causal
```

The machine result includes:

```text
involved nodes
applicable constraints
hard invariants
authority boundaries
claim fences
unsatisfied gates
required evidence classes
reopen reviews
authority adjudication rules
relevant constraint-relation edges
a deterministic explanation trace
```

The graph itself declares the supported operation profiles and their constraint seeds/gates. The evaluator therefore does not hide product policy in TypeScript. R1 supports these bounded operations:

```text
compose
promote-shared-core
claim-human-value
select-product
enter-g0
replace-provider
replace-engine
external-effect
```

The output disposition vocabulary is deliberately narrow:

```text
NO_GRAPH_BLOCK
NO_GRAPH_BLOCK_WITH_FENCES
BLOCKED_PENDING_EVIDENCE_OR_ADJUDICATION
AUTHORITY_ADJUDICATION_REQUIRED
```

`NO_GRAPH_BLOCK` does **not** mean “approved”, “true”, “selected”, “released”, or “safe to perform any external effect”. It means only that this exact graph projection found no unresolved graph-level gate for the bounded request. The trace always reports `semanticAuthorityClaimed=false`, `productSelected=false`, and `g0Entered=false` because those truths cannot be minted by this evaluator.

For the concrete `E03 -> PC02` composition request, mechanical evidence can leave the composition structurally unblocked while retaining both the mechanic-wave mechanical claim ceiling and the pre-G0 product-selection fence. Asking instead to promote that composition into shared Game Core activates the cross-game-promotion gate and core-primitive high bar; cross-product-consumer and semantic-counterexample evidence can permit review/adjudication, but still cannot auto-promote the core.

Currentness is equally explicit: the evaluator binds the exact workspace graph digest and reports `WORKSPACE_GRAPH_ONLY_NOT_LIVE_OWNER_STATE`. Any decision that depends on live Task, provider, tool, release, participant-study, or service standing must still re-enter the natural owner named by the graph.
