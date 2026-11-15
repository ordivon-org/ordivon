# Ordivon Media · Existing LEGO / capability reference

**Reference, not registry:** these links resolve to the actual modules, native tools, Profiles and existing consumer receipts. Current tool schemas have one source in [agent_surface_contracts.py](../src/ordivon_studio/agent_surface_contracts.py) and selected execution is dispatched by [agent_surface.py](../src/ordivon_studio/agent_surface.py); actual output standing is determined by each Production and its natural Owner. For doing tasks use [Human](human-guide.md) or [Agent](../AGENTS.md) guidance; for rationale see [Studio architecture](../STUDIO.md).

| Real capability / LEGO | Natural implementation / existing mature dependency | Human task | Agent input → observed output and boundary |
| --- | --- | --- | --- |
| Agent tool discovery | [source-only contracts](../src/ordivon_studio/agent_surface_contracts.py), [selected dispatcher](../src/ordivon_studio/agent_surface.py) | See the available actions without installing or running a media provider | Nine stable schemas; discovery imports no providers, and validated selection imports only its needed implementation before exercising existing pre/post/evidence |
| Media activation / representation | [Constitution](../MEDIA.md), [authority](authority.md) | Decide whether a specific expression really needs Media | Source binding → scoped observer projection; not new source truth |
| Production / Claim / Output | [production context](../src/ordivon_studio/production_context.py), [models](media-model.md), [real works](../productions/) | Select work and review Claims | `studio_production_standing` then explicitly selected `studio_production_context`; no invented current intent |
| Exact Blob and local CAS | [assets.py](../src/ordivon_studio/assets.py), [storage](storage-layout.md) | `ordivon-studio hash`, `archive`, `materialize` | Selected files → SHA-256 and verified recovery; Artifact/source owns bytes |
| Native stream inspection | [QC](../src/ordivon_studio/qc.py) | `ordivon-studio probe` | `qc.probe_media` via FFprobe → stream/container facts, not delivery approval |
| AV Profile | [Profile](../processing/profiles/av-sdr-web-1080p30-noaudio.json), [FFprobe adapter](../processing/bin/probe-av.sh) | Check selected video stream, codec, geometry and color | `videoSource` + pinned Profile → native evidence |
| Audio Profile | [Profile](../processing/profiles/audio-program-48k-mono-lufs23.json), [FFmpeg adapter](../processing/bin/probe-audio.sh) | Check a specific loudness/true-peak target | `audioSource` + FFmpeg `loudnorm` → measurements, not listening preference |
| OTIO interchange | [Profile](../processing/profiles/otio-runtime-introduction-v2.json), [OTIO adapter](../processing/bin/probe-otio.sh) | Check timeline cut, track and clip facts | `editorialTimeline` + `otiotool` → editorial evidence, not embedded AV bytes |
| TTML and delivery timed text | [Profile](../processing/profiles/timed-text-runtime-introduction-en.json), [TTML adapter](../processing/bin/probe-timed-text.sh), [source timed_text.py](../src/ordivon_studio/timed_text.py), [Lean model](../formal/TimedTextDeliveryPrecision.lean) | Preserve integer source ticks; reject Cue intervals that collapse in SRT/WebVTT | Exact rational millisecond conversion + explicit positive duration, native FFprobe/ttconv readback; does not establish text meaning |
| Rendered media review | [review.py](../src/ordivon_studio/review.py), [review consumption](review-consumption.md) | `ordivon-studio review-video --help` | Selected render and Claim → disposable review packet; semantic audit stays separate |
| Source frame perception | [perception.py](../src/ordivon_studio/perception.py), [perception guidance](artifact-perception.md) | Inspect frames, contact sheets and timing | FFmpeg-native frames → visual observations, not inferred scene importance |
| Deterministic motion | [Remotion source](../apps/motion-remotion/), [inner loop](fast-inner-loop.md) | Edit and render a selected motion work | Editable source + real renderer → selected output; no hidden publication |
| Shared visual primitives | [React/SVG components](../packages/visuals/), [identity tokens](../packages/identity/) | Reuse typography, colors and visuals | DTCG-derived values + real package consumers; no extra token truth |
| Equipment planning | [equipment.py](../src/ordivon_studio/equipment.py), [equipment world](../research/equipment/equipment-world.json) | `ordivon-studio equipment --help` | `studio_equipment_propose` → availability/operation proposal, not execution |
| Optional Resolve NLE | [official native API guide](resolve-native.md), [historical Free-version compatibility](resolve-compatibility/resolve-free-21.0.3.7.md) | Resolve's installed `Developer/Scripting/README.txt` and a native Windows Python/Lua session | Blackmagic owns edits; Ordivon verifies selected source/output and never infers native acceptance from old test receipts |
| Creative navigation | [index](../src/ordivon_studio/creative_index.py), [Creative Library](../creative-library/README.md) | Find work and versions | `studio_creative_index_query` → rebuildable navigation, not source authority |
| Host-source ecology | [ecology](../src/ordivon_studio/ecology/), [owner model](media-model.md) | Explore scoped thread and collection views | Source-bounded observer views; never duplicate Host truth |
| Art & Expression / learning | [research](../research/expression/README.md), [learning context](../src/ordivon_studio/learning_context.py) | Compare style, medium craft and observations | `studio_learning_context` → scoped priors, not general human preference |
| Experimental validity | [Media research](../research/media/README.md), [scoring](../src/ordivon_studio/research/null_attack_scoring.py) | Pose a falsifiable research question | Frozen Winner and bounded holdout → evidence; PG ledger only for consumed experiments |
| Selected off-machine replica | [R2 adapter](../src/ordivon_studio/cloudflare_r2.py), [storage](storage-layout.md) | `ordivon-studio r2 --help` | Credential-bound remote readback and exact hashes; not live NLE directory |
| Publication / human-response | [Studio model](../STUDIO.md), [Review](review-consumption.md) | Decide what was technically and creatively demonstrated | Destination Owner publishes; audience claims need relevant observations |

The narrow, independently discoverable Agent entrypoints are
[Production workflow](../../../.agents/skills/media-studio-navigation/SKILL.md)
and [Native Processing](../../../.agents/skills/media-native-processing/SKILL.md).
Neither Skill implements media operations or grants source/effect authority.

## Optional mature provider candidates 鈥?not yet admitted as LEGO

For both Human and Agent users, **discover an actual consumer first**.
Netflix [libvmaf](https://github.com/Netflix/vmaf) may compare a selected
source and encoded video objectively when there is a meaningful reference,
but its score does not prove artistry, legal clearance or audience response.
[MediaInfo](https://mediaarea.net/en/MediaInfo) offers an alternative media
metadata inspection surface; compare it against selected FFprobe fields
before adding an adapter. Local/hosted ASR providers may be considered for
an actual narration transcription consumer after observing real provider
availability and source-language rights.

Human: identify which visual/audio/linguistic defect a candidate measures,
inspect an actual source/Output pair and decide whether the metric changes
the creative or publication decision.

Agent: require a named Production, exact source Blob/output, provider
version and provenance, repeatable native measurement, an existing
Output/Claim consumer and a distinct admission decision before adding
any selected Profile to the current processing directory. A candidate
listed here is **not installed, enabled, or proven** merely by listing it.

## Discover live actions (don't copy a second schema)

From `capabilities/media`:

~~~bash
python3 scripts/studio-agent-surface.py
python3 scripts/studio-agent-surface.py studio_processing_profiles --arguments '{}'
~~~

The nine current Studio semantic actions are:
`studio_dependencies_status`, `studio_dependencies_propose`,
`studio_production_standing`, `studio_production_context`,
`studio_learning_context`, `studio_creative_index_query`,
`studio_processing_profiles`, `studio_processing_probe_plan`,
`studio_equipment_propose`.

Four built-in Processing families use mature FFmpeg/FFprobe, ASWF OpenTimelineIO and TTML/ttconv engines. A source Profile being listed **does not prove** its native provider is installed, a Job has run, or the work is accepted. MediaInfo, VMAF/QCTools and other tools remain external *candidates* until a real consumer and comparative evidence justify adoption.

### Documentation and source standards

- [Diátaxis](https://diataxis.fr/): separate how-to, reference and explanation by reader need, not duplicate actual tool contracts.
- [FFprobe documentation](https://ffmpeg.org/ffprobe.html): native observable stream and container facts.
- [OpenTimelineIO documentation](https://opentimelineio.readthedocs.io/en/latest/): editorial interchange and references to external AV, not video/audio embedding.
- [Current R2.1 LEGO graph](../planning/lego-plan-r1.json): contracts and evidence standing; source-level table rows alone are not refinement proofs.

## Native Color / loaded media: current observed operation

The existing `scripts/resolve-native-produce.py` now accepts complete
RGB ASC CDL slope/offset/power plus saturation and records all four
effective native parameters in `gradeCDL`. The same script
uses official Resolve source-item readback to produce
`nativeTimelineMediaReadback` with file digests. This
composes **existing** official Resolve and Asset/Blob operations;
it is not a separate color module, new registry or invented media
decoder. For a human walkthrough see [Resolve](resolve-native.md)
and [Human](human-guide.md); for Agent preconditions and evidence
see [Agent](../AGENTS.md) and the current
`media-studio-navigation` Skill.
