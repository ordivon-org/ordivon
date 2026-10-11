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
