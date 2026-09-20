---
schema_version: 1
id: game.r1.direct-play-access.20260911
title: Ordivon Game — R1 Direct-Play Access and Human Learning Lane
profile: product-discovery
type: research-decision
lifecycle: active
source_role: current-r1-direct-play-access
visibility: public
owners:
  - ordivon-game
updated: 2026-09-14
summary: Read-only access census and compact Human reference-learning portfolio. Direct play is one active pre-G0 learning lane, not a global gate that blocks competing product theses or independent throwaway prototypes; no Human experience claim exists yet.
evidence_status: local-read-only-census-plus-official-access-sources
readiness: PORTFOLIO_SELECTED_PILOT_READY_HUMAN_PLAY_NOT_STARTED
---
# R1 Direct-Play Access and Human Learning Lane

## 0. Boundary
Wave-1 desk teardown is complete, but first-person experience remains unobserved. This document governs the **reference direct-play lane only**; it does not freeze the rest of pre-G0 exploration.

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

Storage was rechecked on 2026-09-14 after workstation cleanup:

```text
WSL root available ≈ 665 GiB
C: available        ≈ 113 GiB
D: available        ≈ 149 GiB
```

A deeper Steam reconciliation found two **stale app manifests**, not installed game bytes:

```text
Slay the Spire   appid 646570   manifest present   library metadata bytes=0
Mortal Kombat 11 appid 976310   manifest present   library metadata bytes≈117.6 GB
D:/SteamLibrary/steamapps/common  empty at observation cut
```

Therefore neither title is currently admitted as installed. A manifest is not executable-byte evidence and does not prove present ownership/licensing. These titles remain lawful reinstall candidates only if the Steam account actually grants them. Epic installed-manifest roots were absent on this machine at the same cut.

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
Every direct-play session uses the same top-level structure before a **reference-specific R2 causal reproduction claim** can be considered:

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

## 4. Compact canonical-learning portfolio — selected 2026-09-14

The first Human portfolio is intentionally small and cross-form. It is selected by **information gain + mature grammar + 1–3 hour legibility + realistic lawful access**. Access convenience is allowed only as a tiebreaker after reference value is established.

| Order | Learning game | Why it belongs | Current carrier | Frozen first-session causal question |
| --- | --- | --- | --- | --- |
| P0-B | **Slay the Spire** | canonical deck/run decision grammar; repeated context changes the value of the same symbolic action | stale Steam manifest; executable bytes absent; reinstall/ownership check required | Does draw/resource/deck composition make card value materially context-dependent, and does failure change later route/deck decisions? |
| P1-A | **Mortal Kombat 11** | mature direct-action fighting grammar; commitment, spacing, blocking and punish are visible quickly | stale Steam manifest; executable bytes absent; large reinstall/ownership check required | Do startup/recovery, spacing and defense create legible commitment/punish learning within a short session, rather than success feeling like opaque execution noise? |
| P0-A | **Factorio Demo 2.0.77** | canonical automation/systemic leverage; directly attacks the hypothesis that automation moves cognition from repetition to diagnosis/architecture | official free public demo; not yet installed | As automation appears, does player attention shift from manual execution toward bottleneck diagnosis, layout and system redesign? |
| P1-B | **Candy Crush Saga** | mature compact puzzle/live-product grammar; tiny action vocabulary under changing goals/blockers/move budgets | free mobile/Windows client; not yet installed in the checked PC surface | Do goals, blockers and move scarcity materially change evaluation of the same swap grammar and the reason for retry? |

External pressure evidence at selection time:

- Steam still describes Slay the Spire as a roguelike deckbuilder with dynamic deck building and changing routes/encounters; its current page shows sustained recent and cumulative positive review volume.
- Steam still exposes Mortal Kombat 11 as a competitive/local-multiplayer fighter with sustained recent review activity.
- Factorio's official download page explicitly provides a free stable 2.0.77 demo whose stated purpose is to teach the basic mechanics.
- Candy Crush remains available as an official mobile/Windows app; no account is required merely to begin play, though account use is a separate optional continuity concern.

Sources:
- https://store.steampowered.com/app/646570/Slay_the_Spire/
- https://store.steampowered.com/app/976310/Mortal_Kombat_11/
- https://www.factorio.com/download
- https://apps.apple.com/us/app/candy-crush-saga/id553834731

### Why the huge Wave-1 references are not first Human assignments

Counter-Strike 2, Dota 2, Fortnite, Minecraft, GTA V, ELDEN RING, Baldur's Gate 3, Mario Kart 8 Deluxe, Animal Crossing and Beat Saber remain important references. They are not deleted or demoted. The first Human portfolio avoids forcing large installs, specialized hardware or long onboarding when a smaller canonical learning game can answer the same class of first-order question.

```text
Flagship importance        preserved
Canonical learning order   compacted
Large install requirement  avoided unless evidence demands it
Product selection          still false
```

### Session order and duration

```text
P0-A Factorio Demo     60–90 min   official free demo; download only after user authority
P0-B Slay the Spire    60–90 min   stale manifest; reinstall only after ownership/access is established
P1-A Mortal Kombat 11  45–60 min   stale manifest; large reinstall deferred unless its causal question becomes necessary
P1-B Candy Crush       30–45 min   mobile/Windows install only after user authority
```

Factorio is now the default first canary because it is both a canonical high-information learning reference **and** has an official no-account public demo. Access convenience is not its admission reason; it only resolves learning order among already-valid references. Slay the Spire remains the preferred second symbolic-decision canary if lawful reinstall access is established. MK11's large reinstall burden makes it a later direct-action canary rather than an automatic download.

No purchase is required by the current first canary. Downloads/installs are not performed merely because the portfolio exists; they remain explicit user-authority actions.

## 5. Admission law

```text
AccessAvailable
!= ExperienceObserved

OneHumanCanary
!= PopulationClaim

DirectPlaySurvival
!= ReferenceR2Admission

ReferenceR2NotAdmitted
!= ProductPrototypeForbidden
```

After one owner canary, R1 may revise the causal hypothesis and observation protocol. Reference-specific R2 remains closed until the mechanism to reproduce is stable enough that implementation would answer a real causal question rather than imitate a famous game's surface. Independent product-thesis prototypes may proceed in parallel when they test their own explicit hypotheses and make no unsupported reference-transfer claim.

## 6. Current standing

```text
R1 Desk Teardown           COMPLETE
R1 Access Census           COMPLETE
R1 Learning Portfolio      SELECTED_4
R1 Observation Template    READY
R1 Human Direct Play             NOT_STARTED
Reference R2 Baseline             NOT_ADMITTED_FOR_SELECTED_CLAIMS
Competing Product Theses          MAY_PROCEED_IN_PARALLEL
Throwaway Product Prototypes      MAY_PROCEED_IN_PARALLEL
ProductSelected                    false
G0Entered                          false
```

The next action **inside this lane** is a real owner canary session using the frozen observation sheet; Factorio Demo remains the default first reference canary and download/install still requires explicit user authority. At the same time, the overall front half may generate competing product theses and bounded throwaway prototypes. The Factorio session is therefore useful evidence, not a global prerequisite for touching Godot.
