# Finance R3 - NautilusTrader 2.0.0rc9 native simulation qualification

Native Windows Python3.15 BacktestNode/OMS from SPY close-derived SYNTHETIC
bid=close-0.01, ask=close+0.01, artificial 21:00 UTC quote timestamps.
These are NOT real historical market microstructure, PIT observations,
or the previous-close decision -> next-open fills expected by PG PaperClose.

Run the sibling OpenBB/Qlib capture first, then in this separate env:
  uv venv .venv --python 3.15
  uv pip sync --python .venv/Scripts/python.exe requirements.lock
  .venv/Scripts/python.exe etf_nautilus_native.py
Optionally set ORDIVON_FINANCE_R3_SPY_CSV to the local capture CSV.
Price/size from Cboe EOD, but spread, timestamp and liquidity synthetic.

Nautilus native Equity/QuoteTick/ParquetDataCatalog, VenueConfig,
DefaultFillModel, MakerTakerFeeModel, EmaCross, BacktestNode
and generate_fills_report all execute. Setting
BacktestRunConfig.dispose_on_completion=False retains cache/report access.
Order.events() includes OrderInitialized, OrderSubmitted, OrderFilled.

IMPORTANT native v2 reports: client_order_id is Pandas INDEX. Reset index
before converting records; plain to_dict(orient=records) loses identity.
The script now reconciles every cached native OrderFilled against its
native report on (client_order_id,trade_id), exact event/account/instrument,
quantity, price, commission and nanosecond ts_event. All 18 sample records
refine correctly; one simulated account only. This validates the local
BacktestNode cache identity and economics, NOT a complete or authenticated
external venue event history. A correction/void causes this bounded
consumer to fail closed. event_id may differ across separate replays.

Native backtest does not make broker orders, PG postings or capital effects.
Do NOT send these synthetic fills to Coordinator's strict next-open bridge.
Source quote authority, correction/restart replay and real economics UNKNOWN.