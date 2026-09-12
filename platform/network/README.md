# Ordivon Network v2

Greenfield network substrate built from mature external projects. It has zero runtime or source dependency on the legacy Ordivon network stack.

## Rules

1. External implementation first; configuration before code.
2. No import, schema, state, service-name, port, or compatibility dependency on legacy Network.
3. Tests precede Ordivon-specific abstraction.
4. Production data plane and test/observation planes stay separable.
5. New custom network daemons are forbidden in R0.
6. Unsupported host capabilities are recorded, not hidden behind compatibility shims.

## R0 local candidate

- sing-box — data plane
- AdGuard dnsproxy — DNS carrier
- blackbox_exporter — black-box measurement
- Prometheus — evidence time series
- Toxiproxy — deterministic L4 fault injection
- Linux network namespaces + veth — local controlled topology
- iperf3, curl, mtr, tcpdump — measurement/diagnostics
- bpftrace — deep forensic tool

## Reference full-fidelity lab

A later standard-Linux runner will test containerlab + Docker + tc/netem. No unvalidated containerlab/Docker configuration is shipped in R0 because this WSL2 kernel cannot satisfy those kernel requirements.

## Acceptance path

`syntax -> isolated smoke -> observation -> L4 fault injection -> controlled topology/performance -> recovery -> full-fidelity Linux lab -> provider paths -> soak -> reboot -> independent falsification`.

Legacy migration is explicitly out of scope until the new stack independently graduates.

## R4 provider priority failover candidate

R4 keeps provider ownership outside Network v2. sing-box remains the HTTP CONNECT carrier on each physical path, while HAProxy TCP mode owns only deterministic primary/backup selection. The provider carrier is the normal server; native direct is a `backup` server. Active TCP checks issue a CONNECT to a public HTTPS target through each carrier, so a listening-but-unusable carrier is not counted healthy. Stopping only the temporary provider carrier proves failover to direct; restoring the same carrier and passing the configured rise threshold proves failback to provider.

An earlier live POC used sing-box `urltest` and did prove failover/failback in one observation window. R4 intentionally does not productize that mechanism because URLTest is latency selection, not a stable provider-primary/direct-backup policy: during canonicalization it failed over correctly but legitimately stayed on the lower-latency direct path after provider recovery. The migration therefore replaces policy mechanics instead of wrapping that semantic mismatch in custom code.

This is canonical acceptance equipment, not consumer authority and not a production provider controller. It does not modify provider namespaces, machine default routing, system proxy state, Cloudflare control-plane ingress, or Runtime/Host MCP listeners. See `docs/FAILOVER_R4.md`.
