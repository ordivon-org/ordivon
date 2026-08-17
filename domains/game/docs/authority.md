---
schema_version: 1
id: game.authority
title: Game Content Authority
type: decision
profile: engineering
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-game
audience:
  - maintainer
  - player
  - designer
  - builder
  - agent
updated: 2026-08-17
summary: Decision separating registered Station Zero execution, canonical G0-G8 product lifecycle authority, Game Core treatments, the R1–R25 foundations corpus, v3 reference evidence, exact P0-P3 contracts, long-range Game vision, and machine truth.
evidence_status: not_applicable
readiness: READY
applies_to:
  - ordivon-game
related:
  - game.start
  - game.product.station-zero
  - game.product.station-zero-v3
  - game.architecture
  - game.vision
  - game.station-zero-v3.encounter
  - game.station-zero-v3.reducer
  - game.station-zero-v3.execution
  - game.station-zero-v3.planning
---
# Game Content Authority

## Context

Game simultaneously contains one registered executable, one broader product vision, and an implemented but unregistered v3 replacement path. Treating the newest phase file as the whole product would confuse deployed behavior, target design, and future possibility.

## Decision

[`../README.md`](../README.md) is the canonical repository entry and must state which Scenario and Ruleset are registered. [`PRODUCT.md`](PRODUCT.md) owns the registered Station Zero player experience and acceptance. [`ARCHITECTURE.md`](ARCHITECTURE.md) owns the registered executable architecture and state ownership. [`VISION.md`](VISION.md) owns long-range principles and possibilities but creates no feature commitment. [`DEVELOPMENT_MODEL.md`](DEVELOPMENT_MODEL.md) owns the cross-game development process and is the **only authority for G0–G8 product-stage semantics**. [`GAME_CORE_RESEARCH_RESET.md`](GAME_CORE_RESEARCH_RESET.md), [`GAME_CORE_DIRECTION_SPACE.md`](GAME_CORE_DIRECTION_SPACE.md), [`GAME_CORE_EXPERIMENT_FINDINGS.md`](GAME_CORE_EXPERIMENT_FINDINGS.md), and [`GAME_CORE_EXPERIMENT_CASEFILE.md`](GAME_CORE_EXPERIMENT_CASEFILE.md) own the earlier Game Core research decisions and executable treatments. [`GAME_FOUNDATIONS_RESEARCH_R1_R17.md`](GAME_FOUNDATIONS_RESEARCH_R1_R17.md) owns the canonical synthesis of the first seventeen completed foundation rounds; [`GAME_FOUNDATIONS_RESEARCH_R18.md`](GAME_FOUNDATIONS_RESEARCH_R18.md) owns the R18 decomposition of motivation, goals, needs, values, preferences, utility and commitment; [`GAME_FOUNDATIONS_RESEARCH_R19.md`](GAME_FOUNDATIONS_RESEARCH_R19.md) owns the R19 decomposition of strategic interdependence, conflict, cooperation, competition, coordination, bargaining, negotiation, commitment, reputation and equilibrium; [`GAME_FOUNDATIONS_RESEARCH_R20.md`](GAME_FOUNDATIONS_RESEARCH_R20.md) owns the R20 decomposition of creation, creativity, construction, expression, authorship, customization, style, tool/material/grammar, curation and co-creation; [`GAME_FOUNDATIONS_RESEARCH_R21.md`](GAME_FOUNDATIONS_RESEARCH_R21.md) owns the R21 decomposition of embodiment, body/avatar/control locus, control/input/command/delegation, skill, affordance, responsiveness, game feel and presence; [`GAME_FOUNDATIONS_RESEARCH_R22.md`](GAME_FOUNDATIONS_RESEARCH_R22.md) owns the R22 decomposition of uncertainty, probability, randomness, ambiguity, risk, luck, variance, determinism, predictability and fairness; [`GAME_FOUNDATIONS_RESEARCH_R23.md`](GAME_FOUNDATIONS_RESEARCH_R23.md) owns the R23 decomposition of temporal frames, sequence/order, simultaneity/concurrency, duration/timing/tempo/rhythm, turns/phases/ticks, temporal windows/deadlines, waiting, persistence, reversibility and temporal agency; [`GAME_FOUNDATIONS_RESEARCH_R24.md`](GAME_FOUNDATIONS_RESEARCH_R24.md) owns the R24 decomposition of entity identity, self, character, persona, role, social/collective identity, identifiers, recognition, status, rank, reputation, continuity, transformation, cloning and generative identity; [`GAME_FOUNDATIONS_RESEARCH_R25.md`](GAME_FOUNDATIONS_RESEARCH_R25.md) owns the R25 decomposition of persistent relationships, directed/shared/institutional relational state, attachment, care, intimacy, trust, reliability, commitment, loyalty, obligation, reciprocity, dependence, communal/exchange norms, rivalry, betrayal, repair and social-network topology; [`GAME_FOUNDATIONS_RESEARCH_MAP.md`](GAME_FOUNDATIONS_RESEARCH_MAP.md) owns the compact R1–R25 navigation model; [`GAME_FOUNDATIONS_CONTINUATION.md`](GAME_FOUNDATIONS_CONTINUATION.md) owns the context-switch handoff and exact next foundation frontier. None of these research records assigns a product stage or selects a shipped product.

[`STATION_ZERO_V3_CONTRACTION.md`](STATION_ZERO_V3_CONTRACTION.md) owns only current Game-local contraction verdicts, negative regions, and reopen conditions. Ordivon Computing owns the cross-project synthesis that informed them. This record does not register v3, define World transitions, or make historical rejections permanent law.

[`STATION_ZERO_V3_PRODUCT.md`](STATION_ZERO_V3_PRODUCT.md) owns the stable human-facing definition of the unregistered v3 **reference target**: player fantasy, game form, Agent participation, core loop, product pillars, historical G3/G4/G5 evidence, production profile, and replacement boundary. Its historical stage labels do not select the next Ordivon Game product or redefine current Game Core research.

[`STATION_ZERO_V3_VERTICAL_SLICE.md`](STATION_ZERO_V3_VERTICAL_SLICE.md) owns the historical production/calibration claim set produced by the v3 programme and its then-current G4 exit judgment. Those receipts remain valid for what they measured, while `DEVELOPMENT_MODEL.md` remains the sole G0–G8 stage authority and Game Core research treats Station Zero v3 as one pressure test.

[`STATION_ZERO_V3_PRODUCT_VALUE.md`](STATION_ZERO_V3_PRODUCT_VALUE.md) owns the G4 comparative product-value lane: mature analogue decomposition, transferable design laws, same-state/relevant-state product experiments, surfaced-control subtraction, and Content Grammar v0. It may narrow what the player is shown when evidence proves a control has no value, but it does not invent World mechanics merely to justify existing schema fields.

The exact v3 target contracts remain [`STATION_ZERO_V3_P0.md`](STATION_ZERO_V3_P0.md) for encounter and content decisions, [`STATION_ZERO_V3_P1.md`](STATION_ZERO_V3_P1.md) for the pure deterministic reducer contract, [`STATION_ZERO_V3_P2.md`](STATION_ZERO_V3_P2.md) for durable Planning, execution, evidence, and recovery, and [`STATION_ZERO_V3_P3.md`](STATION_ZERO_V3_P3.md) for Commander Orders, bounded Agent planning, Plan Preview/Commit, the dedicated v3 API, and the separate `/v3` first-playable. These documents do not register v3 or replace the current root browser and HTTP product.

`src/registry.ts`, source code, SQLite schema, deterministic tests, generated or retained receipts, replay verification, product acceptance scripts, and the running service remain stronger owners for exact executable registration, fields, transitions, and observed behavior. `AGENTS.md` governs repository work rather than product truth.

For the unregistered v3 target, Agent cognition and Game action authority remain separate through Game-owned Candidate admission, exact Faction Plans, canonical Turn Batch admission, and authoritative World resolution. Historical P3 research also proved a stronger `Subject × Cognition × Actor × Intent` binding without importing Harness/World-private schemas; GC1 removed that dormant optional mechanism after confirming that no production caller enabled it and current product/recovery behavior was unchanged. The law remains; the unused binding machinery does not. Game still acquires no global Embodiment, Presence, Subject, or Cognition registry.

## Consequences

The registered Station Zero executable, v3 reference experiment, Concept Lab, and Casefile treatment are deliberately separate. No recent treatment is a selected product winner. The R1–R25 foundations corpus is now durable repository state rather than conversation-only context. R18 establishes Need / Value / Desire separation, contextual Preference, Goal adoption/Commitment, late scalarization, minimum-sufficient motivational complexity and Playable Motivation. R19 establishes Strategic Relevance/Topology, conflict/competition/cooperation/coordination separation, bargaining and commitment semantics, equilibrium as incentive diagnostic, minimum-sufficient strategic cognition, and Playable Strategy. R20 establishes Creation/Creativity/Expression/Authorship separation, Authorial Causality, Creative Contribution Topology, constraint-structured creative possibility space, mixed-initiative contribution roles, and Playable Creation/Expression. R21 establishes the Intent→Input/Command→Mapping→Resolution→Feedback control chain, Action Causality, Control Locus, Intent Fidelity, Control Contribution Topology, relational Affordance, agency/ownership separation, and Playable Control/Embodiment. R22 establishes Uncertainty/Randomness/Determinism separation, epistemic/aleatory model-relative structure, distributional Risk, DecisionQuality versus OutcomeQuality, Outcome Contribution Topology, Distributional Agency, plural Fairness, and Playable Uncertainty/Risk. R23 establishes multi-frame temporality, causal/partial ordering, Simultaneity/Concurrency and Turn/Phase/Tick separation, action intervals/windows, Temporal Causality/Agency, strategic waiting, temporal fairness/contract, persistence without continuous computation, reversal/knowledge separation, and Playable Temporality. R24 separates entity/numerical identity from qualitative similarity, self-model, role/social identity, public presentation and reputation; it adds Continuity Profile, Identity Authority, Identity/Recognition Topology, Identity Causality, branch-aware continuity, development-versus-drift, implementation-independent Agent identity, Playable Identity and Playable Continuity. R25 establishes four-layer relational state, Relational Authority/Compression, separation of attachment/care/intimacy/trust/reliability/commitment/loyalty/obligation/reciprocity/dependence, communal versus exchange norms, multiplex Relationship Topology, Relationship Causality, Relational Contract/Affordance/Agency, betrayal/repair semantics, human–AI relational-layer separation and Playable Relationship. The exact next foundation frontier is R26 emotion, affect, feeling, mood, valence, arousal, appraisal, regulation, empathy and expression. Foundation rounds remain research methods and do not create G-stage claims. Product narrowing remains deferred until the remaining foundational dimensions and a later synthesis justify an intentional canonical G0. `STATION_ZERO_V3_PRODUCT.md` preserves v3 reference identity and historical programme evidence; P0/P1/P2/P3 remain canonical for their exact owner-local contracts.

## Status

Accepted and active. Reopen when v3 is registered, the current executable is removed, a second world is admitted, or stable human-oriented specifications replace the phase-coded target set.
