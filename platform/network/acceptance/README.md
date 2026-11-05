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

- `egress/` — opt-in live NS2 witness: real installed config byte equality,
  per-consumer positive/negative HTTP CONNECT observed independently on host
  and provider namespace, bounded by time and exact provider/process PID.
  Run `mise run behavior-live` as an eligible local Network operator.
  No raw capture files are retained. This proves only sampled IPv4 HTTPS
  Carrier forwarding, not all possible DNS, IPv6 or direct paths.
