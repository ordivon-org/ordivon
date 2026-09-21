# workstation-lab retirement acceptance — 2026-09-21

Standing: **ARCHIVED_IN_PLACE**

Scope: retire `/root/workstation-lab` from active/current Ordivon composition while preserving the repository in place as an exact historical Git carrier.

This acceptance is intentionally not a physical deletion. Historical Creative Library records still bind exact source revisions and paths in this repository.

## Final source identity

- archived path: `/root/workstation-lab`;
- archived revision: `ee41e995d0bd98ac08de54d9d11c876345f4f182`;
- final subject: `creative-library: retire geospatial presentation classification`;
- source worktree at retirement gate: clean.

The final staged Creative Library contraction was validated and committed before retirement. No dirty bytes were hidden inside the retirement transition.

## Full historical archive

A separate full Git bundle exists:

- bundle: `/root/ordivon-migration-backups/2026-09-21-workstation-lab-archive/workstation-lab.bundle`;
- bundle SHA-256: `e1f397e0b75ec24e47e3ea4b8f549c9e8d9cfad7747a04b021507885375ee311`;
- bundle verification: PASS.

The in-place repository and independent bundle are complementary: the in-place repository supports exact historical lookup, while the bundle supplies an independent reconstructible Git archive.

## Responsibilities drained

Before retirement, the two remaining material live residuals were decomposed instead of preserving workstation-lab as a mixed owner.

### Preservation

The standard-native Preservation profile was extracted into `capabilities/preservation`.

Preservation semantics remain externally owned by OAIS / ISO 14721, Archivematica, Artefactual Fixity, PREMIS/METS, PRONOM/E-ARK, systemd and Docker Compose. Ordivon retains only the bounded local composition and evidence binding.

### Creative Library

Creative Library was extracted as an identity-preserving filtered source slice and appended under `capabilities/media`.

Media hosts the catalog/presentation projection only. It does not acquire work identity or source-byte authority.

The current forward API no longer uses:

- `workstation_root`;
- `ORDIVON_WORKSTATION_ROOT`;
- `source:workstation`;
- `workstation:creative-library`.

The forward projection uses `creative_library_root` and `source:creative-library`.

### System Constellation Atlas

The future atlas generator no longer includes workstation-lab as a current repository. It discovers standalone `/root/projects/ordivon-*` repositories plus the canonical `/root/projects/ordivon` monorepo.

The 2026-09-15 source snapshot and SVG/PNG/GeoPackage carriers were not rewritten. Their historical digests remain unchanged.

## Repository-side retirement fence

The monorepo now contains:

- policy: `docs/migration/retirement/workstation-lab-policy.json`;
- checker: `tools/repo/check_archived_source_boundary.py`;
- synthetic test: `tools/repo/test-check-archived-source-boundary.sh`;
- root verification entrypoint: `mise run repo:retirement:verify`.

The checker is semantic rather than a raw string-zero rule.

Allowed reference classes are restricted to historical/documentary surfaces:

- documentation;
- committed artifacts/evidence;
- frozen production source/render carriers;
- historical experiments/evaluation fixtures;
- authority/planning/migration snapshots;
- two extraction source-boundary records;
- four exact negative/synthetic test fixtures;
- the policy itself.

At the final host retirement gate:

- tracked files containing the historical locator: **61**;
- explicitly allowed: **61**;
- forbidden forward references: **0**.

The synthetic checker test proves that a new ordinary source file containing the retired locator fails closed.

## Host-side active dependency gate

The final host-side gate found:

- active systemd references to `/root/workstation-lab`: **0**;
- cron references: **0**;
- running process command-line references: **0**;
- process current-working-directory references: **0**;
- current immutable recovery launcher references: **0**;
- compatibility aliases `/root/projects/workstation`, `/root/projects/workstation-lab`, and `/root/workstation`: **0**.

The current Workstation recovery generation uses:

`CONTROL_REPOSITORY=/root/projects/ordivon-workstation-v2`

and does not use workstation-lab as a current backup/control input.

A later semantic-recovery prune timeout observed in the Workstation backup service is a separate recovery-maintenance issue and is not caused by workstation-lab.

## Historical exact-source carrier

Creative Library currently contains **78** historical work records whose source repository is `/root/workstation-lab`.

The retirement gate independently checked all 78 records:

- 78 distinct bound revisions;
- exact `revision:path` Git lookup attempted for every record;
- lookup failures: **0**.

For this reason physical deletion would reduce historical reproducibility. The correct retirement mode is therefore `ARCHIVED_IN_PLACE`, not DELETE.

## Standalone source-carrier boundary

Some pre-overlay standalone source carriers, notably `/root/projects/ordivon-media@30f6d122`, still contain the older workstation-lab locator in source that predates the monorepo-only Creative Library composition.

This does not make workstation-lab an active owner:

- no live unit or process executes the standalone Media source;
- Creative Library is explicitly an intentional monorepo-only overlay and was not back-ported to the standalone source carrier;
- the archived workstation-lab path remains present for historical compatibility and exact source lookup.

This retirement does not itself retire standalone Media, Workstation, Harness, Game, Artifact, or other source repositories. Those repositories require their own retirement gates.

## Meaning of ARCHIVED_IN_PLACE

After this acceptance, workstation-lab is not:

- a current Workstation owner;
- a deployment source;
- a current recovery/control repository;
- a current Creative Library owner;
- a Preservation owner;
- a current repository-discovery input;
- an admitted target for new feature development.

It remains:

- a readable Git provenance carrier;
- an exact old-revision/source-path lookup target;
- an independently bundled historical repository.

No active/current Ordivon responsibility may be reintroduced there without explicitly reopening this retirement standing.

## Non-claims

This acceptance does not:

- delete or rewrite workstation-lab history;
- rewrite historical evidence locators;
- rewrite frozen production snapshots;
- retire unrelated standalone repositories;
- claim all monorepo source migrations are complete;
- resolve the separate Workstation semantic-recovery prune timeout.
