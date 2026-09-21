# Demo/Testnet Execution Preflight R7 — 2026-09-14

> **Historical qualification notice — 2026-09-21:** this document records the 2026-09-14 demo/testnet component preflight. Nautilus rc4 config construction remains replayable candidate evidence under tools/nautilus_rc4, but it is not a current execution owner. Current demo/live write authority remains fail-closed under config/demo_execution_policy.json and the external-write policy.


## Standing

`PREPARED_NOT_ADMITTED`

The mature execution components already exist locally:

- OKX: NautilusTrader `OKXExecutionClientConfig` / factory, environment `DEMO`.
- Binance Spot: NautilusTrader `BinanceExecutionClientConfig` / factory, environment `TESTNET`.

Both configuration objects have been constructed locally with no credentials and no network session. No exchange client was reimplemented.

This milestone does **not** authorize a demo/testnet order. `demoWriteAdmission`, `liveWriteAdmission`, and `externalFinancialWritesAllowed` remain false. A future demo/testnet qualification requires a separate explicit authorization for non-live external writes, plus fresh clock/read-only-reality gates and a bounded reconciliation/recovery test matrix.
