# Workstation v2 machine inventory

Workstation v2 owns the **generic node-local inventory and realization-discovery boundary**, not a universal capability registry.

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

## Live executable observation for Agents

The bounded, dependency-free `inventory/probe_executables.py` reads **the current
process PATH**, reporting node, a process user hint, PATH digest, and resolved
command paths. Run it **under the intended Runtime execution target/identity**:

```bash
python platform/workstation/inventory/probe_executables.py git gh mise uv python pnpm cargo
```

On Windows where Python is not available to a service identity, use the native
PowerShell `Get-Command <name> -CommandType Application -ErrorAction SilentlyContinue`
from that **same** identity. When Python is available, the script works for both
Windows and Linux. Do not run the inventory under an interactive account and
apply the result to a service account or vice versa.

For a project-owned tool, resolve **from the intended owner's directory**,
even when the system PATH contains a tool of the same name:

```bash
cd tools/formal
/usr/bin/python3 ../../platform/workstation/inventory/probe_executables.py --mise z3 lean
```

The optional `--mise` view invokes the existing `mise which` in that directory
(up to 16 names, five seconds per lookup). It does not install tools, change
trust, or replace the PATH observation. A resolved path is a candidate for
the actual invocation, not evidence of task success. If unresolved, check
the owner's native provider and intended target; a resolver error or trust
refusal is not absence. For Python dependencies, check the owner interpreter
and locked `uv run` environment, not imports in system Python. If the lock
is not materialized, use the owner's locked sync and verify the intended
consumer; distinguish an offline cache miss from a missing installation.
The optional `--mise-installed` view reports existing supplier records, even
when a tool is not selected in the current project. Missing exact inventory
keys are resolved using native `mise which NAME --plugin` in the owner scope
(up to 16 additional lookups, five seconds each). `providerKeys` records the
supplier key, for example `github:leanprover/lean4` for Lean and Lake.
`unmatchedNames` still identifies unresolved names, not missing installations.
Use scoped `mise which` for the executable; a supplier error is UNKNOWN.
Do not install duplicate tools merely because PATH or Gateway discovery fails.

An `on_path` result is only command resolution; `not_on_path` is **not**
an installation verdict. Windows installed applications are separately observed
from WinGet/uninstall registry, Linux packages from the actual package manager,
Runtime target/context from `runtime.describe`, and authorization/readiness
from the actual provider. Use `mise which`, `mise tasks ls`, provider-native
`--version`/health, or locked toolchain commands as relevant, without silently
upgrading inventory into a global capability result.

### Resolve the owner environment before declaring an execution blocker

A PATH miss, a missing Python import, a cache miss and an admission refusal
are different observations. For a configured project tool, first inspect
the owner's actual `mise.toml` and lockfile. Use the admitted mise/uv
entrypoint in that owner directory, rather than installing a duplicate
system executable or invoking a project interpreter outside Runtime's
configured executable roots.

For example, from the respective owner directories:

```sh
# apps/web: select the existing project toolchain
mise ls --installed
mise exec -- pnpm --version
# tools/formal: select the existing formal toolchain
mise exec -- lean --version
# services/harness: use the locked project interpreter and dependencies
uv run --locked --offline python -m pytest -q tests/test_p0_continuity_records.py
```

If a locked offline invocation identifies a missing package, inspect
`uv cache dir` in the same Runtime context. When network use is authorized,
materialize the existing lock with the normal `uv run --locked` or
`uv sync --locked` path, then verify the actual requested consumer.
Do not change versions to make a cache miss disappear. An offline pass in
one Workspace does not establish cold-Workspace readiness: check cache
scope when cross-Workspace reuse matters. A rejected executable or
execution identity remains an admission issue for Runtime/Workstation,
not evidence that the software is absent; do not bypass that boundary.

Agent routing: [root AGENTS.md](../../../AGENTS.md) →
[Capability Catalog](../../../catalogs/capabilities/README.md) →
natural Owner's own CLI/MCP/Skill → provider and consumer readback.

### Windows service and interactive-user probes

Windows does not require Python for command lookup. Run the bundled
`probe_executables.ps1` through the **target** Windows Runtime identity:

```powershell
pwsh -NoProfile -NonInteractive -Command "& './platform/workstation/inventory/probe_executables.ps1' -Names @('git','gh','mise','uv','pnpm')"
```

The result includes `executionPrincipal`, current-node identity and a PATH digest.
Invoke it separately with service and `active_user` Runtime authorities.
Do not merge the two observations: a missing service PATH entry does not
establish that the application is absent from the interactive user.
