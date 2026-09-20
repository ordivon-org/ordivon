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
4. direct pinned `wireguard-go` userspace TUN/UAPI lifecycle as a differential counterpart to kernel WireGuard.

## Current standing

`STANDARD_LINUX_REFERENCE_GRADUATED` on a clean Arch Linux KVM guest. The authority evidence is `../../evidence/reference-linux-20260912.json`. The acceptance run used an immutable qcow2 base plus a disposable overlay and local OCI/tool fixtures so registry or module-proxy availability was not part of network correctness.
