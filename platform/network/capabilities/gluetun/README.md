# Gluetun capability

This capability tracks and qualifies the upstream Gluetun mechanism as a potential physical provider-carrier realization.

It does not own Ordivon consumer policy, ClientIdentity authority, ProviderProfile semantics, production effect admission, or consequence readiness.

## R1 standing

- Upstream: https://github.com/passteque/gluetun.git
- Candidate: v3.41.3
- Exact revision: 3d1e20c5551e9cae1f9d938dc7b7214a6987f27e
- Production authority: none
- Activation mode with current Surfshark Linux identity: serialized-only

The first acceptance lane is source-only. It proves that the pinned upstream revision is fetchable and has the expected source entrypoints. It does not inspect protected provider material or start a VPN.


## R1 compatibility topology

The R1 source candidate keeps the existing consumer endpoint 10.252.246.2:19680 and uses sing-box only as a compatibility adapter. Its only candidate outbound is an HTTP proxy at host-veth 10.252.246.1:19682, where a future serialized Gluetun container can expose its upstream HTTP proxy.

The candidate OCI artifact is pinned separately in external/gluetun-image.lock. The non-secret runtime knobs are in config/serialized-candidate.env. Provider identity material is intentionally absent.

A live Gluetun container is not yet admitted. The current legacy WireGuard realization remains active.


## Pre-review hardening

The candidate realization is bound to the immutable OCI lock as well as the source lock. The non-secret runtime contract disables Gluetun public-IP discovery and binds its HTTP control server to container loopback.

The compatibility-hop script is a read-only currentness preflight only. It validates the existing namespace-to-host-veth route, candidate configuration syntax, and candidate proxy port vacancy. It starts no listener and explicitly does not claim two-hop execution proof.

## R1 source-only port and proxy evidence — 2026-10-14

The previous source candidate exposed the Gluetun HTTP proxy at container
`:8888` and pointed the sing-box compatibility HTTP outbound to host-veth
`10.252.246.1:19682`, but lacked a materialized port-publication contract.

Source-only Quadlet candidate:
`quadlet-candidate/gluetun-serialized-candidate.container`.
Its exact `PublishPort=10.252.246.1:19682:8888/tcp` binds the host-veth
listener, NOT all host interfaces, and `FIREWALL_INPUT_PORTS=8888`
permits container-side ingress. The candidate uses upstream Podman
`Network=bridge`, not a custom network or a second alias named
`nv2-browserless-prod`; `Pull=never` and the pinned amd64 OCI digest
remove mutable-tag fallback. The candidate has NO `[Install]` section
and is not included in Network-v2 install/converge tasks. Its protected
WireGuard profile is a **read-only external bind** (never checked into Git).
These declarations do not authorize container startup or concurrent use
of the existing single-session Surfshark identity.

The Podman Quadlet system generator validates `--publish
10.252.246.1:19682:8888/tcp` in **dryrun** (no listener or container).
The offline two-hop fixture is run with:

`python3 capabilities/gluetun/acceptance/isolated-two-hop-fixture.py`

It runs a **real sing-box process** under a temporary loopback-only
candidate config, followed by a local HTTP CONNECT proxy fixture. It
proves an HTTP response traverses those two local proxies and a private
destination cannot reach the fixture. No Gluetun process, provider identity,
production namespace, Podman container, network route, or existing service is
used. Its result `twoHopExecutionProven=true` is deliberately qualified
by `transport=real-sing-box-loopback-httpproxy-fixture`, alongside
`gluetunContainerPortProven=false` and
`gluetunFirewallRuntimeProven=false`.

Missing evidence before M3B: runtime container port publication, Gluetun
own firewall actual ingress, real VPN forwarding/kill-switch behavior,
effect admission/current workload drain, and independent owner consequence
parity. **M3B remains HOLD.**
