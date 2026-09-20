# Network E2E stack

## Generic live platform

| Problem | Mature component | Disposition |
|---|---|---|
| Dual-stack application proxy | sing-box 1.14.x | live |
| DNS | AdGuard dnsproxy 0.84.x | live |
| Process lifecycle | systemd | live |
| Active HTTP/DNS/TCP probes | blackbox_exporter 0.28.x | live |
| Evidence time series | Prometheus 3.14.x | live |
| L4 fault injection | Toxiproxy 2.12.x | accepted |
| Local topology | Linux iproute2/netns/veth | accepted |
| UDP/QUIC/full-IP | sing-box TUN in isolated netns | accepted on demand |
| Performance | iperf3 | diagnostic |
| Path diagnostics | mtr/curl/dig/ss | diagnostic |
| Deep forensics | bpftrace | diagnostic |

## Optional reusable capabilities

| Requirement | Component | Boundary |
|---|---|---|
| Encrypted tunnel | WireGuard / wg-quick | kernel WireGuard on reference Linux; official wireguard-go fallback accepted on WSL |
| Deterministic TCP primary/backup | HAProxy | only when ordered failover semantics are required |
| Packet delay/loss/reorder | tc/netem | standard-Linux fidelity gate; unavailable in current WSL kernel |
| Multi-node topology fidelity | containerlab | standard-Linux reference lane |

## Deliberately absent from generic core

Provider catalogs, provider credentials, consumer destination policies, consumer fail-closed rules and migration shadows are not generic Network components. They live under `providers/` and `consumers/` and compose the generic mechanisms when needed.

The management/control plane is also outside this stack. Runtime and Cloudflare ingress must continue operating when the tested Network data plane is stopped.
