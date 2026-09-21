# Media standalone source-carrier archive-in-place acceptance — 2026-09-21

Standing: **ARCHIVED_IN_PLACE**

Scope: retire /root/projects/ordivon-media from active/current Media composition while retaining the repository in place as an exact historical Git and recovery carrier.

This is intentionally not a physical deletion. Creative Library and one bounded OMPC fixture still bind historical revisions through the standalone repository path.

## Active owner

Current active Media source owner:

/root/projects/ordivon/capabilities/media

The standalone repository is not a live service source, systemd WorkingDirectory, cron source, or running-process source. Forward Media evolution, including the Media-hosted Creative Library overlay, belongs to the canonical monorepo owner.

## Archived source identity

- archived path: /root/projects/ordivon-media
- archived revision: 30f6d1228a4270a68cd715ca9a7b17742478958e
- archived worktree at gate: clean
- remaining physical worktrees after Runtime close and Git prune: standalone root only

The clean Runtime audit workspace ws-media-meta-system-scope-audit-r1-20260920 was closed by Runtime with exact sourceStateDigest comparison before this standing was prepared. Stale/missing temporary worktree registrations were pruned.

## Exact historical lookup requirement

Creative Library currently contains 137 records whose sourceRepo is /root/projects/ordivon-media.

Observed retirement gate:

- historical records: 137
- distinct bound revisions: 133
- exact revision:path lookup failures: 0

Physical deletion would therefore reduce direct historical reproducibility unless every bound locator were replaced by a separately mounted archive namespace. No such rewrite is required for the monorepo migration.

The correct disposition is ARCHIVED_IN_PLACE.

## OMPC recovery fixture

capabilities/media/research/media/engineering-consumption/fixtures/studio-expression-card-lineage.json explicitly records /root/projects/ordivon-media as currentRecoveryRepository for one historical Studio lineage fixture.

The fixture also states that this recovery locator does not rewrite the historical authority fence or currentize the Claim. It is therefore compatible with archive-in-place standing and is not evidence that the standalone repository remains a current semantic owner.

## Complete Git preservation

Fresh all-refs bundle:

/root/ordivon-migration-backups/2026-09-21-media-retirement/media-all-refs.bundle

Observed archive proof:

- ordinary Git refs: 899
- bundle SHA-256: 75b911870a95e73709e849cbf59ddc17acdddcfa1be4270cb71579a2f3e5a3b5
- refs manifest SHA-256: d2b33f3183e53edf09eefa26c13d69817a8f02ddd5d40948e349e44a04e631db
- bundle missing refs: 0
- bundle mismatched refs: 0
- mirror restore missing refs: 0
- mirror restore mismatched refs: 0

Archive proof record:

/root/ordivon-migration-backups/2026-09-21-media-retirement/media-archive-proof.json

The earlier 2026-09-20 Media bundle remains historical migration evidence; retirement relies on the fresh all-refs archive above.

## Ignored/non-Git state

The standalone repository exposed 13,219 ignored paths.

A path-component-aware classification found:

- rebuildable dependency/cache paths: 13,219
- non-rebuildable ignored paths: 0

The apparent nested paths under apps/*/node_modules and packages/*/node_modules are package-manager dependency links/binaries or webpack caches, not unique Media authority state.

Classification:

/root/ordivon-migration-backups/2026-09-21-media-retirement/media-ignored-classification-v2.json

## Repository-side archived-source fence

Policy:

docs/migration/retirement/media-standalone-policy.json

The shared checker:

tools/repo/check_archived_source_boundary.py

classifies the remaining standalone Media locator references into explicit historical/recovery classes.

Observed gate on the candidate:

- tracked files containing /root/projects/ordivon-media: 21
- explicitly allowed: 21
- forbidden forward references: 0

Allowed classes are limited to:

- historical/migration/research documentation;
- committed artifacts/evidence;
- frozen production source/render carriers;
- migration/planning records;
- the exact OMPC Fixture B recovery locator;
- the policy itself.

The root repo:retirement:verify task now iterates all archived-source policies, so workstation-lab and Media use the same fail-closed mechanism.

## Repository governance baseline

The archive candidate did not claim a globally green root governance gate.

On the unmodified canonical base b39196328351d11db6759a0ea902e05f1b7256a1, tools/repo/check_github_governance.py already fails because its expected uv-owner set still includes services/gateway while that directory is absent from the committed tree. The Media candidate reproduces the same failure.

This is concurrent Gateway/convergence governance debt, not a Media retirement regression. The Media acceptance therefore requires the archived-source boundary, synthetic fail-closed retirement test, affected-owner tests, and diff check; it does not rewrite unrelated Gateway governance state.

## Meaning of ARCHIVED_IN_PLACE

After acceptance, /root/projects/ordivon-media is not:

- the current Media source owner;
- a live service/deployment source;
- a current Creative Library owner;
- an admitted target for new feature development;
- a current runtime state authority.

It remains:

- a readable Git historical carrier;
- an exact old revision/path lookup target;
- a recovery locator for bounded historical fixtures;
- independently recoverable from an all-refs bundle.

No new forward responsibility may be introduced into the standalone repository without explicitly reopening this standing.

## Non-claims

This acceptance does not:

- rewrite Creative Library provenance;
- rewrite production snapshots;
- make Media historical records monorepo-native retroactively;
- physically delete /root/projects/ordivon-media;
- retire unrelated standalone repositories;
- merge Media runtime/service authority into another owner.
