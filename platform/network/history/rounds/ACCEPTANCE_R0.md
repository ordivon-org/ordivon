# R0 local acceptance

Date: 2026-09-11

## Passed

- `systemd-analyze verify` for all five R0 service definitions.
- `sing-box check` for the direct data-plane configuration.
- `blackbox_exporter --config.check`.
- `promtool check config`.
- Direct chain: dnsproxy -> sing-box -> HTTPS returned success.
- Observation chain: blackbox_exporter probe succeeded and Prometheus ingested `probe_success=1`.
- Fault injection: Toxiproxy passed the healthy request and a timeout toxic then made the same request fail.
- Controlled topology: three Linux namespaces with two veth links routed end-to-end; ping and iperf3 succeeded.

## Host capability findings

- Docker bridge networking is unavailable on the current WSL2 kernel because Docker cannot create the required NAT/addrtype rule.
- `tc netem` is unavailable on the current WSL2 kernel (`qdisc kind is unknown`).
- R0 deliberately does not patch the WSL kernel or create a compatibility layer for either limitation.

## Not yet admitted

- Gluetun/Surfshark WireGuard or OpenVPN paths.
- sing-box direct VPN endpoint comparison against Gluetun.
- packet-level netem scenarios.
- containerlab topology on a standard Linux runner.
- multi-path selection/failover.
- reboot recovery.
- long-running soak.
- external-vantage corroboration.
- legacy workload migration.

R0 is therefore a local greenfield baseline, not a graduated replacement for the legacy Network system.
