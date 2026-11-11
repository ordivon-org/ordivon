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
