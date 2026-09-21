# Workstation Edge monorepo live-carrier cutover acceptance — 2026-09-21

Standing: **LIVE_CARRIER_CUTOVER_ACCEPTED**

Scope: move the live Cloudflare Edge provider carrier from the standalone Workstation source path to the canonical modular-monorepo Workstation owner without changing provider semantics or invoking a destructive garbage-collection effect.

## Canonical source

- canonical monorepo: `/root/projects/ordivon`;
- accepted source commit: `dea7e9342f6a007a3ea934dda0af7c4d7866b320`;
- owner path: `platform/workstation/providers/cloudflare`;
- accepted Workstation subtree tree: `0a6ddf6dd407101bdb6f9f10b421d8d0a5665105`.

The source commit is reachable from the current canonical main, and no later Workstation change occurred before this acceptance was prepared.

## Source refactor

The forward provider locator was changed from:

`/root/projects/ordivon-workstation-v2/providers/cloudflare`

to:

`/root/projects/ordivon/platform/workstation/providers/cloudflare`

for:

- `ordivon_edge_gc.py` default provider root;
- `ordivon_edge_release.py` default provider root;
- `ordivon-edge-gc.service` WorkingDirectory;
- current operator/provider documentation.

The explicit `ORDIVON_CLOUDFLARE_PROVIDER_ROOT` override remains supported. The historical `ORDIVON_WORLD_REPO` fallback was not removed in this cut because compatibility retirement is a separate concern.

## Source-native gates

The change was developed with a RED/GREEN contract:

- GC default provider root test: RED before implementation, GREEN after;
- Release default provider root test: RED before implementation, GREEN after;
- systemd WorkingDirectory test: RED before implementation, GREEN after.

Accepted source gates:

- targeted Python tests: 25 PASS;
- Cloudflare provider TypeScript tests: 29 PASS;
- provider Python suites: 33 PASS;
- provider policy/config checks: PASS;
- systemd static operations check: PASS;
- Wrangler build: PASS with `--dry-run`;
- Workstation owner test suite: 151 PASS;
- Workstation root verification: PASS;
- old forward provider locator in current provider source/docs/unit: 0;
- `git diff --check`: PASS.

## Live-carrier preflight

Before the live change, the installer-visible carrier census showed exactly three byte differences from canonical source:

- `/usr/local/sbin/ordivon-edge-release`;
- `/usr/local/sbin/ordivon-edge-gc`;
- `/etc/systemd/system/ordivon-edge-gc.service`.

The installed Edge client, provider policy, lifecycle controller and GC timer were already byte-identical to canonical source.

At preflight:

- `ordivon-edge-gc.service`: inactive/dead, previous result success;
- `ordivon-edge-gc.timer`: active/waiting/enabled.

## Live cutover

Only the three differing carriers were replaced. A rollback copy was written before mutation.

The GC oneshot was not started during the carrier replacement. The timer was not restarted.

After `systemctl daemon-reload`:

- installed Release controller digest equals canonical source;
- installed GC controller digest equals canonical source;
- installed systemd service digest equals canonical source;
- service WorkingDirectory is the monorepo provider path;
- service remains inactive/dead;
- timer remains active/waiting/enabled;
- installed old standalone provider locator count: 0.

Local before/after/rollback receipt:

`/var/lib/ordivon/retired/source-carrier-cutovers/2026-09-21/edge-provider-monorepo`

## Non-destructive end-to-end validation

Both installed extensionless scripts were loaded without invoking their CLI and resolved:

`ROOT=/root/projects/ordivon/platform/workstation/providers/cloudflare`.

Then the installed GC controller was executed with:

`--dry-run --limit 100`.

Result:

- exit code: 0;
- status: completed;
- dry_run: true;
- scanned cleanup tasks: 0;
- failed tasks: 0;
- remote deletion attempted: false;
- local GC receipt: `/root/backups/ordivon-world/cloudflare-gc/gc-20260921T062330Z.json`.

## Post-cutover source-path census

After cutover, no live systemd unit references `/root/projects/ordivon-workstation-v2` as an Edge provider source carrier.

At that census, the only remaining live systemd source-path dependency among the migrated standalone repositories was the Artifact Temporal worker under `/root/projects/ordivon-artifact-v2`.

## Boundary

This acceptance changes the live provider source carrier only. It does not:

- retire the standalone Workstation repository;
- rotate Cloudflare credentials;
- deploy a new Cloudflare Worker version;
- modify R2 lifecycle policy;
- perform a destructive garbage-collection pass;
- change consumer/domain authority.
