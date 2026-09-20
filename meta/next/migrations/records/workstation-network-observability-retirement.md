# Workstation network observability retirement

- Workstation source retirement commit: `614354078b770d4905059003103fb285ef1aad50`
- Operations Gatus ownership commit: `d76310daf5f006d4cedc9a0127395e9d8ad92226`
- Operations Cloudflare Prometheus commit: `a2a1d8b995ff53cef8fedf1c1d40051f0582f404`
- Assessed: 2026-09-14
- Disposition: **BESPOKE_CONTINUITY_RETIRED / MATURE_OBSERVABILITY_ACTIVE**

## Substitution

The old Workstation `netcontinuity` observer mixed destination reachability, provider context, Cloudflare connector state and a global health classification. No current business/domain repository consumed its receipt directly. Its useful consequences were decomposed into mature/provider-native surfaces:

- Gatus: point-in-time endpoint reachability, including native A/B loopback carrier probes;
- Prometheus: raw production Cloudflare connector metrics, including `cloudflared_tunnel_ha_connections`;
- Cloudflare direct-route lifecycle: exact source/route convergence;
- Network v2/domain consumers: network/domain acceptance rather than an Operations-level global verdict.

Production Gatus cutover passed with Operations-owned config/unit bytes. The four A/B endpoint records appeared through Gatus. At the cutover observation Cloudflare trace passed through A and B while GitHub returned Bad Gateway through both; the migration deliberately preserved observed failure rather than manufacturing a green status.

Operations Prometheus then converged with A/B Cloudflare targets `up`; the HA connection series reported 4 for connector A and 4 for B at verification time.

## Physical retirement

The following current Workstation artifacts were archived under `/var/lib/ordivon/retired/network-continuity-observer/` and removed from active authority:

- `ordivon-network-continuity-observe.service`;
- `ordivon-network-continuity-observe.timer`;
- `/etc/ordivon/network-continuity-contract.toml`;
- `/root/tools/bin/netcontinuity`.

Both systemd units now report `LoadState=not-found`. Historical observation state under `/root/.local/state/ordivon-workstation/network-continuity` was intentionally preserved. Historical source `scripts/network_continuity.py` also remains reopenable and is not a current first-PATH or scheduled authority.

Finance transport paths were not changed by this migration.
