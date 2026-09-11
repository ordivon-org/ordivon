# Platform boundary

The local WSL2 host is accepted only for capabilities it actually exposes.

Verified locally:
- Linux network namespaces and veth pairs work.
- sing-box 1.14.x, dnsproxy, Toxiproxy, blackbox_exporter, Prometheus, iperf3 and mtr run natively.

Not available in the current WSL2 kernel:
- Docker bridge networking: Docker fails while creating NAT PREROUTING because the required addrtype/netfilter support is unavailable.
- `tc netem`: the kernel reports the qdisc kind as unknown.

R0 does not patch or replace the WSL kernel to hide those limitations. Local tests therefore use `ip netns` + veth for topology and Toxiproxy for deterministic L4 faults. The reference full-fidelity lab remains containerlab + Docker + tc/netem on a standard Linux runner; that runner must pass the same black-box acceptance suite before any migration decision.
