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

## Long-horizon execution

The source-bound 49-obligation DAG and acceptance catalog is
[planning/execution-program-r1.md](planning/execution-program-r1.md).
Host Work owns mutable task state; this is not a second status registry.
The first NS2 source-only spy extension covers Codex, Discord and Model
Provider, but cannot itself certify deployed no-bypass or process behavior.

## Repository boundaries

```text
config/        generic live configuration
systemd/       generic live lifecycle
acceptance/    generic capability acceptance
capabilities/  optional reusable mechanisms such as WireGuard/failover
providers/     provider-specific profiles and evidence
consumers/     consumer-specific policy and migration artifacts
docs/          current architecture, decisions and acceptance matrix
evidence/      current capability standing
```

## Native task composition

The root `Taskfile.yml` is the public orchestration surface, not a dumping
ground for provider and application scripts. Native Go Task `includes` with
`flatten: true` bind each submodule's own `Taskfile.yml` into exactly the same
public `provider:*`, `consumer:*`, `capability:*` and `reference:*` task names.
The included Taskfiles deliberately inherit the repository-root working
directory; executing one as a standalone Taskfile is not the supported
deployment entrypoint.

Examples of natural Owner files:

- `providers/gluetun/Taskfile.yml` — physical Provider source and acceptance
- `providers/surfshark/Taskfile.yml` — provider catalog and profiles
- `consumers/browserless/Taskfile.yml` — shared carrier and legacy cutover
- `consumers/codex/Taskfile.yml` — Codex scoped proxy
- `consumers/mobile-tailnet-exit/Taskfile.yml` — Tailscale exit
- `consumers/finance/Taskfile.yml` — separate Finance destination authority
- `capabilities/wireguard/Taskfile.yml` — reusable WireGuard capability
- `reference/linux/Taskfile.yml` — external Linux reference fidelity

Other application consumers use the same convention. The root retains generic
platform lifecycle, cross-module acceptance and evidence operations. There is
no additional task router or custom registry. Run `task --list-all`,
`task all:validate` and `mise run ci` from `platform/network/` before release.
Validation proves declared source/config contracts; `task ...:verify` checks
deployed SourceCut and real consumer consequences separately.

Generic core tasks do not depend on provider or consumer profiles.
Old round evidence is recoverable in Git and is not retained as current documentation.
The selected Gluetun Quadlet owns the single physical provider session.
The physical mode now uses native Surfshark WireGuard server selection
for Singapore and Japan, with a Podman Secret and official Gluetun health
recovery. See `providers/gluetun/README.md` for the physical SourceCut.
Codex and mobile Tailscale Exit Node keep separate readiness contracts.

## Public workflow

```text
# Source/config validation
task core:validate

# Verify the currently installed live generation
task core:verify

# Converge idempotently: skip installation when core:verify already passes
task core:converge

# Isolated generic tests without live convergence
task accept:source

# Revalidate current live lifecycle/protocol/resilience
task accept:live

# Full local WSL graduation
task accept:local
```

Optional provider and consumer surfaces use their own namespaces, for example `provider:gluetun:*, provider:surfshark:*` and `consumer:finance:*, consumer:codex:* and consumer:mobile-tailnet-exit:*`. They are not generic Network graduation prerequisites.

## Current standing

The checked-in WSL acceptance record reports **LOCAL_WSL_GRADUATED** at **2026-09-12T15:23:44Z**, for its exact recorded source and platform fingerprints. It is a historical acceptance witness, **not** a claim that the current WSL installation has passed a fresh full graduation since later reconfiguration and outages.

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


### Owner-native test selection

The source-local `mise run ci` runs upstream ShellCheck **and** the Network
Owner's checked-in Python pytest suite using Python 3.15 and pytest 9.1.1.
It must fail when either native tool fails. These tests protect the exact
source currently present in this repository; their PASS does **not** certify
real-network/provider behavior, a full external Gluetun cutover, or additional
tests from divergent unpublished source revisions. Production acceptance
remains separately scoped to actual owned provider and consumer evidence.
