# Consumers

Consumer-specific destination policy, fail-closed semantics, shadow topology and migration evidence live here. A consumer profile is not part of generic Network graduation and does not receive production authority merely by existing in this repository.

- `browserless/`: serialized differential migration gate for real Browserless Chromium over a v2-owned provider namespace; endpoint discovery remains a separate provider concern.
- `supply-chain/`: dual-provider, destination-fenced OCI/container registry authority for Docker Hub, Google registries and currently consumed Elastic registry traffic; Docker daemon binding is explicit and fail-closed.


## Shared provider egress

Provider-bound consumers compose the semantic provider-egress authority. The current physical
realization still uses the historical Browserless namespace and service names for compatibility.
Those physical identifiers are not consumer-policy authority and must not be used to infer that
Browserless owns Claude, Finance, Supply-Chain, ChatIngress, X Reality, or future consumers.
