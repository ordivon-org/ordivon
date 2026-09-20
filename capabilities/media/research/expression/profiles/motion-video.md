# Motion / Video expression profile

## Responsibility

This profile translates the shared Art & Expression core into time-based audiovisual production. It owns **medium craft priors and inspection expectations**, not source-domain truth and not one permanent Ordivon film style.

Current real consumers include the Remotion compositions under `apps/motion-remotion/` and the editable `productions/runtime-introduction` pipeline. Resolve, Remotion, OTIO and FFmpeg are production equipment; none of them owns the meaning of the work.

## What the medium can manipulate

Motion/video can deliberately control:

- frame composition, scale, position, depth cues and figure/ground;
- shot or scene duration, cut position and temporal density;
- movement, velocity, acceleration, hold and stillness;
- reveal order, anticipation, interruption and return;
- continuity and discontinuity across events;
- typography and graphic animation over time;
- color, light, contrast and image treatment;
- voice, music, effects, ambience and silence when audio is present;
- audio/image synchrony and counterpoint;
- aspect ratio, crop, safe area and delivery duration.

The profile does not assume every production should use all of these controls.

## Hard constraints

The following are stronger than aesthetic preference when they apply:

- source claims remain bound to their owning revision and information boundary;
- exact frame/time identity uses the Production working profile rather than floating-point timing guesses;
- selected media bytes, editable sources and outputs retain their declared provenance;
- color metadata, pixel format, dimensions, frame rate and audio stream expectations are machine-inspected for approved outputs;
- programmatic motion without audio must not acquire a meaningless empty audio stream;
- caption/timed-text source remains distinct from delivery subtitle formats;
- an interchange artifact such as OTIO does not pretend to preserve proprietary effects or every NLE state;
- delivery encodes are outputs, not the only editable master;
- a visual or temporal choice may not leak hidden world/product truth merely because it makes the sequence more dramatic.

Technical details are owned by `docs/technical-baseline.md`, `docs/media-model.md`, the Production manifest, and the relevant renderer/editor adapters. This profile points to those constraints; it does not clone them.

## Durable craft priors

These are `medium_prior` defaults, not laws:

- **event continuity before surface continuity** — preserve the audience's model of what continues, changes or causes the next event;
- **pattern before violation** — repetition or expectation gives surprise and discontinuity force;
- **duration is meaning** — holds, gaps and compression alter emphasis even when frames contain identical facts;
- **motion implies change** — animation can accidentally claim trend, causality, urgency or agency;
- **cut order implies relation** — juxtaposition can create causal, comparative or rhetorical meaning not present in isolated shots;
- **sound reorganizes the image** — voice, rhythm, silence and effects can redirect attention or interpretation rather than merely decorate visuals;
- **screen geometry can become world geometry** — placement, direction and movement can imply location, bearing or pursuit;
- **medium-native transfer** — carry focalization, event model and tension across media; do not animate a Web layout merely because it already exists.

## Common semantic failure modes

Audit real renders for at least these classes when relevant:

- a cut implies causality that the source only supports as correlation or sequence;
- movement implies a state transition although only presentation changed;
- direction/position implies an unsupported world bearing;
- color or dramatic sound assigns danger, trust, probability or outcome before evidence permits it;
- a countdown, progress motion or repeated pulse invents urgency or trend;
- privileged audience knowledge remains visible after focalization should close;
- an edit compresses uncertainty until a hypothesis reads as settled fact;
- polished trailer language makes an experimental/target product appear current;
- captions, voice and image disagree about temporal or factual state.

A technically valid render can still fail this semantic audit.

## Render and inspection

Current production equipment provides several distinct evidence boundaries:

```text
Remotion source
→ deterministic frame/video render
→ frame-level visual inspection

Production + Assets + OTIO
→ Resolve assembly/conform
→ editable NLE state

rendered media
→ ffprobe / QC
→ codec, frame rate, dimensions, pixel format, color and audio facts
```

Use actual frames or playback for expressive judgment. Source JSX, timeline metadata and design rationale are not the final perceptual artifact.

For time-based claims, inspect more than a single attractive frame. A frame can verify composition; it cannot prove pacing, reveal, continuity or audio/image relation.

A useful Agent observation path can be progressive: coarse temporal contact sheet → exact full-resolution frames → continuous playback when the unresolved claim is temporal. Change metrics may help choose where to look, but must not be treated as event importance or semantic meaning.

## Protocol specialization

```text
FRAME
experience + audience + duration/encounter + audio assumptions
    ↓
BIND
source claims + focalization + temporal state + allowed reveal
    ↓
EXPRESS
sequence + shot/graphic composition + rhythm + motion + sound strategy
    ↓
RENDER
real frames / video / audio / NLE state as appropriate
    ↓
AUDIT
technical QC + temporal/visual/audio implicit semantics
    ↓
DECIDE
revise / no-op / promote
```

Promotion of a film/output does not promote a local editing choice into cross-medium Core knowledge.

## Context signals

Platform duration norms, short-feed pacing, fashionable transitions, current subtitle treatments, thumbnail conventions and present audience expectations are `context_signal`, not this profile's durable craft. Retrieve them near a production and allow them to expire.

## Current local evidence

A3-1 through A3-3 established three useful local pressures for motion work:

1. response loss is stronger as a **temporal rupture/recovery trajectory** than as animated component geometry;
2. suspense can preserve an Agent information boundary only if privileged truth is deliberately opened and closed;
3. affect can be produced through reveal rhythm, withholding and sustained unresolved framing without inventing hidden threat events.

These observations inform the profile but remain falsifiable by later productions.
