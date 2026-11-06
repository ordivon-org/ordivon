# Finance consumer network profile

Finance owns nine scoped loopback authorities and domain semantics; it no longer owns a WireGuard identity.

## Current topology

Provider-bound venue traffic is lowered through the single native Network v2 Gluetun provider adapter at `10.252.246.2:19680`. The carrier runs inside `nv2-browserless-prod` over one Surfshark WireGuard identity. Finance keeps exact inbound+domain+port fencing in its own sing-box process, so sharing the physical carrier does not merge semantic authority.

The provider-bound authorities remain OKX/Binance REST/WS on `127.0.0.1:19283-19290`. U.S. Treasury (`19291`) and FRED (`19292`) remain explicit `public-direct` lanes; direct is an admitted carrier for those authorities and never a fallback for exchange venues.

There is no Finance `provider-endpoints.json`, provider URLTest, provider DNS race, second WireGuard session, or provider credential materialization in the current design. Legacy R5/R6/R7 evidence files had no current consumers and were retired from the working tree; their contents remain in Git history for specific investigations. The retired DNS-race executable is not an active consumer or test: it depended on the removed `/etc/network-v2/finance/provider-endpoints.json` and is available from Git history when needed for forensic review. It must not be reactivated as a live readiness or transport provider.

## Readiness and fault boundaries

Finance owns nine scoped HTTPS authorities. Treasury and FRED remain
explicitly direct macro lanes, never fallback paths for OKX or Binance.

Routine verification compares installed authority, route and service files
with their source, then invokes read-only finance-ready all 90.
The selected Gluetun adapter is not changed or restarted.

The former production-smoke script acted on the retired Browserless carrier
and therefore no longer represented the selected physical Provider.
Physical fault acceptance belongs in a disposable native systemd/Gluetun
environment with independent consumer witnesses.

## Independent Finance lane acceptance

The native consumer:finance:verify Task composes the existing read-only
Finance readiness with acceptance/egress/finance-lane-witness.py, which
reuses the Network live Carrier observer. The witness binds the exact
nine-lane source/installed configuration and running proxy PIDs, checks
seven shared Carrier routes and two explicit public-direct routes, and
samples denied hostname, denied port and local TCP direct-fallback canaries.
This proves sampled IPv4 HTTPS behavior and local no-fallback, not universal
DNS/IPv6 noninterference, process memory identity or financial-write authority.
No new VPN session, monitor or long-running service is introduced.
