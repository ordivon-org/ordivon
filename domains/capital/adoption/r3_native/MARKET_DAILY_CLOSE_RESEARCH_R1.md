# Finance Market Daily Close Research R1

Purpose: a real Finance Human/Agent can read one synchronized market
snapshot, observe QQQ vs SPY/SMH, Mag7 participation and volatility
metrics, and know exactly what the evidence does NOT establish.

The Markets natural owner remains authoritative for data admission.
The R3 consumer is a read-only adapter; not a price provider, optimizer,
finance agent, brokerage adapter, new calendar service or Paper ledger.

Physical private inputs in this iteration:

    /root/projects/ordivon-private/finance/market-daily/capture-20261114-r3/
      daily_close_panel_20261113.csv
      panel_manifest.json
      nasdaq_manifest.json
      volatility_manifest.json

Native read-only invocation from Ordivon repository root:

    uv run --no-project --python 3.11 --with pandas==3.1.1 \
      --with exchange_calendars python \
      domains/capital/adoption/r3_native/market_daily_close_consumer.py \
      --panel /root/projects/ordivon-private/finance/market-daily/capture-20261114-r3/daily_close_panel_20261113.csv \
      --manifest /root/projects/ordivon-private/finance/market-daily/capture-20261114-r3/panel_manifest.json

Mature external composition: official OpenBB/Cboe OHLCV capture, Nasdaq
native history for the 11/13 equities, Cboe VIX-family official CSVs,
exchange_calendars for XNYS sessions, pandas for EMA and daily returns.
No new generic platform, source registry or HTTP stack.

Data-quality counterexamples:
- Source SPY and 37 other securities contained a fake 2025-05-26
  (Memorial Day) row. The source cannot own the exchange trading calendar.
- Cboe VIX dates may differ from XNYS; 28 non-XNYS VIX historical rows
  were excluded from the common equity-session panel.
- Across 43 sources, a prior full audit found 433 individual OHLC-bound
  violations. Preserve that quarantine, never silently change vendor highs
  or lows; only descriptive close fields are used in this consumer.
- Backfilled raw close is NOT the adjusted-close input required by
  Markets.historical_close_snapshot and NOT the paper-eligible raw mark
  required by Markets.etf_eod_snapshot (rights and corporate actions
  are independently unqualified). No Research->PortfolioIntent promotion.

Validation: native full 43-source private consumer and source-free negative
controls in tests/test_market_daily_close_consumer.py. A digest only
guarantees local byte equality, not publisher signature or historical PIT.

Future boundary: sample-level formal/source refinement; rights/license
verification; official corporate-actions/total-return normalization;
publisher correction/revision handling; historical first-public timestamps;
precommitted held-out hypotheses, matched benchmarks and independent
economic/forecast verification. UNKNOWN stays UNKNOWN.
