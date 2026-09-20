# Live Endpoint Test-Account Policy — 2026-09-14

The Owner Principal explicitly authorizes the existing OKX and Binance live accounts to be used as non-production qualification accounts under a bounded test-capital envelope.

This does **not** change protocol reality: the endpoints remain LIVE, not Demo/Testnet. Market Capital records the role as `TEST_ACCOUNT_BY_OWNER_POLICY`.

Owner mandate, provider/currentness facts, qualification, and effect admission are separate. Before any order submission, current authoritative provider facts must establish account balance/value, trade permission, absence of withdrawal/transfer authority, instrument filters/minimums, a healthy reconciliation read path, and current clock qualification. An owner statement that the account has negligible funds defines policy context; it is not current balance evidence.

A hard local test cap of 1 quote unit is imposed. If the venue's minimum executable notional exceeds that cap, qualification stops; the software may not silently increase the cap. Production trading, withdrawals and transfers remain unauthorized.

The Owner Principal mandate is already present. `accountQualificationStanding=PENDING_FRESH_PRIVATE_ACCOUNT_VERIFICATION` and `orderSubmissionAdmission=NOT_ADMITTED` remain separate current facts, so order submission stays disabled. This boundary must not be bypassed by alternate credential-reading code or by treating owner mandate as provider permission/currentness evidence.

## Canary tiering

Live-test validation is split into two different authorities:

1. **Non-matching validation canary** — authorized. This means a venue-native signed test/precheck operation which is explicitly documented not to create an order in the matching engine, such as Binance `order.test`.
2. **Real matching-engine order** — not currently admitted under the bounded test-capital envelope and current qualification standing. The current hard cap is 1 quote unit, while the locally retained fresh Binance Spot qualification evidence records a 5 USDT minimum notional for both BTCUSDT and ETHUSDT. The software must not silently raise the cap merely to satisfy venue minimums.

A successful signature/test endpoint therefore proves credential/trade-parameter admission only; it does not prove fill/reconciliation behavior.
