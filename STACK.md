# R0 stack lock

| Layer | Component | R0 local candidate |
|---|---|---|
| Data plane | sing-box | 1.14.0 distro package |
| Commercial VPN | Gluetun | 3.41.x reference Linux runner; not yet admitted locally |
| DNS | AdGuard dnsproxy | 0.84.2 distro package |
| Metrics | Prometheus | 3.14.0 distro package |
| Probes | blackbox_exporter | 0.28.0 distro package |
| Local lab topology | Linux iproute2 | netns + veth |
| Reference lab topology | containerlab | 0.77.x on standard Linux runner |
| L4 faults | Toxiproxy | 2.12.0 checksum-verified upstream binary |
| Packet faults | tc/netem | required on reference Linux runner; unavailable in current WSL kernel |
| Performance | iperf3 | 3.21 |
| Path diagnostics | mtr | 0.96 |
| Forensics | bpftrace | 0.26.x distro package |

Docker/containerlab are not locally admitted because the current WSL2 kernel cannot satisfy Docker bridge/NAT requirements. No compatibility workaround is part of Network v2.

Gatus, Grafana, CoreDNS, Envoy, HAProxy, Pumba, Cilium, FRR, NetBox, Batfish and Kubernetes remain intentionally absent from R0.
