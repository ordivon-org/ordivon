# Finance consumer network profile

This directory owns the Network v2 transport projection for Finance venue consumers. The current data plane is intentionally a thin composition over **sing-box + systemd**. Finance retains domain semantics and caller TLS.

## Production topology

The provider and consumer transport graph is one mature sing-box process rather than a custom namespace/controller stack:

```text
Surfshark WireGuard Endpoint A ─┐
                               ├─ sing-box provider URLTest ─ provider DNS ─ four fenced loopback CONNECT authorities
Surfshark WireGuard Endpoint B ─┘
```

The WireGuard endpoints use sing-box's native userspace WireGuard Endpoint implementation (`system=false`). Numeric provider endpoints are compiled from the pinned Gluetun Surfshark catalog and the existing protected provider profiles during materialization. No Finance runtime dependency remains on Linux netns, `wg-quick`, `wireguard-go`, a provider-side HTTP carrier, Surfpath, ExteriorAnchor, or a custom recovery controller.

`provider-auto` is the only A/B selector. Its health URL is numeric (`https://1.1.1.1/cdn-cgi/trace`) so provider selection does not depend on host DNS. The provider DNS server is reached through the selected WireGuard endpoint (`detour=provider-auto`), and sing-box's native route `resolve` action resolves each admitted Finance hostname before L3 forwarding. URLTest establishes provider-path health only; real venue consequences remain independent acceptance evidence.

The independent consumer authorities are:

- OKX REST: `127.0.0.1:19283` → exactly `openapi.okx.com:443`.
- Binance Spot public REST: `127.0.0.1:19284` → exactly `data-api.binance.vision:443`.
- Binance Spot public WS: `127.0.0.1:19285` → exactly `data-stream.binance.vision:443`.
- Binance USD-M REST: `127.0.0.1:19287` → exactly `fapi.binance.com:443`.
- OKX public WS: `127.0.0.1:19288` → exactly `ws.okx.com:8443`.
- Binance USD-M public WS: `127.0.0.1:19289` → exactly `fstream.binance.com:443`.

`127.0.0.1:19299` is sing-box's local observation API, not a consumer data authority. Every consumer inbound has an exact inbound + domain + port route. The final route rule rejects everything else. There is no native/direct fallback.

The composition root is `network-v2-finance.target`; it owns only `network-v2-finance-egress.service`. `provider-endpoints.json` is protected deployment material and is deliberately not stored in Git.

Historical R5/R6/R7 namespace/`wg-quick` evidence remains under `history/`; it is evidence, not current desired state.
