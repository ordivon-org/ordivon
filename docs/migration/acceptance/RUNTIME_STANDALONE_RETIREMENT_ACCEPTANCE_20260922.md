# Runtime standalone source-carrier retirement acceptance — 2026-09-22

Standing: **RETIRED_ARCHIVED**

Scope: close the physical retirement of `/root/projects/ordivon-runtime` after canonical monorepo ownership, structured live release cutover, large-Registry health repair, complete Git/worktree/non-Git recovery capture, consumer cutover, quarantine verification, and post-delete recovery proof.

## Canonical owner

- canonical repository: `/root/projects/ordivon`
- owner path: `services/runtime`
- legacy standalone path: `/root/projects/ordivon-runtime`
- legacy standalone HEAD: `af67ed760a31813562745412c2553b8297a10e67`
- canonical release source: `/root/projects/ordivon/services/runtime`
- release publication authority: `origin/main`

The live Runtime executable is installed under `/usr/local/libexec/ordivon`; source checkout paths are not live executable authority.

## Production cutover

The structured Runtime release path deployed commit `7741c2e9e53fc4954ce16b692cfe19b27703caee` with 12/12 release artifacts digest/mode/byte matched, a 23-tool catalog, deployment status `deployed`, service active/running, and no recovery requirement.

The subsequent canonical Runtime owner revision changed documentation/consumer coordinates only; the candidate Runtime executable digest remained byte-identical to the installed executable.

The large-history Registry health regression was repaired before retirement. On the production Registry with more than 250,000 Jobs, direct `registry-status` fell from approximately 9.96 s to approximately 0.02 s and `ordivon-runtime-status --health --json` returned `healthy` in approximately 0.11 s. Registry schema remained version 6.

## Complete recovery capture

Retirement evidence root:

`/root/ordivon-migration-backups/2026-09-22-runtime-retirement`

The source-state census records 810 Git refs, 33 worktrees total, 32 linked worktree HEADs archived in addition to the root worktree, 19 dirty linked worktrees restore-proven, one stash (`964e835adf98730c15a0faa4eaded2c2e34a65ce`), and 28 non-Git/untracked payload files captured separately.

All-refs/worktree bundle: `runtime-all-refs.bundle`

SHA-256: `afce71a2105e1d7199164396e5ed67125e2604c6f393ba94eb5d681d96a933fe`

Linked-worktree payload archive: `runtime-linked-worktree-untracked.tar`

SHA-256: `86223585857cc3e25a8dd659b05fa43e6e8aeefc4719b7d0433631b55c3374f6`

`git bundle verify` passes. A fresh post-quarantine bare restore contains all 810 source refs exactly, including `refs/stash`, and `git fsck --full --strict --no-reflogs` reports no non-dangling errors.

## Archived-source reference fence

Canonical policy: `docs/migration/retirement/runtime-standalone-policy.json`

The policy intentionally preserves historical provenance rather than rewriting it. Allowed references are limited to migration acceptances/receipts, the frozen M0 migration plan/baseline, frozen System Constellation Atlas source topology, four external-authority `provenance.registrationBasis` records, one dated standard-native acceptance record, and the policy itself.

The four Authority Catalog records do not dereference `registrationBasis`. The historical Runtime standard object remains recoverable from the retirement bundle, while canonical `services/runtime/standards/runtime_standard_native_r3.toml` has the same SHA-256 (`03e1dc7d2d59ac2af742a09da1434ca5a0c0438548fc2f444996d847f53d0c1c`).

Two Rust test-only systemd command fixtures retain the locator as an arbitrary workspace example. The retirement policy admits that exact source file only for this bounded test-fixture use; production Runtime path resolution does not consume it.

`mise run repo:retirement:verify` is the persistent fail-closed gate for future tracked references.

## Physical retirement

Pre-quarantine evidence: `/root/ordivon-migration-backups/2026-09-22-runtime-retirement/runtime-physical-retirement-prequarantine.json`

It recorded active old-root references 0, linked worktrees 0, mount references 0, process FD references 0, bundle restore PASS, candidate/install parity 12/12, and Runtime health healthy.

Post-quarantine evidence: `/root/ordivon-migration-backups/2026-09-22-runtime-retirement/runtime-physical-retirement-postquarantine.json`

It recorded deletion authorized by gates, the legacy path absent, 810/810 refs restored, Runtime operator tests 78/78 PASS, MCP tests 66/66 PASS, auth tests 10/10 PASS, Harness Finance tests 20/20 PASS, root repository CI PASS, and Runtime health healthy.

The quarantine carrier was subsequently deleted. No compatibility alias was created.

## Post-delete proof

Final post-delete machine-readable proof:

`/root/ordivon-migration-backups/2026-09-22-runtime-retirement/runtime-post-retirement-proof.json`

The final proof requires the legacy source and quarantine paths absent, bundle verification PASS, all 810 source refs and the stash restored exactly, payload archive digest/entry count exact, zero active process links to the retired root, current release authority bound to canonical `services/runtime`, live Runtime health healthy, archived-source policy PASS, and root repository CI PASS.

## Disposition

- active Runtime source owner: canonical monorepo `services/runtime`
- live Runtime effect carrier: `/usr/local/libexec/ordivon`
- Runtime durable state: Registry under `/var/lib/ordivon/registry`
- legacy standalone source carrier: physically absent
- quarantine carrier: physically absent
- complete Git refs/history/stash/worktree heads: archived and restore-proven
- dirty linked-worktree payload: archived and restore-proven
- historical provenance: retained without rewriting
- new active references to the retired locator: fail closed

This retires only the standalone source carrier. It does not make the monorepo root authoritative for Runtime execution state, deployment receipts, or Registry semantics.
