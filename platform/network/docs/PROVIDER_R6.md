# R6 — Independent Dual-Provider Authority and Fail-Closed Consumer Path

Date: 2026-09-12

## Scope

R6 closes the provider-authority dependency that remained after the R5 `finance-okx` differential. Network v2 can now construct and validate two Surfshark WireGuard provider paths without reading legacy Workstation runtime state, while preserving the read-only Finance policy:

- only provider-backed paths are eligible;
- the admitted consumer destination is exactly `openapi.okx.com:443`;
- loss of one provider continues through the other provider;
- loss of all providers fails closed;
- there is no native/direct fallback;
- provider recovery is detected by the mature path-selection layer.

R6 does **not** authorize production cutover and does not change ports `19083`, `19084`, or `19085`.

## External composition

R6 deliberately reduces custom mechanics instead of extending the earlier temporary harness.

### Provider server authority — Gluetun server catalog

The Surfshark server catalog is pinned from `qdm12/gluetun-servers`:

- tag: `v0.2.0`;
- revision: `0c7381faba8b0ef5d59caec11eae7ef629f6b4c9`;
- file: `pkg/servers/surfshark.json`;
- SHA-256: `aa2d6ecf9f851964d3e5a96f4ae9b08ae178103b0ada15f56652946bcae50ec7`.

The catalog supplies Surfshark WireGuard records including hostname, endpoint IP set, and WireGuard public key. R6 cross-checks the catalog public key against the v2-owned standard Surfshark WireGuard configuration before an endpoint can be admitted.

The admitted catalog records used in the final acceptance included:

- Seoul / `kr-seo.prod.surfshark.com`: `61.97.243.107`, `61.97.244.82`, `61.97.248.26`, `172.216.251.17`;
- Bangkok / `th-bkk.prod.surfshark.com`: `151.240.88.133`, `151.240.88.147`.

### Credential/config authority — standard Surfshark WireGuard configuration

Credentials remain outside Git in root-owned provider files under `/etc/network-v2/providers/`. Private keys are never emitted into repository files or evidence.

Network v2 does not implement a WireGuard configuration parser or provider controller. `yq`'s INI support performs one-time materialization of static candidate profiles from the standard provider configuration plus the pinned Gluetun endpoint IPs.

The materialized profile changes are intentionally narrow:

- remove `DNS` from `wg-quick` ownership because provider DNS is owned by sing-box;
- set `Table = off` so WSL does not invoke unsupported full-tunnel nftables policy;
- set `MTU = 1280`;
- replace hostname `Endpoint` with one catalog numeric endpoint.

Each candidate profile is `0600`, remains outside Git, and is validated with `wg-quick strip` before use.

### WireGuard lifecycle — upstream tools

- `wg-quick` owns interface lifecycle;
- pinned official `wireguard-go` supplies the userspace WireGuard implementation on this WSL kernel;
- Linux network namespaces and veth links provide isolated acceptance topology.

No `wg set ... endpoint` controller remains in R6. Each candidate is a complete static profile handed directly to `wg-quick`.

### Provider carrier, health, selection, and policy — sing-box

Each provider namespace runs the same static `config/provider-carrier.json`:

- provider DNS is explicit;
- private destinations and IPv6 are rejected;
- the HTTP carrier is only a transport surface over the already-admitted provider tunnel.

The root `config/finance-okx-singbox.json` owns:

- the exact `openapi.okx.com:443` destination fence;
- two provider HTTP outbounds;
- a `urltest` group over those two provider outbounds;
- no direct/native outbound;
- local sing-box API observation.

This removes the R5 temporary HAProxy health/state machinery from the provider-only Finance candidate.

## Why R6 uses URLTest although R4 did not

R4 demonstrated a different policy: **provider primary -> native direct backup**. That policy required deterministic priority and failback to the provider even when native direct was faster, so sing-box URLTest was semantically wrong for R4.

R6 has two members of the **same policy class**: both are admitted VPN providers and no direct path is eligible. Finance only requires that an available admitted provider carry the request and that all-provider loss fail closed. Latency-based URLTest selection is therefore compatible with R6 semantics and removes a custom health/priority layer.

## Hostname/NSS finding

R6 explicitly does not trust ambient hostname resolution for Surfshark WireGuard endpoints on this WSL host.

The host `nsswitch.conf` orders `resolve [!UNAVAIL=return]` before `files`. During a focused test, `kr-seo.prod.surfshark.com` resolved to `108.160.169.174` even when the namespace-specific hosts file contained the catalog IP `61.97.243.107`; `wg show endpoints` confirmed that WireGuard received the incorrect `108.160.169.174:51820` endpoint and no handshake occurred.

R6 therefore does not modify global NSS configuration and does not wrap this behavior with custom DNS code. It uses pinned Gluetun numeric endpoint records to materialize static `wg-quick` profiles.

## Final acceptance

Canonical repository-level acceptance was replayed through `task test:r6`, including exact external fetches, digest verification, provider-profile materialization, validation, and destructive dual-provider acceptance:

- Job: `job-01a094e4-46d1-7381-ad35-4c77d4847805`;
- operation digest: `sha256:99b16f3dbb4688bb061d0813bbeced3f05614c2744fdd21162cf4f0f28ee4993`;
- stdout artifact digest: `sha256:d240772e9660e7168c7da766efc50c763f8f58baffe0e1d3b3cb5129a23528a6`;
- terminal evidence digest: `sha256:f0a5bafb20f5c4ccb1e1e119954ec3a9e2aa6cbb08eee9890617fff327d19614`.

Observed provider admission:

- provider A: `kr-seo`, endpoint `61.97.243.107`, successful WireGuard handshake;
- provider B: `th-bkk`, endpoint `151.240.88.133`, successful WireGuard handshake.

Observed consumer sequence:

1. both providers healthy: OKX application request succeeded;
2. provider B down: provider A continued serving OKX;
3. provider B recovered: both providers returned to the URLTest set;
4. provider A down: provider B continued serving OKX;
5. both providers down: request failed closed, curl rc `35`;
6. provider A recovered from all-down: OKX request succeeded again;
7. non-OKX CONNECT was rejected, curl rc `35`.

The sing-box API independently showed both provider delay values as `-` when both providers were down. Functional failure and the mature tool's group observation therefore agreed.

## Control-plane and legacy-production non-interference

Post-replay read-only check Job: `job-01a094e5-b2d2-7130-a54c-886201d11fa4`.

Observed after cleanup:

- `ordivon-runtime.service`: active, listener `127.0.0.1:8897`;
- Cloudflare production A: active, HA connections `4`;
- Cloudflare production B: active, HA connections `4`;
- Cloudflare canary: active, HA connections `4`;
- Cloudflare direct-route service: active;
- Finance legacy listeners `19083`, `19084`, `19085`: still present;
- legacy Finance services: active;
- all temporary R6 units: inactive;
- temporary R6 network namespaces: none.

This preserves the migration invariant that the Runtime/Cloudflare control plane must remain independent of the Network v2 data plane.

## Reproducible entry point

The repository now expresses the external composition through Taskfile tasks:

```text
task external:gluetun-servers
  -> fetch exact pinned catalog revision
  -> verify SHA-256
  -> install public server catalog

task materialize:provider-profiles
  -> yq INI transform of v2-owned standard provider configs
  -> static numeric endpoint profiles, mode 0600
  -> MANIFEST.tsv with endpoint/profile/digest mapping

task test:r6
  -> validate static sing-box configs
  -> ensure pinned official wireguard-go
  -> materialize provider profiles
  -> run dual-provider destructive acceptance
```

No provider credential is committed by these tasks.

## Standing

**R6 provider authority independence on the local WSL platform: PASSED.**

What this closes:

- legacy provider runtime-state dependency;
- custom DoH endpoint candidate collector;
- Python runtime WireGuard config renderer;
- runtime `wg set ... endpoint` mutation;
- custom HAProxy provider health/state layer for the Finance provider-only policy;
- ambient provider-hostname resolution dependency.

What remains before production cutover:

1. create an independently owned Network v2 shadow service from the R6 composition;
2. run repeated/soak differential checks against the current `19083` Finance consumer path;
3. prove service restart and host reboot recovery;
4. run the standard-Linux kernel-WireGuard/Gluetun/containerlab differential path;
5. perform a make-before-break consumer cutover while the Cloudflare/Runtime control-plane DO-NOT-CUT set remains protected;
6. only after zero legacy consumers remain, retire replaced legacy Finance/network mechanics.

R6 is therefore a provider-independence graduation, **not** a production-cutover authorization.
