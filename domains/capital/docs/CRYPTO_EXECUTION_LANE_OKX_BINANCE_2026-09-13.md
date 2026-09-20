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

Direct WSL HTTP probes to both OKX and Binance timed out. Scoped Surfshark transport is now point-in-time qualified using Singapore `sg-sng` over OpenVPN-TCP. Both OKX and Binance public REST endpoints were reached successfully without credentials and BTC/ETH Spot instrument metadata was retrieved. The discovered path digests are evidence, not permanent configuration: every future live public-data session must perform fresh `surfpath` discovery/revalidation before use.

## Next graduation sequence

`qualified public reality -> minimal decision binding -> FIX-aligned order intent -> mature pre-trade/OMS/Risk -> Nautilus execution client -> OKX Demo and/or Binance Demo/Testnet -> authoritative venue reality -> reconciliation -> repeated paper/recovery evidence`

Each arrow is a composition boundary, not a mandate to implement a new subsystem. Only after those steps would any live authorization design be considered.
