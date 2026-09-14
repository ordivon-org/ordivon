# Crypto FIX 4.4 Projection R4 — 2026-09-14

## Standing

`PASS_CRYPTO_MECHANICS_TO_FIX44_PROJECTION`

This milestone does not introduce a new order protocol or a new crypto intent system. It composes the previously qualified NautilusTrader local Spot mechanics with the already admitted FIX 4.4 / QuickFIX-n order-semantic implementation.

The exact four mechanics-only orders from `crypto-shadow-mechanics-r1-20260913.json` are projected to FIX 4.4 `NewOrderSingle (35=D)` messages. Existing Nautilus mechanics `clientOrderId` values are preserved as FIX `ClOrdID`, venue is represented with standard `ExDestination`, order type remains Market, and time-in-force remains IOC.

The projector is deliberately sessionless. It opens no socket, carries no exchange credential, reads no private account state, and cannot send an order. Its only role is deterministic standard-semantic projection through QuickFIX/n 1.14.1.

## Qualified projections

- `MECH-OKX-BTC` → `BTC-USDT`, `ExDestination=OKX`, Market, IOC.
- `MECH-BINANCE-BTC` → `BTCUSDT`, `ExDestination=BINANCE`, Market, IOC.
- `MECH-OKX-ETH` → `ETH-USDT`, `ExDestination=OKX`, Market, IOC.
- `MECH-BINANCE-ETH` → `ETHUSDT`, `ExDestination=BINANCE`, Market, IOC.

All four preserve quantity and identity exactly from the already-qualified Nautilus mechanics evidence.

## Boundary

This is not an investment decision, alpha claim, paper order, demo order, or external financial effect. It only proves that the current crypto mechanics can be expressed through the same mature FIX order vocabulary already used by the equity validation path.

The next boundary is authoritative **read-only** OKX/Binance account/order/trade reality. No order-capable credential is admitted by R4.
