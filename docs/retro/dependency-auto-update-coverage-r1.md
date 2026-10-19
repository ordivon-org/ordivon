# Ordivon dependency auto-update coverage R1 (2026-10-19)

## Decision

Reuse the existing GitHub **Dependabot** upgrade pipeline. Do not install a
second Renovate bot, ad hoc cron downloader, or unbounded root-level upgrade
service while a capable updater is already configured.

An **available update** is not an **accepted release**:

1. Discover available upstream versions and produce a proposed PR.
2. Resolve and lock exact dependencies in source.
3. CI/test/build/qualification before merge.
4. Stage the new binary or deployment and verify owner-native health.
5. Release only across the correct Runtime / Host / network / Workstation
   admission fence, with rollback and a source-identity witness.

Only steps 1-2 are performed automatically by Dependabot. A GitHub PR must
be present on the actual **default branch**, and Dependabot version updates
must be enabled at the repository level. A local Git commit does not schedule
an upstream bot or deploy software to this workstation.

## Existing coverage retained

`.github/dependabot.yml` already schedules weekly GitHub Actions, Python uv,
Node npm/pnpm and Runtime Cargo updates. Existing monorepo lockfiles are the
package-manager authority; do not add duplicate nested schedules for packages
whose dependencies are pinned by a parent workspace lock.

The R1 additions are:

- Nix flake inputs in `platform/workstation/workstation/nix` and
  `capabilities/artifact/artifact-delivery/openxml-nix`, monitored weekly by
  GitHub Dependabot's native `nix` ecosystem.
- A dedicated npm dependency manifest and lockfile in
  `platform/workstation/workstation/nix/codex-cli`, monitored weekly by the
  existing npm ecosystem entry.
- Workstation Home Manager obtains the Codex CLI version directly from
  `codex-cli/package.json`; there is no independently maintained literal
  version string in `nix/home.nix`.

The current Codex package is `@openai/codex@0.163.0`. Its installed
node-local prefix remains
`/root/tools/share/codex-npm-0.163.0`, and Home Manager's link evaluates
to that prefix. The actual account/session, VPN wrapper, and model capability
are separate live verification gates; the npm manifest does not authenticate
them.

## How to accept a proposed Codex CLI update

1. Review the Dependabot npm PR, lockfile change, release notes, source hash
   and any significant CLI/migration changes. Confirm the desired version is
   available in your account.
2. On an isolated workstation carrier, install the exact proposed version into
   the versioned prefix using the existing npm CLI, with scripts disabled
   where supported (do not overwrite the current live prefix).
3. Run `codex --version`, ChatGPT login status, the existing `codex-vpn`
   network wrapper, a named-model + effort test, and bounded MCP startup.
4. Build the Home Manager generation from the matching source revision.
   Verify that the new `tools/bin/codex` target resolves to the preinstalled
   prefix. Maintain the prior generation and versioned CLI for rollback.
5. Only then activate the new generation and independently re-read version,
   authentication, model and external transport health.

This is a **release acceptance**, not a blind nightly `npm update`.
A PR that modifies the manifest without staging its binary must NOT be
deployed; the Home Manager out-of-store link could otherwise point at a
nonexistent path.

## Boundary / risk table

| Surface | Discovery | Local deployment |
| --- | --- | --- |
| Actions, uv, npm, Cargo | Existing weekly Dependabot | PR + project tests |
| Workstation / OpenXML Nix flake inputs | Added weekly Dependabot | Rebuild + qualification + rollback |
| Codex CLI | Added npm Dependabot watch | Staged npm prefix + Home Manager acceptance |
| Mise-managed runtimes | Pinned per project, not audited as live updater | Qualification before toolchain switch |
| Linux Arch packages / kernel | No general auto-upgrade timer confirmed | Keep pacman changes gated; paccache is cleanup, not upgrades |
| Windows, WSL, Browserless images, native agents | Not qualified as automatically updated | Separate environment/provider census + health and rollback |
| Model availability / quotas | Live account catalog, not package update | Explicit model/capability canary |

### Findings and non-claims

- Linux systemd has scheduled backup, capacity, network and maintenance
  timers. None observed was an all-purpose OS/package updater; user-scoped
  timers were not readable from the Runtime service identity.
- Root Git `origin` is on GitHub. However the local update source alone
  does not prove Dependabot is enabled or that any PR was opened.
- The Runtime Workspace admission floor blocked a new isolated Workspace
  when D-drive free space dipped just below 20 GiB. The task reused an
  already clean, idle Workspace and fast-forwarded its checkout; it did
  not delete other agents' assets or reduce capacity fences.
- Optional installed binaries, Windows software and standalone container
  images are not magically managed by GitHub dependency updates.
- GitHub's native Nix flake Dependabot support monitors **version updates**,
  not Nix-specific security advisories; additional vulnerability scanning
  and release acceptance remain separate tasks.

## Success condition for wider automatic deployment

Automate **safe release**, not just version installation: every component
needs an exact input revision, a minimal bounded smoke, current health check,
rollback and currentness/admission fence. Reuse Ordivon Runtime + existing
owner-native release tools when that concrete frontier becomes relevant.
Do not add a generic privileged unattended upgrader now.
## Low-risk automatic merge lane

Repository-native auto-merge is enabled, but no PR bypasses branch protection.
`.github/workflows/dependabot-patch-automerge.yml` queues only Dependabot PRs
whose metadata says **semver patch** and whose dependency is either
`direct:development` or `indirect`.

The workflow uses `pull_request_target` only to obtain write permission for the
repository-owned merge queue. It deliberately does **not** checkout, source, or
execute the Dependabot head branch. It only reads GitHub's Dependabot metadata
and calls `gh pr merge --auto --squash`. Existing required CI and protected-
branch checks must still succeed before GitHub merges the PR.

Production/direct dependencies, minor/major updates, Codex, Nix, Runtime,
network, Windows system changes and container image release changes remain on
the gated acceptance path. Enabling repository auto-merge alone has no effect
without an explicit qualifying workflow or human request.
