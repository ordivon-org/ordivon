# Live Endpoint Test-Account Policy — 2026-09-14

The user explicitly authorized the existing OKX and Binance live accounts to be used as non-production qualification accounts because they are intentionally kept with negligible funds.

This does **not** change protocol reality: the endpoints remain LIVE, not Demo/Testnet. Market Capital records the role as `TEST_ACCOUNT_BY_USER_POLICY`.

Before any order submission, current authoritative evidence must establish account balance/value, trade permission, absence of withdrawal/transfer authority, instrument filters/minimums, a healthy reconciliation read path, and a fresh clock gate. A user statement that the account has no funds is authorization context, not current balance evidence.

A hard local test cap of 1 quote unit is imposed. If the venue's minimum executable notional exceeds that cap, qualification stops; the software may not silently increase the cap. Production trading, withdrawals and transfers remain unauthorized.

The current ChatGPT tool environment blocked fresh private live-account access using trading credentials, so the policy remains `USER_AUTHORIZED_PENDING_FRESH_PRIVATE_ACCOUNT_VERIFICATION` and order submission stays disabled. This boundary must not be bypassed by alternate credential-reading code.

## Canary tiering

Live-test validation is split into two different authorities:

1. **Non-matching validation canary** — authorized. This means a venue-native signed test/precheck operation which is explicitly documented not to create an order in the matching engine, such as Binance `order.test`.
2. **Real matching-engine order** — not currently authorized by policy. The current hard cap is 1 quote unit, while the locally retained fresh Binance Spot qualification evidence records a 5 USDT minimum notional for both BTCUSDT and ETHUSDT. The software must not silently raise the cap merely to satisfy venue minimums.

A successful signature/test endpoint therefore proves credential/trade-parameter admission only; it does not prove fill/reconciliation behavior.
