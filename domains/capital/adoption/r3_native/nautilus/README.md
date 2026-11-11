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

## Narrow native NEXT-OPEN simulation, not live execution

Native Strategy freezes one-share economic intent after previous close
(2026-10-28 16:01 America/New_York), releases native Market IOC only
on the next session open quote (2026-10-29 09:30 New York).
BacktestNode owns market matching, fills, commissions and positions;
there is NO second custom OMS or fill engine. The market quote is
SYNTHETIC from captured Cboe OHLCV with bid/ask=open +/- USD 0.01.

The SPY CSV is hash-matched to the Qlib source receipt and consumed
as a single immutable byte image (no path reopen after checking).
TimeInForce.AT_THE_OPEN is a documented enum but was rejected by
NautilusTrader2.0.0rc9 SimulatedVenue with reason:
'time in force AT_THE_OPEN is not currently supported'.

Native simulation succeeded with 1 opening fill at 09:30 NY,
one simulated USD 768.79 fill and USD 0.02 commission. Native
OrderFilled report comes from the SAME BacktestNode order/cache.
A counterfactual +USD10 next-open price changes the native fill by
+USD10 while order side and quantity remain frozen.

Reproduce on Windows Python3.15 after running sibling OpenBB capture:
  .venv/Scripts/python.exe next_open_native.py
From repo, run native cross-agent bridge probe with same environment:
  .venv/Scripts/python.exe ../tests/probe_native_next_open_consumer.py

The probe normally loads the current integrated Capital bridge. Optional
peer mode loads Agent B's immutable exact Git commit
9f7f948af44233c862b10e34741859bc3cf2c122, NEVER his dirty tree.
It passes the full native BacktestNode to his next_open_native_paper_session
and value_session pure accounting, rejects wrong account, and yields
a one-position in-memory Paper NAV of USD10000.55 from USD10000.
Coordinator has NOT merged these two independent sources into a
production capital consumer. Provider PIT, external PG account binding,
real quotes, market fees, corrections, replay and actual PG posting
remain UNKNOWN or unperformed. The EOD EmaCross sample does not satisfy
this timing contract and must not be sent to the strict next-open bridge.
Agent B independently falsified economic extrapolation: with the same sparse
three-quote synthetic session, native 1-second StaticLatencyModel delayed
the fill to the next 16:01 quote; the strict next-open bridge correctly
REJECTED it. This is a granularity counterexample, not a prediction
of real 1-second market latency. Real tick/quote PIT and execution economics
remain unqualified. U.S. ETF sample settlement is T+1 (2026-10-30),
not T+2; see SEC rule effective May 28 2024.

## Integrated source path

The native next-open consumer probe now defaults to importing the current `ordivon_capital.trading.nautilus_paper_bridge` from the integrated Capital source (`PYTHONPATH=domains/capital/src`). Optional `ORDIVON_FINANCE_R3_BRIDGE_MODE=peer` replays Agent B's exact historical committed bridge, requiring the original Git repository. The probe emits a SHA-256 of the bridge source actually executed. Modelled bid/ask remains synthetic; no PostgreSQL ledger or live venue effect is claimed.
