# DaVinci Resolve — official native integration

**Status:** the dedicated Ordivon Resolve menu Runner, local `resolve-operation.json`/`resolve-result.json` handshake, and `ordivon-studio resolve ...` commands are retired. Do not reinstall the Runner or promote historical compatibility receipts to current editing evidence.

## Natural Owner boundaries

Blackmagic's Resolve owns all NLE project/timeline effects, color, Fusion, Fairlight and delivery render. Media owns selected Production/Asset/Blob identities, exact source digests, native OTIO inspection, technical QC and acceptance; Runtime owns execution Job/Attempt. The existing `processing/bin/probe-otio.sh`, pinned `otiotool` and FFmpeg/FFprobe are sufficient for their respective source and technical checks. No parallel custom editing engine is warranted.

Windows Session 1 native acceptance (2026-11-07): DaVinci Resolve Studio
21.0.3.7 accepted official Python API calls for isolated project creation,
two video clips, one synchronised WAV track, native Color CDL,
editable DRP export and MP4 H.264/AAC render. Resolve and independent
FFprobe read back the output as 640x360/24 fps/4 seconds. Runtime Job
job-01a1b547-8ad5-76c2-b228-b3e73a9ff69d covers the first full
timeline acceptance; job-01a1b542-81ea-7fc0-a876-f942f83ee34c
identified and falsified the earlier one-frame preview error. This
demonstrates the chosen native workflow without a private menu Runner.

## Human workflow

1. Open Resolve on the intended interactive Windows desktop and verify its actual version, edition/license, project, and any required scripting policy. Keep external/network scripting disabled unless separately authorized.
2. Read the installed API guide at `%PROGRAMDATA%\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\README.txt`. Run the matching 64-bit Python in a supported Windows session. Example PowerShell *read-only* capability probe:

   ```powershell
   $env:RESOLVE_SCRIPT_API = "$env:PROGRAMDATA\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting"
   $env:RESOLVE_SCRIPT_LIB = "C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll"
   $env:PYTHONPATH = "$env:RESOLVE_SCRIPT_API\Modules;$env:PYTHONPATH"
   python -c 'import DaVinciResolveScript as dvr; r=dvr.scriptapp("Resolve"); print(r.GetVersionString() if r else "UNAVAILABLE")'
   ```

   If the app is unavailable, return `UNKNOWN`; a Windows executable being installed does not imply a usable scripting session.
3. For an approved edit, use the official `resolve.GetProjectManager()`, `project.GetMediaPool()` and `MediaPool.ImportTimelineFromFile(path, options)`; `ImportMedia` and `AppendToTimeline` are native alternatives where needed. Check the installed API signature and expected target project rather than assuming the current active project is safe to mutate.
4. Compare the imported timeline's actual clips, positions, source refs, native project identity, and export output against the chosen Production. Preserve Resolve editable project exports at requested milestones. Independently run OTIO and media QC, then have the owning consumer accept or reject the work.

## Agent workflow

The `studio_dependencies_status` and `studio_dependencies_propose` tools cover only the Studio JavaScript and Python project environment.
Resolve Studio readiness is observed from the Windows application/session
and its native Scripting API, not from a removed Python `resolve` extra.

- Discover the current selected Production, source Asset/Blob digests, required exact native edit, target Resolve project, and active desktop/session. If any are not observable, report `UNKNOWN` rather than guessing or running an unattended edit.
- Prefer direct task-specific invocations of the **installed official Python/Lua API** using existing Windows Runtime execution; never recreate a persistent menu Runner, operation staging store, separate state engine, or private editing DSL. A few ephemeral lines of API script can be appropriate when the user has requested a real effect.
- Before modifying a project, bind source paths and digests to the selected Production. Avoid implicit writes to the active project, and use an explicit disposable project when testing.
- After invoking native methods, **read back** project, timeline and output facts. Record source identity, exact Runtime Job/Attempt, actual Resolve version/edition when observed, and output digest; capture failures and cleanup outcomes. Native success without supported readback is not `DOMAIN_ACCEPTED`.
- Source code tests with fake Resolve objects, past Free 21.0.3.7 probes, `otiotool` structural checks, or a Windows package version alone cannot prove an actual Studio native edit.

## Kept provenance

Historical `docs/resolve-compatibility/resolve-free-21.0.3.7.{json,md}` and `runtime-introduction-assembly-conform-21.0.3.7.json` remain read-only evidence of specific earlier **Free** version observations. Production OTIO, source Assets, Studio tools and QC are unaffected by this Runner retirement.
## Executable native production

Use the source-owned one-shot script `scripts/resolve-native-produce.py` for selected
visual sources, optional audio, native Color CDL, editable DRP and H.264 MP4.
It invokes the installed Resolve Python API directly. It is not the retired
menu Runner, an alternate editing engine, a staging protocol, or a state store.

From an interactive Windows `active_user` Runtime execution with a fully
initialized Resolve 21.0.3.7 session, run Python 3.11 (the actual native API
module version verified on this workstation):

```powershell
$env:RESOLVE_SCRIPT_API = "$env:PROGRAMDATA\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting"
$env:RESOLVE_SCRIPT_LIB = "C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll"
python capabilities/media/scripts/resolve-native-produce.py `
  --visual C:\sources\shot-01.mp4 `
  --visual C:\sources\shot-02.mp4 `
  --audio C:\sources\voice.wav `
  --output-dir C:\outputs\selected-production `
  --name selected-cut --grade-saturation 1.1
```

Runtime executes this request; Blackmagic owns the project, timeline, grade,
audio track and render. The script imports selected files, builds timeline
tracks, exports the editable `.drp`, renders MP4 and records exact SHA-256
source and output identities in a `.receipt.json`. It closes/deletes only
its newly created isolated project unless `--keep-project` is specified.
Use a selected short source or lower project dimensions for preview; default render covers the full timeline.
Do not infer publication from technical output; a named destination must actually receive and read back its artifact.

For native render-format selection, use values from `GetRenderCodecs('mp4')`.
On the tested 21.0.3 install, the GUI label `H.264` maps to native codec
identifier `H264`; the script selects the native identifier. Use the already
published `studio_processing_profiles` action for FFprobe/FFmpeg, OTIO and
TimedText checks rather than building parallel media parsers.

## OTIO interchange as a native editing input

When editorial cut structure already exists, choose `--otio` instead of
`--visual`. The script calls the **installed Blackmagic**
`MediaPool.ImportTimelineFromFile(path, options)` directly; it does not
parse OTIO, define an Ordivon timeline language or emulate the editor:

```powershell
python scripts/resolve-native-produce.py --otio C:\media\cut.otio `
  --source-clips-dir C:\media\sources `
  --audio C:\media\voice.wav --output-dir C:\media\delivery `
  --name cut-01 --min-timeline-frames 96 --grade-saturation 1.1
```

The API implements native relinking with `sourceClipsPath`; a successful
import does **not** independently hash all references inside the OTIO.
For reliable Windows import, author the interchange using the **official**
`opentimelineio==0.18.1` library and verify it with `otiotool --verify-ranges`.
Pass the actual `--source-clips-dir` whenever native relinking is needed.
On the tested Resolve Studio 21.0.3.7 workstation, an older handwritten OTIO
passed structural checks but failed native import; an official-library OTIO
with explicit media relinking imported, graded and rendered successfully in
Windows Runtime Job `job-01a1b5bd-3146-7da2-82b7-dee5da9cf798`.
Independent FFprobe, duration, codec and SHA-256 checks passed. This is
specific native acceptance evidence, not arbitrary OTIO round-trip fidelity
or external publication.

The receipt hashes the exact .otio input, optional separately supplied audio,
editable DRP and rendered MP4 and reports the timeline's actual frame count.
`otioMediaReferencesIndependentlyVerified=false` is an intentional evidence
boundary, not a failed render. Reconcile linked media against the selected
Production's Asset/Blob declarations before claiming source fidelity.

Before editing, select a named Production, its sources and source digests.
After editing, use the existing `studio_processing_profiles` and
`studio_processing_probe_plan` actions with the native OTIO, FFprobe, audio
loudness and timed-text adapters as applicable; the Runtime Job and generated
raw receipts carry physical observations. Review real picture, speech,
subtitle timing and color in Resolve/Fairlight; output approval is distinct
from publishing to a particular provider and reading back its receipt.
Keep only the selected editable source, accepted output and supporting
consumer evidence. Do not retain every disposable render or test project.

## Parameterized native Color CDL and loaded-source evidence

The one-shot native producer now accepts the ASC-style CDL controls
`--grade-slope R,G,B`, `--grade-offset R,G,B`,
`--grade-power R,G,B`, plus `--grade-saturation N`. Each component
must be finite. Unspecified channels use neutral RGB defaults, and no
grade is applied unless an explicit grade argument is supplied.
This is implemented by Resolve's installed `TimelineItem.SetCDL`,
not an Ordivon color-correction engine. Other Color-page operations
remain with the native application.

Example using an existing OTIO timeline, audio and explicit color intent:

```powershell
python scripts/resolve-native-produce.py --otio C:\media\cut.otio `
  --source-clips-dir C:\media\sources --audio C:\media\voice.wav `
  --output-dir C:\media\delivery --name cut-02 `
  --grade-slope 1.08,1.04,1.02 --grade-offset 0.01,0,0 `
  --grade-power 1,0.98,1.02 --grade-saturation 1.08 `
  --min-timeline-frames 96
```

The script reads back each timeline clip through Resolve's official
`TimelineItem.GetMediaPoolItem()` and
`MediaPoolItem.GetClipProperty("File Path")`; if the reported
file exists, it records its SHA-256 as
`nativeTimelineMediaReadback[].sourceDigest`. The
`nativeTimelineMediaReadbackComplete` boolean means every observed
timeline item's file was available and hashed. It is *not* proof that
every external reference in the original OTIO has been interpreted
identically, so `otioMediaReferencesIndependentlyVerified` continues
to be false until the original OTIO/selected Assets are reconciled.
Compare each observed digest against the selected Production's
allowed Blob identities before claiming editorial source fidelity.
The receipt keeps `schemaVersion=1` and the existing fields.

Observed Windows Session 1 acceptance: Resolve Studio 21.0.3.7
rendered two OTIO-referenced shots and a selected audio track
under a non-neutral four-control CDL. Runtime Job
`job-01a1b583-709d-7ca1-bf2f-428c1c0373a4` committed;
independent FFprobe and SHA-256 readback Job
`job-01a1b586-66da-7df3-9b17-778f1c249772` confirmed
a 4.010667 s H.264/AAC MP4, three physically verified timeline
source files and both output digests. This is a bounded native
technical demonstration, not a platform publish.
