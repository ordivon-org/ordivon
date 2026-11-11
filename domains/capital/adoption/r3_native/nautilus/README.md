# Finance R3 鈥?NautilusTrader 2.0rc9 native simulation qualification

Thin independent native BacktestNode/OMS consumer of provider-derived data.
Run the sibling etf_qlib_consumer.py FIRST to create output/
openbb_cboe_SPY_normalized.csv (local only, not committed because provider
redistribution rights are UNKNOWN).

Run on Windows x64 Python 3.15 (SEPARATE FROM QLIB PYTHON 3.11):
  uv venv .venv --python 3.15
  uv pip sync --python .venv/Scripts/python.exe requirements.lock
  .venv/Scripts/python.exe etf_nautilus_native.py

Override source with ORDIVON_FINANCE_R3_SPY_CSV when necessary.

Source: Cboe historical EOD close. Derived synthetic QuoteTicks use
bid = close - $0.01, ask = close + $0.01, 21:00 UTC for each session.
These ARE NOT real historical quotes or DST-aware exact venue timestamps.
Native ParquetDataCatalog -> Equity + QuoteTick -> BacktestNode
-> built-in EmaCross strategy -> native OrderFilled/Orders/Positions
reports. Model is native DefaultFillModel(slippage 0, seed 42) with
MakerTakerFeeModel; output native_backtest_result.json is ignored by Git.

Set BacktestRunConfig.dispose_on_completion=False to keep cache and
generated reports; the default True drops engine state.
Native cache.orders() exposes order.events() method, including
OrderInitialized, OrderSubmitted, OrderFilled. Simulated trade_id is
repeatable; event_id UUID changes between replays. A fill report's
client_order_id is its DataFrame index. Report alone does not certify
complete correction/void/replay history.

No broker, real exchange quotes, real economic validation, PG writes
or point-in-time authority. Does not conform to Capital's T-1
decision/T-open fill eligibility and MUST NOT be automatically
promoted to PG PaperClose or live execution.

Scope: validate mature BacktestNode, venue config, native instrument,
catalog, fill/commission model, OMS and report/event API semantics.
Production requires independent native-event-replay equivalence checks.
