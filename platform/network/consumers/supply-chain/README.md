# Supply-Chain consumer network profile

This consumer owns bounded HTTPS transport for OCI/container supply-chain acquisition. It does not own a VPN identity.

The sole host authority remains `127.0.0.1:19581`. Exact Docker Hub, Docker blob CDN, Google Container/Artifact Registry, and Elastic registry fencing remains in the Supply-Chain sing-box process. Its only outbound is the shared Network v2 provider carrier at `10.252.246.2:19680`, which runs inside `nv2-browserless-prod` over the single admitted Surfshark WireGuard identity. Unknown destinations are rejected and there is no direct fallback. TLS remains end-to-end between the OCI client and registry/CDN.

This removes the former Supply-Chain `provider-endpoints.json`, URLTest and duplicated provider-DNS/WireGuard ownership. The physical carrier is shared; Supply-Chain semantic authority is not.

Docker daemon binding remains source-owned by `systemd/docker.service.d/ordivon-network-v2-supply-chain-proxy.conf`. Docker restart is intentionally separated into `acceptance/docker-rebind-smoke.sh`; it verifies restart-policy recovery and the pinned OPA image pull.


## Provider-native denial witness and current READY limitation

The current ready.sh demands an explicit HTTP-proxy CONNECT=403 receipt
for an unknown destination before emitting READY. That is a **sufficient
source-specific signal**, not the only way sing-box can enforce a route
reject. The checked native sing-box 1.14.3 in the Network owner isolated
spy fixture can send CONNECT=200 and then terminate the TLS stream
(curl exit 35, origin HTTP 000), while the independent upstream spy sees
no forbidden request. Disabling the terminal reject makes the upstream
spy observe the forwarded request.

Evidence: platform/network/tests/test_egress_routing_behavior.py,
especially test_native_reject_has_no_upstream_effect_even_with_connect_200
and test_terminal_reject_negative_control_is_observable.

Do **not** weaken READY to accept arbitrary CONNECT=200, TLS failure or
curl exit codes: those also arise from real outages and failed proxies.
The source-only READY contract may therefore false-negative on the
installed Provider until a production-compatible, source-bound
independent no-upstream-effect witness is available. Exact deployed
policy/config identity and actual live upstream behavior are still
UNKNOWN. Network NS2 is not fully verified. Formal PR #698 was closed
after this concrete CEGAR counterexample; no erroneous model was merged.
