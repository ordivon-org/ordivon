---
schema_version: 1
id: game.g-series.g6-casefile
title: Casefile — G6 Playable Candidate
profile: product
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
  - producer
updated: 2026-08-16
summary: Current G6 candidate produced by the G-Series reset. Casefile is a server-authoritative short-form social deduction game with three incidents, bounded testimony/evidence, exact legal investigation actions, explicit accusation commitment, and refresh recovery. Technical and fresh-agent playable evidence is accepted; human G6 exit remains open.
evidence_status: verified
readiness: READY
applies_to:
  - casefile-g6-candidate
related:
  - game.g-series.reset
  - game.g-series.product-search
  - game.g-series.selection
---
# Casefile — G6 Playable Candidate

## Current judgment

```text
G5 selection:                 SELECTED
G6 implementation candidate: BUILT
G6 technical/browser gate:   PASS
G6 fresh-agent probe:        PASS as independent play evidence
G6 human player exit:        OPEN / UNKNOWN
G7 vertical slice:           NOT ADMITTED
G8 production:               NOT ADMITTED
```

Casefile is the first post-dogfood Ordivon Game candidate whose implementation begins from a player problem rather than from Agent infrastructure.

## Product sentence

**Casefile is a short-form social deduction game where the player has limited investigation time to reconcile physical traces with conflicting testimony, decide which contradictions deserve deeper pressure, and commit one accusation against an authoritative hidden incident history.**

## Player loop

```text
read the incident
→ inspect a trace or question a person
→ notice support / ambiguity / contradiction
→ choose breadth or depth under a move budget
→ optionally confront a person with exact inspected evidence
→ commit one accusation
→ see the authoritative reconstruction
→ update your investigation model
```

The player never sees a culprit flag, hidden timeline, motive, or reconstruction before terminal commitment.

## Current content

Three bounded incidents are implemented:

1. `relay-sabotage` — The Silent Relay;
2. `missing-med-cache` — The Missing Cache;
3. `false-pressure-alarm` — Pressure Without a Leak.

Each currently uses four crew members, four authored physical traces, adaptive deterministic testimony, eight investigation moves, and one terminal accusation.

The repeated cast is a prototype economy decision, not a permanent product commitment.

## Authority shape

Casefile deliberately does not inherit Station Zero's product architecture.

```text
Casefile scenario content
        ↓ hidden incident truth + authored witness behavior
CasefileService
        ↓ exact legal inspect / question / confront / accuse actions
CasefileStore
        ↓ revision-fenced SQLite state + digest
Casefile public projection
        ↓ no hidden culprit/motive/reconstruction before terminal
Browser
```

No Host Contract, Team scheduler, Commander Order, Planning Head, Plan Preview, Provider pool, generic NPC registry, dialogue framework, or universal Game engine was added.

## Agent participation

The current witness system is a **deterministic local policy**, not a live model.

A witness response may change because retained interaction state changes:

- first question vs repeated pressure;
- inspected evidence creates a legal confrontation;
- confrontation produces an authored response bound to that exact person/trace pair.

This is sufficient to test the current player experience. G5 matched blind play did not demonstrate that live model cognition improves Casefile enough to earn latency/cost/variance.

Reopen model cognition only after a player-facing failure survives a cheaper witness policy.

## Persistence scope

Casefile has its own small SQLite owner:

- one row per Run;
- exact current revision;
- canonical state JSON + digest;
- revision-fenced updates;
- refresh/process reopen recovery.

The store exists because a 10–20 minute investigation should survive browser refresh. It is not a generic Game persistence platform.

## Machine acceptance

Current owner-local evidence establishes:

- three distinct incidents and three distinct culprits;
- nonterminal public views do not expose culprit identity fields, motive, reconstruction, or uninspected clue text;
- confrontation becomes legal only after its exact trace is inspected;
- invented/stale action identities are rejected without spending investigation time;
- deterministic witness behavior changes with retained local interaction history;
- correct and incorrect accusations are explicit terminal commitments;
- only terminal projection reveals authoritative culprit/motive/reconstruction;
- when eight investigation moves expire, only accusation actions remain;
- SQLite close/reopen reconstructs the exact current public view;
- desktop browser journey, reload recovery, terminal reconstruction and mobile layout pass without browser errors.

## Direct visual review

The current player surface has been visually inspected at:

- incident start;
- mid-investigation after trace + testimony + confrontation;
- terminal reconstruction;
- mobile start.

The most important qualitative correction relative to Station Zero is that the visible vocabulary is now game-native:

```text
Traces
People
What you actually learned
Inspect
Question
Confront
Accuse
investigation moves left
Reconstruction
```

The default surface no longer asks the player to reason about Providers, admitted Candidates, model confidence, evidence hashes, bounded projection terminology or revision machinery.

## Fresh-agent independent play

A fresh `deepseek-v4-flash` player received only the real `/casefile` player-visible page and the currently legal action labels. It received no hidden culprit, motive, reconstruction, scenario implementation, design hypothesis, or developer documentation.

Three independent cases produced:

| Case | Result | Decision pattern | Replay self-report |
| --- | --- | --- | ---: |
| The Silent Relay | wrong accusation | broad sampling consumed all 8 moves; no key confrontation before accusation | 0.6 |
| The Missing Cache | wrong accusation | early focus on Mira + broad sampling; missed Nera's decisive service-hatch trace | 0.6 |
| Pressure Without a Leak | correct | sampled accounts, inspected bridge lead, confronted Ivo, accused with support | 0.2 |

The probe used 30 model calls, 23,132 prompt tokens and 2,295 completion tokens. These numbers are evaluation cost, not intended runtime product cost; the Casefile product itself made zero model calls.

### What the failures mean

The two incorrect outcomes were not interface dead-ends or invalid-action failures. The player could articulate the case goal, use traces/testimony, spend the complete budget, commit an accusation, and understand the terminal reconstruction.

The failures expose a real game-design question:

```text
breadth of evidence
vs
focused confrontation
under limited investigation time
```

This is promising because the failure is now inside the intended decision space. It is not yet proof that the pressure is enjoyable.

### What remains unknown

Fresh-agent self-report cannot establish:

- whether humans experience ambiguity as satisfying deduction or arbitrary guesswork;
- whether eight moves is appropriately tense rather than stingy;
- whether confrontation feels like an earned insight;
- whether characters become memorable rather than evidence containers;
- whether a solved case creates desire for another incident;
- whether failure motivates replay or abandonment.

## G6 exit gate

Do **not** mark G6 complete merely because the implementation and fresh-agent probe work.

The next legitimate gate is a small fresh-human play round on the actual browser product without architecture explanation. Observe behavior before asking preference questions.

Useful observations:

- Can the player state the case goal after the first screen?
- What do they inspect first and why?
- Do they notice contradictions without being told to look for them?
- Do they discover/understand confrontation as a distinct verb?
- When do they become willing to accuse?
- If wrong, can they identify which investigation choice they would change?
- Do they voluntarily start another case?

Only after this evidence should G6 exit and G7 admission be reconsidered.

## G7 / G8 stop rule

Until G6 human evidence exists, do not:

- commission final character art or voice;
- add live model dialogue;
- scale to dozens of cases;
- build procedural mystery generation;
- introduce campaign/meta progression;
- generalize witness memory or social simulation into a platform;
- migrate engine/runtime merely for presentation novelty.

The candidate is now good enough to test the game. That is the current frontier.
