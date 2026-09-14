# Operations machine inventory

Operations owns the **generic node-local inventory boundary**, not a universal capability registry.

The inventory answers bounded physical questions such as:

- what software/package records are installed on this node;
- which executable paths are materialized or currently running;
- what OS/host facts the node reports;
- which Windows applications are registered locally;
- which Runtime execution targets are mechanically available.

It does **not** answer whether a task is authorized, whether a domain capability is semantically satisfied, whether production is ready, or whether the machine is globally healthy.

## Source registry

`inventory/sources.json` is the canonical map from fact class to mature upstream source. It deliberately preserves source-native concepts instead of building an Ordivon inventory database.

Current default sources:

- **osquery** — generic Linux/WSL host/process/package-language facts that the installed osquery tables can actually observe;
- **pacman local database** — Arch package installation truth, because this osquery build does not expose ALPM package state;
- **filesystem/PATH observation** — node-local executable materialization only;
- **WinGet + Windows uninstall registry** — Windows package/application inventory;
- **Nix + Home Manager / WinGet Configuration + DSC** — desired state, not observation;
- **Ordivon Runtime** — execution-target availability and exact mechanical execution truth;
- **Syft** — on-demand standard SBOM projection (CycloneDX/SPDX/Syft JSON), not the default quick census.

## Query contracts

Direct osquery SQL remains under `inventory/queries/`. These queries are read-only projections and may be executed with:

```bash
osqueryi --json "$(cat inventory/queries/system_identity.sql)"
osqueryi --json "$(cat inventory/queries/os_version.sql)"
osqueryi --json "$(cat inventory/queries/uptime.sql)"
osqueryi --json "$(cat inventory/queries/running_executables.sql)"
```

Arch package state is read directly from pacman rather than translated into a custom schema:

```bash
pacman -Qq      # all installed packages
pacman -Qqe     # explicitly installed packages
pacman -Qm      # packages foreign to configured sync databases
```

Windows application state is queried through provider-native surfaces (WinGet where recognized, uninstall registry for the broader installed-app projection). Windows desired state remains under `workstation/windows/workstation.dsc.yaml`.

## SBOM rule

Syft is available for cases that genuinely need a standardized software bill of materials. Full-directory SBOM cataloging is intentionally **not** part of the default fast inventory path: it is materially more expensive than native package-manager and osquery reads. When required, emit a standard format such as CycloneDX JSON or SPDX JSON and retain that output as dated evidence.

## Snapshots

`inventory/snapshots/` contains dated observations only. A snapshot is evidence of what was observed at that time; it is never the live authority for future queries.

The 2026-09-14 snapshot records Linux pacman state, selected node-local executable directories, Windows uninstall-registry applications, and selected Windows PATH resolution.

## Ownership boundary

The following distinctions are mandatory:

```text
installed/materialized fact  != Runtime execution availability
Runtime execution availability != task authorization
 task authorization            != domain semantic success
```

No inventory result may be promoted to a global `capability=true`, production authorization, or domain acceptance verdict without the actual owner-specific evidence.
