# Crypto Stream Resilience R3

## Current standing

`BLOCKED_SURFPATH_CONTROL_PLANE_CONTENTION`

R3 adds fail-closed public-stream health semantics and a real reconnect qualification harness without changing any private/demo/live authority boundary.

### Local fault semantics

The public observation plane blocks cross-venue use when any required BTC/ETH stream is missing, when any stream exceeds the 5000 ms monotonic receive-age limit, or when the four-stream source/receive spans exceed the existing 1200 ms coherence limits.

### Reconnect qualification

The reconnect harness supports independent injected disconnects for both OKX and Binance. A venue passes only after a fresh connection generation is established, both BTC and ETH are observed on that new generation, a coherent recovery snapshot passes the unchanged R2 span limits, and three subsequent measured snapshots pass.

The first live R3 campaign did not reach this workload: fresh Surfpath discovery was serialized behind an existing global physical-mutation owner. Unrelated active Surfpath work was left untouched. One Market Capital-owned timed-out orphan transient unit was cleaned. Therefore live reconnect qualification remains false rather than being inferred from implementation or local tests.

## Observability

Market Capital exports canonical evidence state through Prometheus textfile format into the existing Operations-v2 node exporter and shared Prometheus/Grafana stack. No second monitoring stack or new network listener is introduced.

The `private_execution_allowed` metric is conjunctive: external financial-write authority must be admitted, a production grant mechanism must exist, and the clock gate must independently pass. At the current standing all remain fail-closed.

Canonical Prometheus rules are kept in `infra/prometheus/market-capital-crypto.rules.yml`. The minimal alerts cover loss of qualified public streaming, any observed external financial-write attempt, and host clock offset above the frozen 1000 ms private-execution gate. R3 reconnect non-graduation and Surfpath contention remain dashboard/state signals rather than paging alerts.
