# Consumers

Consumer-specific destination policy, fail-closed semantics, shadow topology and migration evidence live here. A consumer profile is not part of generic Network graduation and does not receive production authority merely by existing in this repository.

- `browserless/`: serialized differential migration gate for real Browserless Chromium over a v2-owned provider namespace; endpoint discovery remains a separate provider concern.
- `supply-chain/`: dual-provider, destination-fenced OCI/container registry authority for Docker Hub, Google registries and currently consumed Elastic registry traffic; Docker daemon binding is explicit and fail-closed.
Consumer source and deployed runtime must be checked independently.
Current consumer folders include Codex, Mobile Tailnet Exit, Claude,
Model Provider, Discord, Windows Real Chrome, Finance, Browserless,
Supply Chain, X Reality, Chat Ingress and Developer Egress. The physical
Gluetun WireGuard identity belongs only to providers/gluetun.
