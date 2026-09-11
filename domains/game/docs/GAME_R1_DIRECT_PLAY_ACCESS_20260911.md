---
schema_version: 1
id: game.r1.direct-play-access.20260911
title: Ordivon Game — R1 Direct-Play Access and Human Gate
profile: product-discovery
type: research-decision
lifecycle: active
source_role: current-r1-direct-play-access
visibility: public
owners:
  - ordivon-game
updated: 2026-09-11
summary: Read-only access census and frozen direct-play protocol for the twelve R1 references. Local installation absence is not ownership evidence; downloads, account sign-in, purchases, console use and VR remain explicit user-authority boundaries.
evidence_status: local-read-only-census-plus-official-access-sources
readiness: ACCESS_CENSUS_COMPLETE_HUMAN_PLAY_NOT_STARTED
---
# R1 Direct-Play Access and Human Gate

## 0. Boundary
Wave-1 desk teardown is complete, but first-person experience remains unobserved.

```text
Public documentation/video observation
!= direct play

Not installed here
!= not owned

Synthetic/browser completion
!= Human experience
```

No purchase, account sign-in, credential use, large download or device pairing is authorized by this record.

## 1. Read-only workstation census
The target-only scan checked standard Steam manifests on C:/D:, standard Epic manifest locations, a few title-specific launcher/package paths, and standard SteamVR/Oculus/Meta runtime markers. It did **not** enumerate account libraries or unrelated software.

Result:

```text
12 / 12 target titles: no local installed evidence detected
Epic target manifests surfaced: 0
VR runtime marker: not detected
```

This says only what the checked machine surfaces contained. It says nothing about account ownership, another device, console library, or hardware ownership.

Storage snapshot at the same cut:

```text
WSL root available ≈ 553 GiB
C: available        ≈ 112 GiB
D: available        ≈  57 GiB (92% used)
```

Therefore large reference installs must not default to D:.

## 2. Access census is not the direct-play portfolio
The census above answers **how hard each admitted flagship is to access**, not **which games we should now spend Human time playing**. Treating the twelve flagship references as twelve mandatory play assignments was a category error.

The corrected role separation is:

```text
Flagship Reference
  may be huge
  establishes the success ceiling / mature system interactions
  desk teardown is sufficient initially

Canonical Learning Game
  actual Human direct-play sweet spot
  successful + mature + information-dense
  core grammar becomes legible in roughly 1–3 hours

Micro Baseline
  our later tiny causal reproduction
  used only after a transfer hypothesis survives
```

Therefore:

```text
ReferenceImportance != DirectPlayPriority
DirectPlayPriority != LowestInstallCost
FlagshipDeskTeardown != MandatoryFullPlaythrough
```

CS2, Dota 2, Fortnite, GTA V, ELDEN RING, BG3, Mario Kart, Animal Crossing and Beat Saber may remain essential references without being first-wave direct-play assignments. They can be played later when a specific unresolved claim actually requires their intended condition.

Factorio's public demo, Minecraft's trial and other accessible references remain useful **access options**, but convenience alone cannot nominate the first learning game.

### Direct-play sweet-spot selection rule
Select only **3–5 canonical learning games** for the first Human portfolio. Each should satisfy most of:

- substantial commercial/audience success and mature design practice;
- a core interaction grammar readable within about 1–3 hours;
- bounded setup/onboarding burden;
- materially different player-value/archetype coverage from the other selected games;
- direct play provides evidence that desk teardown cannot provide;
- lawful access is realistic, but access convenience is not treated as proof of design importance.

No download/install request should be made until this compact learning portfolio is selected.

## 3. Frozen observation sheet
Every direct-play session uses the same top-level structure before R2 can be considered:

```text
Reference title / exact edition
Platform + input + hardware
Session timestamp + duration
Prior familiarity (self-report)
Frozen R1 causal question

FIRST 5 MINUTES
- what action vocabulary is learned?
- what feedback makes success/failure legible?
- what does the player misunderstand?

ACTION GRAMMAR
- verbs actually used
- commitment / reversibility
- resource/time/information constraints

CONTEXT SYSTEM
- what changes the value of the same action over time?
- what state persists across attempts/sessions?

FAILURE / RETRY
- failure cause as perceived by player
- retry cost
- evidence of changed behavior after failure

HUMAN EXPERIENCE
- tension / agency / mastery / attachment / flow / confusion as applicable
- concrete moment supporting the report
- competing explanation

R1 HYPOTHESIS TEST
- observation supporting hypothesis
- observation contradicting hypothesis
- strongest alternative explanation
- whether the proposed cheap baseline still targets the right causal claim

VERDICT
SURVIVES_DIRECT_PLAY | REVISE_CAUSAL_HYPOTHESIS | REJECT_TRANSFER | INCONCLUSIVE
```

No demographic/sensitive participant data is needed for this first owner canary.

## 4. No first-session game selected yet
The earlier Factorio-first recommendation is **superseded**. Factorio remains a strong systems-learning candidate, but choosing it merely because a public demo is convenient would repeat the same mistake at a smaller scale.

The next research action is to select the 3–5-game canonical learning portfolio using the sweet-spot rule above. Only after that selection should any title receive a frozen first-session question.

## 5. Admission law

```text
AccessAvailable
!= ExperienceObserved

OneHumanCanary
!= PopulationClaim

DirectPlaySurvival
!= R2Admission
```

After one owner canary, R1 may revise the causal hypothesis and observation protocol. R2 remains closed until the specific mechanism to reproduce is stable enough that implementation would answer a real causal question rather than imitate a famous game's surface.

## 6. Current standing

```text
R1 Desk Teardown           COMPLETE
R1 Access Census           COMPLETE
R1 Human Direct Play       NOT_STARTED
R2 Baseline Reproduction   NOT_ADMITTED
ProductSelected            false
G0Entered                  false
```

The next transition is **not installation**. First select a compact 3–5-game canonical learning portfolio. Only then request explicit user authority for whichever lawful carrier is actually chosen.
