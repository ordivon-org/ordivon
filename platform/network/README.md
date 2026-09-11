# Ordivon Network v2

Greenfield network substrate built from mature external projects. It has zero runtime or source dependency on the legacy Ordivon network stack.

## Rules

1. External implementation first; configuration before code.
2. No import, schema, state, service-name, port, or compatibility dependency on legacy Network.
3. Tests precede Ordivon-specific abstraction.
4. Production data plane and test/observation planes stay separable.
5. New custom network daemons are forbidden in R0.

## R0 components

- sing-box 1.14.x — data plane
- Gluetun 3.41.x — Surfshark provider adapter (candidate; must earn permanence)
- AdGuard dnsproxy 0.84.x — DNS carrier
- Prometheus 3.13.x LTS — evidence time series
- blackbox_exporter 0.28.x — black-box probes
- Docker Engine — laboratory runtime
- containerlab 0.77.x — declarative network laboratory
- Toxiproxy 2.12.x — L4 fault injection
- Linux tc/netem — packet impairment
- iperf3 3.21, curl, mtr, tcpdump — measurement/diagnostics
- bpftrace 0.26.x — deep forensic tool

## First acceptance gates

`config -> syntax -> isolated smoke -> fault injection -> recovery -> performance -> soak -> reboot -> independent falsification`.

Legacy migration is explicitly out of scope until the new stack independently graduates.
