---
schema_version: 1
id: game.core-research.experiment-casefile
title: Casefile — Epistemic Game Core Experiment
profile: research
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
summary: Executable epistemic/social-deduction treatment used to pressure-test Ordivon Game Core. It preserves hidden authoritative incident truth, bounded testimony/evidence, legal investigation actions, accusation commitment and recovery; it is not a selected product or G-stage claim.
evidence_status: verified
readiness: READY
applies_to:
  - casefile-core-experiment
related:
  - game.core-research.reset
  - game.core-research.direction-space
  - game.core-research.experiment-findings
---
# Casefile — Epistemic Game Core Experiment

## Research identity

Casefile is an executable **Game Core treatment**, not a product winner and not a G6 candidate.

```text
Research axis: epistemic / social inference
Core pressure: authoritative hidden truth + bounded evidence + testimony + commitment
Implementation maturity: executable browser treatment
Product stage: none assigned
Product commitment: none
```

The treatment exists to ask whether separating World truth from what subjects observe, believe, say, and what the player infers can generate valuable play.

## Experimental loop

```text
read an incident
→ inspect a trace or question a person
→ notice support / ambiguity / contradiction
→ choose breadth or depth under a move budget
→ optionally confront a person with exact inspected evidence
→ commit one accusation
→ see the authoritative reconstruction
→ update the player's model
```

The player never sees culprit, hidden timeline, motive, or reconstruction before terminal commitment.

## Current implementation

Three bounded incidents are retained:

1. `relay-sabotage` — The Silent Relay;
2. `missing-med-cache` — The Missing Cache;
3. `false-pressure-alarm` — Pressure Without a Leak.

Each uses four crew members, four authored traces, deterministic stateful testimony, eight investigation moves, exact confrontation admission and one terminal accusation.

This content breadth is enough for the current research treatment. It is not a production/content plan.

## Authority shape

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

The treatment deliberately did not inherit Station Zero's Host Contract, Team scheduler, Commander Orders, Planning Heads, Provider pool or replay architecture. This remains useful evidence for “local game form first; infrastructure only when earned.”

## Cognition finding

The current witness system is deterministic policy, not a live model.

A witness response may change because retained interaction state changes:

- first question vs repeated pressure;
- inspected evidence creates an exact confrontation;
- confrontation produces an authored person/trace-specific response.

Matched Concept Lab evidence did not show enough player-value advantage from richer autonomy to earn live-model latency/cost/variance.

This is a local cognition result, not a claim that social games do not need models.

## Machine and browser evidence retained

The treatment has verified evidence that:

- three distinct incidents and culprits exist;
- nonterminal public views hide culprit, motive, reconstruction and uninspected clue text;
- confrontation appears only after its exact trace is inspected;
- invented/stale action identities fail closed without spending investigation time;
- witness behavior changes with retained local interaction history;
- accusation is an explicit terminal commitment;
- terminal projection reveals authoritative reconstruction;
- exhausted investigation budget leaves only accusation actions;
- SQLite close/reopen recovers the exact current public view;
- desktop and mobile browser journeys pass without browser errors.

## Fresh-agent blind-play evidence

A fresh `deepseek-v4-flash` player was given only the real player-visible `/casefile` surface and legal action labels.

| Case | Result | Main observed pattern | Replay self-report |
| --- | --- | --- | ---: |
| The Silent Relay | wrong accusation | broad sampling consumed the move budget; no decisive confrontation | 0.6 |
| The Missing Cache | wrong accusation | sampled broadly; missed the decisive service-hatch direction | 0.6 |
| Pressure Without a Leak | correct | inspected bridge lead, confronted Ivo, accused with support | 0.2 |

The experiment itself made zero runtime model calls; model calls were evaluation cost only.

The useful finding is not the 1/3 solve rate. It is that failure could occur inside an intended choice tension:

```text
breadth of evidence
vs
focused confrontation
under limited investigation time
```

## What this treatment establishes

Promising evidence:

- epistemic separation can be expressed in player-native game language;
- hidden authoritative truth can create an inference problem without exposing debug machinery;
- confrontation can turn accumulated evidence into changed social information;
- a very small local architecture is enough to test this mapping.

Unknown:

- whether humans find the ambiguity satisfying rather than arbitrary;
- whether the move budget is good tension;
- whether people become characters rather than evidence containers;
- whether this structure supports sustained replay;
- whether richer cognition eventually improves social interpretation;
- whether any future Ordivon product should use this form.

## Stop rule

Do not expand Casefile because the treatment happens to be executable.

Only modify it when a specific Game Core hypothesis requires new evidence. Otherwise retain it as a cross-game pressure test beside Station Zero and other experiments.
