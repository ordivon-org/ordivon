# Creative Library Slice Migration Acceptance — 2026-09-21

Standing: **ACCEPTED_SOURCE_ONLY**

Scope: extract the still-live Creative Library residual from historical workstation-lab and host it inside `capabilities/media` as a rebuildable cross-domain catalog/presentation projection.

## Historical source

The workstation-lab staged geospatial presentation-classification contraction was independently validated and committed before extraction:

- historical source revision: `ee41e995d0bd98ac08de54d9d11c876345f4f182`;
- owning tests: 9/9 PASS;
- catalog after contraction: 304 works / 3315 carriers / 45 relations;
- catalog digest: `sha256:f0d0fb35cdec69454411f70c599b6ff01b5ddb0fd7be8f885109bc2067e6ee81`;
- pre-existing staged backup patch SHA-256: `68a5cdcec9f016428e7afdcb04af750c6c80f580161c39b9c932e9cd1438e678`.

A full clean archive was then created without claiming retirement:

- bundle: `/root/ordivon-migration-backups/2026-09-21-workstation-lab-archive/workstation-lab.bundle`;
- bundle SHA-256: `e1f397e0b75ec24e47e3ea4b8f549c9e8d9cfad7747a04b021507885375ee311`;
- source head: `ee41e995d0bd98ac08de54d9d11c876345f4f182`.

## Filtered Creative Library source

A minimal functional closure was extracted with `git-filter-repo` revision `a40bce548d2c`.

Included paths:

- `artifacts/creative-archive/historical-works-r2-source-complete.json`;
- `artifacts/creative-library/**`;
- `creative-library/**`;
- `scripts/creative_library.py`;
- `tests/test_creative_library.py`.

The frozen Creative Archive JSON fallback is part of the closure because the catalog build supports it as the reproducible archive input.

Extraction identity:

- filtered base: `78fd667498bfa030068ddba54ac99c559976bee0`;
- final source revision: `d9d6181fd2773543edad6d1c00a82ca6d6ece883`;
- source tree: `7a711a8af250af362a0b673e034f663dbea234ca`;
- bundle: `/root/ordivon-migration-backups/2026-09-21-creative-library-extract/creative-library.bundle`;
- bundle SHA-256: `03d80ebb3b86097fa762482fd3a0ec7fd1a668c3002de4b0ec0c82424f871142`.

The extracted source passed 9/9 owning tests and catalog digest verification.

## Append-only slice import

Creative Library was not allowed to replace the existing Media owner subtree.

The migration primitive enforces:

- existing target owner required;
- verified exact source bundle/ref/revision;
- zero target-path collisions;
- diff consists only of `A` entries for exact source paths;
- every appended path preserves Git mode/type/blob OID;
- existing Media bytes remain unchanged;
- collision-negative synthetic test fails closed.

On the current canonical base `0067965de71efa52a98ef43d9aa52bab3d1a3fbe`:

- append-only helper commit: `a615e9905`;
- Creative Library slice merge: `6a4f3cabdf57f793a7417cc7b16547357c70fd55`;
- migration receipt commit: `4d18c4618f8cc14fce657c23e81f1be57d14316e`;
- target prefix: `capabilities/media`;
- path collision count: 0.

## Forward authority cleanup

Forward Media code was deliberately refactored after history import:

- replayed refactor commit: `f26ee2609`;
- `workstation_root` removed;
- `ORDIVON_WORKSTATION_ROOT` removed;
- `source:workstation` removed from Creative Library forward projection;
- `workstation:creative-library` removed;
- new input: `creative_library_root`;
- optional explicit locator: `ORDIVON_CREATIVE_LIBRARY_ROOT`;
- default locator: current Media owner root;
- projection source: `source:creative-library`;
- catalog membership: `creative-library`.

No compatibility alias was retained.

Historical catalog records keep their original owner, source repository, source revision, source path and exact Git carrier binding. Media hosting does not acquire those authorities.

## Owner-native acceptance

The accepted Media tree was validated before replay:

- Ruff 0.16.8: PASS;
- Node 26.9.0;
- pnpm 12.4.2;
- Python 3.14.7;
- Media owner-environment test: **165 tests PASS**;
- Media cold-start: **165 tests PASS**;
- TypeScript typecheck: PASS;
- Vite production build: PASS;
- Creative Library is included in the default Media Python test surface;
- forward stale Workstation Creative-Library locator references: 0;
- source-boundary checks: PASS;
- final integrated gate: `overall=0`.

The accepted Media subtree tree OID was:

`35b2e7a588295f1bf446ec2d1f5ab10cc240d293`.

The replay on canonical base `0067965d...` produced the **same exact Media subtree tree OID**, so no source or behavior bytes changed between the tested tree and the replayed tree. Acceptance is therefore rebound by exact tree identity rather than rerunning an identical suite for a different parent commit.

A real default Creative Index query on the accepted tree produced 313 nodes and 372 relations and exposed `source:creative-library`, not `source:workstation`.

## Authority boundary

Creative Library is a disposable projection, not a source truth store. It does not own:

- domain work identity;
- exact source-byte authority;
- preservation format identity;
- physical standing;
- publication approval;
- artistic quality;
- Human value.

Media is the host/consumer owner for the projection. Source truth remains owner-native.

## workstation-lab status

This acceptance does not retire workstation-lab.

At the acceptance boundary:

- no live systemd unit directly executed/referenced `/root/workstation-lab`;
- no running process directly referenced it;
- a verified full historical bundle exists;
- Workstation recovery still contains a protected-source/backup-data relationship;
- Media/historical production material and migration evidence still contain provenance references that must be classified before physical retirement.

Therefore workstation-lab remains **DRAINING**.
