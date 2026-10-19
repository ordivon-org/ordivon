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

## Remaining frontier / risk tier

- GitHub Dependabot source config must be on the *remote default branch*
  and version updates enabled at GitHub; repository source alone is not proof
  any PR has actually been created.
- Windows app updates: qualify `winget` using the interactive Windows user
  identity, or install App Installer through a supported Windows workflow,
  before introducing a scheduled Windows app checker. Existing Windows Update
  tasks do not imply all applications are updated.
- Mise self-update on this node is package-manager controlled; `mise outdated`
  targets project tools and is not a substitute for an OS package upgrade.
- Production Runtime/Host/Network/Podman releases require exact source
  revision, tests, rollout fence and a rollback plan.
- Storage headroom and routine GC remain a separate user-managed concern.

The next rung for **automatic installation**, not just discovery, is an
isolated accepted release path for a named low-risk update family and a
verified rollback. Do not add a global root-level `pacman -Syu` cron job.

## Windows native update discovery qualification (R4)

Windows keeps the same read-only discovery boundary instead of reusing Linux
package-manager mechanisms.

- `Microsoft.DesktopAppInstaller` is installed for all users at version
  `1.29.380.0`.
- The Runtime service identity is `NT AUTHORITY\\SYSTEM`, so the interactive
  user's WinGet alias is not on PATH. The implementation resolves the All-Users
  App Installer package and invokes its official `winget.exe` directly.
- A real read-only `winget upgrade --source winget --accept-source-agreements
  --disable-interactivity` query returned **11** available application updates.
- Windows Update remains owned by its native scheduled tasks and `wuauserv`;
  Ordivon records health only and does not install OS updates.
- `platform/workstation/windows/update_candidate_report.ps1` stores private
  atomic JSON under `C:\\ProgramData\\Ordivon\\UpdateDiscovery\\current.json`.
- `platform/workstation/windows/install_update_discovery.ps1` installs an
  idempotent SYSTEM scheduled task named `Ordivon Update Discovery`, daily at
  06:30 local time with a five-minute execution bound.

### SYSTEM payload ACL repair

The first live ACL audit found that the interactive local user inherited Full
Control on `C:\\ProgramData\\Ordivon\\UpdateDiscovery` and on the PowerShell
payload later executed by the SYSTEM/Highest scheduled task. That is a local
privilege-escalation seam because a writable parent can replace a SYSTEM task
payload.

The installer now removes inherited ACLs from both the task directory and the
installed script before task registration. Only these principals retain Full
Control:

- `NT AUTHORITY\\SYSTEM`
- `BUILTIN\\Administrators`

The live host was reinstalled with the hardened installer. Independent readback
confirmed:

- the interactive user is absent from both ACLs;
- the installed script SHA-256 equals
  `cf440c326ec01201425e428964cd9ac2868d398c066059193f5b024ff7a2fd1b`;
- the scheduled task's latest run returned 0;
- the next daily trigger is 06:30 local time;
- the report still contains 11 WinGet candidates; and
- all upgrade, restart, install and reboot effect counters remain zero.

Do not weaken these ACLs merely to make the report easier for a standard user
to read. A consumer that needs the report should use an explicit bounded read
path, not write access to a SYSTEM task directory.
