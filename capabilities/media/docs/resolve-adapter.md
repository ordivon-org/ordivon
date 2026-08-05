# Resolve adapter

The Resolve adapter is a DaVinci Resolve-specific bridge inside Ordivon Studio. It is not a general media runner and it does not duplicate the Production model.

## Boundary

Studio owns cross-tool production facts. The adapter compiles one bounded Resolve operation, installs one internal menu script, and reads one structured result. Resolve remains the editable editorial, color, Fusion, and Fairlight master.

The first operation is deliberately read-only:

```text
prepare probe
→ Workspace > Scripts > Utility > Ordivon > Ordivon Studio Runner
→ inspect the running Resolve application
→ write resolve-result.json
```

It does not create a project, import media, change a timeline, render, or run continuously in the background.

## WSL workflow

```bash
uv run ordivon-studio resolve install
uv run ordivon-studio resolve prepare-probe
```

Restart Resolve after first installation so it rescans user scripts. Run **Ordivon Studio Runner** from the Workspace Scripts menu, then inspect the result:

```bash
uv run ordivon-studio resolve result
```

The control files live under the Windows user's local application-data directory. The installed config contains the Windows path; repository files contain no user path or credential.

## Why one menu action

Resolve Free does not expose the supported external scripting session used by Resolve Studio. The menu script therefore executes inside Resolve. External Studio tooling only prepares a finite operation and verifies its result. It does not patch Resolve, maintain a hidden socket, or automate the full GUI.

## Verified capability

The read-only probe passed on DaVinci Resolve Free 21.0.3.7. The menu environment injected a working `resolve` object and exposed:

- product and version identity;
- current page;
- Project Manager and local project database;
- current Project and Timeline count;
- Media Pool availability;
- timeline frame rate and resolution.

The result contained no private filesystem path or database address. Resolve's embedded menu-script environment does not define `__file__`; the runner therefore uses the Windows local-application-data control directory directly and treats a colocated config as optional.

The bounded mutation acceptance also passed on Resolve Free 21.0.3.7. One reserved-name Smoke Project was created at 1920×1080 and 30 fps, one SHA-256-bound fixture was imported into `01_SMOKE`, one `Assembly` timeline was created, the clip was appended to V1 and A1, the project was saved, and the previously open project was restored.

The action is replay-safe: it reuses the reserved project, bin, media item, and timeline when they already exist, and it refuses to append over unexpected timeline contents. A successful operation result with the same identity and digest is returned without repeating Resolve mutations.

Resolve reported two items from the target Folder after one media import and one timeline creation. The adapter therefore treats Folder item count as diagnostic only; imported-media identity is established by the file name, expected digest, and the actual timeline items rather than by assuming Folder counts contain media clips only.

## Resolve Free 21.0.3.7 compatibility profile

A six-case disposable-project probe now records the installed build's actual timeline semantics. The normalized evidence is in [`resolve-compatibility/resolve-free-21.0.3.7.md`](resolve-compatibility/resolve-free-21.0.3.7.md) and its adjacent JSON profile.

The probe established that `TimelineItem.GetEnd()` is an exclusive timeline boundary and that `GetDuration()` equals `GetEnd() - GetStart()`. Source-end behavior is not uniform across operations: full-media Append, explicit source-range Append, and OTIO import expose different conventions. The adapter therefore does not apply one generic `+1` or `-1` rule.

Explicit source-range Append is not a production path on this profile. The installed official example labels source `0…23` as 24 frames, while the live 21.0.3.7 result produced a 23-frame TimelineItem. Full-media Append remains diagnostic-only.

Native `ImportTimelineFromFile` OTIO conform succeeded with both existing Media Pool sources and `sourceClipsPath` import. Both preserved a 24-frame clip, a 6-frame gap, a 30-frame clip, the `01:00:00:00` start timecode, and the 60-frame total. Runtime Introduction assembly will therefore compile a Resolve-facing OTIO, import verified media into controlled Bins, use the existing-source OTIO path, and verify the resulting Timeline by scanning V1.

The compatibility operation is prepared with:

```bash
uv run ordivon-studio resolve prepare-compatibility
```

It is locked to DaVinci Resolve Free 21.0.3.7, Windows internal-menu execution, the installed Developer Package digest, and content-addressed test fixtures. A Resolve upgrade requires a new profile rather than silently reusing these assumptions.

## Runtime Introduction native conform acceptance

The full Runtime Introduction Assembly v0 has now passed a real disposable-project conform acceptance on Resolve Free 21.0.3.7. The normalized evidence is stored in [`resolve-compatibility/runtime-introduction-assembly-conform-21.0.3.7.json`](resolve-compatibility/runtime-introduction-assembly-conform-21.0.3.7.json).

The adapter compiled the canonical Production, Asset manifest, and `assembly.v0.otio` into one local Resolve-facing OTIO, verified all eleven media digests before mutation, imported the media into controlled Bins, and invoked `ImportTimelineFromFile` with `importSourceClips=False` and the two controlled source folders.

Resolve produced exactly eleven V1 items. Every item matched the requested start frame, duration, and imported MediaId. The Timeline began at `01:00:00:00`, occupied frames `108000…110340`, and therefore measured exactly 2340 frames or 78 seconds. The operation restored the previously open project and deleted the disposable probe project.

This closes the compatibility question for the current workstation profile. Native OTIO conform is now the accepted assembly mechanism. The old explicit source-range Append implementation remains only as historical and diagnostic code; it is not an approved production path.
