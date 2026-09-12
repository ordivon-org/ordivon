# Platform boundary

The local WSL2 host is accepted only for capabilities it actually exposes.

Verified locally:
- Linux network namespaces and veth pairs work.
- sing-box 1.14.x, dnsproxy, Toxiproxy, blackbox_exporter, Prometheus, iperf3 and mtr run natively.
- `wg-quick` can create and recover userspace WireGuard interfaces when explicitly pointed at the pinned official `wireguard-go` binary.
- the userspace WireGuard lifecycle passed create -> connectivity -> deliberate teardown -> expected failure -> recreation -> connectivity recovery.

Not available in the current WSL2 kernel:
- Docker bridge networking: Docker fails while creating NAT PREROUTING because the required addrtype/netfilter support is unavailable.
- `tc netem`: the kernel reports the qdisc kind as unknown.
- in-kernel WireGuard interface creation: `ip link add ... type wireguard` returns `Unknown device type`.

Network v2 does not patch or replace the WSL kernel to hide those limitations. For WireGuard on this host it delegates to `wg-quick` plus the official userspace implementation rather than creating a custom compatibility layer. Local topology tests use `ip netns` + veth and deterministic L4 fault tests use Toxiproxy.

The reference full-fidelity lab remains containerlab + Docker + tc/netem on a standard Linux runner. That runner should prefer the kernel WireGuard implementation and must pass the same black-box acceptance suite before any migration decision.
