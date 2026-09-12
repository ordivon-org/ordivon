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
