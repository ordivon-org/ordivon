# M7 — Foundational Media Expansion Program

## Objective

Expand Studio's media world model from three mature/current consumers plus three provisional baselines into a falsifiable seven-foundation research program:

```text
Writing
Still Visual
Audio
Motion / Video
Interactive
Spatial / 3D
Live / Realtime
```

The goal is not profile count. The goal is to discover the smallest set of medium distinctions that lets an Agent predict meaningful production failures, choose medium-native expression, inspect the real artifact, and transfer learning without confusing platform fashion with durable structure.

The canonical topology is [`media-topology.md`](./media-topology.md).

## Research contract

Every foundational pass must answer the same questions.

1. **Observer relation** — how does the audience encounter and control the artifact?
2. **Irreducible affordance** — what can this medium express/control that the Core alone under-specifies?
3. **Manipulable variables** — what can the producer deliberately change?
4. **Hard constraints** — what is mechanically, legally, accessibility-, synchronization-, spatial-, latency-, or delivery-bound rather than taste?
5. **Durable craft priors** — what professional defaults are useful but falsifiable?
6. **Implicit semantics** — how can medium properties accidentally become claims?
7. **Render / inspect boundary** — what is the real artifact and how can an Agent perceive it?
8. **Alternate representation** — what information is lost when the medium is unavailable and how can accessibility/translation preserve function or meaning?
9. **Composition boundary** — which responsibilities belong to another foundation, encounter profile, distribution surface, or tool adapter?
10. **Falsifier** — what evidence would show that this medium does not deserve its own profile or that a retained prior is too broad?

No pass may graduate by literature summary alone. Each needs real artifact pressure.

## Evidence ladder

```text
external literature / standards / durable craft
                     ↓
provisional medium hypothesis
                     ↓
minimal discriminating production
                     ↓
rendered / audible / playable / live inspection
                     ↓
semantic + technical failure audit
                     ↓
cross-medium transfer / ablation
                     ↓
ordinary production reuse
                     ↓
profile promotion, narrowing, split, merge, or rejection
```

A profile becomes `active` only after it changes real production decisions and survives at least one materially different use from the experiment that motivated it.

## M7-0 — Topology and schema

### Deliverables

- seven-foundation topology;
- common mature-profile contract;
- explicit distinction among `foundation`, `specialization`, `encounter`, `distribution context`, and `tool adapter`;
- profile graduation/demotion criteria;
- cross-medium ablation protocol.

### Pass condition

An Agent should be able to classify a new form such as podcast, livestream, VR film, presentation, interactive article, or game without inventing a new foundational profile merely from its industry label.

## M7-1 — Seven reconnaissance passes

Each pass combines theory, mature craft, standards, current tools only where they expose constraints, and existing Ordivon production evidence.

### M7-W — Writing

**Current authority:** active Writing profile.

Research expansion:

- symbolic semantics versus rendered typography;
- argument, explanation, narrative and script as specializations;
- reader-controlled pace and nonlinear rereading;
- citation/evidence placement as part of rhetoric;
- compression and summarization failure;
- translation/localization and semantic preservation;
- text accessibility separate from publisher accessibility.

**Discriminating experiment:** express one evidence-bound proposition as a concise explanation, an argumentative passage, and a narration script while holding source truth fixed. Test whether Writing-specific priors predict epistemic drift and reader-model changes independently of Web/video layout.

**Ablation:** remove Writing profile and give the Agent only Core + Web/Motion. Measure whether claim order, paragraph rhetoric and title/body certainty defects increase.

### M7-S — Still Visual

**Current authority:** provisional baseline.

Research expansion:

- photography, illustration, graphic design and diagrams;
- simultaneous visual hierarchy versus authored timeline;
- figure/ground, scale, depth cues, crop and viewing distance;
- typography as visual form versus Writing semantics;
- color management, reproduction and alternate-text boundaries;
- data/diagram truth semantics.

**Discriminating experiment:** communicate the same bounded system relation through a diagram, editorial graphic and photographic/illustrative key visual. Hold written claim text constant. Inspect whether geometry, scale, color, crop or symbol creates unsupported meaning.

**Ablation:** use only generic Core hierarchy/grouping priors. If repeated still-specific crop, reproduction, visual-weight or diagram-semantics defects survive, Still Visual earns a stronger profile.

### M7-A — Audio

**Current authority:** provisional baseline plus narration production evidence.

Research expansion:

- speech/prosody;
- sound design, ambience and silence;
- music expectation, rhythm, harmony, timbre and affect;
- masking/intelligibility;
- loudness and true-peak engineering;
- stereo/spatial field and playback variation;
- transcript/caption/description relationships;
- object-based/spatial audio as possible Audio × Spatial composition.

Useful standards anchors include ITU-R BS.1770 for programme loudness/true peak and W3C/WAI time-based-media accessibility guidance. These constrain delivery/measurement; they do not define artistic quality.

**Discriminating experiment:** produce the same narration with controlled changes to prosody, silence, ambience/music and loudness while keeping words identical. Test which observer inferences change without textual change.

**Ablation:** replace audio reasoning with Writing + Motion timing priors. If certainty, affect, masking, spatial hearing or playback failures remain unexplained, Audio is irreducible.

### M7-M — Motion / Video

**Current authority:** active Motion / Video profile.

Research expansion:

- camera versus graphic motion;
- edit/montage semantics;
- pacing and event segmentation;
- continuity and discontinuity;
- audiovisual synchronization/counterpoint;
- live-action versus generated/animated source;
- frame/time identity and delivery metadata;
- video-only accessibility and descriptive alternatives.

SMPTE time-code practice is a useful engineering anchor for exact temporal identity; W3C treats audio/video as time-based media with distinct live/prerecorded accessibility obligations.

**Discriminating experiment:** keep every still frame/factual element available but alter ordering, duration and motion. Test which causal, urgency and state-change inferences appear only through temporal construction.

**Ablation:** reduce the artifact to a contact sheet plus Audio. If pacing, continuity or montage failures disappear from the model but remain in playback, Motion / Video remains irreducible.

### M7-I — Interactive

**Current authority:** provisional generic profile; Web owns a mature concrete consumer profile.

Research expansion:

- action → state → feedback loops;
- affordance and state legibility;
- reversibility/recovery;
- input modality;
- latency versus failure semantics;
- branching/focalization and information entitlement;
- accessibility of state-changing controls;
- dark-pattern/pressure semantics;
- interactive narrative versus generic UI.

**Discriminating experiment:** build one deterministic interactive explanation with at least one reversible choice, one delayed operation and one recoverable error. Compare screenshot/source review against trajectory-based inspection.

**Ablation:** represent all states as a static document or prerecorded video. If the critical defects concern action consequence, hidden state or recovery rather than presentation alone, Interactive is irreducible.

### M7-X — Spatial / 3D

**Current authority:** candidate; no current foundational profile.

Research expansion:

- explicit reference spaces and transforms;
- viewpoint/head/camera pose;
- scale, depth, occlusion and parallax;
- navigation/locomotion and reach;
- world anchoring and persistence;
- embodiment and proxemics;
- spatial audio composition;
- VR/AR comfort and safety;
- 2D render versus actual spatial encounter.

OpenXR's explicit `XrSpace` reference-space model is a useful engineering anchor: spatial coordinates only have meaning relative to declared reference spaces. WebXR similarly makes device pose, viewpoint and tracked movement part of the render loop. These are technical facts, not aesthetic laws.

**Discriminating experiment:** create one simple scene whose semantic judgment changes under viewpoint, scale, occlusion or reference-frame manipulation while object facts remain constant. Inspect both 2D captures and the spatial encounter.

**Ablation:** pre-render the experience as fixed video. Any semantic/comfort/agency effect that disappears when viewpoint and spatial relation are frozen identifies the spatial contribution.

### M7-L — Live / Realtime

**Current authority:** candidate; no current foundational profile.

Research expansion:

- future not yet fixed at encounter time;
- live state currentness and liveness proof;
- latency, jitter and synchronization;
- improvisation and turn-taking;
- interruption, moderation and correction;
- audience/world feedback;
- failure recovery under public consequence;
- delayed versus realtime versus prerecorded signaling;
- live accessibility, especially captions and alternate streams.

WebRTC's current W3C Recommendation and the IETF WHIP standard are useful technical anchors for realtime media transport/ingest. W3C accessibility guidance separately distinguishes live and prerecorded time-based media. These standards support the claim that liveness creates operational constraints; they do not by themselves prove a separate artistic foundation.

**Discriminating experiment:** run one bounded Agent-hosted live explanation/performance with scripted source facts but unpredictable interruption and one injected stale-state/correction event. Compare the live trace with an edited replay of the same material.

**Ablation:** give an Agent the full event history in advance and let it produce a polished replay. Any decision, correction, pacing, moderation or trust failure that only exists when the future is unknown is evidence for Live / Realtime irreducibility.

## M7-2 — Cross-medium transfer matrix

Do not run seven isolated silos. Use the same bounded source proposition/event across multiple media.

Minimum transfer set:

```text
Writing ↔ Still Visual
Writing ↔ Audio
Still Visual ↔ Motion/Video
Motion/Video ↔ Interactive
Interactive ↔ Spatial/3D
Motion/Video ↔ Live/Realtime
Interactive ↔ Live/Realtime
```

For each pair record:

- what transfers: event model, focalization, tension, hierarchy, causal relation;
- what does not transfer: geometry, timing assumptions, interaction grammar, spatial coordinates, live future knowledge;
- new semantic leaks introduced by translation;
- alternate representations that preserve meaning versus merely preserve content fragments.

## M7-3 — Three mandatory ablation families

### A. Medium-profile ablation

Core + all other media, but remove the target profile. Does failure detection or production quality degrade on target-medium tasks?

### B. Encounter freezing

Convert the medium into a less expressive encounter where possible:

```text
Interactive → static state sequence
Spatial → fixed-camera video
Live → prerecorded replay
Motion → still contact sheet
Audio → transcript
```

Measure which consequences disappear. The lost consequences help locate irreducible structure.

### C. Surface-transfer falsifier

Mechanically copy the successful surface form from one medium into another while retaining meaning. If it fails while event/focal/tension transfer succeeds, that is evidence for medium-native craft rather than universal style.

## M7-4 — Graduation rules

A provisional/candidate foundation may become an active profile only when all are true:

1. at least one real production exposes a medium-specific failure or opportunity;
2. the profile changes an Agent decision before final promotion;
3. the change survives real render/listen/play/experience inspection;
4. at least one materially different production or transfer confirms usefulness;
5. an ablation shows meaningful information is lost without the profile;
6. the retained prior is narrower than the evidence and names its falsifier;
7. no simpler specialization/context explanation fits the evidence better.

Demotion/merge remains normal if later evidence removes the distinction.

## M7-5 — Composite-form world model

Only after foundation pressure should Studio map common production forms.

Candidate composite families:

- article/report/book;
- poster/key visual/social card;
- podcast/audio drama/music release;
- film/video essay/short-form motion;
- website/app/interactive article;
- presentation/performance;
- game;
- livestream/live event;
- 3D visualization;
- VR/AR/XR experience;
- installation;
- hybrid Agent conversation/performance.

Each composite should declare the foundations it consumes and its encounter/distribution context instead of defining another universal creative theory.

## Research ordering

The seven should not receive equal budget merely for symmetry.

Recommended order:

```text
M7-0 topology/schema
    ↓
Still Visual + Audio + Interactive
    ↓
Spatial/3D + Live/Realtime
    ↓
Writing + Motion/Video regression / boundary refresh
    ↓
cross-medium transfer + ablation
    ↓
profile graduation
```

Reason: Writing and Motion already have active evidence; the greatest information gain is currently in the three provisional foundations and the two missing candidates. Existing mature profiles are controls, not neglected areas.

## Immediate first experimental packet

Start with one source-bounded proposition/event and derive seven deliberately minimal artifacts. Avoid polished showcase work.

```text
W: 250–500 word explanation
S: one still diagram/key visual
A: 45–90 second audio expression
M: 15–30 second motion expression
I: one 2–4 state interactive encounter
X: one simple navigable/viewpoint-dependent 3D scene
L: one bounded 3–5 minute live/realtime encounter
```

The objective is not to rank which medium is best. The objective is to discover which variables and failure modes become visible only when each observer relation is real.

## Relationship to Web

Web remains an important consumer, not the owner of the seven-foundation theory.

Web should consume combinations such as:

```text
Writing + Still Visual + Interactive
+ optional Motion/Video + Audio
```

and retain browser-specific authority over responsive layout, semantic HTML, navigation, accessibility, publication state and browser encounter. It should not absorb generic Interactive, Still Visual, Audio, Spatial or Live theory merely because those media can appear in a browser.

## Stop conditions

Stop expanding taxonomy when:

- a proposed new medium is explained adequately as a specialization/composition/context;
- a profile accumulates terminology but does not change real production decisions;
- experimental evidence only measures Agent preference rather than artifact consequence;
- a platform convention is being mistaken for medium law;
- seven-way symmetry becomes more important than explanatory compression.

The desired endpoint is the **smallest revisable topology that predicts real creative and semantic failure across the widest set of human-facing artifacts**.
