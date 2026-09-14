# Finance consumer network profile

This directory owns the Network v2 transport projection for Finance venue consumers. It is a thin composition over mature WireGuard, Linux network namespaces, systemd and sing-box. Finance retains domain semantics and caller TLS.

## Production topology

One provider substrate is shared rather than duplicated per venue:

```text
provider A WireGuard ─┐
                     ├─ sing-box provider carriers ─ root sing-box ─ four fenced loopback CONNECT authorities
provider B WireGuard ─┘
```

The independent consumer authorities are:

- OKX REST: `127.0.0.1:19283` → exactly `openapi.okx.com:443`.
- Binance USD-M REST: `127.0.0.1:19287` → exactly `fapi.binance.com:443`.
- OKX public WS: `127.0.0.1:19288` → exactly `ws.okx.com:8443`.
- Binance USD-M public WS: `127.0.0.1:19289` → exactly `fstream.binance.com:443`.

`127.0.0.1:19299` is sing-box's local observation API, not a consumer data authority. Every consumer inbound has its own URLTest group and an exact inbound + domain + port route. The final route rule rejects everything else. There is no native/direct fallback.

The Binance WS group uses the stable Binance USD-M public REST time endpoint only as provider-path health evidence. Real `fstream.binance.com` consequence is verified separately; Finance performs the application-level WebSocket frame acceptance.

The composition root is `network-v2-finance.target`. Provider namespace/WireGuard/carrier units are shared by all four authorities.

Historical `finance-okx` R5/R6/R7 evidence remains under `history/`; it is evidence, not current desired state.
