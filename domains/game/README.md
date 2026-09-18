---
schema_version: 1
id: game.start
title: Ordivon Game
type: start
profile: organization
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-game
audience:
  - player
  - designer
  - builder
  - agent
updated: 2026-09-12
summary: Canonical entry to Ordivon Game, its cross-game development model, current Station Zero executable, research treatments, and the R1–R29 foundations corpus without selecting a new product.
evidence_status: verified
readiness: READY
applies_to:
  - ordivon-game
related:
  - game.product.station-zero
  - game.product.station-zero-v3
  - game.product.station-zero-v3.vertical-slice
  - game.architecture
  - game.vision
  - game.development-model
  - game.authority
---
# Ordivon Game

## Purpose

**Authoritative interactive worlds for people and Agents.**

Ordivon Game currently ships one executable world: **Station Zero**, a deterministic multi-Agent mission game. The player commands Engineer, Medic, and Security specialists through standing doctrine and consequential interventions rather than moving units directly.

## Current boundary

The registered executable remains Station Zero `station-zero@2` with Ruleset `station-zero-core@3`. Station Zero v3, Casefile, Last Light, Echo Hunt, Concept Lab and Pre-G0 playables are retained as **Game Core research / regression apparatus**, not candidate product momentum. No new Ordivon Game product has been selected. D1–D8, G0–G8 and the four-part minimal interaction model are now optional repository-local Skills rather than canonical Game process or ontology. Creative composition defaults open; evidence and external effects remain separately bounded.

## Start here

- [`docs/PRODUCT.md`](docs/PRODUCT.md) defines the current Station Zero product and player experience.
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) defines the current Station Zero v2 product architecture and state ownership.
- [`docs/GAME_E2E_OWNERSHIP_BOUNDARY.md`](docs/GAME_E2E_OWNERSHIP_BOUNDARY.md) defines what Big Game may own and forbids promoting product mechanics into a generic Game framework without cross-product evidence.
- [`docs/GAME_DOMAIN_PACKAGE_GRAPH_R1.md`](docs/GAME_DOMAIN_PACKAGE_GRAPH_R1.md) is the creative-open Game knowledge graph: products, experiments, mechanics/compositions, advisory Skills, teardown-derived mechanism-combination patterns, evidence fences, tools and horizontal service dependencies.
- [`docs/GAME_EXTERNAL_KNOWLEDGE_BASE_R1.md`](docs/GAME_EXTERNAL_KNOWLEDGE_BASE_R1.md) is the external knowledge entry: standards, accessibility, design/research models, engine practice, primary developer teardowns and external Agent Skills are source-scoped and routed into optional lenses, mechanism patterns, experiments or owner-native practice rather than new Game law. Machine sources are `standards/game_external_knowledge_base_r1.json`, `standards/game_teardown_queue_r1.json` and `standards/game_external_skill_watchlist_r1.json`; `pnpm knowledge:external -- --type sources|teardowns|skills ...` is a retrieval-only query surface.
- [`docs/GAME_MECHANISM_EXPERIENCE_LIBRARY_R1.md`](docs/GAME_MECHANISM_EXPERIENCE_LIBRARY_R1.md) decomposes primary-source teardowns into fine-grained mechanism interactions, tensions, inversions, substitutions, failure modes and production responses, each with confounds, transfer risks, a falsifier and cheap probe. Query with `pnpm knowledge:mechanisms -- ...`; composition exploration may recall matches, but they remain advisory hypotheses and never block novel combinations.
- [`docs/GAME_MECHANISM_RELATIONSHIP_GRAPH_R1.md`](docs/GAME_MECHANISM_RELATIONSHIP_GRAPH_R1.md) derives cross-game mechanism co-occurrence, non-exhaustive retrieval facets and source-grounded Conditionalities from the Experience Library. `pnpm knowledge:relationships -- ...` retrieves them; `pnpm build:relationship-graph` deterministically rebuilds the graph from the authored relationship spec plus Experience Library. It provides apparent conflicts and cheap discriminators, never compatibility verdicts.
- [`docs/GAME_DESIGN_COUNTEREXAMPLE_MEMORY_R1.md`](docs/GAME_DESIGN_COUNTEREXAMPLE_MEMORY_R1.md) retains rejected, removed, cancelled, redesigned and conditionally successful choices as contextual counterexamples. Query with `pnpm knowledge:counterexamples -- ...`; matches expose failed assumptions and cheap discriminators, never anti-pattern law, ranking, blacklist or creative rejection.
- [`docs/GAME_COUNTEREXAMPLE_SYNTHESIS_R1.md`](docs/GAME_COUNTEREXAMPLE_SYNTHESIS_R1.md) adds eight overlapping, non-exhaustive retrieval themes across Counterexamples. Query with `pnpm knowledge:counterexample-themes -- ...`; themes group recurring failure structures for retrieval only and cannot classify exhaustively, rank designs, recommend fixes, or block novel combinations.
- [`docs/GAME_WHOLE_PRODUCT_RECOMPOSITION_R1_20260918.md`](docs/GAME_WHOLE_PRODUCT_RECOMPOSITION_R1_20260918.md) applies that memory back onto PC01/PC02/PC03 and E01/E02/E03 through four bounded recomposition falsifiers. Current exact mechanical standing is R01/R02 subsumed, R03 conditional survivor, R04 no-fit; `productSelected=false`, `G0=false`, and Human claims remain unobserved.
- [`experiments/product-composition-r1/pc01-e03-playable-r1/README.md`](experiments/product-composition-r1/pc01-e03-playable-r1/README.md) realizes the sole R03 survivor as **Causal Lag Lab**, a bounded playable where current diagnosis informs a one-step delayed commitment under a visible next-context forecast. Mechanical acceptance keeps forecastability and cause persistence independently falsifiable; it remains `productSelected=false`, `G0=false`, with Human value unobserved.
- [`experiments/product-composition-r1/pc01-e03-multiround-r2/README.md`](experiments/product-composition-r1/pc01-e03-multiround-r2/README.md) extends Causal Lag Lab into a four-round **Memory Run**. Resolved cause transitions become the only player-visible history; a hidden run-level stability process makes past outcomes mechanically relevant to later information value, while posterior/model probabilities remain private to the falsification oracle. `humanLearningEstablished=false`, `productSelected=false`, `G0=false`.
- [`experiments/product-composition-r1/causal-lag-session-r3/README.md`](experiments/product-composition-r1/causal-lag-session-r3/README.md) closes the first **stateful session** layer: player architecture and latent cause now persist across chained contexts, scan/switch costs accumulate against one four-round contract, and the browser exposes explicit `SUCCESS` / `FAILURE` end states. It remains an experimental candidate rather than a registered product.
- [`docs/VISION.md`](docs/VISION.md) defines the broader Game direction without turning possibilities into commitments.
- [`docs/GAME_FRONT_HALF_EXTERNAL_REFERENCE_PROFILE.md`](docs/GAME_FRONT_HALF_EXTERNAL_REFERENCE_PROFILE.md) is an optional comparable-game discovery profile; teardown and controlled experiments are available techniques rather than mandatory product admission.
- [`docs/GAME_R0_SUCCESS_UNIVERSE_20260911.md`](docs/GAME_R0_SUCCESS_UNIVERSE_20260911.md) owns the current R0-A/R0-B success-universe census and archetype coverage: external success surfaces are observed before feasibility filtering and are never collapsed into one fake global rank.
- [`docs/GAME_R0_REFERENCE_STACKS_20260911.md`](docs/GAME_R0_REFERENCE_STACKS_20260911.md) owns current R0-C: flagship/canonical/cheap-causal stacks and the broad R1 reference-teardown admission.
- [`docs/GAME_R1_REFERENCE_TEARDOWN_WAVE1_20260911.md`](docs/GAME_R1_REFERENCE_TEARDOWN_WAVE1_20260911.md) owns the current twelve-game R1 desk teardown: observed product facts are separated from causal hypotheses/confounds and small falsifiable baselines; direct-play experience claims remain pending and R2 implementation is not admitted.
- [`docs/GAME_R1_DIRECT_PLAY_ACCESS_20260911.md`](docs/GAME_R1_DIRECT_PLAY_ACCESS_20260911.md) owns the current direct-play access census and participant-evidence access boundary; [`docs/GAME_R1_DIRECT_PLAY_OBSERVATION_SHEET.md`](docs/GAME_R1_DIRECT_PLAY_OBSERVATION_SHEET.md) is the blank session carrier. No download, purchase, account sign-in or Human evidence is implied by their existence.
- [`docs/GAME_R0_EXTERNAL_REFERENCE_CLASS_20260911.md`](docs/GAME_R0_EXTERNAL_REFERENCE_CLASS_20260911.md) is the superseded first R0 attempt. Its Balatro / Vampire Survivors / Mini Metro set is retained only as cheap-baseline learning support.
- [`skills/game-stage-lens/SKILL.md`](skills/game-stage-lens/SKILL.md) packages G0–G8 as an optional disposable coordination lens; [`docs/DEVELOPMENT_MODEL.md`](docs/DEVELOPMENT_MODEL.md) is retained source/history.
- [`skills/game-development-lenses/SKILL.md`](skills/game-development-lenses/SKILL.md) packages D1–D8 as optional questions; [`docs/GAME_DEVELOPMENT_CORE.md`](docs/GAME_DEVELOPMENT_CORE.md) is retained source/history rather than a required methodology.
- [`docs/GAME_DEVELOPMENT_PARADIGM_RESEARCH.md`](docs/GAME_DEVELOPMENT_PARADIGM_RESEARCH.md) records the external-method comparison that motivated the stage-vs-core repair.
- [`docs/GAME_EXTERNAL_MATURE_PRACTICE_ADOPTION_R1.md`](docs/GAME_EXTERNAL_MATURE_PRACTICE_ADOPTION_R1.md) is the current external-first adoption policy: directly use mature standards and platform-native mechanisms within their scope, and keep only Game-specific profiles/semantics rather than rebuilding generic HCD, research, experimentation, lifecycle, provenance or release systems.
- [`docs/GAME_DEVELOPMENT_CASE_PRESSURE_TESTS.md`](docs/GAME_DEVELOPMENT_CASE_PRESSURE_TESTS.md) pressure-tests D1–D8 against real development histories rather than framework vocabulary alone.
- [`docs/GAME_CONTENT_PROGRESSION_ARCHITECTURE.md`](docs/GAME_CONTENT_PROGRESSION_ARCHITECTURE.md) is the current D5 construction model for aligning possibility, player-learning assumptions, content exposure/progression and sustainable production.
- [`docs/GAME_PLAYER_EVIDENCE_PROGRAMME.md`](docs/GAME_PLAYER_EVIDENCE_PROGRAMME.md) is the current claim-relative player-evidence ecology: subject, method, measure, horizon, population transport and causal scope stay separate.
- [`docs/GAME_PRODUCTION_AGENT_ENVIRONMENT.md`](docs/GAME_PRODUCTION_AGENT_ENVIRONMENT.md) compares current Unity/Unreal/Roblox/Godot production environments and defines consume/adapt/fork/own pressure for Agent-first development without making Game an engine/editor owner.
- [`research/README.md`](research/README.md) is the thin canonical Game research entry point: current GDF0–GDF3, practical GPR reconstruction, coverage/frontier, R/F genealogy, negative/superseded history, and product/direction research are separated without moving the underlying evidence tree.
- [`docs/STATION_ZERO_V3_CONTRACTION.md`](docs/STATION_ZERO_V3_CONTRACTION.md) records only Game-local contraction verdicts and reopen conditions; cross-project synthesis stays in Ordivon Computing.
- [`docs/GAME_CORE_RESEARCH_RESET.md`](docs/GAME_CORE_RESEARCH_RESET.md) preserves the historical reset that once used G0–G8 as lifecycle vocabulary; current creative work is not stage-gated by it.
- [`docs/GAME_FOUNDATIONS_RESEARCH_R1_R17.md`](docs/GAME_FOUNDATIONS_RESEARCH_R1_R17.md) preserves the complete first seventeen foundation rounds across game form, mechanics, loops, player value, world, subjects, agency, time, economy, society, topology, and information without selecting a product.
- [`docs/GAME_FOUNDATIONS_RESEARCH_R18.md`](docs/GAME_FOUNDATIONS_RESEARCH_R18.md) decomposes Need, Desire, Value, Preference, Utility, Goal and Commitment, defines minimum-sufficient motivational structures across game forms, and introduces Playable Motivation without selecting a product.
- [`docs/GAME_FOUNDATIONS_RESEARCH_R19.md`](docs/GAME_FOUNDATIONS_RESEARCH_R19.md) decomposes strategic interdependence, conflict, competition, cooperation, coordination, bargaining, negotiation, commitment, reputation and equilibrium, and introduces Playable Strategy without selecting a product.
- [`docs/GAME_FOUNDATIONS_RESEARCH_R20.md`](docs/GAME_FOUNDATIONS_RESEARCH_R20.md) decomposes Creation, Creativity, Construction, Expression, Authorship, Customization, Style, Tool, Material, Constraint, Grammar, Curation and Co-creation, and introduces Authorial Causality, Creative Contribution Topology, Playable Creation and Playable Expression without selecting a product.
- [`docs/GAME_FOUNDATIONS_RESEARCH_R21.md`](docs/GAME_FOUNDATIONS_RESEARCH_R21.md) decomposes Embodiment, Body, Avatar, Control Locus, Input, Command, Delegation, Skill, Affordance, Responsiveness, Game Feel and Presence, and introduces Action Causality, Intent Fidelity, Control Contribution Topology, Playable Control and Playable Embodiment without selecting a product.
- [`docs/GAME_FOUNDATIONS_RESEARCH_R22.md`](docs/GAME_FOUNDATIONS_RESEARCH_R22.md) decomposes Uncertainty, Probability, Randomness, Ambiguity, Risk, Luck, Variance, Determinism, Predictability and Fairness, and introduces Uncertainty Topology, Outcome Contribution Topology, Distributional Agency, Uncertainty Contract, Playable Uncertainty and Playable Risk without selecting a product.
- [`docs/GAME_FOUNDATIONS_RESEARCH_R23.md`](docs/GAME_FOUNDATIONS_RESEARCH_R23.md) decomposes temporal frames, sequence/order, simultaneity/concurrency, duration/timing/tempo/rhythm, turns/phases/ticks, windows/deadlines, waiting, persistence and reversibility, and introduces Temporal Causality, Temporal Agency, Temporal Contract and Playable Temporality without selecting a product.
- [`docs/GAME_FOUNDATIONS_RESEARCH_R24.md`](docs/GAME_FOUNDATIONS_RESEARCH_R24.md) separates entity identity, self-model, character, persona, role, social identity, identifiers, recognition, status, rank, reputation and continuity, and introduces Continuity Profile, Identity Authority, Identity/Recognition Topology, Identity Causality, Playable Identity and Playable Continuity without selecting a product.
- [`docs/GAME_FOUNDATIONS_RESEARCH_R25.md`](docs/GAME_FOUNDATIONS_RESEARCH_R25.md) decomposes persistent relational state across directed, shared and institutional layers; separates attachment, care, intimacy, trust, reliability, commitment, loyalty, obligation, reciprocity, dependence, communal/exchange norms, rivalry, betrayal and repair; and introduces Relational Authority, Relationship Causality/Topology, Relational Contract/Affordance/Agency and Playable Relationship without selecting a product.
- [`docs/GAME_FOUNDATIONS_RESEARCH_R26.md`](docs/GAME_FOUNDATIONS_RESEARCH_R26.md) decomposes Affect, Emotion, Feeling, Mood, Valence, Arousal, Appraisal, Action Tendency, Regulation, Expression and Empathy; emotion is a coordinated temporal episode rather than one scalar, and affective state becomes gameplay only through causal future differences.
- [`docs/GAME_FOUNDATIONS_RESEARCH_R27.md`](docs/GAME_FOUNDATIONS_RESEARCH_R27.md) synthesizes Learning, Adaptation, Memory, Belief Revision, Skill/Habit, Personality and Self-model as Persistent Subject Change, with explicit update targets, authority, provenance, causality, contracts and playable learning/adaptation.
- [`docs/GAME_FOUNDATIONS_RESEARCH_R28.md`](docs/GAME_FOUNDATIONS_RESEARCH_R28.md) decomposes Culture, Convention, Custom, Tradition, Ritual, Symbol, Shared Meaning, Legitimacy, Collective Memory, cultural transmission/change and Subculture as distributed socially reproduced structure; introduces Cultural/Transmission/Legitimacy topology, Cultural/Ritual/Symbolic/Tradition causality, Cultural Agency and Playable Culture without selecting a product.
- [`docs/GAME_FOUNDATIONS_RESEARCH_R29.md`](docs/GAME_FOUNDATIONS_RESEARCH_R29.md) synthesizes and falsifies the R1–R28 corpus, freezes provisional Game Foundations v1 around nine semantic coordinate families, demotes recurring domain concepts to typed derived views where justified, compresses Playable/Causality/Topology/Authority/Contract families, and closes foundation expansion without selecting a product.
- [`docs/GAME_FOUNDATIONS_RESEARCH_MAP.md`](docs/GAME_FOUNDATIONS_RESEARCH_MAP.md) is the compact conceptual map for the R1–R29 foundations corpus and its cross-domain abstractions.
- [`docs/GAME_FOUNDATIONS_CONTINUATION.md`](docs/GAME_FOUNDATIONS_CONTINUATION.md) is the context-switch handoff; after R29 the foundation-expansion programme is provisionally frozen; the next product frontier is the external-reference front-half profile, with prior Pre-G0 search retained only as supporting research/apparatus.
- [`docs/GAME_PRE_G0_DIRECTION_SEARCH.md`](docs/GAME_PRE_G0_DIRECTION_SEARCH.md) records DS0, the first Pre-G0 direction-search surface and D01–D16 mechanism basis; its GameForm↔Agent coupling/search-priority semantics are superseded by the decoupling authority below.
- [`docs/GAME_PRE_G0_DS1_CHEAP_FALSIFIERS.md`](docs/GAME_PRE_G0_DS1_CHEAP_FALSIFIERS.md) records the first executable cheap-falsifier battery: D03/D04/D05/D14 structural survival, D02/D15 realization deletion/demotion, the D03 information-scarcity ablation, and the first negative evidence against unnecessary high-cost Agent cognition.
- [`docs/GAME_PRE_G0_FORM_AGENT_ROLE_DECOUPLING.md`](docs/GAME_PRE_G0_FORM_AGENT_ROLE_DECOUPLING.md) is retained as an anti-Agent-bias guard and GameForm/Agent-role coverage vocabulary under the external-reference front half; it no longer selects or prioritizes products.
- [`docs/GAME_PRE_G0_PLAYABLE_PROOF_PORTFOLIO.md`](docs/GAME_PRE_G0_PLAYABLE_PROOF_PORTFOLIO.md) is retained as reusable prototype/evidence apparatus under the external-reference front half; its C0/C1/C2 history does not replace claim-specific mature Human playtest practice or admit G0.
- [`docs/GAME_PRE_G0_PLAYABLE_WAVE1_APPARATUS.md`](docs/GAME_PRE_G0_PLAYABLE_WAVE1_APPARATUS.md) records the bounded automated A/D/I apparatus materialization and its exact non-claim boundary: mechanical browser evidence exists, while C0/C1 human Player Value evidence remains unobserved.
- [`docs/GAME_CORE_DIRECTION_SPACE.md`](docs/GAME_CORE_DIRECTION_SPACE.md) maps the early Core → Experience search space, missing dimensions, and experimental contract.
- [`docs/GAME_CORE_EXPERIMENT_FINDINGS.md`](docs/GAME_CORE_EXPERIMENT_FINDINGS.md) records what Station Zero, Casefile, Last Light, and Echo Hunt actually established without promoting a product winner.
- [`docs/GAME_CORE_EXPERIMENT_CASEFILE.md`](docs/GAME_CORE_EXPERIMENT_CASEFILE.md) retains exact Casefile engineering/blind-play evidence as an epistemic Game Core treatment.
- [`docs/STATION_ZERO_V3_PRODUCT.md`](docs/STATION_ZERO_V3_PRODUCT.md) preserves the stable human-facing v3 reference target and the historical G3/G4/G5 evidence produced by that programme.
- [`docs/STATION_ZERO_V3_VERTICAL_SLICE.md`](docs/STATION_ZERO_V3_VERTICAL_SLICE.md) preserves the historical machine/production slice, calibration evidence, and then-current G4 judgment; current product-stage meaning remains governed by the canonical Development Model and Game Core research reset.
- [`docs/STATION_ZERO_V3_PRODUCT_VALUE.md`](docs/STATION_ZERO_V3_PRODUCT_VALUE.md) owns G4 comparative product-design research, control/information/pressure/identity experiments, and Content Grammar v0.
- [`docs/STATION_ZERO_V3_DOMAIN_VALUE_GV.md`](docs/STATION_ZERO_V3_DOMAIN_VALUE_GV.md) owns the failure-driven GV consumer-validation lane, external failure transfer rules, live-vs-fixture ablation evidence, and the fresh-player boundary.
- [`docs/STATION_ZERO_V3_P0.md`](docs/STATION_ZERO_V3_P0.md), [`P1`](docs/STATION_ZERO_V3_P1.md), [`P2`](docs/STATION_ZERO_V3_P2.md), and [`P3`](docs/STATION_ZERO_V3_P3.md) define the exact encounter, reducer, durable execution, and planning/browser contracts beneath that target.
- [`docs/authority.md`](docs/authority.md) identifies which records may define current or target behavior.

## Station Zero

A damaged station is losing power, oxygen, communications, and crew health at the same time. Each specialist receives bounded local context, proposes only actions permitted by their capability, and may communicate through local or station-radio channels. Compatible proposals execute together in one atomic World Tick.

The player can:

- choose a Command Doctrine;
- assign or replace cognition Providers;
- approve or deny consequential actions;
- redirect objectives;
- pause, resume, or cancel specialist work;
- inspect verified mission history;
- compare deployments and outcomes.

The default loop is:

```text
configure deployment
→ run until intervention
→ approve, deny, redirect, or change doctrine
→ continue from durable state
→ reach a verified outcome
→ replay, diagnose, and compare
```

## Authority model

```text
Player / Browser
        ↓ doctrine, commands, approvals
Station Zero Mission Control
        ↓ bounded product state and intervention rules
Station Zero specialist coordination
        ↓ Contexts, Messages, Proposals, authority, coordination
Deterministic Station Zero World
        ↓ atomic Tick and authoritative state transition
SQLite product evidence
        ↓ recovery and derived product projections
Replay / Diagnosis / Comparison
```

The model never owns World state. It cannot create objects, capabilities, observations, approvals, actions, or completion claims. Every accepted consequence is checked by the World and independently represented as evidence.

## Current contract

```text
Scenario: station-zero@2
Ruleset: station-zero-core@3
Actors: Engineer, Medic, Security
Persistence: SQLite
Service: one local Node.js process
Runtime dependencies: none
```

Only this Scenario and Ruleset are registered as the current product. Older executable paths, compatibility APIs, migration layers, milestone fixtures, and release-era evidence have been removed from the repository.

## Station Zero v3 preview

The next Station Zero form is retained under `experiments/station-zero-v3/src/`. Its stable product definition is [`docs/STATION_ZERO_V3_PRODUCT.md`](docs/STATION_ZERO_V3_PRODUCT.md); exact implementation contracts remain:

- [`docs/STATION_ZERO_V3_P0.md`](docs/STATION_ZERO_V3_P0.md): frozen encounter and content contract;
- [`docs/STATION_ZERO_V3_P1.md`](docs/STATION_ZERO_V3_P1.md): deterministic Turn reducer and pure replay contract;
- [`docs/STATION_ZERO_V3_P2.md`](docs/STATION_ZERO_V3_P2.md): durable SQLite Turn execution, exact receipt/recovery, and bounded Mission Control projection;
- [`docs/STATION_ZERO_V3_P3.md`](docs/STATION_ZERO_V3_P3.md): Commander Orders, bounded Agent planning, policy expansion, sealed three-faction Preview, explicit Commit, and browser first-playable.

```text
Target Scenario: station-zero@3
Target Ruleset: station-zero-core@4
Target form: three-faction deterministic turn-based tactical encounter
P1: reducer and pure replay complete
P2: durable Turn authority and recovery complete
P3: isolated playable planning layer and /v3 browser complete
G3-era reference evidence: strategic viability, plurality, and bounded live-Agent realization accepted
Current research role: delegation / tactical Game Core reference experiment
New product selection: none
Optional stage lens: G0–G8 may be used from skills/game-stage-lens/SKILL.md when useful
Encounter budget: 20 Turns
```

The v3 reference experiment remains available through a separate API namespace, SQLite database, and browser surface. It is still absent from `products/station-zero-v2/src/registry.ts` and does not replace the current root product. Additional content is not implied by its technical maturity; changes should serve an explicit Game Core hypothesis or a later intentionally selected product.

## Run

Requirements:

- Node.js 26 or newer;
- pnpm 10.33.2.

```bash
scripts/owner-environment bootstrap
scripts/owner-environment doctor
scripts/owner-environment test
pnpm start
```

`scripts/owner-environment cold-start` proves the default typecheck/webcheck/test surface from a copied source fence without inheriting `node_modules`. Browser/E2E and model-backed evaluation remain explicit higher-capability gates.

The default server mounts only the registered Station Zero product. Retained Game Core / Pre-G0 research apparatus is not a default executable affordance and does not materialize its v3 or Casefile stores. Enable those surfaces explicitly for reproduction work:

```bash
pnpm start:research
```

Open:

```text
Registered Station Zero (default): http://127.0.0.1:4173/
Research profile only — Station Zero v3: http://127.0.0.1:4173/v3
Research profile only — Game Core Concept Lab: http://127.0.0.1:4173/lab
Research profile only — Casefile: http://127.0.0.1:4173/casefile
Research profile only — Pre-G0 apparatus: http://127.0.0.1:4173/pre-g0
```

Browser acceptance journeys:

```bash
pnpm e2e
pnpm e2e:v3
pnpm e2e:lab
pnpm e2e:casefile
```

## Product API

### Current product

```text
GET  /api/runs
GET  /api/providers/preflight

GET  /api/mission-control/catalog
GET  /api/mission-control/state
GET  /api/mission-control/timeline
POST /api/mission-control/initialize
POST /api/mission-control/advance
POST /api/mission-control/command

GET  /api/replay/timeline
GET  /api/replay/report
GET  /api/replay/frame

GET  /api/deployments/manifest
GET  /api/compare
```

### Casefile research treatment

Available only when `ORDIVON_GAME_RESEARCH_SURFACES=1`.

```text
GET  /api/casefile/catalog
GET  /api/casefile/runs
POST /api/casefile/runs
GET  /api/casefile/state
POST /api/casefile/action
```

Casefile is an executable epistemic/social-deduction research treatment with a separate SQLite store and exact state-derived action surface. Nonterminal public projections do not expose culprit, motive, reconstruction, or uninspected clue text. The current witness policy is deterministic; Casefile runtime makes no model calls. Its existence does not select a product or product stage.

### Station Zero v3 preview

Available only when `ORDIVON_GAME_RESEARCH_SURFACES=1`.

```text
GET  /api/station-zero-v3/catalog
GET  /api/station-zero-v3/runs
POST /api/station-zero-v3/runs
POST /api/station-zero-v3/resume
GET  /api/station-zero-v3/state
POST /api/station-zero-v3/order
POST /api/station-zero-v3/preview
POST /api/station-zero-v3/commit
```

The v3 preview uses `data/station-zero-v3.sqlite3` by default and does not add v3 Runs to the current `/api/runs` contract.

## Repository map

```text
products/station-zero-v2/src/
    registered Station Zero v2 product implementation: World, product persistence, specialist coordination, Mission Control, replay/diagnosis, deployment profiles, comparison, and product evidence semantics

products/station-zero-v2/web/
    registered Station Zero v2 browser carrier

products/station-zero-v2/test/
    Station Zero v2 product tests and test support

products/station-zero-v2/scripts/
    Station Zero v2 product E2E/evaluation entry points

tools/canonical-digest.ts, tools/browser-equipment.ts, tools/external-json-model.ts
    repository-mechanical helpers; not Big Game runtime APIs

products/station-zero-v2/src/build.ts
    Station Zero v2 build/input identity owned by the registered product

products/station-zero-v2/src/server.ts
    registered product HTTP/browser carrier only

experiments/research-preview/server.ts
    explicit multi-surface research/E2E preview harness; not Big Game or product infrastructure

experiments/station-zero-v3/{src,web,assets,test,scripts}/
    retained Station Zero v3 research/regression apparatus

experiments/casefile/{src,web,test,scripts}/
    retained Casefile research apparatus pending Phase 4 enclosure

experiments/concept-lab/web/, experiments/pre-g0/web/, experiments/veilwild-r1/, research/
    Game research/evidence apparatus and historical experiments; see experiments/README.md

docs/
    Game-domain development, research, evaluation, product, and authority records
```

See [`docs/PRODUCT.md`](docs/PRODUCT.md), [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), and [`docs/VISION.md`](docs/VISION.md).

## Project family

- [Public project directory](https://ordivon.com/projects) — current product, v3 preview status, project role, and next steps.
- Current project-family migration/classification is maintained in Ordivon Next; use the public project directory above and owner-native repositories for current authority.
- Related owners: concrete games own their product semantics; Runtime owns generic Agent execution, Temporal owns durable workflow execution, mature engines/platforms own engine mechanics, Operations owns observability, Artifact/Engineering own build/provenance mechanics, and Distribution owns release/distribution mechanics. Big Game does not duplicate those owners.

## License

Apache License 2.0.
