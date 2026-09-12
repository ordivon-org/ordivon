# Network mechanism decision matrix

The Network E2E decision process starts from workload requirements and selects a mature mechanism. No universal Ordivon network controller is introduced.

| Requirement | Preferred mechanism | Notes |
|---|---|---|
| IPv4/IPv6 routing | Linux kernel + iproute2 | Generic connectivity primitive |
| DNS with redundant upstreams | AdGuard dnsproxy | Parallel upstreams, cache, UDP/TCP |
| HTTP/SOCKS application proxy | sing-box mixed/http/socks | Normal TCP workloads |
| UDP / QUIC / full-IP | sing-box TUN + dedicated netns | Avoid host-wide route takeover |
| Encrypted peer/provider tunnel | WireGuard / wg-quick | Kernel WireGuard on reference Linux; wireguard-go fallback on WSL |
| Deterministic TCP primary/backup | HAProxy | Only when ordered primary/backup semantics are actually required |
| L4 fault injection | Toxiproxy | Connection latency/reset/down scenarios |
| Packet loss/delay/reorder | tc/netem | Requires capable standard Linux kernel |
| Multi-node topology | containerlab | Reference Linux fidelity lane |
| Active HTTP/DNS/TCP/ICMP probe | blackbox_exporter | Functional evidence, not process state |
| Metrics/time series | Prometheus | Evidence plane |
| Process lifecycle | systemd | Process state only; not functional readiness |
| Path/performance diagnosis | curl, dig, ss, mtr, iperf3, bpftrace | Diagnostics, not a custom control plane |

## Classification rules

```text
requires_udp_or_full_ip
  → choose TUN/netns, not HTTP CONNECT

requires_encrypted_tunnel
  → choose WireGuard

requires_ordered_primary_backup
  → choose HAProxy

requires_dns_redundancy
  → choose dnsproxy parallel upstreams

requires_l4_fault
  → choose Toxiproxy

requires_packet_impairment
  → require netem-capable Linux

requires_topology_lab
  → require containerlab/reference Linux
```

Consumer policies belong under `consumers/`; provider material belongs under `providers/`. They may compose generic mechanisms but must not redefine generic Network behavior.
