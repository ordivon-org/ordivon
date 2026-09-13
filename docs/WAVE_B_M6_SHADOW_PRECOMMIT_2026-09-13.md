# Market Capital Clean-Room — Wave B / M6 Shadow Order Precommit

Date: 2026-09-13

## Standing

**SHADOW_ORDER_PRECOMMIT_FROZEN**.

M6 freezes a pre-market shadow order plan before any post-decision market data is available. It does not execute an order, open a brokerage/FIX session, or create an external financial effect.

## Why this precommit exists

The Wave A target became canonical at `2026-09-12T14:59:29Z`, after the 2026-09-11 U.S. session had completed. M5 correctly reports that no post-decision daily bar exists yet.

To prevent hindsight from entering the first causal shadow measurement, M6 commits the execution intent in advance using only information already available before the next eligible session:

`frozen target -> 2026-09-11 provider-origin close -> LEAN buying-power sizing -> FIX 4.4 NewOrderSingle intent -> frozen shadow plan`.

## Frozen inputs

- target portfolio SHA-256: `137265667683455c302adff94466eaf38444ed7d51b5959c4ad065505792c14d`;
- pricing provider: Nasdaq public historical service;
- pricing session: 2026-09-11;
- pricing field: daily close;
- execution reserve: 1%;
- sizing owner: LEAN `CalculateOrderQuantity`;
- precommit/TransactTime: `2026-09-13T09:39:11Z`;
- intended execution trigger: first eligible post-decision session open;
- FIX protocol: 4.4 `NewOrderSingle` (`35=D`);
- order type: Market (`40=1`);
- time in force: At the Opening (`59=2`).

The provider-origin raw and normalized-series digests used by the plan are preserved in `evidence/wave-b-m6-precommit-20260913.json`.

## Frozen shadow orders

| Symbol | 9/11 close used for sizing | Quantity | ClOrdID |
|---|---:|---:|---|
| AAPL | 332.2700 | 99 | `mc_2f8f15cfd2293c0a1fa3cf89` |
| MSFT | 495.6300 | 66 | `mc_b8bdf89297d764975836e800` |
| NVDA | 218.2900 | 151 | `mc_c41ff3a48f45d60d1d1fe9d5` |

Each FIX intent also has the SHA-256 of the exact QuickFIX/n serialization.

## No execution occurred

The algorithm ran in explicit `plan-only` mode:

- FIX intents generated: 3;
- shadow plan rows generated: 3;
- LEAN orders emitted: 0;
- transaction rows: 0;
- broker credentials: none;
- external financial writes: none.

## Compatibility invariant

Adding M6 must not rewrite M4 history. The final M6 acceptance reran M4 and reproduced the exact frozen M4 FIX semantic identities (`ClOrdID`, message digest, and FIX-to-LEAN link). M6 uses its own precommit time/TIF seed only when the precommit lane is explicitly enabled.

## Next causal measurement

Once M5 admits a complete common post-decision session, the next stage may evaluate this exact frozen plan against that session. It may not resize from the new price, change symbols, change quantities, change TIF, or mint new order IDs and still call itself the same precommit experiment.
