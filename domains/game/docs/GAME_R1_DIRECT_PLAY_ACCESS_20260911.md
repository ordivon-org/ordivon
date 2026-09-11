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

## 2. Access ladder
### A — lowest-friction: Factorio official demo
Wube publishes a free public demo and explicitly says its purpose is to teach the basic mechanics and help a player decide whether the game interests them. No purchase is required. Source: https://factorio.com/download

This is the recommended first carrier because the R1 hypothesis is narrow: does automation transform cognition from repeated manual execution toward architecture, bottleneck diagnosis and persistent leverage?

**Still requires explicit permission to download/install/launch local software.**

### B — Minecraft official trial
Mojang publishes Java/Bedrock trials; Java supports Windows and Linux. The trial includes the core Survival experience, but the official flow requires a Microsoft account sign-in. Source: https://www.minecraft.net/en-us/free-trial

This is useful for persistent transformation/self-authored intention, but account sign-in is a separate user-authority boundary.

### C — free-to-play launcher/account products
Counter-Strike 2, Dota 2 and Fortnite can be accessed without a base-game purchase, but Steam/Epic onboarding, account state, networking and much larger downloads make them higher-friction first sessions.

Sources:
- https://help.steampowered.com/en/faqs/view/4D81-BB44-4F5C-9B6B
- https://store.steampowered.com/app/570/Dota_2/
- https://store.epicgames.com/all-experiences/fortnite

### D — Candy Crush Saga
Free-to-play, but current official access is via supported app stores rather than browser play on King.com. Device/app installation remains a separate boundary.

### E — ownership/access unknown
Grand Theft Auto V, ELDEN RING and Baldur's Gate 3 have no detected local install evidence. We did not query stores/accounts and therefore do not know whether the user owns them.

### F — console condition
Mario Kart 8 Deluxe and Animal Crossing: New Horizons require a Nintendo Switch access condition for valid direct-play evidence. Workstation absence says nothing about console access.

### G — VR condition
Beat Saber cannot be truthfully evaluated for embodied rhythm through keyboard/mouse substitution. No standard local VR runtime marker was detected; intended VR hardware/runtime/game access is required.

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

## 4. First-session Factorio protocol
Frozen question:

> Does the transition from manual work to automation change the player's planning from repeated execution toward system design and bottleneck diagnosis?

Observe three cuts:

```text
A. before useful automation
B. immediately after the first useful automated chain
C. after the first visible bottleneck / throughput failure
```

Record:
- what task the player stops doing manually;
- what new planning problem replaces it;
- whether throughput failure is diagnosable from visible state;
- whether the player voluntarily redesigns the chain;
- whether automation feels like leverage or merely waiting.

Do **not** test the giant technology tree, enemies, mods, late-game megabase or commercial retention in this canary.

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

The next transition requires explicit user authority for one lawful direct-play carrier. Current recommended first carrier: **Factorio official demo**.
