# Ordivon Network v2

Greenfield network substrate built from mature external projects. It has zero runtime or source dependency on the legacy Ordivon network stack.

## Rules

1. External implementation first; configuration before code.
2. No import, schema, state, service-name, port, or compatibility dependency on legacy Network.
3. Tests precede Ordivon-specific abstraction.
4. Production data plane and test/observation planes stay separable.
5. New custom network daemons are forbidden in R0.
6. Unsupported host capabilities are recorded, not hidden behind compatibility shims.

## R0 local candidate

- sing-box — data plane
- AdGuard dnsproxy — DNS carrier
- blackbox_exporter — black-box measurement
- Prometheus — evidence time series
- Toxiproxy — deterministic L4 fault injection
- Linux network namespaces + veth — local controlled topology
- iperf3, curl, mtr, tcpdump — measurement/diagnostics
- bpftrace — deep forensic tool

## Reference full-fidelity lab

A later standard-Linux runner will test containerlab + Docker + tc/netem. No unvalidated containerlab/Docker configuration is shipped in R0 because this WSL2 kernel cannot satisfy those kernel requirements.

## Acceptance path

`syntax -> isolated smoke -> observation -> L4 fault injection -> controlled topology/performance -> recovery -> full-fidelity Linux lab -> provider paths -> soak -> reboot -> independent falsification`.

Legacy migration is explicitly out of scope until the new stack independently graduates.

## R4 provider priority failover candidate

R4 keeps provider ownership outside Network v2. sing-box remains the HTTP CONNECT carrier on each physical path, while HAProxy TCP mode owns only deterministic primary/backup selection. The provider carrier is the normal server; native direct is a `backup` server. Active TCP checks issue a CONNECT to a public HTTPS target through each carrier, so a listening-but-unusable carrier is not counted healthy. Stopping only the temporary provider carrier proves failover to direct; restoring the same carrier and passing the configured rise threshold proves failback to provider.

An earlier live POC used sing-box `urltest` and did prove failover/failback in one observation window. R4 intentionally does not productize that mechanism because URLTest is latency selection, not a stable provider-primary/direct-backup policy: during canonicalization it failed over correctly but legitimately stayed on the lower-latency direct path after provider recovery. The migration therefore replaces policy mechanics instead of wrapping that semantic mismatch in custom code.

This is canonical acceptance equipment, not consumer authority and not a production provider controller. It does not modify provider namespaces, machine default routing, system proxy state, Cloudflare control-plane ingress, or Runtime/Host MCP listeners. See `docs/FAILOVER_R4.md`.

## R5 first-consumer differential

The first real consumer chosen for migration is the read-only `finance-okx` public-time path. A temporary differential harness compared the current production proxy with a Network v2 composition over the same two provider namespaces and preserved the consumer's actual policy: two provider paths only, current production member as primary, the other provider as backup, no direct fallback, exact CONNECT destination `openapi.okx.com:443`, and fail-closed behavior when both providers are unavailable.

The differential passed twice independently while the legacy production listeners and processes remained unchanged and Cloudflare/Runtime control-plane guards stayed green. The temporary harness intentionally is **not** part of this repository because it consumed legacy `/run/ordivon` state only to bind the comparison to the same physical providers. Shipping that dependency would violate Network v2's greenfield boundary. See `docs/FINANCE_OKX_R5.md`.

## R6 independent dual-provider authority

R6 removes the legacy provider-runtime dependency for the read-only `finance-okx` candidate. Provider endpoint/public-key authority now comes from the pinned Gluetun Surfshark server catalog, standard v2-owned Surfshark WireGuard configurations remain the credential authority, `yq` materializes root-only static numeric-endpoint `wg-quick` profiles, and the pinned official `wireguard-go` supplies the WSL userspace tunnel implementation.

For the provider-only Finance policy, sing-box now owns the remaining transport semantics: provider DNS inside each tunnel namespace, exact `openapi.okx.com:443` admission, two-provider URLTest health/selection, local API observation, and all-provider fail-closed behavior with no direct fallback. This does not conflict with R4: R4 required deterministic `provider -> direct` priority/failback, while R6 contains only equally eligible admitted provider paths.

The final destructive acceptance proved independent Seoul + Bangkok WireGuard admission, one-provider survival in both directions, recovery, all-provider fail-closed behavior, and destination rejection. Runtime/Cloudflare control-plane services and legacy Finance listeners remained unchanged. R6 therefore graduates provider independence but **does not authorize production cutover**. See `docs/PROVIDER_R6.md` and `evidence/acceptance/provider-r6-20260912.json`.

## R7 persistent finance-okx shadow

R7 converts the graduated R6 provider composition into an independently owned, non-production systemd shadow at `127.0.0.1:19283` with sing-box API observation at `127.0.0.1:19289`. systemd owns namespace, WireGuard, carrier, and root-shadow lifecycle; `wg-quick` + pinned official `wireguard-go` own the tunnels; sing-box owns provider transport, URLTest health/selection, exact OKX destination fencing, and fail-closed behavior. No new persistent Ordivon controller is introduced.

Shadow startup validates the already-graduated local R6 inputs by exact version/digest/manifest and does not fetch upstream sources. A falsification run also confirmed that `systemd active` is not sufficient readiness evidence: the final gate waits for a real OKX application response and sing-box API readiness before destructive tests. Canonical `task test:r7` proved B-down/A-survival, B recovery, A-down/B-survival, all-provider fail-closed, recovery from all-down, root shadow restart recovery, and non-interference with legacy Finance plus Runtime/Cloudflare.

The shadow remains active but explicitly disabled at boot, while production authority stays on legacy `19083/19084/19085`. R7 therefore graduates the persistent shadow but **does not authorize production cutover**. See `docs/FINANCE_OKX_R7.md` and `evidence/acceptance/finance-okx-r7-20260912.json`.

## R9 generic Network platform graduation

R9 graduates the generic Network v2 platform on the current WSL execution environment independently of any Finance or other consumer migration. R0 is now dual-stack: dnsproxy carries both A and AAAA, sing-box uses a normal `prefer_ipv6` strategy instead of an artificial IPv4-only policy, and Blackbox/Prometheus independently observe HTTP IPv4, HTTP IPv6, DNS A, DNS AAAA, and the sing-box TCP listener.

The acceptance surface now rejects small-request false greens. `task test:r9` proves forced IPv4 and forced IPv6 HTTPS, normal dual-stack operation, four concurrent connections, a 5 MB isolated long flow, exact live materialization, a whole-platform cold stop/start, a 1 MB post-cold-start long flow, and automatic sing-box process recovery. Generic R0 lifecycle is owned by one `network-v2-r0.target`; only that target is enabled at boot, while dnsproxy/sing-box/blackbox/Prometheus are individually disabled and bound to the target.

The current WSL kernel still does not provide the `netem` qdisc (`Specified qdisc kind is unknown`). Network v2 records that as a platform capability boundary instead of adding a compatibility shim. Packet-level netem, containerlab, and kernel-WireGuard differential acceptance remain standard-Linux reference-runner gates. An actual machine reboot is also intentionally not claimed from inside the active Runtime/Cloudflare control-plane session.

Standing: **generic Network v2 on the current WSL platform is PASSED**. Consumer migration remains separate. See `docs/PLATFORM_R9.md` and `evidence/acceptance/network-r9-20260912.json`.

## R11 protocol divergence and isolated UDP/QUIC

R11 hardens the graduated generic platform against protocol-specific false greens without changing live R0 routing. The live loopback mixed proxy now has explicit acceptance for HTTP/1.1, HTTP/2, DNS over UDP and TCP, five-sample stable public egress identity, and three repeated 5 MB transfers.

UDP/QUIC is expressed with a mature sing-box TUN inbound confined to a temporary Linux network namespace rather than a host-wide TUN. Canonical `task test:r11` proved HTTP/3 over that isolated TUN plus ordinary TCP through the same path, then verified that the transient namespace/TUN was removed, host default routes were unchanged, live R0 remained green, and Runtime/Cloudflare remained independent.

The default platform policy therefore stays conservative: loopback mixed proxy for normal live TCP workloads; isolated netns TUN on demand for UDP/QUIC/full-IP workloads. Host-wide default-route takeover is not part of Network v2. See `docs/PROTOCOL_R11.md` and `evidence/acceptance/network-r11-20260912.json`.

## R12 local resilience and WSL reboot recovery

R12 closes the remaining local resilience false-green classes without changing live R0. Deterministic local tests prove bidirectional address-family fallback (`prefer_ipv6` to IPv4 and `prefer_ipv4` to IPv6), DNS parallel-upstream survival when one peer is dead, fail-closed `SERVFAIL` behavior for uncached/expired names when all upstreams are unavailable, and recovery when an upstream returns without restarting dnsproxy.

During this work a real WSL boot boundary occurred independently. The previous R0 target stopped cleanly, and on the next WSL boot `network-v2-r0.target` plus dnsproxy, sing-box, blackbox_exporter and Prometheus automatically returned under the target-owned lifecycle. A full `task verify:live` passed after boot. This upgrades the lifecycle standing from cold-start simulation to **real WSL instance reboot recovery**. It does not claim Windows physical-host reboot plus WSL auto-launch, which is a Workstation/bootstrap concern.

Standing after R12: **generic Network v2 on the current WSL platform is locally graduated for data plane, dual stack, DNS, observability, protocol divergence, UDP/QUIC isolation, failure/recovery, and WSL reboot recovery**. Remaining Network fidelity gates require a standard Linux environment: `tc/netem`, containerlab, and kernel-WireGuard differential. See `docs/RESILIENCE_R12.md` and `evidence/acceptance/network-r12-20260912.json`.
