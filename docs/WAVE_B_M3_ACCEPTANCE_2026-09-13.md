# Market Capital Clean-Room — Wave B / M3 Acceptance

Date: 2026-09-13

## Standing

**PASS_BOUNDED_PROVIDER_ORIGIN_DATA_NON_CAUSAL**.

Wave B / M3 replaces the synthetic AAPL/MSFT/NVDA execution fixture with daily OHLCV responses retrieved directly from Nasdaq's public historical-data service, preserves raw-response and normalized-series SHA-256 provenance, converts those bars into LEAN-native daily files, and re-runs the same M2 feasibility/execution path.

This is deliberately **not** called market-truth or causal strategy validation. Nasdaq is the provider of the retrieved historical series, but M3 does not prove SIP/UTP consolidated-feed equivalence or execution-grade tick truth.

## Data interval and causality

The admitted interval is 2026-09-01 through 2026-09-11. The Wave A portfolio target was produced after this interval. Therefore these bars may validate provider-origin data plumbing, normalization, order sizing, fills, fees/slippage models, and portfolio-state transitions only.

They **must not** be used to claim out-of-sample performance, alpha, or a post-decision track record.

A causal shadow lane begins only with market data whose timestamps are later than the target/decision artifact timestamp.

## Provider-origin data evidence

Each retrieved series contains 8 daily rows:

- AAPL — stocks
- MSFT — stocks
- NVDA — stocks
- SPY — ETF benchmark input

The runtime manifest records for every series:

- exact provider request URL;
- retrieval timestamp;
- raw JSON SHA-256;
- normalized LEAN CSV SHA-256;
- row count;
- first and last dates.

Raw responses and converted LEAN data remain generated runtime artifacts under `.artifacts/wave-b-m3/`; the repository persists the acquisition/validation code and compact acceptance evidence rather than treating mutable downloaded data as source code.

## Execution result

Using the same Wave A research-gated 1/3 target weights and the M2 1% validation execution reserve:

- AAPL: LEAN pre-trade quantity 101; filled on 2026-09-02 at about 326.865; fee USD 1.
- MSFT: LEAN pre-trade quantity 65; filled at about 499.85; fee USD 1.
- NVDA: LEAN pre-trade quantity 151; filled at about 218.785; fee USD 1.
- Total fees: USD 3.00.
- Data requests: 5 succeeded / 0 failed.
- Engine errors: 0.
- End portfolio value: about USD 100193.86.
- End cash: about USD 1456.85.

LEAN models remain:

- `InteractiveBrokersFeeModel`;
- `VolumeShareSlippageModel(0.30, 0.05)`;
- `EquityFillModel`;
- LEAN buying-power sizing via `CalculateOrderQuantity` and the configured free-portfolio reserve.

## What M3 closes

M3 closes the synthetic-price-fixture dependency for the bounded historical execution lane. It proves:

`provider-origin OHLCV -> provenance manifest -> LEAN-native normalization -> target feasibility -> orders -> fills -> fees/slippage -> resulting portfolio state`.

## What M3 does not close

Still open:

- causal post-decision shadow evidence;
- real-time/near-real-time quote or trade feed admission;
- execution-grade venue/consolidated-feed semantics;
- broker/account-specific buying power;
- broker credentials and paper brokerage connectivity;
- any external financial write;
- production/live authorization.
