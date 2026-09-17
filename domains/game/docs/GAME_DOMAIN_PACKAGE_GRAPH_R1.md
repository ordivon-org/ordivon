---
schema_version: 1
id: game.domain-package-graph.r1
title: Ordivon Game Creative-Open Knowledge Graph
profile: engineering
lifecycle: active
source_role: derived-navigation
visibility: public
owners:
  - ordivon-game
updated: 2026-09-18
summary: Creative-open knowledge graph for Game mechanics, compositions, experiments, evidence fences, optional Skills, teardown-derived mechanism-combination patterns, tools and horizontal owners. Creative combinations default open; claims and external effects remain bounded.
evidence_status: verified
readiness: READY
---
# Ordivon Game Creative-Open Knowledge Graph

## 1. Core rule

The graph no longer decides whether a game idea or mechanic combination is legal.

```text
CREATION / COMPOSITION / EXPERIMENT
    default = OPEN_EXPLORATION

CLAIMS
    evidence-bounded

AUTHORITY
    owner-bounded

EXTERNAL EFFECTS
    explicitly authorized
```

Unknown or unmodeled creative structure is an exploration signal, not a rejection signal.

## 2. What moved out of Game law

Three formerly central models are now repository-local Agent Skills:

```text
skills/game-development-lenses/SKILL.md
  D1-D8 optional development questions

skills/game-stage-lens/SKILL.md
  G0-G8 optional coordination vocabulary

skills/game-minimal-interaction-model/SKILL.md
  World/State -> Observation -> Action -> Transition working model
```

All three are advisory, replaceable and removable. None may block a mechanic, genre, rule, interaction, control scheme, content structure or novel game composition merely because the idea does not fit the model.

The former `kernel-minimality`, `stage-core-separation`, and Foundation-freeze creative gates are retired from the machine graph. The R1-R29 foundations corpus remains useful research knowledge but is not a creative admission system.

## 3. What remains hard

The graph keeps boundaries whose purpose is to prevent false claims or unauthorized effects rather than to narrow invention:

- mechanical or synthetic evidence is not Human evidence;
- evidence for component A plus evidence for component B is not automatically evidence for composition A+B;
- render/file/tool success is not Game semantic correctness or Player Value;
- credential/capability is not effect authority;
- Host continuity is not Game/domain truth;
- historical standing is not current standing;
- provider/model output does not directly become an authoritative World effect in products that use that boundary;
- external effects require the exact effect authority.

These constraints say what may be **claimed or executed**, not what may be imagined or prototyped.

## 4. Mechanism-combination experience library

`standards/game_domain_package_graph_r1.json` keeps only a compact `mechanismCombinationPatterns` layer distilled from the earlier twelve-game comparative teardown. Fine-grained experience is externalized to `standards/game_mechanism_experience_library_r1.json` and documented by `GAME_MECHANISM_EXPERIENCE_LIBRARY_R1.md`, so the architecture graph remains small instead of becoming a mechanic ontology. Cross-game relationship mining is externalized again to `standards/game_mechanism_relationship_graph_r1.json`; Design Counterexample Memory is externalized to `standards/game_design_counterexample_memory_r1.json`. The domain graph stores only pointers, not relationship nodes/edges/facets/Conditionalities or counterexample records.

Examples include:

```text
Counter-Strike 2
  lethal commitment + partial information + short reset

Dota 2
  role asymmetry + shared objectives + long power curve + combinatorics

Minecraft
  persistent transformation + self-authored goals + resource constraint

GTA V
  cross-system verbs + dense world + escalating response

ELDEN RING
  combat commitment + readable telegraphs + route freedom + retry

Baldur's Gate 3
  multiple solution paths + persistent consequence + later acknowledgement

Factorio
  automation + persistent leverage + bottleneck feedback + redesign

Mario Kart 8 Deluxe
  driving mastery + catch-up volatility + short races

Animal Crossing
  persistent place + routine + real-time change + acknowledgement

Candy Crush
  tiny action grammar + goal/blocker/scarcity recontextualization

Beat Saber
  embodied input + rhythm prediction + directional mapping + multimodal feedback
```

Every pattern is explicitly `ADVISORY_HYPOTHESIS_PATTERN`, includes confounds and a falsifier, and has `canBlockNovelCombination=false`.

The library is therefore **experience**, not recipe:

```text
Pattern similarity
  -> suggest analogy / contrast / falsifier
  != approve design
  != reject design
  != transfer evidence
```

## 5. Composition Explorer

The repository exposes:

```bash
pnpm explore:composition -- \
  --intent explore \
  --elements mechanic.e03,invented.time-reversal-dialogue-physics \
  --mechanisms commitment,time-reversal,dialogue-as-physics
```

The explorer preserves unknown elements verbatim. It does not require every creative element to be pre-registered as a graph node.

It reports:

- known vs unmodeled elements;
- optional Skill lenses;
- relevant teardown-derived coarse pattern analogies;
- fine-grained Mechanism Experience matches with confounds, transfer risks, falsifiers and cheap probes;
- cross-game Relationship Facets and Conditionalities;
- contextual Design Counterexample matches with failure signals and cheap discriminators;
- epistemic fences;
- claim-specific evidence requirements;
- authority/effect boundaries when the requested intent crosses them.

Creative intent returns `OPEN_EXPLORATION` even for novel combinations. Claim/effect intents may instead return:

```text
EVIDENCE_NOT_TRANSFERABLE
EXTERNAL_EFFECT_BLOCKED
AUTHORITY_REQUIRED
```

Those dispositions constrain only the claim/effect, not the creative experiment itself.

## 6. Evidence does not compose automatically

One retained epistemic rule is:

```text
Evidence(A) + Evidence(B) != Evidence(A+B)
```

A combination may be better, worse, stranger or qualitatively different from its parts because interaction can create emergent behavior.

Therefore:

```text
component evidence
    -> useful provenance
    -> candidate hypotheses
    -> experiment design hints

but never
    -> automatic composition evidence
```

## 7. Stable graph blocks

The machine graph still contains concrete stable blocks where useful:

- foundations/research packages as knowledge;
- mechanics E01-E03;
- compositions PC01-PC03;
- concrete products/experiments;
- thin Game tools;
- advisory Skill plane;
- external horizontal owners such as Research, Runtime, Host, Harness, Workstation, Artifact, Media, Distribution, Network and Security.

Dependency edges do not imply semantic ownership, and none of these blocks form a closed universe of possible games.

## 8. Non-goals

This graph is not:

- a universal Game ontology;
- a list of allowed genres;
- a closed mechanic vocabulary;
- a mandatory development lifecycle;
- a product selector;
- a stage gate;
- a creativity scorer;
- a ranking of good game combinations;
- a replacement for Human play or direct evidence;
- a generic arbitration engine.

Its job is narrower: preserve useful knowledge, provenance, anti-self-deception boundaries and owner boundaries **without turning accumulated research into a cage for future games**.
