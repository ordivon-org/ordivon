# Finance consumer network profile

This directory owns the Network v2 transport projection for Finance venue consumers. The current data plane is intentionally a thin composition over **sing-box + systemd**. Finance retains domain semantics and caller TLS.

## Production topology

The provider and consumer transport graph is one mature sing-box process rather than a custom namespace/controller stack:

```text
Surfshark WireGuard Endpoint A ─┐
                               ├─ sing-box provider URLTest ─ dual provider-DNS response race ─ scoped loopback CONNECT authorities
Surfshark WireGuard Endpoint B ─┘
```

The WireGuard endpoints use sing-box's native userspace WireGuard Endpoint implementation (`system=false`). Numeric provider endpoints are compiled from the pinned Gluetun Surfshark catalog and the existing protected provider profiles during materialization. No Finance runtime dependency remains on Linux netns, `wg-quick`, `wireguard-go`, a provider-side HTTP carrier, Surfpath, ExteriorAnchor, or a custom recovery controller.

`provider-auto` is the only A/B selector. Its health URL is numeric (`https://1.1.1.1/cdn-cgi/trace`) so provider selection does not depend on host DNS. Finance uses both Surfshark provider resolvers (`162.252.172.57` and `149.154.159.92`) through the selected WireGuard endpoint. sing-box 1.14 evaluates the first resolver, marks its response as a race candidate, speculatively evaluates the second resolver in parallel, and returns the first response that contains an acceptable IPv4 address. The route `resolve` action intentionally omits a fixed server so admitted Finance hostnames enter this DNS rule engine before L3 forwarding. URLTest establishes provider-path health only; real venue consequences remain independent acceptance evidence.

The independent consumer authorities are split by explicit carrier class. Exchange authorities use `provider-auto`; official public macro data that does not require a regional provider tunnel may use a destination-fenced direct carrier. Direct is an admitted carrier for that authority, never a fallback:

- OKX REST: `127.0.0.1:19283` → exactly `openapi.okx.com:443`.
- Binance Spot public REST: `127.0.0.1:19284` → exactly `data-api.binance.vision:443`.
- Binance Spot public WS: `127.0.0.1:19285` → exactly `data-stream.binance.vision:443`.
- Binance USD-M REST: `127.0.0.1:19287` → exactly `fapi.binance.com:443`.
- OKX public WS: `127.0.0.1:19288` → exactly `ws.okx.com:8443`.
- Binance USD-M public WS: `127.0.0.1:19289` → exactly `fstream.binance.com:443`.
- Binance Wallet/API REST: `127.0.0.1:19290` → exactly `api.binance.com:443`.
- U.S. Treasury public rates REST/XML: `127.0.0.1:19291` → exactly `home.treasury.gov:443` over explicit `public-direct`.

`127.0.0.1:19299` is sing-box's local observation API, not a consumer data authority. Every consumer inbound has an exact inbound + domain + port route. The final route rule rejects everything else. No authority falls back between carriers: venue authorities remain provider-bound, while Treasury is explicitly direct-bound.

## DNS resilience

Finance DNS must not collapse back to a single provider resolver. Configuration validation freezes both provider DNS addresses and the `evaluate` / `match_response` / `race` / speculative-evaluation structure. `acceptance/dns-race-smoke.sh` runs an off-production-port sing-box instance twice: once with DNS-1 replaced by an unreachable TEST-NET address and once with DNS-2 replaced. The surviving provider resolver must still carry the public OKX time probe through the same `provider-auto` WireGuard composition.

This is separate from provider A/B endpoint fault injection: provider-path redundancy and DNS-server redundancy are different failure dimensions.

The composition root is `network-v2-finance.target`; it owns only `network-v2-finance-egress.service`. `provider-endpoints.json` is protected deployment material and is deliberately not stored in Git.

Historical R5/R6/R7 namespace/`wg-quick` evidence remains under `history/`; it is evidence, not current desired state.

## Lifecycle and readiness

`network-v2-finance.target` is the persistent composition root and is enabled at materialization so the Finance transport returns after host/WSL boot without an operator-issued start. Process state is not treated as data readiness. `/usr/local/libexec/network-v2/finance-ready` performs bounded consequence probes through the exact admitted loopback authorities and fails closed; it never falls back to direct Internet access and never loads broker credentials. `public` proves the credential-free market/macro authorities (OKX REST, Binance USD-M REST, Binance Spot public REST, U.S. Treasury); `all` additionally requires the Binance Wallet/API authority, so a private-account-side venue outage does not block public research-data convergence.

Canonical convergence is `task consumer:finance:converge`: materialize exact provider/consumer bytes, enable the target, restart the composition root onto those exact installed bytes, then prove the credential-free public market/macro authority set. Binance Wallet/API readiness remains an explicit separate/full probe. Venue outage and provider convergence remain distinguishable from a running sing-box process.
