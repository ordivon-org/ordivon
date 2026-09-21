# Network v2 standalone retirement acceptance — 2026-09-21

Standing: **RETIRED_ARCHIVED**

Scope: retire the legacy Network v2 standalone Git source carrier after identity bridging, Finance recovery reconciliation, current-metadata cutover, complete final all-refs recovery proof, live source-independence proof, and post-delete readback.

## Canonical owner

- canonical repository: `/root/projects/ordivon`
- owner path: `platform/network`
- standalone source before deletion: `/root/projects/ordivon-network-v2`
- standalone source HEAD: `9aec70bbfa3c8847dbd52c03a939c61f45e2f338`
- standalone source tree: `ba601ac2cce2e7ac88a960cfc4d4c3edd534a533`

The original Network import had already been identity-bridged to the exact accepted source revision. Canonical Network subsequently evolved with DNS resilience, monorepo navigation, and Finance recovery work, so final subtree equality is not a retirement requirement.

## Finance recovery WIP

A previously dirty Runtime worktree, `ws-network-finance-recovery-sndk-20260920`, had six changed paths:

- `Taskfile.yml`;
- `consumers/finance/README.md`;
- `consumers/finance/acceptance/production-smoke.sh`;
- `consumers/finance/config/egress.json`;
- `consumers/finance/config/binance-wallet-rest-authority.json`;
- `consumers/finance/ready.sh`.

Before force-close, that worktree was captured and exact-replay proven under:

`/root/ordivon-migration-backups/2026-09-21-network-retirement/worktree-ws-network-finance-recovery-sndk-20260920`

Its restore proof reproduced the exact dirty status and all six compared file digests.

The later canonical commit `f605785b44028ee2fcdbad3189b09709fed64baa` was audited against the restored WIP. It is not a byte-for-byte transplant: it is a **superseding reconciliation**. It preserves the Binance Wallet/API authority and adds stronger dual-provider-DNS response racing, explicit seven-authority validation, readiness checks, DNS-race acceptance, and control-plane-state fencing.

The reconciliation parent and DNS-hardening commit were already ancestors of canonical main, and the reconciliation patch applied cleanly.

The reconciliation was replayed onto the then-current monorepo and became canonical as:

`dac057c6668c83e085bb3ae3b910866fd349b4eb`

Non-destructive validation passed:

- `network:verify`;
- sing-box direct configuration;
- Surfshark provider configuration;
- seven Finance inbounds;
- exact Wallet/API route;
- dual provider-DNS race structure;
- systemd unit verification;
- blackbox exporter config;
- Prometheus config;
- all authority metadata;
- shell syntax for readiness/acceptance scripts.

The destructive Finance fault-injection acceptance was intentionally **not** run as part of source retirement.

## Current metadata cutover

Before physical retirement, current Next provider/package metadata was rebound from the standalone source path to:

- repository: `/root/projects/ordivon`;
- owner path: `platform/network`;
- observed monorepo revision: `dac057c6668c83e085bb3ae3b910866fd349b4eb`.

The metadata/policy cutover entered canonical at:

`05ddb7945d44e9f0868e2281debadaa1a67930d8`

Both `network:verify` and `next:verify` passed.

## Strict old-source reference policy

Policy:

`docs/migration/retirement/network-v2-standalone-policy.json`

The policy permits only explicit historical reference classes:

- migration acceptances/receipts;
- dated Network migration records;
- frozen M0 plan/baseline;
- frozen system-topology carriers.

Before deletion the policy reported nine tracked historical references, nine allowed, zero forbidden. Current provider/package metadata no longer named the standalone repository.

## Final Git preservation

An earlier bundle had been created while Runtime worktrees still existed, so it included worktree pseudo-heads and missed one later closed ordinary ref. It was not used as the final retirement archive.

After all linked worktrees were drained, the source had one physical root worktree and 36 ordinary refs.

Final bundle:

`/root/ordivon-migration-backups/2026-09-21-network-retirement/network-final-all-ordinary-refs.bundle`

SHA-256:

`7a2dafcf693299348bfff700d206ca560941277fe22a9eb0e97aa1c4d711305e`

Final verification:

- source ordinary refs: 36;
- bundle ordinary refs: 36;
- missing/mismatch: 0;
- fresh mirror restore before deletion: 36/36 exact;
- fresh mirror restore after deletion: 36/36 exact.

The older dirty Finance WIP capsule is retained independently and is not replaced by this final bundle.

## Non-Git state

At final source freeze:

- untracked entries: 0;
- ignored entries: 0;
- non-rebuildable non-Git state: 0.

Network durable/live state is held by installed system configuration, OS networking facilities, provider material, and service-specific state rather than the Git checkout.

## Live source-independence proof

Before deletion, the active Network realization used installed paths only.

Eleven Network services remained active:

- blackbox exporter;
- Browserless DNS;
- Browserless forwarding;
- Browserless netns;
- Browserless WireGuard;
- DNS proxy;
- Finance egress;
- Prometheus;
- Public-Web bridge;
- Public-Web egress;
- sing-box direct plane.

Their service definitions use `/etc/network-v2`, `/usr/bin`, `/usr/local/libexec`, namespaces, and service-owned state. No live systemd, cron, process argv, cwd, or open-fd reference pointed into `/root/projects/ordivon-network-v2`.

Read-only pre-delete checks passed:

- installed direct sing-box config;
- installed Finance sing-box composition;
- Prometheus health;
- blackbox health;
- DNS consequence.

## Explicit deployed-vs-canonical drift

Source retirement uncovered a pre-existing partial deployment, which was **not** silently repaired inside the retirement transaction.

Canonical source after `dac057c6` defines seven Finance authorities, including Binance Wallet/API on loopback port 19290.

The installed live egress still defines six authorities. It already contains dual provider DNS but does not contain the Wallet/API authority.

Read-only consequence probes proved all six deployed authorities:

- OKX REST — HTTP 200;
- Binance Spot public REST — HTTP 200;
- Binance USD-M REST — HTTP 200;
- Binance Spot public WebSocket endpoint — expected HTTP 404 without WebSocket upgrade;
- OKX public WebSocket endpoint — expected HTTP 400 without upgrade;
- Binance USD-M WebSocket endpoint — expected HTTP 404 without upgrade.

The installed readiness helper separately reported READY for:

- OKX;
- Binance Spot;
- Binance USD-M.

Its `all` mode returns exit 4 because the helper already expects the not-yet-deployed Wallet/API authority.

This state is recorded under:

`/root/ordivon-migration-backups/2026-09-21-network-retirement/network-live-deployment-standing-predelete.json`

Disposition: preserve the current live carrier during source retirement. Converging the canonical seven-authority source to production is a separate effect-bearing Network change and was not performed here.

## Physical retirement

Pre-delete receipt:

`/root/ordivon-migration-backups/2026-09-21-network-retirement/network-physical-retirement-predelete.json`

The final gate required:

- canonical revision `05ddb7945d44e9f0868e2281debadaa1a67930d8`;
- canonical repository clean;
- Finance reconciliation reachable;
- strict retirement policy PASS;
- standalone source clean;
- one root worktree only;
- final 36-ref bundle and restore proof PASS;
- dirty Finance WIP restore proof PASS;
- non-Git state count 0;
- canonical Network owner verification PASS;
- live old-source references 0;
- all eleven live Network services active;
- installed config validation PASS;
- six-authority live consequence proof PASS;
- production Network convergence/restart count 0.

Only after these gates passed was `/root/projects/ordivon-network-v2` physically removed.

## Post-delete proof

With the source path absent:

- final bundle restored 36/36 refs exactly;
- canonical `network:verify` passed;
- all eleven live Network services remained active;
- installed direct and Finance sing-box configs remained valid;
- Prometheus health passed;
- blackbox health passed;
- OKX/Binance Spot/Binance USD-M readiness remained PASS;
- retirement policy remained PASS.

Post-delete proof:

`/root/ordivon-migration-backups/2026-09-21-network-retirement/network-post-retirement-proof.json`

No production network restart, provider rotation, route mutation, namespace recreation, or Finance cutover was performed by the retirement transaction.

## Disposition

- active source owner: canonical monorepo `platform/network`;
- standalone Network source carrier: physically absent;
- Git refs/history: archived and restore-proven;
- dirty Finance recovery WIP: archive-proven and superseded by validated canonical reconciliation;
- non-Git source state: none;
- live Network realization: source-independent and preserved;
- deployed Finance standing: six authorities healthy;
- canonical Finance standing: seven authorities in source;
- Wallet/API production convergence: **pending separate effect-bearing change**;
- historical provenance: preserved without rewriting.

This acceptance retires only the standalone source carrier. It does not claim that canonical source bytes have all been deployed, and it does not turn repository state into live Network truth.
