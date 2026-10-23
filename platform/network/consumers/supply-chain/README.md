# Supply-Chain consumer network profile

This consumer owns bounded HTTPS transport for OCI/container supply-chain acquisition. It does not own a VPN identity.

The sole host authority remains `127.0.0.1:19581`. Exact Docker Hub, Docker blob CDN, Google Container/Artifact Registry, and Elastic registry fencing remains in the Supply-Chain sing-box process. Its only outbound is the shared Network v2 provider carrier at `10.252.246.2:19680`, which runs inside `nv2-browserless-prod` over the single admitted Surfshark WireGuard identity. Unknown destinations are rejected and there is no direct fallback. TLS remains end-to-end between the OCI client and registry/CDN.

This removes the former Supply-Chain `provider-endpoints.json`, URLTest and duplicated provider-DNS/WireGuard ownership. The physical carrier is shared; Supply-Chain semantic authority is not.

Docker daemon binding remains source-owned by `systemd/docker.service.d/ordivon-network-v2-supply-chain-proxy.conf`. Docker restart is intentionally separated into `acceptance/docker-rebind-smoke.sh`; it verifies restart-policy recovery and the pinned OPA image pull.
