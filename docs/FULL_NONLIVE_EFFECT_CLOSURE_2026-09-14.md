# Market Capital full effect-path closure — 2026-09-14

## Standing

`PASS_FULL_EFFECT_PATH_OKX_LIVE_PROVIDER_BOUND_NO_EXTERNAL_EFFECT_ADMISSION`

Two independently bounded paths are now closed.

The non-live effect/capital path is:

```text
FIX-aligned intent
→ NautilusTrader Risk / Execution / simulated exchange
→ provider order/fill reality
→ Market Capital reconciliation
→ EffectDisposition {RETAIN, RELEASE, CONSUME}
→ TigerBeetle pending reservation resolution
→ process restart
→ exact durable provider-history reconciliation
```

The current live-provider capability path is:

```text
unified external secret root
→ Network v2 scoped OKX authority
→ @okx_ai/okx-trade-cli 1.4.7 authenticated private API
→ current provider permissions {read_only, trade}
→ private balance/open-orders currentness
→ NautilusTrader 2.0.0rc4 OKX LIVE execution configuration
```

This is not a hand-written exchange implementation. NautilusTrader owns execution/simulation mechanics, TigerBeetle owns accounting/pending-transfer mechanics, the OKX Trade CLI owns the current authenticated venue API surface, and Network v2 owns scoped egress. Market Capital retains only thin binding, currentness/proof, effect disposition and reconciliation semantics.

## Destructive non-live matrix

| Scenario | Provider behavior | EffectDisposition | Capital result after restart |
|---|---|---|---|
| FILL | market order filled | CONSUME | CONSUMED / MATCH |
| PARTIAL_FILL_SLICES | one order filled through multiple provider fill slices | CONSUME | CONSUMED / MATCH |
| CANCEL | accepted limit order then cancel | RELEASE | RELEASED / MATCH |
| DENY | provider risk denial for insufficient funds | RELEASE | RELEASED / MATCH |
| UNKNOWN_AFTER_SUBMISSION | current provider reality unavailable | RETAIN | RESERVED / MATCH |

An exact replay of a consumed TigerBeetle resolution returns `EXISTS`; it does not post twice.

## Current OKX LIVE provider binding

Fresh provider evidence proves:

```text
authenticated private API     = CURRENT
account config query           = PASS
balance query                  = PASS
open-orders query              = PASS
provider Read permission       = CURRENT
provider Trade permission      = CURRENT
provider Withdraw permission   = ABSENT
Nautilus OKX LIVE config       = BOUND
```

The executor credential is bound from `/root/.config/ordivon/secrets/okx/live-trade/config.toml`; secret bytes remain outside the repository.

## Authority separation

Provider capability is not effect admission.

```text
OKX provider Trade capability                  = CURRENT
provider Trade capability bound to effect      = false
ExternalFinancialWriteAdmission                = NOT_ADMITTED
orderSubmissionAllowed                         = false
effectVerifier                                  = NOT_IMPLEMENTED
```

So Market Capital now knows that the owner-authorized provider credential is genuinely order-capable, but no real matching-engine order is submitted merely because that capability exists.

## Demo/Testnet status

OKX Demo and Binance Spot Testnet remain optional non-live venue qualification lanes. Their provider-side credentials are still unprovisioned, but this no longer blocks the current OKX LIVE provider binding or the full local effect/capital closure.

## Canonical entry points

```text
scripts/check-okx-live-provider-binding --output evidence/okx-live-provider-binding-20260914.json
scripts/run-market-capital-fullpath-closure --output evidence/full-nonlive-effect-closure-20260914.json
```
