# Live Test Account — Local Admission Handoff

The current ChatGPT execution tool blocks direct use of live private financial credentials even with explicit user authorization. The boundary is not bypassed.

A local admission-only runner is provided instead:

```bash
cd /root/projects/ordivon-market-capital-next
./scripts/run-live-test-admission-local binance
```

or:

```bash
./scripts/run-live-test-admission-local okx
```

The runner performs no order placement. It consumes the already-existing local observer/admission code, removes raw private-account output after processing, and emits only a small sanitized admission summary under `.artifacts/live-test-admission-local/`.

For Binance, admission requires reading + Spot-trade permission, no withdraw/internal/universal transfer authority, no non-USDT nonzero balance, USDT balance <= 1, and no open orders. OKX currently checks credential identity/permissions but remains blocked until the balance admission is extended with a local authoritative balance read.
