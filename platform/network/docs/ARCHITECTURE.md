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

**Monitoring SourceCut precommit LEGO** (Network Owner, Taskfile.yml /
scripts/monitoring-sourcecut-preflight.py). Before core:install makes its
first live write, compare the two existing Blackbox/Prometheus configuration
bytes against the deployed pair:

- Neither live file exists: FIRST_INSTALL, after native configuration validation.
- Both exist with identical bytes: IDENTICAL_SOURCECUT, idempotent installation.
- A partial pair, symlink, or any different bytes: BLOCKED, without an install.

This is the minimum no-silent-overwrite guarantee selected from the historical
Network R6 consumer-failure branch. It intentionally does **not** resurrect the
old multi-consumer monitoring registry, restore retired alert rules, introduce a
YAML parser/production dependency, or claim semantic YAML equivalence. Changing
live monitoring requires a separately qualified migration; no broad automatic
overwrite is authorized. Native source/fault tests:
tests/test_monitoring_precommit.py, accepted through mise run ci.
The preflight prevents static drift; it is not an atomic lock against another
process changing live files after the check.

## Reference environments

Current local execution target:

- WSL platform: locally graduated.

Reference fidelity standing:

- standard Linux kernel `tc/netem`, containerlab, kernel WireGuard, and direct userspace wireguard-go differential: graduated on an isolated KVM reference guest.

Unsupported host capabilities are recorded explicitly rather than hidden behind compatibility shims.

## Standard Linux reference lane

WSL is a supported local execution target, not the cross-platform fidelity authority for kernel networking.

The reference lane lives under `reference/linux/` and requires a dedicated, privileged standard-Linux VM/runner. Its runner is provisioned independently and must expose:

- `tc/netem`;
- Docker + containerlab;
- kernel WireGuard;
- the tooling required to run the pinned userspace `wireguard-go` counterpart.

The lane proves deterministic packet impairment, a real two-node containerlab topology, and kernel-vs-userspace WireGuard lifecycle behavior. The graduated reference run used a clean immutable Arch Linux KVM base and a disposable qcow2 overlay; the guest shut down cleanly after acceptance and the base digest remained unchanged. A WSL host is rejected by preflight rather than treated as a failed reference implementation.

The Network reference workflow is currently a **source template** at `platform/network/.github/workflows/network-reference-linux.yml`. Its nested `.github/workflows/` location is not the monorepo-root `.github/workflows/` directory required for GitHub Actions workflow registration. The monorepo has an `origin` remote, but that does not establish an active Network reference workflow, a matching self-hosted runner, or a successful remote execution. Activating this lane requires a separately verified root-workflow integration and runner qualification; until then, this is a reference contract rather than remote execution evidence.

## Consumer lifecycle boundary

Browserless provider/consumer migration may fail closed when an observed upper-layer workflow is actively using the path, but Network does not start, restart, enable, or require an Agent Automation/Temporal consumer service as part of network cutover or acceptance. Consumer lifecycle belongs to its own owner. A successful Network Browserless cutover proves the network/provider path and leaves upper-layer reconciliation to the consumer.
