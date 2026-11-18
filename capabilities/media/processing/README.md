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

OpenTimelineIO and ttconv use existing version-pinned wrappers
(`processing/bin/otiotool-pinned.sh` and `processing/bin/ttconv-pinned.sh`)
via `mise` and `uv tool run` when the selected adapter executes. The ttconv
command is named `tt`: absence of a global `otiotool`, `tt`, or `ttconv`
command does not prove the pinned adapter unavailable. Native readiness is
established by the actual Runtime Job and tool receipt, not by discovery.

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


## Agent composition entry

The existing Studio Agent surface advertises studio_processing_profiles for
source-owned profile and native adapter discovery. Select one row and supply
its profileDigest and adapterDigest to studio_processing_probe_plan together
with an exact inputPath and evidenceDirectory. The result is an ordered native
bash invocation proposal using the current adapter; Runtime executes it and
the adapter produces raw tool observations and a profile evidence receipt.

The Discovery catalog gives each supported profile its real first-argument
role: videoSource (AV), audioSource, editorialTimeline (OTIO), or
timedTextDocument (TTML). Unknown profile kinds have no advertised input
roles and no executable adapter. These role names are discovery hints, not
proof that a supplied file matches its role.

For an already materialized **local Linux Runtime input**, callers can also pass
the optional \`expectedInputDigest\` (lowercase \`sha256:<hex>\`) to
\`studio_processing_probe_plan\`. In that case Studio validates the selected
source bytes, resolves the actual file pathname and emits the existing Runtime
\`execution.hostDependencies\` for the exact input, profile and adapter files.
Compile and execute in the **same Runtime host/workspace namespace**: the
absolute committed paths must refer to those very files at admission. Existing
plans without this optional field remain source-only proposals; they do not
bind input bytes. Runtime validates declared dependencies on admission and
dispatch, watches host-namespace path continuity, but cannot prove that an
opaque tool consumed those bytes. The consuming Production must compare the
adapter's raw \`artifact.digest\` or \`input.digest\` with the selected digest.
No new registry, executor, or adapter-specific digest engine is created.

The compiler does not implement FFmpeg, OTIO, or subtitle processing; it
does not check tool installation, mutate source media, or grant execution
authority. A profile check is a mechanical predicate, never aesthetic or
publication approval.
