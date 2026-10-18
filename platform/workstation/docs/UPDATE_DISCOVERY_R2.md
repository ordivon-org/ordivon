# Ordivon native update discovery R2

Date: 2026-10-19.

## Decision

Reuse the installed native package-manager update probes. This is a scheduled
**read-only update-discovery** capability, not an unattended OS or production
release worker. GitHub Dependabot already opens package update PRs for
GitHub Actions, uv, npm/pnpm, Cargo, Workstation/OpenXML Nix flakes and Codex CLI.

At this node:

| Surface | Native discovery | State at initial census |
| --- | --- | --- |
| Arch Linux | `checkupdates --nocolor` from pacman-contrib | Installed; real probe found available updates |
| mise runtime tools | `mise outdated --json` | Installed; current root-project request range had no updates |
| Podman container images | `podman auto-update --dry-run --format json` | Installed; no eligible autoupdate-labelled containers |
| Windows Update | Microsoft Windows scheduled update tasks | Present; service account inspection only, effectiveness unqualified |
| Windows desktop applications | `winget upgrade` | Not available to current limited Windows Runtime principal; App Installer not present for that principal |

**Do not** enable `podman-auto-update.timer`: unlike this discovery dry-run,
that upstream timer can pull images and restart production containers. Podman
lifecycle/release acceptance remains separate.

## Composition and effects

`platform/workstation/tools/update_candidate_report.py` runs exact bounded
native tool probes. It does not parse private provider credentials, install
packages, update lockfiles, restart applications, or create a second software
updater. It generates a minimal JSON envelope with source, timestamp,
per-source candidate counts and an explicit `UNKNOWN` or `missing` when a
probe cannot determine version standing.

The Arch `checkupdates` exit code **2** means no available updates, while
other errors mean **UNKNOWN**. Mise now discovers **all Git-tracked `mise.toml` / `.mise.toml` files** using `git ls-files -z`, then uses the upstream `mise outdated --bump --json --local` per project. Four native probes run concurrently with a 12-second per-scope limit and a maximum of 64 scanned configurations. Failures, invalid paths and scopes outside the bounded limit are explicit `partial` / `unknown` coverage, never treated as `current`. The `bump` flag surfaces new versions even when current exact pins would hide them.
The Podman result `no_eligible_containers` must not be displayed as
"every container image is up to date".

Native systemd unit/timer:

- `platform/workstation/systemd/ordivon-update-discovery.service`
- `platform/workstation/systemd/ordivon-update-discovery.timer`

The timer runs daily with a randomized delay, storing private atomic JSON
under `/var/lib/ordivon-update-discovery/current.json`. Only one known
oneshot service does the three bounded checks; systemd remains the scheduler.
Outputs are 0600 and contain no tokens or secrets. A failed source is
preserved as unknown, not silently suppressed.

## Verification

Automated tests:
`python -m pytest -q platform/workstation/tests/test_update_candidate_report.py`.

Real node smoke produced typed state:
`arch=updates_available`,
`mise=updates_available`,
`podman=no_eligible_containers`.

A subsequent full tracked-configuration smoke on the local node covered **19/19** independent mise configuration directories, with **52 scope-qualified outdated tool declarations** and 0 unchecked scopes. Results are declarations across directories, not 52 distinct products. The earlier root-only `mise=current` was misleading and is superseded. This smoke was read-only; no changes were applied to installed packages.

For first installation after mainline integration:

```sh
systemctl link /root/projects/ordivon/platform/workstation/systemd/ordivon-update-discovery.service
systemctl link /root/projects/ordivon/platform/workstation/systemd/ordivon-update-discovery.timer
systemctl daemon-reload
systemctl start ordivon-update-discovery.service
systemctl enable --now ordivon-update-discovery.timer
systemctl is-enabled ordivon-update-discovery.timer
systemctl list-timers --all ordivon-update-discovery.timer
```

The `service` invocation can take several minutes for registry and package
metadata. Interpret status using `systemctl show`, `journalctl -u` and the
current JSON; do not report success before first execution reaches exit zero.

## Windows native discovery

Windows keeps the same LEGO boundary instead of reusing Linux mechanisms:

- Windows Update remains owned by Windows' existing scheduled tasks and
  `wuauserv`. A direct `Microsoft.Update.Session` search under the real
  SYSTEM principal exceeded 90 seconds, so Ordivon does **not** add a second
  OS-update scanner.
- Desktop application discovery resolves the installed
  `Microsoft.DesktopAppInstaller` package and invokes its real
  `winget.exe` directly. This avoids the false assumption that a missing
  SYSTEM PATH alias means WinGet is absent.
- `platform/workstation/windows/update_candidate_report.ps1` stores a
  private atomic JSON report under
  `C:\ProgramData\Ordivon\UpdateDiscovery\current.json`.
- `platform/workstation/windows/install_update_discovery.ps1` installs an
  idempotent SYSTEM Task Scheduler job named `Ordivon Update Discovery`,
  daily at 06:30 local time with a five-minute execution bound.
- The WinGet table is parsed from the right: package ID, current version and
  available version are the final three tokens; the remaining prefix is the
  display name. This handles long localized names that overflow WinGet's
  visual Name column.

Live Windows qualification under the real SYSTEM task completed with
`LastTaskResult=0`, Windows Update native scheduler present, and **11**
WinGet upgrade candidates. The regression case
`Nvidia.PhysX 9.23.1019 -> 9.26.0703` parsed correctly after two earlier
parsers were falsified by long names. The report explicitly records
`packagesUpgraded=0`, `windowsUpdatesInstalled=0`,
`processesRestarted=0`, and `rebootRequested=false`.

## Remaining frontier / risk tier

- GitHub PR #148 carried the Nix/Codex/Workstation discovery source to the
  protected public `main`; its required `root-verification` check passed,
  the PR entered the merge queue, and GitHub merged it as
  `1ad9af5cf51c410a343b81f1c1915e37d6d5268a`.
- Windows application **installation** remains gated. The scheduled WinGet
  task performs discovery only; applications such as VPNs, Git and GPU
  support software need per-family acceptance/rollback before automatic
  upgrade is considered.
- Mise self-update on this node is package-manager controlled; `mise outdated`
  targets project tools and is not a substitute for an OS package upgrade.
- Production Runtime/Host/Network/Podman releases require exact source
  revision, tests, rollout fence and a rollback plan.
- Storage headroom and routine GC remain a separate user-managed concern.

The next rung for **automatic installation**, not just discovery, is an
isolated accepted release path for a named low-risk update family and a
verified rollback. Do not add a global root-level `pacman -Syu` cron job.
