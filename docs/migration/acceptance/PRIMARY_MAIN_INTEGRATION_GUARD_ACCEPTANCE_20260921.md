# Primary monorepo main integration guard acceptance — 2026-09-21

Standing: **ACCEPTED_REPOSITORY_MECHANIC**

Scope: prevent shared-primary-checkout drift while many detached Runtime worktrees develop and qualify independent Ordivon changes.

This mechanic owns only Git integration hygiene. It does not own Runtime jobs, Host continuity, domain truth, owner-native verification, release authority, provider effects, or scientific standing.

## Failure observed

The physical primary checkout at /root/projects/ordivon is the checkout of refs/heads/main. Multiple agents qualified candidates in detached Runtime worktrees and then advanced refs/heads/main through commands targeted at the physical repository.

Git ref movement performed outside the primary checkout does not automatically rewrite that checkout's index/worktree. Two real stale-primary states were observed.

### Incident 1

At the first census:

- main/HEAD: ba46f7b7cd9c1359ab8fdc073d7e26d56aba5ff6 after concurrent Gateway/Plugin/Workstation integration
- primary index tree before the first repair: 9fd20fb4ad3b46cbbb9de54f89fe5f5e682f554e
- the stale index was exactly the tree at 6cf76a491 plus the already-committed Capital standalone-retirement patch
- that Capital patch was byte-identical to commit e3bc5f2487e003ae50e642d686c015604485e888
- e3bc5f248 was already an ancestor of main
- unstaged paths: 0
- untracked paths: 0

The stale bytes were therefore committed/recoverable state, not unique work. Recovery evidence was frozen under:

/root/ordivon-migration-backups/2026-09-21-primary-checkout-sync

The primary checkout was then explicitly synchronized to main and verified clean.

### Incident 2

The same failure mode reproduced while the guard was being developed:

- main/HEAD: 11a4818ccbaf64a4984c639667bc8f6dbc0f3e95
- primary index tree: d4a95da2d7a2feea05a84cfa820741f041798e72
- that tree exactly matched committed revision eddec707e81df7694268e8015cde855c89d0359d
- eddec707 was already an ancestor of current main
- unstaged paths: 0
- untracked paths: 0

The apparent Cloudflare reversions were therefore a stale-tree projection, not active uncommitted Cloudflare work. A second exact recovery snapshot was frozen before synchronization.

These two incidents establish a repository-mechanics problem rather than an owner/domain problem.

## Accepted mechanics

### check-primary-main.sh

tools/repo/migration/check-primary-main.sh validates one physical primary checkout and fails closed unless all of the following hold:

- checked-out branch is main
- HEAD equals refs/heads/main
- index tree equals HEAD tree
- tracked worktree bytes equal the index
- index equals HEAD
- no untracked paths are present

It never stashes, resets, commits, merges, or repairs bytes.

### integrate-main.sh

tools/repo/migration/integrate-main.sh is the accepted serialized main-integration entry point.

It:

1. resolves the primary repository;
2. acquires a non-blocking flock under the common Git directory;
3. runs the primary-checkout invariant after taking the lock;
4. optionally fences the exact expected main revision;
5. resolves one exact candidate commit;
6. returns idempotently when the candidate is already contained;
7. uses fast-forward integration when current main is an ancestor of the candidate;
8. otherwise requires a successful git merge-tree --write-tree preview;
9. rechecks the primary invariant and main revision immediately before mutation;
10. performs the Git merge;
11. reruns the primary invariant;
12. proves the candidate is an ancestor of resulting main.

It deliberately does not run owner tests. Owner-native qualification must happen before candidate integration.

It deliberately does not auto-stash or auto-reset a dirty/stale primary checkout. A dirty primary remains a fail-closed recovery event requiring evidence-aware handling.

## TDD coverage

tools/repo/migration/test-integrate-main.sh constructs disposable Git repositories and proves:

- a clean descendant candidate fast-forwards and leaves the primary exactly synchronized;
- externally advancing refs/heads/main while leaving the physical index/worktree stale is rejected by both checker and integrator;
- a conflicting divergent candidate is rejected before mutation and leaves current main clean and unchanged.

Standing:

- integration-helper smoke: PASS
- ShellCheck: PASS
- root repo:ci with the helper test: PASS

## Root task surfaces

The root exposes:

- repo:integration:test — hermetic disposable-repository test for the integration waist
- repo:primary:verify — local operational check of /root/projects/ordivon

repo:ci runs the hermetic integration-helper test but does not require the machine-specific physical-primary path.

## Governance drift found during acceptance

The first repo:ci run exposed a pre-existing root-governance drift: services/gateway carried uv.lock but Dependabot did not include /services/gateway in the uv directories list.

The unmodified base reproduced the same failure.

The root Dependabot uv owner list was corrected, after which:

- github governance: valid
- uv owner directories: 12
- npm owner directories: 5
- cargo owner directories: 1
- root repo:ci: PASS

This is repository governance correction, not Gateway semantic ownership.

## Real dogfood integration

After Incident 2 was proven recoverable and the primary checkout was synchronized, the new helper integrated the guard candidate itself against a concurrently advanced main.

Observed result:

- previous main: 11a4818ccbaf64a4984c639667bc8f6dbc0f3e95
- candidate: 76386f77f0219ac987d23ffa51218832db836bc4
- integration mode: MERGE_COMMIT
- resulting main: cb6f1eea76fb67196204833ad36dac258efd90eb

Post-integration:

- primary-main invariant: PASS
- HEAD == main: PASS
- index tree == HEAD tree: PASS
- tracked worktree clean: PASS
- untracked paths: 0
- candidate ancestry: PASS
- root repo:ci: PASS

## Boundary

The accepted rule is:

candidate worktree -> owner-native verification -> serialized Git integration -> post-integration primary proof

not:

arbitrary agent -> mutate shared primary index -> infer intent later

The physical primary checkout is therefore a shared integration carrier, not an agent scratch workspace.
