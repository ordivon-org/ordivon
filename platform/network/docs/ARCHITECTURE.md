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

## Consumer-backed module boundaries (DSM audit, 2026-11-07)

Folder boundaries encode *responsibilities*, not isolated processes.
This inventory is a source/installed/consumer map, not a second registry:

| Actual folder | Responsibility | Consumer/replacement edge |
| --- | --- | --- |
| config/, systemd/ | Generic DNS, proxy, monitoring and systemd core | network-v2-r0.target |
| capabilities/wireguard/ | Encrypted tunnel differential and lifecycle | Gluetun/reference acceptance |
| capabilities/failover/ | Ordered TCP primary/backup mechanism | Optional authorized failover workload |
| providers/gluetun/ | Single physical Surfshark WireGuard, Podman Secret, native firewall and healing | Shared VPN carrier and mobile exit |
| providers/surfshark/ | Provider catalog, explicit serial recovery materials | Inactive Browserless fallback path |
| substrates/shared-egress/ | Shared namespace, forwarding and carrier readiness | Existing nv2-browserless-prod and scoped consumers |
| consumers/browserless/ | Legacy provider rollback and Browserless migration acceptance | Browserless-specific recovery only |
| consumers/chat-ingress/ | Chat transport policy and relay | Chat workloads |
| consumers/claude/ | Claude allowlist, client namespace and bridge | Claude Code |
| consumers/codex/ | Scoped ChatGPT transport + read-only process observation | Codex consumer; Windows startup owned by Workstation |
| consumers/developer-egress/ | Optional developer process network environment | Explicit caller only |
| consumers/discord/ | Discord API/Gateway destination policy | Discord app |
| consumers/finance/ | Exchange REST/WS and explicit macro direct routes | Finance Owner |
| consumers/mobile-tailnet-exit/ | Tailscale Exit Node in Gluetun namespace | iPad/iPhone |
| consumers/model-provider/ | Bounded model API HTTPS | Model callers |
| consumers/supply-chain/ | OCI registry routing and Docker binding | Image acquisition |
| consumers/windows-real-chrome/ | Public web proxy plus Windows-local relay | Chrome and native OS system proxy |
| consumers/x-reality/ | X API exact destination | X client, auth external |
| acceptance/, tests/, formal/ | Functional, implementation and abstract proof respectively | Effect witnesses, model contracts |
| reference/linux/ | Standard Linux kernel and topology fidelity | Kernel/netem/containerlab/WireGuard comparisons |
| docs/, evidence/, planning/ | Read-only guides, source evidence and plan | Host Work owns changing execution state |

## Real network failure-domain graph (consumer evidence, 2026-11-14)

```text
one ZTE U30 Pro MU5358 / China Mobile 5G WAN (single observed failure domain)
  └── LAN gateway 192.168.0.1, same learned gateway MAC
      ├── Windows Wi-Fi Realtek 8852BE ───┐
      └── Windows Remote NDIS USB ────────┤
                                          └── Windows selected route → WSL2
                                              ├── Host / Gateway / Runtime control
                                              ├── direct IPv4 Blackbox proof
                                              └── one Gluetun/Surfshark WG
                                                  ├── native WireGuard health restart
                                                  ├── existing 1-minute systemd recovery
                                                  └── shared Carrier → Claude / Codex
                                                                     → Finance (9 lanes)
                                                                     → model/supply chain/Chrome
                                                                     → Tailscale server exit
```

The existing ZTE U30 Pro read-only Provider observer independently returned
MU5358/China Mobile 5G current PPP connected, RSRP -72 dBm and SNR 27 dB,
with ten gateway pings and no loss at 2026-11-14 16:23 CST. These are
**current** cellular/LAN observations, not historical cause proof for
08:41–14:20; no physically independent second WAN is established.

This diagram describes one observed first-hop failure domain. It does
not prove an ISP internal component is the root cause. On 2026-11-14
08:41:29 CST both Windows NCSI Internet capabilities failed together,
all direct and VPN probes simultaneously dropped, and Gluetun's own
health loop retried 3,178 times. Windows NCSI recovered both at
14:20:44; first successful direct/VPN/Agent Prometheus samples followed
within 11–34 seconds.

An interface-level failover between Wi-Fi and USB RNDIS sharing the same
gateway MAC is NOT a validated independent physical WAN failover.
The physical alternative must be measured with distinct active egress
and direct HTTPS via each WAN BEFORE software can route to it.

One Provider source contains two distinct recovery concepts:
native Gluetun health restarts for tunnel availability, plus the
existing systemd one-shot for quality-aware trials ONLY when independently
verified physical Internet works and current Claude/Codex/PyPI user
traffic fails. Historical successful countries are source/Prometheus
trial candidates, never simultaneously connected standby sessions.
No new watch daemon, PostgreSQL table, duplicate tunnel or custom
network controller is required for this fallback. Consumers validate
effect, not a successful VPN API response alone.

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
```

The generic DNS and proxy data plane must not import provider or consumer destination policy. Prometheus' read-only evidence plane may include consumer-owned scrape declarations through upstream-native `scrape_config_files`; this does not start or authorize those consumers.

**Monitoring SourceCut precommit LEGO** (Network Owner, Taskfile.yml /
scripts/monitoring-sourcecut-preflight.py). Before core:install makes its
first live write, compare all three existing Blackbox/Prometheus configuration
files (Blackbox modules, generic scrape jobs, and consumer alert rules),
plus each Prometheus-native consumers/*.yml scrape fragment, byte-for-byte
with the deployed generation. The native scrape-pool and active-target APIs
also verify that all consumer jobs are loaded:

- None of the three live files exists: FIRST_INSTALL, after native validation.
- All three exist with identical bytes: IDENTICAL_SOURCECUT, idempotent installation.
- Partial files, symlinks, or different bytes: BLOCKED, before any install write.

This is the minimum no-silent-overwrite guarantee selected from the historical
Network R6 consumer-failure branch. It intentionally does **not** resurrect the
old multi-consumer monitoring registry, introduce a YAML parser/production
dependency, or claim semantic YAML equivalence. The adopted consumer rules and
Blackbox modules are the 2026-11-06 verified active live configuration, not
a reconstruction from old logs. Prometheus natively loads rule_files and
Blackbox natively loads its declared modules; consumer domain policy remains
outside Network. Changing
live monitoring requires a separately qualified migration; no broad automatic
overwrite is authorized. Native source/fault tests:
tests/test_monitoring_precommit.py, accepted through mise run ci.
The preflight prevents static drift; it is not an atomic lock against another
process changing live files after the check.

## Rename and cleanup decision

The stable units network-v2-r0.target and nv2-browserless-prod have active
source, installed and loaded consumers. Their historical naming is imperfect,
but a cosmetic rename would create a migration seam for several live scoped
proxies. Do not clone the namespace, duplicate a provider, or add aliases
merely to make directories appear tidy. An eventual rename requires a
source-to-installed-to-consumer dependency graph and equivalent production
request/denial/failover evidence.

The provider rollback inputs in providers/surfshark and consumers/browserless
are still referenced by explicit native recovery paths. They are not an
active second tunnel or disposable log files. By contrast, the manually
launched Windows Codex wrapper had no current startup consumer and was retired.
The source directory is small; do not use file age or size as a deletion rule.
Clean generated resources only through their natural owner (Git, Podman,
systemd, Runtime) after consumer reachability is disproved.

The Gluetun native LAN route setting is currently 192.168.0.0/24. Upstream
FIREWALL_OUTBOUND_SUBNETS permits all outbound protocols to that private
subnet and modifies routing/firewall; it is not a UDP-only ACL.
The publicly routed default must continue to use Surfshark. The setting
must not overlap the WireGuard tunnel range. On LAN renumbering, verify
iPad direct-vs-DERP, loaded Gluetun rules, and actual client IPinfo
before accepting the new SourceCut. For off-LAN iPad clients DERP is a
functional but higher-latency fallback, not a public direct-IP escape.

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

The Network reference CI definition is a **non-installed, standalone repository template** at `platform/network/reference/linux/workflows/network-reference-linux.yml`, co-located with its `reference/linux/` implementation. It is not a workflow registered with the monorepo root `.github/workflows/`, and GitHub does not execute it here. To run it in a dedicated extracted repository, install it as that repository's `.github/workflows/network-reference-linux.yml` after qualifying the self-hosted `network-e2e` runner and matching reference paths. The monorepo's `origin` remote does not establish this physical lane; until separately executed, this template is only a reference contract.

## Consumer lifecycle boundary

Browserless provider/consumer migration may fail closed when an observed upper-layer workflow is actively using the path, but Network does not start, restart, enable, or require an Agent Automation/Temporal consumer service as part of network cutover or acceptance. Consumer lifecycle belongs to its own owner. A successful Network Browserless cutover proves the network/provider path and leaves upper-layer reconciliation to the consumer.
