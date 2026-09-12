# Network E2E architecture

Network E2E is a composition and verification environment, not a custom network stack.

## Boundary

Network E2E owns:

- generic data-plane composition;
- DNS composition;
- optional proxy, full-IP/TUN, encrypted-tunnel and failover capabilities;
- independent probes and evidence;
- deterministic fault acceptance;
- lifecycle acceptance.

Network E2E does not own:

- Runtime or Cloudflare management ingress;
- consumer business policy;
- application retries;
- consumer cutover or legacy retirement;
- Windows-to-WSL bootstrap.

The primary invariant is:

```text
MANAGEMENT PLANE MUST NOT DEPEND ON TESTED DATA PLANE
```

## Generic live platform

```text
network-v2-r0.target
├─ network-v2-dnsproxy.service
├─ network-v2-singbox.service
├─ network-v2-blackbox.service
└─ network-v2-prometheus.service
```

`network-v2-r0.target` is retained as the stable live systemd identity. The historical `r0` token is not a conceptual dependency and is not used to organize the source tree.

The generic live path is:

```text
TCP workload
  → 127.0.0.1:28080
  → sing-box mixed proxy
  → dual-stack direct network

DNS
  → 127.0.0.1:25353
  → dnsproxy
  → parallel upstream resolvers
```

For UDP/QUIC/full-IP workloads, Network E2E uses an on-demand sing-box TUN confined to a dedicated Linux network namespace. Host-wide TUN/default-route takeover is intentionally not the default model.

## Source boundaries

```text
config/                 generic live configuration
systemd/                generic live lifecycle
acceptance/             generic capability acceptance
capabilities/           optional reusable mechanisms
providers/              provider-specific profiles and evidence
consumers/              consumer-specific network policy and shadow migration
history/                prior round/evolution evidence
```

The generic core must not import provider- or consumer-specific configuration.

## Reference environments

Current local execution target:

- WSL platform: locally graduated.

Reference fidelity target:

- standard Linux kernel for `tc/netem`, containerlab and kernel-WireGuard differential acceptance.

Unsupported host capabilities are recorded explicitly rather than hidden behind compatibility shims.

## Standard Linux reference lane

WSL is a supported local execution target, not the cross-platform fidelity authority for kernel networking.

The reference lane lives under `reference/linux/` and requires a dedicated, privileged standard-Linux VM/runner. Its runner is provisioned independently and must expose:

- `tc/netem`;
- Docker + containerlab;
- kernel WireGuard;
- the tooling required to run the pinned userspace `wireguard-go` counterpart.

The lane proves deterministic packet impairment, a real two-node containerlab topology, and kernel-vs-userspace WireGuard lifecycle behavior. A WSL host is rejected by preflight rather than treated as a failed reference implementation.

For CI, the repository carries a GitHub Actions workflow targeting a dedicated self-hosted runner with `[self-hosted, linux, x64, network-e2e]`. The repository currently has no Git remote, so the workflow is a ready contract rather than an executed remote proof.
