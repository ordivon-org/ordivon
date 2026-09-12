# Standard Linux reference lane

This lane closes fidelity gaps that the current WSL kernel cannot prove. It is intended for a dedicated standard-Linux VM/runner with low-level network authority, not an unprivileged container runner.

Required runner capabilities:

- Linux, non-WSL;
- `iproute2` with the `netem` qdisc available;
- Docker daemon;
- containerlab;
- kernel WireGuard (`ip link add ... type wireguard`);
- `wireguard-tools`;
- Go/Make/Git only when the pinned `wireguard-go` differential is materialized;
- passwordless root/network administration appropriate for an isolated CI runner.

Recommended CI routing is a dedicated self-hosted runner label such as:

```yaml
runs-on: [self-hosted, linux, x64, network-e2e]
```

The runner should be provisioned independently. Acceptance tests verify capabilities; they do not bootstrap an arbitrary host into a privileged network test machine.

Reference acceptance covers:

1. deterministic `tc/netem` loss plus delay/reorder;
2. a two-node containerlab Linux topology and real data-interface reachability;
3. kernel-WireGuard lifecycle;
4. the existing pinned `wireguard-go` userspace lifecycle as a differential counterpart.
