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
