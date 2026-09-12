# Ordivon Network E2E

Network E2E composes mature networking mechanisms and proves that the resulting path satisfies a workload requirement. It is not a custom network stack or a universal network controller.

## Model

```text
Requirement
  → classify network problem
  → select mature mechanism
  → compose an isolated realization
  → falsify failure modes
  → emit evidence
```

The generic live platform is intentionally small:

```text
network-v2-r0.target
├─ dnsproxy           DNS carrier, A/AAAA, parallel upstreams, cache
├─ sing-box           dual-stack mixed proxy data plane
├─ blackbox_exporter  functional probes
└─ Prometheus         evidence time series
```

`network-v2-r0.target` is the stable live unit name. The historical `r0` token is retained only to avoid an unnecessary service-identity migration.

## Repository boundaries

```text
config/        generic live configuration
systemd/       generic live lifecycle
acceptance/    generic capability acceptance
capabilities/  optional reusable mechanisms such as WireGuard/failover
providers/     provider-specific profiles and evidence
consumers/     consumer-specific policy and migration artifacts
history/       archived evolution/round evidence
docs/          current architecture, decisions and acceptance matrix
evidence/      current capability standing
```

Generic core tasks do not depend on provider or consumer profiles.

## Public workflow

```text
# Source/config validation
task core:validate

# Verify the currently installed live generation
task core:verify

# Isolated generic tests without live convergence
task accept:source

# Revalidate current live lifecycle/protocol/resilience
task accept:live

# Full local WSL graduation
task accept:local
```

Optional provider and consumer surfaces use their own namespaces, for example `provider:surfshark:*` and `consumer:finance-okx:*`. They are not generic Network graduation prerequisites.

## Current standing

Current WSL platform standing: **LOCAL_WSL_GRADUATED**.

Proven locally:

- IPv4 and IPv6;
- A/AAAA DNS over UDP/TCP;
- bidirectional address-family fallback;
- HTTP/1.1 and HTTP/2;
- long-flow and concurrent traffic;
- isolated TUN TCP + UDP/QUIC/HTTP3;
- DNS partial failure, all-upstream fail-closed behavior, cache expiry and recovery;
- Blackbox + Prometheus evidence;
- Toxiproxy L4 faults;
- netns/veth topology;
- process recovery, whole-platform cold start, and real WSL reboot recovery;
- control-plane independence while the generic R0 data plane is stopped.

Standard-Linux reference fidelity is also graduated independently of WSL:

- `tc/netem` packet loss plus delay/reorder: PASS;
- containerlab two-node data topology: PASS;
- kernel WireGuard initial/failure/recovery: PASS;
- direct userspace `wireguard-go` initial/failure/recovery: PASS;
- kernel-vs-userspace WireGuard differential: PASS.

The reference authority uses a clean Arch Linux KVM base plus a disposable qcow2 overlay; the base remains immutable across acceptance.

Windows-host reboot plus WSL auto-launch belongs to Workstation/bootstrap. Consumer cutover and legacy retirement belong to consumer migration.

See `docs/ARCHITECTURE.md`, `docs/DECISION_MATRIX.md`, `docs/ACCEPTANCE_MATRIX.md`, and `evidence/current-capabilities.json`.

## Evidence and reference fidelity

A full `task accept:local` run now refreshes `evidence/current-capabilities.json` only after all local acceptance gates pass. `task evidence:verify-local` detects source/platform drift against that generated projection.

Cross-platform kernel fidelity is expressed separately under `reference/linux/`. The standard-Linux reference lane has now passed on an isolated KVM guest. Future CI can replay the same `task reference:linux:accept` contract on a dedicated non-WSL self-hosted runner labelled `network-e2e`; the checked-in GitHub Actions workflow remains a replay contract until this repository is attached to an appropriate Git remote/runner.
