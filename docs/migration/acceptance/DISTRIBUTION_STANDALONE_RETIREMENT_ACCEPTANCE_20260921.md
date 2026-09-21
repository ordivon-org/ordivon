# Distribution standalone source-carrier retirement acceptance — 2026-09-21

Standing: **RETIRED_ARCHIVED**

Scope: retire the legacy standalone Distribution source carrier at /root/projects/ordivon-distribution-v2 after identity-preserving monorepo import, optional-effect source acceptance, current metadata cutover, Runtime drainage, complete Git preservation, and post-delete owner verification.

This retirement does not authorize or perform a provider write, external publication, destructive external effect, credential change, or provider-account mutation.

## Legacy source identity

At the physical-removal boundary:

- legacy path: /root/projects/ordivon-distribution-v2
- legacy HEAD: 00d919f3f54c636704f6401e407dcff12a685600
- legacy tree: 9189ed36e8a68fa02e097a5c89d13e3c67a976c6
- tracked status: clean
- physical Git worktrees: one, the standalone root itself
- Runtime workspaces rooted at the legacy source: zero
- process references: zero
- systemd references: zero
- /etc and /root/.config references: zero

The canonical source owner is /root/projects/ordivon/capabilities/distribution.

Its retirement-boundary tree was:

221417f0836f48faa5bc1c6ed48e48fb67ab0d31

The canonical tree intentionally differs from the frozen standalone tree by monorepo forward evolution: owner-local Dependabot configuration was removed and mise configuration was adapted to the monorepo environment. The prior Distribution import acceptance already proves exact source/history import before this forward evolution.

## Current metadata cutover

Current Distribution provider metadata now binds Source to:

/root/projects/ordivon/capabilities/distribution

and records the standalone observation revision separately as historical provenance.

The Distribution package metadata now names the same canonical current source owner while preserving the exact historical standalone observation at 03ccc562160b.

Current metadata cutover commit:

e3357d1059b53e27693d82462d6a1554281a4260

Validation before retirement:

- meta/next full pytest: PASS
- canonical Distribution mise run verify: PASS
- uv lock/sync: PASS
- Ruff: PASS
- external-first authority-bound structure: PASS
- approval/effect-authority suites: PASS
- reconciliation semantics: PASS
- ShellCheck: PASS
- GitHub provider-native historical read positive control: PASS

No provider write was performed by these gates.

## Git preservation

Complete all-refs bundle:

/root/ordivon-migration-backups/2026-09-21-distribution-retirement/distribution-all-refs.bundle

SHA-256:

dd9f6d4a82242d1d7f34356427eb4236bb5bb4eb624be69524abe14313611154

Ordinary refs manifest:

/root/ordivon-migration-backups/2026-09-21-distribution-retirement/distribution-all-git-refs.tsv

SHA-256:

385079416065e824c7644fc897c5355c434637ee4ff7379485997012e8a78123

The manifest contains 16 ordinary refs. It includes the Web-retirement handoff branch and the repository-modernization archive tag.

Before deletion:

- missing refs from bundle: 0
- ref digest mismatch: 0

After physical deletion the bundle was cloned into a fresh mirror repository and all 16 refs were resolved again:

- missing: 0
- mismatch: 0

## Non-Git state

The standalone root contained 230 ignored entries. File-level classification found zero non-cache ignored files.

The ignored state consisted only of rebuildable environment/cache material such as the Python virtual environment, bytecode/cache entries and Ruff cache. No unique runtime database, research evidence, provider receipt or non-Git payload required a separate data archive.

## Physical retirement receipts

Pre-delete receipt:

/root/ordivon-migration-backups/2026-09-21-distribution-retirement/distribution-physical-retirement.json

SHA-256:

aab4041c0df6c66215ef745382b8f9f513e5f1910a0bf4f82a1c95fc0ed91c07

Post-delete proof:

/root/ordivon-migration-backups/2026-09-21-distribution-retirement/distribution-post-retirement-proof.json

SHA-256:

2284eea2a7374e8de6c2d5886db89b1a5fedc6955335ce6272c4000d58efbbcc

## Post-delete functional proof

With /root/projects/ordivon-distribution-v2 physically absent:

- canonical Distribution mise run verify: PASS
- provider current source metadata: canonical
- package current source metadata: canonical
- live OS references to the old root: 0
- Git restore proof: 16 refs, missing=0, mismatch=0
- provider write performed: no
- external publication performed: no

Nine tracked files still contain the old path intentionally. They are bounded historical/provenance material: migration receipt/acceptance, M0 migration planning/baseline, the dated System Constellation Atlas snapshot, one exact historical standalone observation in package metadata, and a negative Workstation regression that forbids reintroducing the old source binding.

Physical retirement does not rewrite provenance.

## Disposition

- active Distribution source owner: /root/projects/ordivon/capabilities/distribution
- legacy standalone path: physically absent
- standalone Git history: archive/restore proven
- Web retirement handoff history: preserved
- compatibility alias at the old path: none
- provider/external write from this retirement: none

If historical Distribution source must be recovered, materialize it into a bounded recovery path from the recorded bundle. Do not recreate /root/projects/ordivon-distribution-v2 as a compatibility alias.
