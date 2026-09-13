# Network v2 / Workstation network residual status

- Network v2 source: `/root/projects/ordivon-network-v2`
- Observed Network v2 revision: `22791d742f3fcd9a2c51e5086a277d78e4b808f8`
- Assessed: 2026-09-14
- Disposition: **NETWORK_V2_CURRENT_AUTHORITY / LEGACY_WORKSTATION_CONSUMERS_HOLD**

## Current authority

Network v2 is the current network capability authority. Its generic WSL platform is graduated and current production cutovers already exist for Browserless and Finance OKX. Historical Network research code in `/root/workstation-lab` is not the default production authority.

That does **not** mean every historical Workstation transport process can be deleted immediately. A live-consumer census on 2026-09-14 found remaining consumers that must be migrated by consequence rather than by directory name.

## Remaining legacy consumers

### Finance — frozen in this cleanup round

Several live `egress-pool`, `exterior-anchor`, and `exterior-connect` transient services still serve Finance/Binance/OKX workload paths. These are explicitly out of scope for this cleanup round and must not be stopped merely because Network v2 exists. Finance migration remains consumer-owned and requires its own exact cutover/acceptance.

The `net-e2e-tcp-r1-20260910` exterior anchor is also still named by the Finance Binance recovery/currentness configuration, so it is **not historical garbage** even though its origin is the old Workstation network lineage.

### Research — no standing source dependency

Research v2 source at `860af11cc32cc066cd0ad8899926f8f9bf0441c6` contains no `surfpath`, `scoped-egress`, `exterior-connect`, `exterior-anchor`, `egress-pool`, or `/root/workstation-lab` dependency.

A Paper-2/GROBID activation attempt used `surfpath` as a one-off execution choice to acquire `docker.io/grobid/grobid:0.9.1-full` after ordinary Docker/Podman registry acquisition was unreliable. That worker naturally terminated after acquisition. The image was successfully imported into Podman and a local GROBID container was subsequently started. Therefore this is execution provenance, **not a Research architecture dependency that needs to be copied into Research**.

Future Research container/image acquisition should use ordinary OCI tooling (`skopeo`/Podman/container runtime) under the current network authority. If a recurring destination-specific path is required, add a bounded Network-v2 consumer profile only after a real workload demonstrates that need. Do not reintroduce a generic Research-owned network controller or hard-code `surfpath` into Research.

### Continuity observer — retired after mature-observability substitution

The Workstation `netcontinuity` scheduled observer was retired on 2026-09-14 after its useful current consequences were transferred to mature/provider-native surfaces rather than copied into another custom daemon:

- Gatus deployment/configuration authority moved from Workstation to Operations v2 at `d76310daf5f006d4cedc9a0127395e9d8ad92226`;
- Operations-owned Gatus now performs bounded Cloudflare/GitHub probes through the existing native-A/native-B loopback CONNECT carriers;
- Operations Prometheus at `a2a1d8b995ff53cef8fedf1c1d40051f0582f404` scrapes production Cloudflare connector metrics on ports 20243/20244; both targets were `up` after convergence and `cloudflared_tunnel_ha_connections` was observed as 4 for A and 4 for B;
- Cloudflare source/route convergence remains with the existing direct-route lifecycle rather than a duplicate continuity verdict.

Workstation commit `614354078b770d4905059003103fb285ef1aad50` removed current Gatus ownership plus the continuity tool/runtime-contract/systemd/global-doctor surfaces. Full owner validation passed: 1106 Workstation tests, 6 Browserless tests, 105 Agent Automation tests and 14 Node policy/runtime-domain tests. The timer/service now report `LoadState=not-found`; `/root/tools/bin/netcontinuity` and `/etc/ordivon/network-continuity-contract.toml` are absent. Historical `network_continuity.py`, observation state and receipts remain provenance/reopen material.


## Migration rule

1. Network v2 remains source/current authority.
2. Do not stop Finance transport paths in a non-Finance migration.
3. Do not migrate one-off Research acquisition strategy into Research source unless it becomes a repeated requirement.
4. Retire remaining Workstation network wrappers only after exact current-consumer census reaches zero or each consumer is explicitly cut over; `netcontinuity` already satisfies this rule and is retired.
5. Preserve historical Network research/evidence as reopenable provenance after runtime consumers disappear.
