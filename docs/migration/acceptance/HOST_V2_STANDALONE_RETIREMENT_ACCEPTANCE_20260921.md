# Host v2 standalone retirement acceptance — 2026-09-21

Standing: **RETIRED_ARCHIVED**

Scope: retire the legacy standalone Host v2 Git source carrier after source/history migration, unfinished-work preservation and migration, complete all-refs recovery proof, live release independence proof, and post-delete Host history readback.

## Canonical owner

- canonical repository: `/root/projects/ordivon`
- owner path: `services/host`
- standalone source before deletion: `/root/projects/ordivon-host-v2`
- standalone source HEAD: `a95a8e112edfbe85582ff8e6fa25bb268038ea48`
- standalone source tree: `9c2ea9690d790b9dbe83b57eae34f0a53062f79f`

The original rewritten Host import was already identity-bridged to the exact standalone source identity. The canonical Host subsequently evolved beyond the standalone main, so final subtree equality is not a retirement requirement.

## Valuable dirty worktree preservation

The remaining dirty Runtime workspace `ws-host-friction-r1-20260920` contained seven real changes rather than cache:

- Host Friction Observatory documentation;
- read-only production friction measurement code;
- two measurement/connector-friction planning records;
- Host LEGO freeze-rule updates;
- standard MCP `serverInfo.version` binding from the PEP 621 package version;
- corresponding MCP surface tests.

Before any closure, a self-contained WIP capsule was created under:

`/root/ordivon-migration-backups/2026-09-21-host-retirement/friction-wip`

It contains the detached Git base bundle, tracked binary patch, untracked tar, exact status, and changed-file digests. Fresh-clone restoration reproduced the exact Git status and all seven changed-file digests.

The seven changes were then deterministically transplanted into canonical `services/host`. Byte equality against the dirty worktree was proven for every changed file.

Canonical Friction migration commit:

`d98b2b4bb5b9239f1a51d7bd07fc5dfa55452608`

## Friction migration validation

The ordinary Host owner gate passed:

- Ruff: PASS;
- default pytest: 18 passed / 18 skipped;
- `git diff --check`: PASS.

Because the skipped tests are PostgreSQL vertical tests, a disposable PostgreSQL 18 UTF-8 cluster was created outside production. On an empty database:

- public tables before migration: 0;
- Alembic upgraded through 0001→0002→0003→0004→0005;
- Alembic current: `0005 (head)`;
- full pytest: **36 passed, 0 skipped**;
- Ruff: PASS;
- direct MCP proof: `serverInfo.name=ordivon-host-v2`, `serverInfo.version=0.1.0`.

The disposable cluster was stopped and removed. Production Host PostgreSQL was not mutated by this validation.

After canonical migration and restore-proven WIP capture, the dirty Runtime workspace was force-closed using its unchanged exact `sourceStateDigest`. The other linked Host standards worktree was clean and closed normally through Runtime.

## Complete Git preservation

After worktree drainage the standalone source had one physical worktree and 29 ordinary refs. The closed standards revision `cb75a9264571c34a05de10b4cbce940c44bcc479` was retained under a Runtime closed ref.

All refs bundle:

`/root/ordivon-migration-backups/2026-09-21-host-retirement/host-all-refs.bundle`

SHA-256:

`7aac26c40bd505b6deacd7e9788793891f8ae529d6a9e5bc6d374bce8fd60bee`

Fresh mirror restore before deletion:

- source refs: 29;
- restored refs: 29;
- missing or mismatch: 0.

Fresh mirror restore after physical deletion repeated the same result: 29/29 exact.

## Non-Git state

Seven ignored entries were present:

- `.venv/`;
- pytest cache;
- Ruff cache;
- Python bytecode caches.

Non-rebuildable entries: **0**.

The virtual environment is rebuildable from canonical `services/host/pyproject.toml`, `uv.lock`, and Python 3.14.7. Canonical fresh-environment validation was performed as part of the owner/full PostgreSQL gates. Host durable continuity state is PostgreSQL-owned, not stored in the source checkout.

## Live release independence

Before deletion, the live service was:

- active/running;
- WorkingDirectory: `/opt/ordivon/host-v2/current`;
- current release: `/opt/ordivon/host-v2/releases/a95a8e112edfbe85582ff8e6fa25bb268038ea48`;
- process cwd: the immutable release directory;
- process executable: release-managed Python 3.14.7;
- Host DSN: PostgreSQL on the dedicated Host database.

The current immutable release contained zero references to `/root/projects/ordivon-host-v2`. Systemd, cron, process argv, cwd, and open-fd scans also found zero active old-source references.

A pre-delete live Host `host.status(detail=history)` readback reported schema 5 and a healthy full-history Doctor.

## Archived-source reference fence

Canonical policy:

`docs/migration/retirement/host-v2-standalone-policy.json`

Before physical deletion, all tracked occurrences of the old source locator were classified as historical migration receipts/records, M0 planning snapshots, or frozen topology artifacts. Forbidden current references: **0**.

The root `repo:retirement:verify` gate now checks this policy on every run.

## Physical retirement

Pre-delete receipt:

`/root/ordivon-migration-backups/2026-09-21-host-retirement/host-physical-retirement-predelete.json`

The final gate required:

- canonical repository clean;
- Host Friction migration reachable;
- retirement policy PASS;
- standalone source clean;
- standalone worktrees = one root only;
- all-refs bundle/restore PASS;
- WIP capsule restore PASS;
- non-rebuildable non-Git state = 0;
- current live release independent of standalone source;
- systemd/process/cwd/open-fd references to old source = 0.

Only after all gates passed was `/root/projects/ordivon-host-v2` physically removed.

No compatibility alias was created.

## Post-delete proof

With the source path absent:

- all 29 refs restored exactly from the bundle;
- canonical Host owner verification passed;
- live Host service remained active/running from the immutable release;
- archived-source policy remained PASS.

A second live MCP `host.status(detail=history)` readback after deletion reported:

- journal backend: PostgreSQL;
- schema: 5;
- events: 14,986;
- Tasks: 2,124;
- Board messages: 17,136;
- Doctor healthy: true.

Doctor checks all reported `ok`:

- `postgres.schema`;
- `task.current_checkpoint`;
- `task.current_event`;
- `command_receipts.complete`;
- `board.reply_integrity`;
- `task.history_contiguous`;
- `checkpoint.history_digest`.

Post-delete proof:

`/root/ordivon-migration-backups/2026-09-21-host-retirement/host-post-retirement-proof.json`

## Disposition

- active Host source owner: canonical monorepo `services/host`;
- live Host effect carrier: immutable `/opt/ordivon/host-v2/current` release;
- durable Host continuity authority: PostgreSQL;
- standalone Host source carrier: physically absent;
- Git refs/history: archived and restore-proven;
- unfinished Friction work: archived, migrated, and fully validated;
- standalone ignored state: rebuildable environment/cache only;
- historical provenance: preserved without rewriting.

This acceptance retires only the standalone source carrier. It does not collapse Host authority into the monorepo root or make Git/release state authoritative for Host continuity semantics.
