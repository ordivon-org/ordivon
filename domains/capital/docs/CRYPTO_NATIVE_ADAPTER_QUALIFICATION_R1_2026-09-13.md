# Crypto Native Adapter Qualification R1

## Decision

Market Capital does **not** require one framework to own every market-data transport. Adapter admission is venue-specific and evidence-based.

- **OKX Spot:** NautilusTrader `2.0.0rc4` native public data client is admitted for the current public-data lane.
- **Binance Spot:** NautilusTrader `2.0.0rc4` native data client is not admitted because startup repeatedly ends in `data-connect timeout` before any QuoteTick is emitted.
- **Binance public market data:** use Binance's credential-free official public REST/WebSocket boundary, normalize into the common Market Capital public-observation schema, and keep Nautilus for the already-qualified local OMS/Risk mechanics.

This is intentionally asymmetric. It avoids building a custom trading framework while also avoiding a false requirement that Nautilus must own transport, OMS, risk, and reconciliation simultaneously.

## OKX evidence

With a fresh scoped Surfshark path, the Nautilus OKX data client connected, subscribed to `BTC-USDT.OKX` and `ETH-USDT.OKX`, emitted QuoteTicks for both, and shut down cleanly. No credentials or execution client were configured.

Standing: `PASS_NATIVE_OKX_PUBLIC_QUOTES`.

## Binance evidence

The following were independently proven over scoped VPN:

- official public REST ping/time/exchangeInfo returned HTTP 200;
- official public WebSocket completed HTTP 101 upgrade and emitted a BTCUSDT bookTicker frame;
- Nautilus Spot JSON mode builds and starts without credentials;
- however, the rc4 Nautilus data client does not reach connected state with either Sockudo or Tungstenite and emits no QuoteTicks before the connection deadline.

Standing for native rc4 client: `BLOCKED_DATA_CLIENT_STARTUP`.

This is not evidence that Binance public data is unavailable. The official public boundary is admitted and already used by Crypto Public Shadow R1.

## Hard boundary

Do not add Binance API keys, Ed25519 keys, private streams, or SBE credentials merely to turn a public-data qualification green. Private account data and every execution lane remain separately blocked.
