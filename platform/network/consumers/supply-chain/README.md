# Supply-Chain consumer network profile

This consumer owns bounded HTTPS transport for OCI/container supply-chain acquisition. It removes Docker/OCI verification from historical ad-hoc proxy carriers without turning Finance, ChatIngress, or Browserless into generic mega-proxies.

The data plane reuses the graduated Surfshark provider owner exactly as Finance does: protected provider profiles under `/etc/network-v2/providers/` are compiled at materialization into two sing-box WireGuard Endpoints, `provider-auto` performs URLTest selection, and the two Surfshark DNS resolvers are response-raced through the selected provider. Provider secrets remain outside Git.

The sole host proxy is `127.0.0.1:19581`. It accepts TCP/443 only for the declared Docker Hub, Docker blob CDN, Google Container/Artifact Registry, and currently consumed Elastic registry families. Unknown destinations are rejected and there is no direct fallback. TLS remains end-to-end between the OCI client and registry/CDN.

Docker daemon binding is source-owned by `systemd/docker.service.d/ordivon-network-v2-supply-chain-proxy.conf`. Materialization removes the retired `ordivon-preservation-vpn-proxy.conf`. Docker restart is intentionally separated into `acceptance/docker-rebind-smoke.sh`; it fails before restart if any currently running container lacks an automatic restart policy, then proves all previously-running containers return and the pinned OPA image can be pulled.
