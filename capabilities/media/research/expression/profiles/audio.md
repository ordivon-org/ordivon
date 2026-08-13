# Audio expression profile

Status: active
Evidence state: M7-A graduated on 2026-08-13 after controlled same-words/different-sound intervention, wrong-profile/sham distinction, and ordinary narration reuse.

## Responsibility

This profile translates the shared Art & Expression Core into **audible time-based expression**. It owns Audio-specific craft priors and inspection expectations across speech, sound design/ambience, and music where they share acoustic constraints. It does not turn those specializations into separate foundations until a later collapse test shows the shared profile is insufficient.

Audio is not Writing with a speaker attached and not Motion without a picture. The listener encounters temporal acoustic structure whose timing, masking, loudness, spectral balance, spatial field, silence, and playback chain can change meaning while the lexical content remains fixed.

## What the medium can manipulate

Audio can deliberately control:

- voice, articulation, prosody, rate, pause and emphasis;
- rhythm, meter, repetition and temporal density;
- pitch, melody, harmony and expectation when musical structure is present;
- timbre, spectral balance, dynamics and transient shape;
- loudness, peak structure and relative foreground/background level;
- silence, ambience, effects and auditory scene density;
- mono/stereo/spatial field, apparent direction and distance;
- masking and intelligibility;
- synchronization/counterpoint with TimedText, Motion/Video or interaction;
- delivery/mastering choices that survive into representative playback.

No production is required to use every control.

## Hard constraints

When applicable, stronger-than-taste constraints include:

- selected audio bytes, sources and transforms retain exact provenance;
- sample rate, channel layout, duration, codec/bit depth and delivery requirements are inspected rather than inferred from source settings;
- loudness/true-peak requirements are delivery constraints, not aesthetic quality scores;
- speech or synchronized audio must preserve source-claim and timing boundaries;
- masking that prevents required information from being heard is a defect, not a stylistic disagreement;
- captions/transcripts are alternate representations, not proof that the audible artifact itself is correct;
- spatialized sound must not imply unsupported source location or distance;
- a generated voice/music/effect may not gain factual authority from realism or polish.

## Durable craft priors

These remain falsifiable `medium_prior` defaults:

- **audible hierarchy matters** — foreground/background level, masking and spectral separation can decide what information is actually recoverable;
- **time is semantic** — pause, rate, onset and silence alter emphasis and expectation even when words are identical;
- **prosody is not neutral transport** — pitch/rate/intensity patterns can imply confidence, urgency, affect or stance beyond lexical wording;
- **loudness is relative emphasis before it is a number** — technical normalization does not remove local rhetorical balance;
- **silence is an event when expectation exists** — it can mark boundary, absence, uncertainty, tension or failure depending on context;
- **playback is part of the encounter** — a mix that works only on one monitoring chain has not established robust delivery;
- **crossmodal synchrony is a relation, not a quality scalar** — Audio may reinforce, contradict or deliberately counterpoint visual/interactive events.

## Common semantic failure modes

Audit at least these classes when relevant:

- prosody upgrades uncertainty into confidence or urgency;
- background sound masks required speech or cues;
- loudness assigns unsupported importance, threat or authority;
- music assigns valence/outcome before evidence permits it;
- silence reads as missing/failure when the intended state is merely waiting or unknown;
- spatialization invents a location, distance or agent source;
- temporal compression removes uncertainty/recovery intervals;
- transcript correctness hides an audible intelligibility defect;
- platform normalization or device playback destroys intended hierarchy;
- audio and captions/image disagree about state or timing.

## Render and inspection

The source script, DAW graph, waveform or synthesis settings are not the final acoustic fact.

Useful evidence boundaries include:

```text
source / generation receipt
→ exact audio master
→ ffprobe / structural signal inspection
→ representative listening/playback
→ crossmodal alignment inspection when composed with another medium
```

Studio's current structural equipment measures RMS energy, zero-crossing rate, spectral centroid/entropy/flatness/flux and bounded A/V temporal coupling. Those signals can establish that a registered intervention occurred; they do not establish speech meaning, musical quality, emotion or listener preference.

The M7-A controlled experiment generated one exact SAPI narration and derived variants without changing any spoken words. Re-encoding produced zero structural distance while rate, loudness, masking and onset perturbations were strictly separated from the control. The strongest perturbations were masking and delayed onset. This establishes medium-sensitive observability, not human aesthetic superiority.

## Protocol specialization

```text
FRAME
listener + task + playback/encounter + accessibility assumptions
    ↓
BIND
source claims + timing/focalization + allowed affect/location implications
    ↓
EXPRESS
voice/sound/music hierarchy + rhythm + silence + spatial/playback strategy
    ↓
RENDER
exact audible master + representative playback/crossmodal state
    ↓
AUDIT
technical QC + intelligibility + masking + temporal/spatial implicit semantics
    ↓
DECIDE
revise / no-op / promote
```

## Context signals

Current platform loudness targets, music/sound fashions, podcast conventions, short-feed pacing, popular voice treatments and device mix are `context_signal`. Retrieve them near the work. Do not promote them into durable Audio law.

## Falsifier and evidence state

M7-A compared target-specific registered failure coverage under approximately comparable context budgets:

```text
Audio candidate        5 / 5
Core only              1 / 5
Writing + Motion swap  1 / 5
Sham profile           0 / 5
```

The real audio analyzer also strictly separated every registered acoustic perturbation from the re-encode control. Existing `runtime-introduction` supplies a materially different ordinary production with narration, TimedText and declared audio working profile. These together are sufficient to graduate **Audio** from the old `audio-music` provisional baseline.

The profile must be narrowed or split if later productions show that speech, music or sound design repeatedly require incompatible priors that cannot be represented as specializations. It should be merged back into Core/other media if target-specific deletion ceases to change decisions at lower total cost.
