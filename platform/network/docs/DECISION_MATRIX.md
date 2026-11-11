# Network mechanism decision matrix

The Network E2E decision process starts from workload requirements and selects a mature mechanism. No universal Ordivon network controller is introduced.

| Requirement | Preferred mechanism | Notes |
|---|---|---|
| IPv4/IPv6 routing | Linux kernel + iproute2 | Generic connectivity primitive |
| DNS with redundant upstreams | AdGuard dnsproxy | Parallel upstreams, cache, UDP/TCP |
| HTTP/SOCKS application proxy | sing-box mixed/http/socks | Normal TCP workloads |
| UDP / QUIC / full-IP | sing-box TUN + dedicated netns | Avoid host-wide route takeover |
| Encrypted peer/provider tunnel | WireGuard / wg-quick | Kernel WireGuard on reference Linux; wireguard-go fallback on WSL |
| Deterministic TCP primary/backup | HAProxy | Only when ordered primary/backup semantics are actually required |
| L4 fault injection | Toxiproxy | Connection latency/reset/down scenarios |
| Packet loss/delay/reorder | tc/netem | Requires capable standard Linux kernel |
| Multi-node topology | containerlab | Reference Linux fidelity lane |
| Active HTTP/DNS/TCP/ICMP probe | blackbox_exporter | Functional evidence, not process state |
| Metrics/time series | Prometheus | Evidence plane |
| Process lifecycle | systemd | Process state only; not functional readiness |
| Path/performance diagnosis | curl, dig, ss, mtr, iperf3, bpftrace | Diagnostics, not a custom control plane |

## Capability LEGO and method LEGO selection

A capability LEGO is a replaceable mechanism with actual runtime effects.
A method LEGO guides a decision or proof but does not operate a network.
Reuse the upstream mechanism before constructing a new Ordivon wrapper.

| Problem | Capability LEGO / implementation | Method LEGO | Real consumer-bound acceptance |
| --- | --- | --- | --- |
| Query resolution | AdGuard dnsproxy parallel upstream/cache | State transition and Z3 induction | A/AAAA UDP/TCP, expired cache, outage recovery |
| Generic application proxy | sing-box HTTP/SOCKS/TCP | Protocol and first-match route semantics | Actual origin TLS plus forbidden no-forward |
| Physical VPN | Gluetun + native Surfshark WireGuard | Single-writer/identity invariant | One Podman secret/session, VPN exit, health recovery |
| Shared namespace / carrier | Native iproute2 netns/veth, systemd units, Gluetun adapter | DSM coupling and stable interface refinement | Installed byte parity, no default route, real provider and consumers |
| Mobile exit | Tailscale userspace in Gluetun netns | E2E source/installed/client witness | Admin-approved node, iOS-selected exit and IPinfo |
| Scoped app access | sing-box bounded consumer policies | Assume/guarantee and Z3 refinement | Exact host+port admit, negative canary, no direct fallback |
| Optional failover | HAProxy native TCP backend priority | Reliability fault tree / replay | Failover/failback of real accepted workload |
| Observability | Blackbox + Prometheus native scrape/rules | Evidence provenance and signal completeness | Loaded scrape graph, target and failure time series |
| Service lifecycle | systemd units/targets/restart/timers, Podman Quadlet | Dependency graph / DSM | Cold start, PID readback and functional readiness |
| Linux fidelity | iproute2, netns, tc/netem, containerlab | Differential/causal fault experiments | Independently executed standard-Linux kernel lane |
| Knowledge/architecture | Existing Human/Agent docs | DSM, C4 and Diataxis | Consumer can find owner, task and verification without a second registry |

For an ADMITTED formal LEGO, use the repository Recursive LEGO R2.1 typed
contract (I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold), not a new local
calculus. A concrete mobile example: I is the authorized Tailscale peer and
selected Provider; O is proxied IPv4 traffic and a recorded failure; pre is
approved Exit Node plus healthy provider; inv is no second VPN identity and
no default public direct egress; post is the device's actual public
Surfshark IP or a scoped UNKNOWN; eff is the permitted namespace traffic.
One TCP ping does not discharge the full postcondition.

Human workflow: identify the affected app/device, check the actual public
IP and real request, and consult its consumer task and operator guide.
Agent workflow: identify owner/consumer, SourceCut and accepted assumptions;
select one suitable mature mechanism, independently falsify a negative path,
check source/installed/loaded/consumed, and publish through Git PR + CI.
Do not add a new Network registry, VPN manager or custom DNS watcher.

External references: systemd.unit (freedesktop.org), Tailscale connection
types/exit nodes (tailscale.com), Gluetun native firewall/DNS/health options
(github.com/qdm12/gluetun-wiki), MIT Eppinger/Browning DSM, and Diataxis.
A documentation or model PASS is not evidence that a physical iOS request
used the intended tunnel.

## Namespace ownership before VPN establishment (R8 physical counterexample)

**Hard requirement:** If an approved Tailscale Exit Node forwards a client
request, the Linux kernel must enforce VPN egress or denial, even during
container replacement, early boot, and failed VPN establishment. Provider
service state, a present default route, or an online Tailnet daemon do not
independently prove the requirement.

On 2026-11-11 isolated, credential-free Podman 6.1.1 native experiments
established the useful mechanism and an equally important negative example:

- Podman Pod with --infra=true --share=net --network=none kept the **same
  kernel network namespace inode** while two disposable member containers
  were created and removed in sequence. The Pod infra container, not its
  members, owns the stable namespace. This can reduce future reconnects.
- A separate credential-free Pod with --network=bridge had a normal kernel
  default route **before any Gluetun/WireGuard process existed**, and a
  direct HTTP request from that namespace reached the Internet by the
  host's CN egress. No TUN device, VPN secret or second provider session
  was used. A stable namespace alone therefore does not entail a
  fail-closed Exit Node.

These shadow experiments do **not** imply the existing production Gluetun
kill switch is defective. The current source is deliberately bound to
Network=network-v2-gluetun-owned.network (without Pod=), with Tailnet joined
to the provider-owned disposable namespace. This has a bounded reconnect
window rather than a persistent potentially unsafe pre-WG path. The
consumer:mobile-tailnet-exit:ready owner task composes the existing readiness
checker with GNU timeout to observe native systemd/Tailscale rejoin for up to
120 seconds. It does not change the provider or prove iOS device egress.

An additional Podman 6.1.1 native lifecycle attempt tested the proposed
two-phase alternative: create/start Pod infra with --network=none, install both
IPv4 and IPv6 OUTPUT DROP before attaching any external network, then use
podman network connect podman <infra-container>. The first two phases were
valid, but the last operation returned exit 125, invalid network mode.
Therefore the current platform **cannot claim** that the simpler native
two-phase Pod network-attach sequence is a working migration path. Its
failure is a mechanism counterexample, not an excuse to remove the
pre-VPN fail-closed requirement. The isolated Pod was removed.

A separate recurring operational issue is that merely checking Mobile
readiness and repeatedly hand-installing files obscures *why* a restart is
necessary. The existing owner-native Go Task now exposes sourcecut,
materialize and converge. Sourcecut compares exact installed files and
systemd loaded-unit staleness **without any external probes**. Materialize
only writes on source drift; converge uses systemctl start (a no-op for
active services) when source matches, and reserves a Mobile-only restart
for an explicit opt-in request after source drift and installation.
Readiness is checked separately with the bounded native recovery task.
External DNS/VPN failures alone must never trigger reinstallation.
The change does not add another scheduler or background controller.

Before replacing this topology with a stable Pod, Network's natural Owner
must independently demonstrate all of:

1. Pod-infrastructure-owned **pre-VPN default-deny** kernel egress which
   survives fresh Pod creation and Gluetun member removal/restart; no
   unauthorized direct IPv4/IPv6 TCP, UDP/QUIC or DNS/DoH escape.
2. Bounded provider handshake and control-plane traffic, separated from
   client data-plane forwarding; no host default route accepted as fallback.
3. Source to installed to native Podman/systemd loaded to kernel routing/
   filtering to actual consumer VPN or explicitly denied effects. Exercise
   boot, container replacement, VPN outage, recovery, rollback.
4. Real device-origin iPad/iPhone Exit Node choice, public IP and DNS
   evidence; server READY and aggregate DNS counters are insufficient.

Under Recursive LEGO R2.1, inv means remote-client public traffic never
falls back to direct host egress, while post means a consumer-bound VPN
effect or a witnessed denial, not merely systemctl active. A stable Pod is
**QUALIFIED AS A POSSIBILITY, NOT ADMITTED**; do not mutate the one live
physical VPN because a disposable Pod survived member replacement.

Mature native mechanisms: Podman Pod shared netns/infra
(https://docs.podman.io/en/stable/markdown/podman-pod-create.1.html);
systemd NetworkNamespacePath/JoinsNamespaceOf
(https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html).

## SourceCut is three-valued, not a Boolean permission to mutate (R10)

Native Go Task status is a Boolean skip optimization. Its failure can mean
installed bytes differ **or** a local observation could not be completed.
Therefore a nonzero status alone is not permission to install, reload systemd,
or restart any unit.

The natural Network owners (core, shared-egress, mobile-tailnet-exit) now
expose a **read-only** classify task with three semantic outcomes:

| Outcome | Minimum evidence | Allowed effect |
| --- | --- | --- |
| MATCH | Source and installed bytes agree; owner-specific systemd state agrees | Skip installation; idempotent start only if explicitly requested |
| DRIFT | Observed byte mismatch, missing installed file in accessible parent, or known systemd difference | Admit only natural-owner materialization/reconciliation |
| UNKNOWN | cmp I/O error, source unreadable, failed/unexpected systemd query, or ambiguous symlink | No installation, reload, restart; report failure |

The classifier is executed **again as the first materialization command**
whenever a Boolean status check fails. The caller cannot guess why status
failed. It is a source admission safeguard, not a new transaction manager.
Classifiers have no external DNS/VPN/HTTP health probes. Actual consumer
Readiness is checked afterwards, independently and with a finite window.

Per-file atomic rename does not make a multi-file release crash-atomic.
A failed/uncertain release requires fresh source/install/loaded observation;
durable rollback belongs to existing Runtime/Artifact release capabilities,
not another Network daemon. No success is inferred solely from Task exit code
without verifying actual consumer effects.

## Consumer-owned SourceCut composition (R11)

The same R10 trivalent admission logic extends to the existing Claude,
Finance, Supply Chain, X Reality, Chat Ingress and Browserless owner tasks.
Each retains its previous validate, start, ready, verify, stop and specialized
consumer interfaces; the source/installed/loaded classifier adds a local
admission check, **not** an extra network manager or deploy transaction.

| Task state | Native Go Task action | Owner-side effect |
| --- | --- | --- |
| MATCH | status skips materialize; converge uses idempotent systemctl start | No configuration rewrite, daemon-reload or restart |
| DRIFT | First materialization command reclassifies then proceeds | Only that owner's existing install/reload/restart sequence |
| UNKNOWN | Even --force reaches the rejecting first-command guard | No installed configuration write, service reload or restart |

The shared classifier is scripts/native-sourcecut.py: Python standard library,
stat/SHA-256 and native systemctl, no daemon or network probe. It checks
installed content and expected installed **mode** (0644 normally, 0755 for
the executable ready helpers), rejects symlinks anywhere in the source or
installed parent path, distinguishes missing first-install targets from an
unreadable target, checks retired-file absence, and refuses ambiguous or failed
systemd readbacks. Checkouts may carry different file modes; source executable
permissions are **not** the installed-mode authority.

The Supply Chain materializer cannot start its Browserless dependency before
its own SourceCut has admitted DRIFT. The Browserless owned-mode classifier
combines its own legacy-unit SourceCut with the natural Shared Egress owner's
classifier: both must MATCH for a global MATCH; UNKNOWN on either side blocks
writes, including when the other side has DRIFT. While Gluetun is selected,
all retired legacy provider services must independently be inactive. An
unreadable Gluetun systemd state never admits a second physical WireGuard.

Source-bound Z3 checks nine owner entrypoints (R10's Core/Shared/Mobile plus
these six owners) and proves the two-owner Boolean-OR UNKNOWN counterexample.
Independent real Go Task isolated shadow fixtures cover MATCH/no effect,
systemd observation failure/no effect even with --force, and known source
DRIFT/admitted witness. These prove **selection**, not multi-file crash
atomicity, TOCTOU-freedom between comparison and later install, correct
runtime process configuration, or real iPad/iPhone Exit Node and DNS outcomes.
Use the existing Runtime/Artifact natural owner for any future durable release
bundle. A healthy external endpoint does not replace SourceCut, and a
matching SourceCut does not replace a consumer's real ready/verify.

## Running process is a separate release dimension (R12)

An isolated native Go Task negative control reproduced a **post-install /
pre-restart crash** for all five fixed-configuration sing-box owners (Claude,
Finance, Supply Chain, X Reality, Chat Ingress): all new installed bytes MATCH,
but the old process is still active. The previous converge ran systemctl start,
which does not replace an already active process; a successful Task return was
not proof of a new loaded configuration.

R12 makes two independent, three-valued observations before effects:

| Installed SourceCut | Running process birth-order witness | Allowed effect |
| --- | --- | --- |
| MATCH | MATCH | Idempotent start; no installation or restart |
| MATCH | DRIFT | Owner-only target restart; **no redundant installation** |
| DRIFT | MATCH or DRIFT | Existing owner materialization, local restart, then re-observe both |
| UNKNOWN or other axis UNKNOWN | Any | No installation, restart, or guessed rollback |

The same native sourcecut.py adds the read-only unit-process-file probe.
It uses systemd's existing system D-Bus MainPID and
ExecMainStartTimestamp (realtime microseconds), the /proc/PID/exe device/inode
matching the declared /usr/bin/sing-box executable, and the exact
/proc/PID/cmdline argv suffix matching run -c ABSOLUTE_CONFIG.
The real installed file's mtime/ctime and double-read unit/file identity
reject a stale or changing observation. For these five static
Type=simple sing-box services, a process created
**before** a subsequent installed file metadata change is proven too old;
its owner restart was missed or an independent owner rewrote its config.
The file SourceCut remains separate from this process freshness check.
Malformed systemd replies, changed unit/PID, wrong executable inode,
non-matching complete invocation, symlinks, invalid clock ordering and
unavailable unit identity return UNKNOWN. When an installed config exists
but systemd independently confirms LoadState=not-found, a partially installed
first release returns DRIFT instead of treating the missing service as
an unknowable transport failure.

X Reality previously had no PartOf dependency on its target, so even a
systemctl restart network-v2-x-reality.target could leave its egress service
untouched. R12 binds that service to its natural target using the native
PartOf directive. After each convergence, the owner confirms its sing-box
service is active, rechecks installed SourceCut, and rechecks process
birth order; interrupted work is detectable on the next invocation.

**Evidence scope:** source-bound Z3 proves two-axis effect-selection under
successful-action assumptions and proves the old MATCH/old-process
counterexample. The actual Go Task executable was used for 40 disposable,
credential-free positive/negative owner cases. The systemd D-Bus observation
was read against the five live Linux processes without restarting them.

This is a **restart-loss recovery bound**, not a claim that file birth order
cryptographically proves a process's in-memory config bytes. It assumes
native systemd owns the observed Type=simple main process, sing-box consumes
the named file on startup, and the process/file timestamps share an
unambiguous realtime epoch. Clock steps or metadata manipulation can defeat
a timestamp-only inference; independent application-layer loaded-digest
evidence remains an open requirement. A multi-file crash can still leave
partially installed content until the next safely admitted reconciliation;
durable generation/rollback across /etc/network-v2, /etc/systemd/system and
/usr/local/libexec needs an independently qualified Runtime/Artifact or
OS-native generation owner, not a Network-only transaction daemon. The
current Runtime structured release interface is for Runtime self-release,
not a generic Network publish permission.

Upstream native authorities:
- https://freedesktop.org/software/systemd/man/latest/org.freedesktop.systemd1.html
- https://freedesktop.org/software/systemd/man/latest/systemd.unit.html
- https://www.freedesktop.org/software/systemd/man/latest/systemctl.html
- https://nix.dev/manual/nix/2.34/package-management/profiles

## Classification rules

```text
requires_udp_or_full_ip
  → choose TUN/netns, not HTTP CONNECT

requires_encrypted_tunnel
  → choose WireGuard

requires_ordered_primary_backup
  → choose HAProxy

requires_dns_redundancy
  → choose dnsproxy parallel upstreams

requires_l4_fault
  → choose Toxiproxy

requires_packet_impairment
  → require netem-capable Linux

requires_topology_lab
  → require containerlab/reference Linux
```

Consumer policies belong under `consumers/`; provider material belongs under `providers/`. They may compose generic mechanisms but must not redefine generic Network behavior.

Consumer-specific migration may observe active workload state to avoid disrupting a live effect, but it must not make consumer service lifecycle part of Network acceptance.
