# R0 stack lock

| Layer | Component | R0 pin / policy |
|---|---|---|
| Data plane | sing-box | 1.14.x stable |
| Commercial VPN | Gluetun | 3.41.x, containerized |
| DNS | AdGuard dnsproxy | host package 0.84.x |
| Metrics | Prometheus | 3.13.x LTS container |
| Probes | blackbox_exporter | 0.28.x container |
| Lab | Docker Engine | distro package |
| Lab topology | containerlab | 0.77.x |
| L4 faults | Toxiproxy | 2.12.x container |
| Packet faults | tc/netem | kernel/iproute2 |
| Performance | iperf3 | 3.21 |
| Path diagnostics | mtr | 0.96 |
| Forensics | bpftrace | 0.26.x |

Gatus, Grafana, CoreDNS, Envoy, HAProxy, Pumba, Cilium, FRR, NetBox, Batfish and Kubernetes are intentionally absent from R0.
