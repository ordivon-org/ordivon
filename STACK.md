# Network v2 stack lock

| Layer | Component | Current disposition |
|---|---|---|
| Data plane | sing-box | 1.14.0 distro package; R9 live dual-stack R0 |
| Priority failover | HAProxy | 3.4.4 distro package; R4 primary/backup acceptance passed |
| WireGuard lifecycle | wg-quick + official wireguard-go | userspace fallback admitted for current WSL; source pinned in `external/wireguard-go.lock` |
| Commercial VPN | Gluetun | reference standard-Linux runner; not yet admitted locally |
| OpenVPN | OpenVPN upstream client | binary available locally; real provider authority not yet admitted |
| DNS | AdGuard dnsproxy | 0.84.2 distro package; R9 live A + AAAA |
| Metrics | Prometheus | 3.14.0 distro package; R0 live |
| Probes | blackbox_exporter | 0.28.0 distro package; R0 live |
| Local lab topology | Linux iproute2 + sing-box TUN | netns + veth; isolated TCP/UDP/QUIC TUN acceptance passed in R11 |
| Reference lab topology | containerlab | 0.77.x on standard Linux runner |
| L4 faults | Toxiproxy | 2.12.0 checksum-verified upstream binary |
| Packet faults | tc/netem | required on reference Linux runner; unavailable in current WSL kernel |
| Performance | iperf3 | 3.21 |
| Path diagnostics | mtr | 0.96 |
| Forensics | bpftrace | 0.26.x distro package |

The current WSL kernel cannot create an in-kernel WireGuard device with `ip link add ... type wireguard`. Network v2 does not patch the kernel or emulate the protocol. Instead, `wg-quick` is allowed to use the official `wireguard-go` userspace implementation through `WG_QUICK_USERSPACE_IMPLEMENTATION`. R2 proved create -> failure -> recreation -> recovery with that exact composition.

The Docker CLI is present locally, but the full-fidelity containerlab/netem lane is not locally graduated. The current WSL2 kernel specifically rejects the `netem` qdisc, so packet-level delay/loss/reorder acceptance remains a standard-Linux runner requirement. No compatibility workaround is part of Network v2.

Gatus, Grafana, CoreDNS, Envoy, Pumba, Cilium, FRR, NetBox, Batfish and Kubernetes remain intentionally absent from the current local stack. HAProxy entered the local candidate only at R4 after canonicalization falsified sing-box URLTest as a deterministic primary/backup authority; it is not used by the R0 direct path.
