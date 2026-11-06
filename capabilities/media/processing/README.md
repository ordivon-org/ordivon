# Media processing

This is the Media owner's **external-tool processing and technical evidence** boundary,
not a new rendering engine, editorial authority, asset database or distribution service.
Each adapter invokes an established tool, retains raw observations, and checks only the
declared technical profile against exact artifact bytes.

Source and production truth remain with the owning domain; Workstation owns installed
tool identities and Runtime owns process execution. A technical PASS is never a claim
about narrative meaning, edit quality, rights, accessibility acceptance or publication.

## Current native tools

| Profile | Primary native tool | Smoke verification |
| --- | --- | --- |
| Audio/video | FFprobe and FFmpeg | `bash processing/tests/smoke.sh` |
| Audio loudness | FFprobe and FFmpeg `loudnorm` | `bash processing/tests/audio-smoke.sh` |
| Timed text | IMSC/TTML `ttconv` | `bash processing/tests/timedtext-smoke.sh` |
| Editorial interchange | OpenTimelineIO `otiotool` | `bash processing/tests/otio-smoke.sh` |

Run from `capabilities/media`. Use `processing/bin/` for exact profile checks and
`processing/profiles/` for the declared mechanical acceptance bounds. The tools
own media parsing/encoding, loudness computation, subtitle conversion and timeline
interchange; these shell adapters must not reimplement those semantics.

The dependency-light `studio_processing_profiles` Agent action lists the source
profile and adapter paths with their independent SHA-256 byte identities. It does
not invoke equipment or claim it is installed. Execute a selected adapter through
Runtime only after the actual tool and source artifact are available.

## Dependency and ownership boundaries

The AV technical adapter intentionally does **not** invoke the Studio asset, QC,
video, perception or rich-perception implementations. Those may be activated
separately by a real production, never as implicit authority of an FFprobe result.

MediaInfo, VMAF/QCTools, DVC, OCI/ORAS, C2PA and specialist review platforms are
**optional external candidates**, not a mandated stack. Add them only when an
actual consumer and a falsifiable delivery requirement justify their use.
Provider-native distribution/readback remains with its natural owner.
