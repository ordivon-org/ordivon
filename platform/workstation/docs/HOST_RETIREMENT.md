# Legacy Host v1 retirement

Date: 2026-09-12

## Purpose

Host v1 is a legacy continuity authority that predates the Standards-first composition. Its responsibilities now have mature owners:

- durable process state -> Temporal;
- physical execution -> Ordivon Runtime;
- integration edge -> n8n;
- async contracts -> CloudEvents + AsyncAPI;
- operational projection -> Temporal Visibility + Operations observability;
- collaboration/news surfaces -> their owning domain/integration systems.

Host Event History is **not** Temporal Event History and will never be fabricated as such.

## Retirement admission rule

A Host `ready` projection means a resumable historical continuation, not proof that a process is currently executing. Retirement may archive such projections rather than bootstrap all of them into Temporal when all of the following are true:

1. Host has zero active leases;
2. no established client connection exists on `127.0.0.1:8898`;
3. no `ready` projection has been updated within the defined activity window;
4. no active systemd service depends on Host;
5. the complete Host durable state is preserved with an integrity-verifiable retirement receipt.

The 2026-09-12 inventory found 2,025 task projections: 1,749 completed, 43 cancelled and 233 ready. All 233 ready projections were older than six hours; 122 were already 7–14 days old. There were zero leases and zero established consumers.

## Archive model

Retirement intentionally avoids duplicating the ~2.2 GiB Host tree. The original state root remains the historical archive after the service is disabled. A small independent retirement archive contains:

- a SQLite online-backup copy of `host.sqlite3` with `integrity_check=ok`;
- a gzip manifest containing SHA-256 for every durable regular file in the Host tree;
- a separate archive of all `ready` task projections;
- a JSON retirement receipt with state counts, latest event, source/database digests, archive digests and disposition.

Transient SQLite `-wal`/`-shm` files and the maintenance lock are excluded from the durable content root.

## Disposition

No bulk Temporal bootstrap is authorized. A future owner may explicitly bootstrap one archived continuation into a new Temporal Workflow using the immutable Host snapshot as input evidence, but that creates a **new Workflow history** and must not pretend continuity of Temporal Event History.

## Production retirement evidence

The retirement was executed after the admission rule passed. Final receipt:

- standing: `RETIRED_READ_ONLY_ARCHIVE`;
- Host service: inactive and disabled;
- legacy listener `127.0.0.1:8898`: absent;
- established consumers: `0`;
- active leases: `0`;
- Temporal bootstrap count: `0`;
- source DB SHA-256: `sha256:48104ae46bc92c6624ad2aa89a00ae4870a274a0a0fb020bf2edf32b7529723e`;
- independent SQLite backup SHA-256: `sha256:70cc55a34f6fdf97609f0593e13227740fb3e887052a629e3b7d8712a9f54e8b`;
- durable tree: `98,224` files / `2,059,439,292` bytes;
- durable tree content root: `sha256:8d15cf760e8267316f6040fcd89315d882651223c49103c97ad9e9cb73757e55`;
- ready-projection archive rows: `233`;
- archive root: `/var/lib/ordivon/retired/host-v1`.

The original `/var/lib/ordivon/host` tree is retained as historical state rather than duplicated. The independent DB backup, per-file digest manifest, ready-projection archive, and retirement receipt are mode `0400`.

## Runtime and public-surface retirement

After the durable-state archive was independently verified, the executable Host installation was retired as a separate step.

Before deletion, `/usr/local/libexec/ordivon/host` was reduced to a provenance manifest rather than copied:

- files: `11,409`;
- bytes: `590,019,750`;
- content root: `sha256:60383abcc8edeaf908a30f7d4ac2e4df47195c5f455f1d15c7825be23e26fdc3`;
- manifest SHA-256: `sha256:06a4a3fb5829637e3464591b64ea9802ed50b4dca8421552ef6783c3cccbbadb`;
- provenance receipt: `/var/lib/ordivon/retired/host-v1/host-v1-install-provenance.json`.

The following live-runtime material was then removed:

- `ordivon-host-mcp.service`;
- Host env/token material under `/etc/ordivon`;
- `/usr/local/bin/ordivon-host-mcp` and `/usr/local/bin/ordivon-host`;
- `/usr/local/libexec/ordivon/host`.

Post-removal verification reports `LoadState=not-found` and no listener on `8898`. The historical `/var/lib/ordivon/host` tree and retirement archive remain intact.

The Cloudflare DNS CNAME for `host-mcp.ordivon.com` was independently inventoried as a Host-specific record and deleted through the canonical Cloudflare account API-token authority. A post-delete authoritative DNS inventory returned an empty set. The old Cloudflare Access application remains as an inert provider-side policy object with no Host DNS entry; it is not considered a live Ordivon surface and should be removed separately when that provider mutation path is available.
