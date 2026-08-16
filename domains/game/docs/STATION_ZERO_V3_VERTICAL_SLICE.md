---
schema_version: 1
id: game.product.station-zero-v3.vertical-slice
title: Station Zero v3 — G4 Vertical Slice
profile: product
lifecycle: accepted
source_role: canonical
visibility: public
owners:
  - ordivon-game
audience:
  - designer
  - builder
  - agent
  - producer
updated: 2026-08-14
summary: G4 production brief and acceptance contract for proving one representative final-ish Station Zero v3 browser slice through mobile command proximity, specialist visual identity, live deliberation presentation, representative audio, and repeatable Game-to-Studio asset integration.
evidence_status: verified
readiness: READY
applies_to:
  - station-zero-v3-unregistered
related:
  - game.product.station-zero-v3
  - game.development-model
  - game.authority
---
# Station Zero v3 — G4 Vertical Slice

## Current Game Core research interpretation

The 2026-08-16 Game Core research reset treats Station Zero as an executable **reference experiment**. Stage labels and admissions below are retained as historical claims about the v3 programme and its measured machine/runtime/production evidence; they do not select the next product. Canonical G0–G8 semantics are owned only by `DEVELOPMENT_MODEL.md`; current research interpretation is in `GAME_CORE_RESEARCH_RESET.md`.


## Current acceptance state

The first G4 production round has passed its **machine-verifiable production acceptance** on the real browser product. This means the source → derivative → runtime pipeline, responsive information order, live deliberation state, presentation audio boundaries, and existing authoritative gameplay journey are all executable together.

Measured browser receipt from the accepted round:

```text
390×844 mobile Commander Order top: 411px
390×844 full tactical map top:      1642px
Specialist tactical tokens:         3
Selected runtime media:             PNG + 3 OGG, HTTP 200
Deliberation state:                 observable without World advance
Complete v3 journey:                20 committed Turns / revision 20
Browser errors:                     0
```

A current live-Provider preflight after the production integration retained the Agent boundary:

```text
selected G3 holdout profiles: 3
verified Runs:                3 / 3
Provider calls:               15 / 15 successful
retries:                      0
hidden references:            0
Preview latency p50:           1886 ms
Preview latency p95:           2007 ms
```

This evidence does **not** establish human-specific claims such as final visual craft, aesthetic preference, delight, or target-player comprehension. Those claims remain explicitly unproven. Under `DEVELOPMENT_MODEL.md`, however, they are not an absolute G4 exit requirement: G4 asks whether one representative slice is worth producing and whether its quality can be produced repeatably. Comparative Product Value research and direct Station Zero falsification now answer the first question; the production/runtime pipeline answers the second.

Therefore:

```text
G4 production pipeline: accepted
G4 machine UX/runtime acceptance: accepted
G4 comparative Product Value: accepted
G4 exit: accepted
G5 bounded Production admission: accepted
Human-specific preference/value claims: unproven; validate during later product stages
```

## G4 calibration round — machine/agent perception gate

A second G4 round converted the remaining machine-falsifiable perception claims into a repeatable evaluator:

```text
pnpm eval:v3:g4
```

The accepted 2026-08-14 calibration run produced:

```text
findings:           25
passed:             25
failed:              0
critical failures:   0
major failures:      0
```

The evaluator covers desktop/mobile hierarchy, horizontal overflow, mobile DOM/Tab reading order, repeated three-Turn deliberation/resolution, exact Preview→Aftermath action/front continuity, specialist silhouette discrimination, media-failure fallback, reduced-motion behavior, a dedicated status announcer, and key-text contrast proxies.

### Defects found and corrected

The calibration was not a ceremonial pass. It falsified three production assumptions:

1. **Busy overlay authority was incomplete.** Pointer input was blocked, but keyboard focus could still enter stale Mission controls. Busy Mission content is now `inert` with `aria-busy=true`, so pointer and keyboard authority agree while the World is frozen.
2. **The whole application was an over-broad live region.** `#app aria-live=polite` could cause large repeated Mission re-announcements on each render. It is now ordinary content plus one persistent atomic status announcer that emits only short truthful lifecycle boundaries: deliberation started, plan ready, resolution started, aftermath ready.
3. **Mobile visual order disagreed with accessibility reading order.** CSS placed Commander Order before Situation, but the DOM remained Situation-first; the scrollable map therefore entered Tab order before controls that appeared visually above it. Runtime presentation now reorders the mobile DOM itself (`Planning → Situation`) while restoring `Situation → Planning` on desktop, aligning visual, screen-reader and keyboard order.

### Calibration evidence

Representative retained facts from the passing evaluator:

```text
Mobile Commander Order top:           411 px
Mobile tactical map top:             1642 px
Mobile DOM order:                    topbar → resources → first-command → planning → situation
Mobile first map Tab stop:           after all Commander Order controls
Specialist alpha-silhouette minimum: 51 / 576 pixels different
Media failure:                       E/M/S + aria-label identity retained
Reduced motion:                      specialist animation = none
Repeated deliberation Turns:         3 / 3 frozen, inert, announced, sealed
Preview Rescue intents:              3 each Turn
Sealed enemy plans:                  2 each Turn
Preview→Aftermath planned actions:   exact for all sampled Actors/Turns
Plan Impact→Plan Review fronts:      exact for all sampled Turns
Minimum sampled text contrast:       6.70 : 1
```

These measurements establish **structural perceptual legibility and accessibility consistency**, not subjective visual quality.

Post-calibration regression receipt:

```text
repository tests:             305 / 305 passed
registered v2 browser E2E:   passed
v3 20-Turn browser E2E:      passed
v3 browser errors:           0
live holdout preflight:      3 / 3 verified Runs
live Provider calls:         15 / 15 successful
live retries:                0
live hidden references:      0
live Provider latency p50:   1932 ms
live Provider latency p95:   2520 ms
live Preview latency p50:    2446 ms
live Preview latency p95:    2557 ms
```

### Human-validation residue after G4

After this calibration, the following claims are closed at machine/agent evidence level:

- command appears before detailed Situation on mobile in geometry, DOM and keyboard order;
- live deliberation/resolution cannot accidentally expose stale controls or advance World state;
- lifecycle changes are announced without turning the entire app into a live region;
- three Rescue specialists retain distinct shape identity plus textual fallback;
- current sampled critical text clears contrast proxy thresholds;
- reduced-motion and missing-media paths retain usable semantics;
- Preview actions/fronts are the same commitments later shown in Aftermath review.

The following remain **human-only product claims** and are deliberately not inferred from the evaluator:

- whether the tactical art direction feels coherent, attractive, or distinctive;
- whether players recognize the three specialist marks quickly without being told their mapping;
- whether repeated 1.5–2.0s live deliberation feels suspenseful/meaningful rather than slow;
- whether Plan Impact/Preview/Aftermath explanations improve real player decisions instead of merely being readable;
- whether the delegated-command fantasy is understood and preferred by the target audience;
- delight, attachment, replay desire, market appeal, or willingness to return.

These claims remain important, but they now belong to **later product validation**, not an invented pre-G5 veto. G5 may scale only the design space already justified by the representative slice and Product Value evidence; Alpha/Beta/product validation must still test the actual game rather than a questionnaire about concepts.

Current lifecycle judgment:

```text
G4 production pipeline:                    accepted
G4 machine runtime/UX acceptance:          accepted
G4 machine/agent perception calibration:   accepted
G4 comparative Product Value:              accepted
G4 exit:                                   accepted
G5 bounded Production admission:           accepted
Human delight / preference / market value: unproven
```

## Purpose

G3 proved that the Station Zero v3 kernel is playable, strategically non-trivial, and capable of bounded live-Agent realization. G4 now asks a different pair of questions:

```text
Is this final-ish form worth playing?
Can we repeatedly produce this quality at an understood cost?
```

This slice must therefore improve **player-perceived command, identity, waiting, and consequence** without inventing another gameplay system.

The current browser + 2D tactical representation remains the default. Godot, Blender, 3D conversion, campaign/meta progression, and broad content production are outside this slice unless this work produces direct evidence that they are required.

---

## Current measured baseline

A 2026-08-14 real Chromium geometry audit of the current `/v3` surface measured:

| Surface | Desktop 1440×1100 | Mobile 390×844 |
| --- | ---: | ---: |
| topbar | y 32–106 | y 12–78 |
| resources | y 122–211 | y 94–285 |
| first-command orientation | y 223–252 | y 297–369 |
| tactical map | y 356–902 | y 502–888 |
| specialists | y 356–586 | y 1105–1334 |
| objectives | y 711–971 | y 1459–1735 |
| Commander Order | y 1004–1508 | **y 1768–2469** |

Desktop can see the tactical Situation and reaches Command at the bottom of the first viewport. Mobile receives the first-command instruction but the actual Commander controls are more than two viewport heights below the page origin.

The current media baseline is also intentionally sparse:

- one generic 3-frame Rescue expression sprite sheet;
- system/hazard SVG signal assets;
- Tiled-authored semantic layout;
- no distinct Engineer/Medic/Security portrait/token source;
- no product audio assets;
- a generic full-screen spinner for Agent deliberation.

These are the G4 production pressures. They are not reasons to change the game engine or representation.

---

## Slice experience target

The representative slice is the existing real encounter, with production investment concentrated on the repeated Turn experience:

```text
Situation
→ Commander Order
→ live Agent deliberation
→ Plan Preview
→ Commit
→ simultaneous consequence
→ Aftermath
```

The same production language must remain coherent through terminal Debrief, but G4 does not authorize additional missions solely to create volume.

Working art direction:

> **salvage-operations tactical instrument panel** — dark operational surface, restrained high-contrast signals, specialist identity carried by compact authored marks rather than decorative illustration, and motion/audio reserved for state change.

The direction is intentionally compatible with the existing browser/tactical UI and does not require a cinematic or 3D scene pipeline.

---

# Production Claim A — Mobile command proximity

## Problem

The mobile player is told to command before the actual command surface is reachable. The full map + specialists + objectives create a long observation inventory between intent and action.

## Game-owned semantic requirement

The information order remains:

```text
minimal Situation awareness
→ actionable Commander Order
→ detailed tactical Situation
```

On desktop, the current wide Situation-first layout may remain because map and Command are both near the first viewport boundary.

On mobile, the DOM/CSS presentation may reorder existing projections, but it may not omit or fabricate World truth.

## Acceptance

At 390×844 after starting a fresh Run:

- first-command orientation remains visible;
- Commander Order begins before y=900;
- full tactical map remains available below Command;
- no gameplay field is removed;
- desktop retains Situation-first layout;
- keyboard/focus semantics remain valid.

---

# Production Claim B — Specialist visual identity

## Problem

The tactical map currently projects every own Actor as the same `R` token. The player has three mechanically distinct specialists but weak visual identity at the point where spatial decisions are read.

## Game-owned semantics

Exact identities:

```text
engineer-imani  → Engineer
medic-reyes     → Medic
security-chen   → Security
```

The visual asset may distinguish these Actors but must not change state, health, capability, location, or hidden-information boundaries.

Enemy contacts remain bounded contacts; do **not** visually reveal a hidden Pirate/Hive identity merely because Studio has art for it.

## Studio production brief

Produce one editable Aseprite source with three 24×24 tactical portraits/tokens:

- Engineer: technical/tool silhouette;
- Medic: medical/support silhouette;
- Security: shield/guard silhouette.

Requirements:

- readable at 18–24 CSS pixels;
- restrained tactical palette compatible with existing dark UI;
- identity must survive grayscale/shape differences rather than hue alone;
- no text baked into the pixel asset;
- export exact runtime PNG + JSON frame metadata;
- keep editable `.aseprite` source in `assets/station-zero-v3/`;
- map token and specialist card may consume the same source.

## Acceptance

- three own Actors render distinct visual marks on map and Specialist cards;
- source and runtime derivative are both retained;
- actor identity mapping is deterministic and tested;
- contact projection remains generic/unknown where World Knowledge is bounded;
- reduced network/media failure falls back to readable textual identity rather than hiding the Actor.

---

# Production Claim C — Live deliberation experience

## Problem

Current live-Agent preview latency is measured in seconds. The UI presents this as a generic blocking spinner over a blurred screen, which communicates technical waiting rather than delegated command.

## Game-owned semantics

During Preview generation:

```text
World revision does not advance
Commander Order is being bound
Rescue specialists are deliberating from bounded Context
Pirate/Swarm commitments remain sealed
no outcome has happened yet
```

The presentation must not invent sub-agent completion progress unless the server actually reports it.

## Expression brief

Replace generic “Agents are deliberating…” presentation with a bounded **Deliberation** state that retains the current tactical context and states only facts known from the request lifecycle:

- `World paused at Turn N`;
- `Binding Commander Order`;
- `Engineer / Medic / Security are selecting admitted actions`;
- `Enemy commitments remain sealed`;
- elapsed time may be shown because it is client-observed fact;
- never show fake percentage progress.

Motion may pulse specialist marks, but `prefers-reduced-motion` must produce a static equivalent.

## Acceptance

- Preview generation no longer visually replaces the game with an opaque generic loading state;
- current Situation remains perceivable but not interactable while request is in flight;
- elapsed waiting time is truthful;
- no fake model/internal progress is exposed;
- fixture and live Provider use the same player-facing state.

---

# Production Claim D — Representative audio

## Purpose

Audio should reinforce state boundaries rather than decorate every event.

## Studio production brief

Produce editable/generatable source recipe plus runtime derivatives for three short non-verbal cues:

1. `plan-ready` — restrained high-frequency confirmation when a new Preview becomes available;
2. `commit` — lower, weightier command confirmation on explicit Commit input;
3. `aftermath` — short resolving signal after authoritative Turn consequence returns.

Constraints:

- no speech;
- no copyrighted samples;
- short, low-fatigue cues suitable for repeated 20-Turn sessions;
- runtime browser format should be compact and locally served;
- no autoplay before user interaction;
- player can mute cues;
- audio failure must not affect gameplay execution;
- audio does not reveal hidden outcome information before authoritative response.

## Acceptance

- exact source/generation recipe is retained;
- runtime outputs are deterministic from that source recipe where practical;
- mute state is local presentation state, not Game truth;
- Plan cue plays only after Preview response;
- Commit cue may play on the player's explicit click;
- Aftermath cue plays only after authoritative committed response;
- tests do not require physical audio output but verify binding and controls.

---

# Production boundary

## Game owns

- Actor IDs and role semantics;
- which state is shown and when;
- mobile information ordering;
- Preview/Commit/Aftermath state boundaries;
- audio cue trigger identity;
- accessibility behavior and fallback semantics;
- runtime asset integration.

## Studio owns

- editable specialist pixel source;
- exported sprite runtime assets;
- cue sound design / generation recipe;
- runtime audio derivatives;
- medium-level QC evidence.

No cross-repository universal asset schema is created by this slice.

---

# G4 exit criteria for this round

This first G4 production round is accepted when:

- all four production claims above are implemented on the real `/v3` surface;
- Game retains exact source → derivative mapping for new media;
- desktop and mobile browser acceptance cover the changed information order;
- reduced-motion and mute paths are explicit;
- `pnpm check`, current-product E2E, and v3 E2E remain green;
- live Provider preflight remains bounded and hidden-safe;
- the slice produces no evidence requiring Godot, Blender, 3D, or broad content expansion.

All criteria above are now satisfied. Together with `STATION_ZERO_V3_PRODUCT_VALUE.md`, the slice also supports the G4 value question strongly enough to enter bounded G5 Production. This proves a **repeatable first production loop and a defensible production thesis**, not final commercial polish. Human-specific aesthetic, fun, retention, and market claims remain scoped until later targeted product validation exists.
