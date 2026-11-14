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

Native invocation using the pinned Capital test toolchain:

    cd domains/capital
    uv run --locked --group test python adoption/r3_native/market_daily_close_consumer.py --panel /root/projects/ordivon-private/finance/market-daily/capture-20261114-r3/daily_close_panel_20261113.csv --manifest /root/projects/ordivon-private/finance/market-daily/capture-20261114-r3/panel_manifest.json

Run the canonical native suite with mise run //domains/capital:verify at
the repository root. The ten new negative controls now belong to
domains/capital/tests, included by ordinary Capital pytest discovery.

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
controls in domains/capital/tests/test_market_daily_close_consumer.py. A digest only
guarantees local byte equality, not publisher signature or historical PIT.

Future boundary: sample-level formal/source refinement; rights/license
verification; official corporate-actions/total-return normalization;
publisher correction/revision handling; historical first-public timestamps;
precommitted held-out hypotheses, matched benchmarks and independent
economic/forecast verification. UNKNOWN stays UNKNOWN.


## Real consumer graph / scoped R2.1 LEGO contract

External Cboe, Nasdaq -> existing Markets natural data boundaries ->
operator-private capture bytes and exchange session calendar ->
exact-byte/digest/source-role-reconciled close panel ->
Finance R3 read-only descriptive consumer -> Human Guide ->
existing Research experiment freeze / independent holdout review.

There is NO verified consumer edge to PortfolioIntent, Accounting
PostgresPaperClose, independent risk budget, or Trading/live effects.

| Contract | Current bounded implementation and limitations |
| --- | --- |
| I | Private close-only CSV plus manifest, source SHA-256, exchange dates and provider origin split |
| O | Date-aligned prices, QQQ EMA200, relative QQQ/SPY and SMH/QQQ, Mag7 breadth, VXN/VIX and evidence limits |
| S | None except local private input files; no new PG or external state |
| pre | Input digests match, symbol/date completeness, XNYS sessions, explicit research-only source and unknowns |
| post | Returned descriptive facts inherit exact local source identity, never assert forecasting, trade profitability or authority |
| inv | Missing does not mean zero; source-timing UNKNOWN never means qualified; no synthetic holidays or implicit fills |
| eff | Read-only file/CPU only, zero Paper/live/venue effect |
| c | Two inputs bounded at 8 MB each, O(asset_count × sessions) evaluation, default 43 by 971 |
| epsilon | Uncertain rights, PIT, total return, issuer revisions, provider OHLC and volume discrepancies retained |
| prov | Source file digests, repo commit, private source receipts, native consumer evidence and test suite |
| unfold | Human question -> Markets authority -> Research read -> optional experiment freeze -> independent future evaluation |

The actual planned CA01 in planning/lego-plan-r1.json currently
describes bounded public market stream qualification (in its existing
source implementation), NOT automatic admission of these ETF raw
closes. It must not be cosmetically treated as this new ETF consumer's
implemented proof. Markets historical adjusted-close and EOD-Paper
admission are distinct existing native contracts; their verified
adjusted prices, rights and corporate actions are still absent.

The existing formal/MarketsCapturePITR1.smt2 only establishes the
specific abstract temporal constraints it models. It neither proves
the actual exchange holiday source nor provides implementation
refinement for this new pandas consumer. The native fake-Memorial-Day
negative test is independent effect-level evidence and must not be
deleted after a model-only formal check.

Next source-shape obligation: the current manifest sourceSplit is
deliberately pinned to Cboe history through 2026-11-12 and Nasdaq
2026-11-13. On future source calendar dates/roles, promote only after
a new source-specific contract and consumer tests, NOT a blind
forward-fill or silent cast. This capture is not yet an unattended
production Markets ingestion system. No duplicate data/owner registry.
