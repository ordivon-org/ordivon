# Crypto Shadow Mechanics R1

This milestone is a local execution-mechanics qualification, not an investment strategy or economic decision.

It reuses the accepted OKX/Binance public observation and venue instrument metadata, applies the real venue price/quantity precision and minimum-size/notional rules, constructs multi-currency Spot cash accounts in NautilusTrader, and simulates one synthetic `10 USDT` IOC intent for BTC and ETH on each venue.

The synthetic notional exists only to exercise precision, sizing, cash-account, OMS, and fill mechanics. No broker is connected, no exchange credential is loaded, and no external financial write occurs.

## Accepted result

`PASS_LOCAL_CRYPTO_SPOT_OMS_MECHANICS`

The accepted run filled four local synthetic IOC intents: BTC and ETH on OKX and Binance. A key qualification finding was that venue order quantity must be produced by the instrument (`instrument.make_qty`) so the venue's order-step precision, rather than the generic asset currency precision, controls the order quantity. Public API padding zeros are likewise normalized to instrument tick/step precision before constructing the simulated market.

