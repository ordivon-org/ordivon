# Finance consumer network profile

Finance owns nine scoped loopback authorities and domain semantics; it no longer owns a WireGuard identity.

## Current topology

Provider-bound venue traffic is lowered through the single Network v2 Browserless provider carrier at `10.252.246.2:19680`. The carrier runs inside `nv2-browserless-prod` over one Surfshark WireGuard identity. Finance keeps exact inbound+domain+port fencing in its own sing-box process, so sharing the physical carrier does not merge semantic authority.

The provider-bound authorities remain OKX/Binance REST/WS on `127.0.0.1:19283-19290`. U.S. Treasury (`19291`) and FRED (`19292`) remain explicit `public-direct` lanes; direct is an admitted carrier for those authorities and never a fallback for exchange venues.

There is no Finance `provider-endpoints.json`, provider URLTest, provider DNS race, second WireGuard session, or provider credential materialization in the current design. Historical R5/R6/R7 and DNS-race evidence remains under `history/` as evidence only.

## Readiness

`finance-ready` verifies real read-only destination consequences. Physical shared-carrier readiness is necessary but not sufficient. `acceptance/production-smoke.sh` proves destination fencing, provider-carrier fail-closed behavior, survival of the direct Treasury/FRED lanes when the provider carrier is intentionally stopped, recovery, and control-plane non-interference. No live financial writes are performed.
