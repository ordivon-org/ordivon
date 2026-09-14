# Market Capital full non-live effect closure — 2026-09-14

## Standing

`PASS_FULL_NONLIVE_EFFECT_PATH_EXTERNAL_DEMO_BINDING_PENDING_PROVIDER_REGISTRATION`

The local engineering path is closed through a real mature non-live execution provider and durable capital resolution:

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

This is not a hand-written exchange simulator. NautilusTrader 2.0.0rc4 owns the simulated exchange/Risk/Execution mechanics; TigerBeetle 0.17.9 owns accounting and pending-transfer mechanics. Market Capital retains only mapping, proof/currentness, effect disposition and durable reconciliation semantics.

## Destructive matrix

The qualification executes five effect classes:

| Scenario | Provider behavior | EffectDisposition | Capital result after restart |
|---|---|---|---|
| FILL | market order filled | CONSUME | CONSUMED / MATCH |
| PARTIAL_FILL_SLICES | one order filled through multiple provider fill slices | CONSUME | CONSUMED / MATCH |
| CANCEL | accepted limit order then cancel | RELEASE | RELEASED / MATCH |
| DENY | provider risk denial for insufficient funds | RELEASE | RELEASED / MATCH |
| UNKNOWN_AFTER_SUBMISSION | current provider reality unavailable | RETAIN | RESERVED / MATCH |

An exact replay of a consumed TigerBeetle resolution returns `EXISTS`; it does not post twice.

## Authority separation

`NonLiveEffectAdmission=ADMITTED` applies only to bounded simulated-exchange effects. It explicitly does **not** mint real financial-write authority.

The separate real-money boundary remains:

```text
ExternalFinancialWriteAdmission = NOT_ADMITTED
providerWriteCapabilityBound = false
effectVerifier = NOT_IMPLEMENTED
```

## External Demo/Testnet binding

The mature OKX Demo and Binance Spot Testnet execution-client configurations construct successfully, but actual provider-side non-live credentials are not yet registered locally:

- Binance Testnet local Ed25519 keypair exists; the public key still needs server-side registration and the resulting API key must be installed.
- OKX Demo credential root exists; a Demo Trading API credential still needs to be created provider-side and installed.

This is now represented as an external provider-registration dependency, not as an unfinished Market Capital mechanism. Live credentials are forbidden from reuse.

## Canonical entry point

```text
scripts/run-market-capital-fullpath-closure --output evidence/full-nonlive-effect-closure-20260914.json
```
