# Workstation recovery monorepo cutover acceptance — 2026-09-21

Standing: **ACCEPTED_LIVE_RECOVERY_CUTOVER**

Scope: move the immutable Workstation recovery generation from the standalone Workstation Git repository to the canonical modular monorepo while preserving Workstation ownership of recovery implementation.

## Authority decomposition

The accepted boundary is:

- Git source identity: `/root/projects/ordivon`;
- Workstation owner source: `platform/workstation`;
- recovery implementation: `platform/workstation/recovery`;
- control repository backup target: `/root/projects/ordivon`;
- generation owner-relative path: `platform/workstation`.

The owner subtree is not treated as a second Git repository.

## Source change

Canonical source commit:

`aefdb6871b27d2141ae4d94bc314857caa850cbd`

Accepted Workstation subtree tree:

`e0cf0de55118af2907e8e0f6973e3d81b926453c`

The recovery generation contract evolved from v0 to v1.

Generation v1:

- derives the enclosing Git repository from the Workstation owner path;
- requires the entire source repository to be clean;
- binds the full Git revision and tree;
- records `ownerRelativePath`;
- clones the complete monorepo into the immutable generation;
- executes recovery implementation from the recorded Workstation owner-relative path;
- backs up the canonical monorepo control repository.

Current recovery configuration:

- role: `ordivon-monorepo-workstation-recovery`;
- control repository: `/root/projects/ordivon`;
- control snapshot tag: `ordivon-monorepo-control`.

Historical `workstation-v2-control` snapshots are not rewritten.

## TDD and owner verification

The old source model was first proven RED because it required the owner directory itself to contain `.git`.

The new model passed:

- recovery generation v1 tests: 5/5;
- all current recovery tests: 30/30;
- Workstation Python suite: 168 PASS;
- Cloudflare provider TypeScript tests: PASS;
- Cloudflare provider Python tests: PASS;
- policy/config checks: PASS;
- systemd operations checks: PASS;
- Wrangler dry-run build: PASS;
- old standalone Workstation locator in current recovery config/README/generator: 0;
- `git diff --check`: PASS.

The replayed Workstation subtree exactly matched the tested subtree before canonical CAS.

## Detached immutable-generation proof

Before production activation, a detached candidate generation was provisioned under a separate candidate install root.

Candidate generation facts:

- schema version: 1;
- kind: `ordivon.workstation.recovery-generation-verification.v1`;
- ownerRelativePath: `platform/workstation`;
- controlRepository: `/root/projects/ordivon`;
- source repository: the candidate monorepo workspace;
- current: false;
- old standalone Workstation locator in launcher/manifest/recovery source: 0.

No production `current` symlink changed during this proof.

## Production provision

After canonical CAS, the production candidate generation was provisioned without activation:

`/opt/ordivon-workstation-recovery/aefdb6871b27d2141ae4d94bc314857caa850cbd`

Verification observed:

- sourceRepository: `/root/projects/ordivon`;
- sourceRevision: `aefdb6871b27d2141ae4d94bc314857caa850cbd`;
- sourceTree: `4c6311898970649c2fe1e782d9befde2a7695701`;
- ownerRelativePath: `platform/workstation`;
- controlRepository: `/root/projects/ordivon`;
- current: false;
- candidate generation: PASS.

The existing `current` generation remained unchanged during this stage.

## Atomic activation

The production generation was then activated by the owner-native generation tool.

Post-activation verification:

- current generation: `aefdb6871b27d2141ae4d94bc314857caa850cbd`;
- schemaVersion: 1;
- kind: `ordivon.workstation.recovery-generation-verification.v1`;
- current: true;
- sourceRepository: `/root/projects/ordivon`;
- ownerRelativePath: `platform/workstation`;
- controlRepository: `/root/projects/ordivon`;
- control snapshot tag: `ordivon-monorepo-control`;
- old standalone Workstation locator in current launcher/manifest/recovery implementation: 0.

The scheduler still executes only:

`/opt/ordivon-workstation-recovery/current/bin/workstation-backup`

The timer remains enabled and active/waiting.

No manual backup was invoked during cutover.

## Preserved independent failure

The Workstation backup oneshot already had a failed state from the earlier semantic-recovery maintenance/prune timeout.

That failure was preserved rather than cleared or attributed to this migration.

The cutover does not claim that the semantic-prune issue is resolved.

## Local cutover receipt

Host-side before/candidate/after evidence is stored under:

`/var/lib/ordivon/retired/source-carrier-cutovers/2026-09-21/workstation-recovery-monorepo`

The receipt records:

- previous current generation;
- detached production candidate;
- activation and verify-current results;
- scheduler before/after state;
- checksums;
- no manual backup invocation.

## Consequence

The active recovery authority no longer requires `/root/projects/ordivon-workstation-v2`.

This removes the major recovery blocker to standalone Workstation retirement. Physical retirement remains separately gated on:

- remaining Git worktrees;
- exact all-refs/recovery proof;
- ignored/non-Git state classification;
- current metadata and consumer references;
- post-retirement owner verification.

This acceptance does not itself delete the standalone Workstation repository.
