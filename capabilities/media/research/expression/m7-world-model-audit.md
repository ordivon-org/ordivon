# M7 media world-model audit

## Scope

This audit records the actual Studio/Web substrate that the foundational-media program is allowed to build on. It separates current code truth from taxonomy hypotheses so M7 does not redesign infrastructure merely because the media vocabulary expands.

Observed source state:

```text
Studio canonical base: 8d583cb3cbc62aa59c9e5b611a1db4424b58b356
M7 design candidate:  2dfc6a148ae614d8c151f728985b690c98a358ee
Web observed HEAD:    ba57d91e7dd0a89cacec9032fe6f565c7cc15eaf
```

## 1. What is already genuinely cross-medium

The strongest parts of Studio do not encode a video-first ontology.

### Production identity and authority

`docs/media-model.md`, the production schemas, and `src/ordivon_studio/models.py` already separate:

```text
Blob
Asset
Claim
TimedText
Editorial Source
Receipt
Production
Output
```

The useful invariants are source authority, exact bytes/revisions, provenance, rights, recoverability, output identity, and the distinction between whole-production lifecycle and one-output delivery state. These survive media expansion.

`Asset` is media-type generic. Its `technical` object is intentionally open and Blob identity is based on exact bytes rather than a fixed media class.

### Cross-medium cognition

`research/expression/creative-system.md`, `protocol.md`, and `knowledge-model.md` already establish the shared cognitive responsibilities:

```text
FRAME → BIND → EXPRESS → RENDER → AUDIT → DECIDE
```

They explicitly keep medium, distribution surface, audience/observer, encounter, and equipment above a slower Core. M7 therefore does not need another universal creative loop.

### Research validity

R4-R6 already provide reusable experimental institutions:

- controlled perturbation versus control;
- profile signatures and structural distance;
- exact artifact/encounter identity;
- search-history and candidate-freeze discipline;
- pristine holdout/OOS boundaries;
- typed consequence instead of one universal quality score;
- `no-op` as a valid result.

The deletion/distinction program should reuse these institutions rather than invent a second evaluation framework.

## 2. Where the current model is still media-shaped

### Flat profile registry

`research/expression/profiles/index.json` currently places these peers in one registry:

```text
web
motion-video
writing
still-graphic
audio-music
interactive
```

They are not ontologically homogeneous. Writing is primarily a symbolic-expression system; Motion/Video introduces authored time; Interactive changes the observer/action relation; Web is a publication/runtime consumer. The registry is operationally useful but should not be mistaken for a complete media ontology.

Do not refactor the registry merely to make the taxonomy prettier. Refactor only after ablation shows which distinctions deserve durable authority.

### Production schema is deliberately narrower than the research world model

`schemas/production.schema.json` currently exposes output kinds:

```text
article
video
audio
image
captions
interactive
publication-package
```

and `workingProfile` currently has only medium-applicable AV fields such as frame rate, canvas, color, and audio parameters.

This is not evidence that Spatial/3D, Live/Realtime, or Haptic/Physical are invalid media candidates. It is evidence that they do not yet have enough ordinary-production pressure to deserve canonical Production fields. Early M7 experiments should keep their evidence in bounded experiment receipts/artifacts instead of expanding the main schema speculatively.

### Perception equipment is asymmetric

`src/ordivon_studio/rich_perception.py` has real analyzers for:

```text
article structure
video temporal/change/luma/saturation structure
audio temporal/spectral structure
A/V temporal coupling
```

It already implements control-versus-perturbation separation and explicit interpretation boundaries. This is strong reusable machinery.

Missing equivalents are:

- Still Visual: composition/crop/reproduction/diagram-semantics inspection beyond generic image bytes;
- Interactive: action → state → feedback trajectory inspection;
- Spatial/3D: viewpoint/reference-space/occlusion/scale encounter inspection;
- Live/Realtime: currentness/latency/interruption/correction event-trace inspection;
- Haptic/Physical challenger: tactile output/embodied-contact evidence if it survives foundation tests.

The right M7 engineering target is therefore **new observation boundaries**, not one giant universal multimodal feature vector.

## 3. Web is already an encounter laboratory

Web's `design/context.json` correctly treats Studio as upstream expression research while Web owns browser-specific constraints and rendered interaction state.

The R6 browser encounter harness already records:

```text
explicit assignment + propensity
real Chromium exposure
exact variant digest
representative screenshot digest
visible-text digest
viewport-intersecting evidence
outcome/event receipts
```

This is enough to reuse Web as the first Interactive experimental substrate. M7-I should extend the encounter from one rendered exposure into explicit state/action trajectories, delayed feedback, recoverable error, and reversal—not build another browser experiment system.

## 4. External discipline / industry cross-check

The first reconnaissance supports decomposition by observer relation rather than file type or platform label.

### Media and publishing standards

W3C keeps audio, video, timed text, realtime communication, immersive Web, graphics/GPU, games, publishing, and accessibility as overlapping technical areas. WCAG time-based-media guidance separately distinguishes audio-only, video-only, synchronized media, interactive combinations, and live versus prerecorded encounters. This argues against treating `Web` or one platform as a sensory foundation.

### Audio engineering

AES Technical Council partitions audio into production, live performance, interactive media/games, motion picture, spatial audio, broadcast/online delivery, network audio, measurement/sound quality, algorithms, acoustics, and more. This strongly falsifies any assumption that `audio-music` is a complete audio model. Speech, music, sound design, spatial audio, and live audio begin as Audio specializations and should split only if shared priors repeatedly fail.

ITU-R BS.1770 supplies a current engineering anchor for programme loudness and true-peak measurement, including advanced/object-based rendering. It constrains measurement; it is not an aesthetic law.

### HCI / interaction

SIGCHI's current conference ecology independently distinguishes interactive media experiences, multimodal interaction, spatial user interaction, tangible/embedded/embodied interaction, virtual reality, interactive surfaces/spaces, and interface systems. Interaction, spatiality, embodiment, and multimodality therefore deserve separate tests rather than being collapsed into `Web`.

### XR / spatial

OpenXR requires explicit reference spaces for interpreting coordinates and exposes viewpoint-relative and world-relative spaces. Spatial semantics are therefore not equivalent to merely having a 3D asset in the production pipeline.

OpenXR also exposes haptic output; W3C's Vibration API explicitly defines vibration as tactile feedback. This creates a serious `Haptic / Physical` challenger to the seven-foundation set.

### Live / realtime

WebRTC and IETF WHIP establish current realtime media and ingest boundaries, while accessibility standards distinguish live and prerecorded time-based media. These are strong engineering reasons to test liveness separately from interaction, but they do not by themselves prove an independent artistic foundation.

## 5. Revised ontology stance

Do not treat seven foundations as a closed periodic table.

Use:

```text
first-pass foundation hypotheses
    Writing
    Still Visual
    Audio
    Motion / Video
    Interactive
    Spatial / 3D
    Live / Realtime

challenger lane
    Haptic / Physical
    Data / Diagram grammar
    Embodied / performance-social relation
    future sensory media
```

A challenger is promoted only if deletion/collapse shows that the first-pass set cannot explain its observer relation, failure modes, inspection boundary, or hard constraints compactly enough.

## 6. What M7 should test, not assume

The important question is not whether a category exists in an industry. It is whether a profile changes Agent decisions enough to justify its cost.

Every candidate must therefore face:

1. **Deletion** — remove the target profile.
2. **Wrong-profile swap** — provide a neighboring but incorrect profile.
3. **Sham profile** — provide fluent generic creative advice with similar context/token mass but no target-specific information.
4. **Collapse / merge** — replace two candidate profiles with one shared profile.
5. **Encounter freezing** — convert interaction/spatial/live/motion/audio into a less expressive representation where possible.
6. **Cross-medium transfer** — retain event/focalization/tension while deliberately refusing surface-copy transfer.
7. **ROI** — compare quality/error-detection/revision benefit against context, compute, rendering, tool, maintenance, and failure-surface cost.

A useful target pattern is:

```text
correct profile > Core only > wrong/sham profile
```

for target-specific failure detection or production consequence. If correct and wrong profiles perform similarly, the supposed medium knowledge is probably generic Core knowledge or ceremonial terminology.

## 7. Engineering consequence

M7 should initially add experiment fixtures and bounded observation equipment only where required. It should **not** yet:

- widen canonical Production output enums for taxonomy completeness;
- add Spatial/Live/Haptic registry authorities before evidence;
- create one shared scalar `media quality` score;
- make Web own generic Interactive theory;
- make Studio own source-domain truth;
- create a profile per platform, genre, tool, codec, or file type.

The next implementation pressure is M7-S + M7-A + M7-I using one source-bounded proposition, followed by Spatial/3D and Live/Realtime. Haptic/Physical remains an explicit challenger sampled during the Spatial/Interactive tranche.