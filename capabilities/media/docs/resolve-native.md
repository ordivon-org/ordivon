# DaVinci Resolve — official native integration

**Status:** the dedicated Ordivon Resolve menu Runner, local `resolve-operation.json`/`resolve-result.json` handshake, and `ordivon-studio resolve ...` commands are retired. Do not reinstall the Runner or promote historical compatibility receipts to current editing evidence.

## Natural Owner boundaries

Blackmagic's Resolve owns all NLE project/timeline effects, color, Fusion, Fairlight and delivery render. Media owns selected Production/Asset/Blob identities, exact source digests, native OTIO inspection, technical QC and acceptance; Runtime owns execution Job/Attempt. The existing `processing/bin/probe-otio.sh`, pinned `otiotool` and FFmpeg/FFprobe are sufficient for their respective source and technical checks. No parallel custom editing engine is warranted.

The Windows install inspected on 2026-11-07 provided DaVinci Resolve `21.0.3.7` and its official `Developer/Scripting/README.txt`, but Resolve was not running. **Studio license activation was not verified** from an interactive session. The retained Free 21 compatibility record does not establish today's Studio capabilities.

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

- Discover the current selected Production, source Asset/Blob digests, required exact native edit, target Resolve project, and active desktop/session. If any are not observable, report `UNKNOWN` rather than guessing or running an unattended edit.
- Prefer direct task-specific invocations of the **installed official Python/Lua API** using existing Windows Runtime execution; never recreate a persistent menu Runner, operation staging store, separate state engine, or private editing DSL. A few ephemeral lines of API script can be appropriate when the user has requested a real effect.
- Before modifying a project, bind source paths and digests to the selected Production. Avoid implicit writes to the active project, and use an explicit disposable project when testing.
- After invoking native methods, **read back** project, timeline and output facts. Record source identity, exact Runtime Job/Attempt, actual Resolve version/edition when observed, and output digest; capture failures and cleanup outcomes. Native success without supported readback is not `DOMAIN_ACCEPTED`.
- Source code tests with fake Resolve objects, past Free 21.0.3.7 probes, `otiotool` structural checks, or a Windows package version alone cannot prove an actual Studio native edit.

## Kept provenance

Historical `docs/resolve-compatibility/resolve-free-21.0.3.7.{json,md}` and `runtime-introduction-assembly-conform-21.0.3.7.json` remain read-only evidence of specific earlier **Free** version observations. Production OTIO, source Assets, Studio tools and QC are unaffected by this Runner retirement.
