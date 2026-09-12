# Generic acceptance

Acceptance is organized by network capability, not by historical round.

- `connectivity/` — direct dual-stack path and address-family fallback
- `dns/` — upstream failure/cache/recovery semantics
- `protocol/` — HTTP versions, DNS transports, egress identity and long flow
- `full-ip/` — isolated TUN TCP/UDP/QUIC
- `observability/` — Blackbox and Prometheus evidence
- `fault/` — deterministic L4 faults
- `topology/` — namespace/veth topology
- `lifecycle/` — process recovery and whole-platform cold start
