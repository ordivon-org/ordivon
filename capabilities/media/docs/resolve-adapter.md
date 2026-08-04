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

Further actions are added only after the current Resolve version proves the relevant mutation APIs work. The next acceptance case is one disposable project containing one bin, one imported clip, and one timeline.
