# Supply-Chain consumer network profile

This consumer owns bounded HTTPS transport for OCI/container supply-chain acquisition. It does not own a VPN identity.

The sole host authority remains `127.0.0.1:19581`. Exact Docker Hub, Docker blob CDN, Google Container/Artifact Registry, and Elastic registry fencing remains in the Supply-Chain sing-box process. Its only outbound is the shared Network v2 provider carrier at `10.252.246.2:19680`, which runs inside `nv2-browserless-prod` over the single admitted Surfshark WireGuard identity. Unknown destinations are rejected and there is no direct fallback. TLS remains end-to-end between the OCI client and registry/CDN.

Docker's official 2026-05-20 Docker Hub release identifies
production.cloudfront.docker.com as an image-layer CDN alongside
production.cloudflare.docker.com. Both exact domains are admitted only
at HTTPS port 443 (not a wildcard for all docker.com).
Official evidence: https://docs.docker.com/docker-hub/release-notes/ .
The source unit now depends on selected
network-v2-gluetun-owned-adapter.service instead of the inactive
legacy Browserless Carrier. Authority metadata no longer encodes the
retired fixed th-bkk providerSite.

This removes the former Supply-Chain `provider-endpoints.json`, URLTest and duplicated provider-DNS/WireGuard ownership. The physical carrier is shared; Supply-Chain semantic authority is not.

Routine `consumer:supply-chain:verify` checks live scoped network behavior and Docker proxy binding, not whether a historical OPA image happens to be cached. The pinned OPA Docker pull belongs only to explicit `consumer:supply-chain:docker-rebind` recovery acceptance, where it exercises an actual image pull rather than inferring transport health from local cache.

Docker daemon binding remains source-owned by `systemd/docker.service.d/ordivon-network-v2-supply-chain-proxy.conf`. Docker restart is intentionally separated into `acceptance/docker-rebind-smoke.sh`; it verifies restart-policy recovery and the pinned OPA image pull.


## Provider-native denial witness

`consumer:supply-chain:ready` establishes **positive OCI HTTPS transport**
only. It explicitly reports `unknownDestination=NOT_EVALUATED` and
`directFallback=NOT_EVALUATED`. The upstream native sing-box reject action
may return CONNECT=200 and then close the connection, so a CONNECT=403 gate
was a false-negative and is no longer an acceptance requirement.

`consumer:supply-chain:verify` now composes positive transport with the
existing `acceptance/egress/live-carrier-witness.py --consumers supply-chain`
against the **installed** source-matched policy and actual shared Carrier.
It observes allowed CONNECT reaching the upstream and denied hostname,
wrong-port, IPv4 and IPv6 literals **not** reaching the upstream, with a
failed client-origin effect. Failure to capture the packet witness is not PASS.
This remains sampled HTTPS/CONNECT evidence, not universal DNS/UDP/IPv6,
application-process binding, or financial authority proof.

The upstream spy negative-control suite is
`tests/test_egress_routing_behavior.py`. It deliberately removes the
terminal reject in a disposable copy to demonstrate an observable forbidden
forward. Do not replace that with a curl status-only heuristic.
