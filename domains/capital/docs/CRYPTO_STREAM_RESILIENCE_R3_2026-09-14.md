# Crypto Stream Resilience R3

## Current standing

`PASS_DUAL_VENUE_PUBLIC_STREAM_RECONNECT_WITH_FAILOVER`

R3 adds fail-closed public-stream health semantics and a real reconnect qualification harness without changing any private/demo/live authority boundary.

### Local fault semantics

The public observation plane blocks cross-venue use when any required BTC/ETH stream is missing, when any stream exceeds the 5000 ms monotonic receive-age limit, or when the four-stream source/receive spans exceed the existing 1200 ms coherence limits.

### Reconnect qualification

The reconnect harness supports independent injected disconnects for both OKX and Binance. A venue passes only after a fresh connection generation is established, both BTC and ETH are observed on that new generation, a coherent recovery snapshot passes the unchanged R2 span limits, and three subsequent measured snapshots pass.

The first live R3 campaign was blocked before workload by an unrelated Surfpath physical-mutation owner; unrelated work was preserved and one Market Capital-owned timed-out orphan unit was cleaned. After the Surfpath owner released naturally, R3 was rerun from a fresh discovery and graduated on `hk-hkg / openvpn-udp / native-a`.

OKX was deliberately disconnected and reconnected as connection generation 2 in 1362.5 ms. Its recovery snapshot passed with 790 ms source-time span and 770.1 ms monotonic receive-time span; all three post-recovery measured snapshots passed. Binance was independently disconnected and reconnected as generation 2 in 1556.5 ms. Its recovery snapshot passed with 322 ms source-time span and 322.7 ms receive-time span; all three post-recovery measured snapshots passed. The frozen 1200 ms coherence gates were not changed.

## Observability

Market Capital exports canonical evidence state through Prometheus textfile format into the existing Operations-v2 node exporter and shared Prometheus/Grafana stack. No second monitoring stack or new network listener is introduced.

The `private_execution_allowed` metric is conjunctive: external financial-write authority must be admitted, a production grant mechanism must exist, and the clock gate must independently pass. At the current standing all remain fail-closed.

Canonical Prometheus rules are kept in `infra/prometheus/market-capital-crypto.rules.yml`. The minimal alerts cover loss of qualified public streaming, any observed external financial-write attempt, and host clock offset above the frozen 1000 ms private-execution gate. R3 reconnect graduation and Surfpath contention remain dashboard/state signals rather than paging alerts; the successful rerun projects reconnect qualification as healthy and Surfpath contention as clear.
