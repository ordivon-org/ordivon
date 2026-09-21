# Artifact v2 standalone source-carrier retirement acceptance — 2026-09-21

Standing: **RETIRED_ARCHIVED**

Scope: retire the legacy standalone Artifact source carrier at /root/projects/ordivon-artifact-v2 after exact history import, canonical monorepo forward evolution, current-consumer cutover, recovery proof for the dirty PowerPoint dogfood worktree, Runtime/worktree drainage, and post-delete owner-native verification.

This acceptance retires only the standalone source carrier. It does not retire the Artifact capability, weaken any Artifact verification profile, publish an external artifact, perform a provider upload, or rewrite historical evidence identities.

## Source and import identity

Legacy standalone identity immediately before retirement:

- path: /root/projects/ordivon-artifact-v2
- HEAD: 3762b3f033f1173aa93609c79284980610301d37
- tree: 5ebd3f5090686b37379486caa31a97d91be973a7
- tracked status: clean
- physical Git worktrees at final gate: one, the standalone root itself

The M2 import receipt binds the legacy source revision to:

- rewritten revision: 1bb82fc159fa95d51c62f254ae994538a8e9d979
- import merge: 3dc5afa7b3f24b94dfd46cd64dd4d66bc7377ea1
- target: capabilities/artifact

The subtree at the rewritten revision is exactly:

5ebd3f5090686b37379486caa31a97d91be973a7

Therefore the imported source tree is byte-identical to the standalone source tree.

At retirement, canonical capabilities/artifact had already evolved forward to tree:

ddd6777141024063ab43117afbd56884557e04d4

That difference is intentional forward evolution after exact import, not migration loss.

The physical retirement transaction observed monorepo main:

4545ccc46c364597f922fc5b9b4d71d9f7907e04

## Current consumer cutover

One current executable consumer still defaulted to the old Artifact root: Media Studio Creative Index query construction.

The default Artifact root was changed from the standalone carrier to:

/root/projects/ordivon/capabilities/artifact

The current Media command documentation was changed with it, and the regression now requires source:artifact to identify the canonical monorepo owner.

Consumer verification:

- changed-file Ruff: PASS
- targeted Creative Index regression: PASS
- Media owner bootstrap: PASS
- Media full Python tests: 167 PASS
- TypeScript typecheck: PASS
- Vite production build: PASS

Consumer cutover commit:

713b541e1576675bb13eb3ae7dcc01b2b12e2bc5

## Current metadata and Skill cutover

A separate semantic-reference census distinguished historical evidence from current operational metadata.

Current owner references were moved to the canonical path in:

- eight artifact-work Skill family references
- Artifact capability README
- Artifact capability package metadata
- Artifact provider metadata
- cross-domain security knowledge graph
- cross-domain security lesson
- private-registry-to-Agent-Skills migration record

Current-owner metadata commit:

337d89930020cf52613b83efc6b0d71b56f42f87

Validation after the cutover:

- Next full pytest: PASS
- Authority Catalog: 168 records / 173 observations
- Authority standing: PASS_LIGHTWEIGHT_PROGRESSIVE_DISCOVERY
- governance persistence: PASS
- reasoning waist: PASS_LOCAL_COMPOSED_SMOKE
- Standard-Native enterprise R2: PASS_CROSS_DOMAIN_DOGFOOD
- all nine Skill source-evidence targets resolve under the canonical Artifact owner

## Historical references deliberately preserved

A final tracked census retained 22 files with the literal old root.

They are bounded to:

- exact Game consumer-acceptance receipts whose artifactSource.repository records the original source identity
- SOURCE_AUTHORITY_ACCEPTANCE_20260912.md
- the negative regression assertion that the live Temporal unit must not contain the old root
- generated/frozen system-constellation source snapshots
- migration receipts and acceptance records
- Game historical evidence
- M0 migration architecture/planning snapshots
- local capability evidence
- the Artifact v2 decomposition record with an exact historical revision

No current Skill, capability/provider metadata, Media executable default, current cross-domain source authority, systemd unit, /etc config or live process points to the retired root.

Physical retirement does not rewrite provenance.

## Runtime and physical worktree drainage

Runtime initially projected two clean Artifact workspaces:

- ws-artifact-mailbox-retire-integration-r1-20260920
- ws-artifact-r2-mailbox-retire-r1-20260920

Both were closed using exact sourceStateDigest compare-and-close and returned closureDisposition=removed.

Two additional physical worktrees remained:

- ws-repo-modernize-artifact-r1-20260920 — clean
- ws-ordivon-ppt-dogfood-r2-20260916 — dirty

The clean modernization worktree was removed after process/reference checks.

The dirty PowerPoint dogfood worktree was not discarded as cache. It contained a build script plus 44 generated/evidence files including editable/final PPTX, companion PDF, eight slide renders, SVG outputs, PowerPoint target evidence, Windows readback receipts and validation reports.

A recovery capsule preserves:

- exact base HEAD e4a534cea195a6894596d1b8116d8de4ee05c809
- Git porcelain status
- tracked binary patch
- untracked path inventory
- ignored path inventory
- untracked tar
- metadata

The first capsule manifest accidentally included itself in its checksum list. The self-referential manifest was preserved as diagnostic evidence, then replaced by a manifest that explicitly excludes manifest files.

Correct capsule manifest SHA-256:

8ab1ea9b42eb3482e159ffc7610b0839971244503b408f68dca27fb838ffddbc

A fresh clone from the Artifact bundle replayed the preserved worktree state. Exact Git status matched and all 45 represented files were recovered byte-for-byte.

Restore proof SHA-256:

f1bbb1e38368db5a6b46716991828c78dfe484cf35c10e55c9cd5e36c3f9d6cd

Only after the exact recovery proof and zero process references was the dirty worktree drained.

Final Runtime workspace count for the standalone Artifact source was zero.

## Complete Git preservation

Complete all-refs bundle:

/root/ordivon-migration-backups/2026-09-21-artifact-retirement/artifact-all-refs.bundle

SHA-256:

c63cf8387f4dda4bb1e4b7dfd6f106811d95ba33a0867bef0e9b957ddca46ed0

Ordinary refs manifest:

/root/ordivon-migration-backups/2026-09-21-artifact-retirement/artifact-all-git-refs.tsv

SHA-256:

1e55289fbd5014c8e7e4fb97c01cec5db2afed84eb3313884aa01316cf8f7d4a

The manifest contains 43 ordinary Git refs.

Before deletion:

- missing from bundle: 0
- digest mismatch: 0

After physical deletion, the bundle was cloned into a new mirror repository and every one of the 43 refs was resolved again:

- missing: 0
- mismatch: 0

## Non-Git standalone state

The standalone root contained 4,254 ignored entries.

A file-level classification found:

- non-cache ignored files: 0

All ignored bytes were rebuildable environment/cache material such as virtual environments, Python bytecode, pytest cache and Ruff cache.

Unlike Game retirement, no unique standalone-root runtime database or scientific payload required a separate non-Git archive.

The unique PowerPoint dogfood outputs lived in the dirty external worktree and are covered by the separately restore-proven capsule described above.

## Canonical Artifact owner gate

Before physical retirement, canonical capabilities/artifact was tested independently of the standalone source carrier.

Hermetic test collection:

381 tests

Gate:

pytest -m "not integration"

Standing:

PASS, 100 percent completion, zero failures; environment-specific integration remains a distinct gate.

The Temporal deployment source-fence regression also passed and requires:

- WorkingDirectory=/root/projects/ordivon/capabilities/artifact
- worker script under the same canonical owner
- no /root/projects/ordivon-artifact-v2 in the live unit

The full-repository Ruff findings observed earlier in this migration were pre-existing on the unmodified base and were not introduced by source-carrier retirement. Changed executable consumer files were lint-clean. Retirement therefore uses the existing M2 hermetic owner boundary rather than conflating unrelated static debt with source-location authority.

## Live Temporal worker

At final retirement, ordivon-artifact-temporal-worker.service was:

- active
- enabled
- sourced from the canonical monorepo Artifact owner
- free of old-root references

The standalone source carrier was therefore not the live worker source at deletion time.

After physical deletion:

- worker remained active
- PID: 1599417
- NRestarts: 0
- process cwd: /root/projects/ordivon/capabilities/artifact
- process command points to the canonical artifact_temporal_worker.py

No worker restart was required to make the old path disappear.

## Physical retirement receipts

Pre-delete receipt:

/root/ordivon-migration-backups/2026-09-21-artifact-retirement/artifact-physical-retirement.json

SHA-256:

85d51f2bb3461ff934ba6647c92199719ef4794aba10baf178f607965aa15190

Post-delete proof:

/root/ordivon-migration-backups/2026-09-21-artifact-retirement/artifact-post-retirement-proof.json

SHA-256:

09edbb0b56a1d1af873939cd97e8afc4d24d258d5c67b9461acd3a43d7717542

## Post-delete functional proof

With /root/projects/ordivon-artifact-v2 physically absent:

- canonical Artifact hermetic suite: PASS
- 381-test collection boundary retained
- Temporal source-fence regression: PASS
- Media Creative Index Artifact consumer regression: PASS
- live Artifact worker: active
- live worker NRestarts: 0
- current operational old-root references: 0
- Git restore proof: 43 refs, missing=0, mismatch=0
- PPT dogfood worktree recovery: 45 files exact

## Disposition

- active Artifact source owner: /root/projects/ordivon/capabilities/artifact
- legacy standalone path: physically absent
- compatibility alias at old path: none
- standalone Git history: archived and restore-proven
- dirty PPT dogfood state: archived and restore-proven
- root ignored/cache state: rebuildable only
- live Temporal worker: canonical and healthy
- external publication/provider mutation from this retirement: none

If historical Artifact source or dogfood state must be recovered, materialize it into a bounded recovery path from the recorded bundle/capsule. Do not recreate /root/projects/ordivon-artifact-v2 as a compatibility alias.
