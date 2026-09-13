# Crypto Execution Lane — OKX + Binance

## Decision

The future broker/venue qualification path is changed from Interactive Brokers to **OKX + Binance**.

This is not a literal substitution inside the historical equity M6/M7 experiment. That experiment is bound to U.S. equities and At-the-Opening semantics. Crypto spot is a continuous 24/7 market, so the canonical crypto lane starts with fresh market-specific evidence and continuous-market execution semantics.

## Selected mature components

NautilusTrader `2.0.0rc4` already contains native Rust/PyO3 adapters for both venues:

- OKX public/live market-data adapter and execution adapter;
- Binance Spot public/live market-data adapter and execution adapter;
- venue-specific Demo/Testnet environments for later non-live execution qualification.

No third-party exchange SDK is added.

## Current admission

**SHADOW_PUBLIC_DATA_ONLY**.

Allowed now:

- construct credential-free OKX Spot public-data configuration;
- construct credential-free Binance Spot public-data configuration;
- qualify instrument identity and market-data normalization;
- use BTC/USDT and ETH/USDT as the initial common universe;
- compare observations across OKX and Binance.

Not admitted:

- private account data;
- demo/testnet order submission;
- any API key use;
- live execution;
- external financial writes.

## Network finding

Direct WSL HTTP probes to both OKX and Binance timed out. Workstation has scoped Surfshark `surfpath` transport authority, but the first Japan/WireGuard discovery attempt timed out after 120 seconds. Exchange public-data connectivity therefore remains a transport qualification problem rather than an adapter failure; no working VPN path is claimed yet.

## Next graduation sequence

`public dual-venue data -> same-cut/clock-quality qualification where needed -> crypto-specific decision/shadow intent -> local Nautilus OMS/Risk -> OKX Demo and/or Binance Demo/Testnet -> venue reconciliation -> repeated paper evidence`

Only after those steps would any live authorization design be considered.
