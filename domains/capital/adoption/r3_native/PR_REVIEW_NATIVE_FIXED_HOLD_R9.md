# Finance R3 native fixed-holding policy: engineering and consumer review

Date 2026-11-12. Parent source revision 33e10ca9d6ec236cbd7d92bc8ac85b869a0156d3.
Standing SIMULATION_ONLY_NON_PIT_NOT_CAPITAL_AUTHORIZED.
Independent Agent audit PENDING.

## Purpose and mature capability LEGO composition

A fixed simple SPY policy must turn an earlier decision into a native BUY,
carry inventory for 5 or 20 complete exchange sessions, SELL at the following
opening and settle all fills with the existing Paper valuation.

Existing capabilities only: Capital Portfolio strategic-contribution provides
USD 10000 total, USD 9000 protected, USD 1000 sleeve, executionAuthorized=false;
native NautilusTrader 2.0rc9 Strategy, BacktestNode, native Limit IOC,
OrderFilled and OrderCanceled; existing Capital Trading next_open_paper_session
and Accounting value_session. No new OMS, exit scheduler, Portfolio optimizer,
PG ledger, live broker adapter or external network component.

Only normalized historical OpenBB/Cboe SPY prices are used; every quote is
a synthetic OPEN/CLOSE-derived bid/ask with a 1-cent half-spread. None of
these historical price proxies proves real fill prices, historical PIT,
broker latency, market microstructure, dividends or adjustment quality.

## True original-source native execution and economic valuation

One fixed share, retrospectively chosen 2025-10-01 decision; actual
native simulated entry is 2025-10-02 OPEN. Exits are NEXT-DAY OPEN
after H FULL trading sessions, not the final holding day's close.

| Scenario | Nautilus native effect | Existing Paper result |
| --- | --- | --- |
| H5 fixed holding | BUY 670.45, SELL 673.51, total fees 0.02 USD | Cash 10003.04 USD, no position/receivable, reserve 9000 |
| H20 fixed holding | BUY 670.45, SELL 683.83, total fees 0.02 USD | Cash 10013.36 USD, no position/receivable, reserve 9000 |
| Entry IOC unfilled | One canceled BUY, no sell order, zero fills | Cash unchanged 10000 USD, zero positions |
| Exit IOC unfilled | Initial BUY filled, exit SELL canceled | Test fails closed; NO successful terminal receipt |

Actual Windows native run Job job-01a1cf4c-70bb-74e3-ae43-1867290a724e.
Three successful runs exit 0 and the expected canceled-exit negative run exit 1.
All market/data/account actions are isolated simulations; real broker/PG effects
remain NONE. The fixed test rule was chosen BEFORE the retrospective backtest
but NOT historically established in 2025.

## Root incompatibility with existing Qlib research

The earlier Qlib H5/H20 label uses T+1 OPEN to T+H CLOSE, while the
executable entry/exit policy here uses T+1 OPEN to T+H+1 OPEN. Overnight
gaps materially change results. Qlib H5 price-only target yielded +2.67 USD
per share, while native H5 after synthetic bid/ask and fee yielded +3.04.
Qlib H20 close target yielded +16.95 per share, while native open exit
yielded +13.36. Do not promote those Qlib forecasts into this strategy.
A future signal must use precisely the actual executable entry/exit horizon.

## Ten-dimensional review and actual evidence standing

| Review category | Status and evidence |
| --- | --- |
| Business goal | PASS bounded: fixed policy enters and exits; no predictive advantage or real investability established |
| Consumer line and effect boundary | PASS simulation-only: preserved capture to Nautilus to existing Paper; no PortfolioIntent, broker, or PG write |
| Data and economic correctness | PASS within synthetic model: two native order/filled events, native cache positions_open=0, Paper cash, fee and settlement; historical PIT/adjusted return UNKNOWN |
| Performance/resources | Four native invocations approximately 2 seconds each; Windows host free RAM before 0.84 GiB/after 0.79 GiB; peak RSS, p95, prolonged leaks UNKNOWN |
| Reliability/recovery | PASS native canceled entry avoids fictitious sale; canceled exit cannot produce settled success; real PG crash/restart N/A |
| Observability/audit | Native order/fill reports, cache event witness, explicit Paper cash, refusal and standing; not certified venue receipts |
| Architecture/evolution | Test-only native consumer; reuse existing strategy/bridge/valuation, no alternative order manager; session-streaming production bridge remains unimplemented |
| Ecosystem/supply chain/compliance | Existing pinned Python/Nautilus and existing Capital source, no new dependencies; Cboe redistribution rights, financial compliance UNKNOWN |
| Tests/formal refinement | Filled sell requires held share and prior-session decision; terminal cash conservation, canceled buy/sell counterexamples; optimized Python rejected |
| Docs/team collaboration | This review and the existing source test. Actual independent Agent review of exact new Git SHA PENDING |

Complete repo CI not run on memory-constrained host, NOT_RUN rather than PASS.
This is NOT a historical backtest with real quotes, and not an investment
recommendation. Maintain the existing simulation-only Risk/Portfolio boundary.

## Reproduction without new infrastructure

Use existing locked NautilusTrader Python environment and Capital src.
Set ORDIVON_FINANCE_R3_SPY_CSV, ORDIVON_FINANCE_R3_SOURCE_MANIFEST,
ORDIVON_FINANCE_R3_RUN_OUT_DIR to a fresh writable isolated directory,
and ORDIVON_FINANCE_R3_HOLD_SESSIONS=5 or 20. Optionally set test-only
ORDIVON_FINANCE_R3_TEST_NO_ENTRY=1 or
ORDIVON_FINANCE_R3_TEST_NO_EXIT=1 for fault scenarios.
Run the existing test-only consumer at
domains/capital/adoption/r3_native/tests/probe_native_buy_hold_exit.py.
Do not use optimized Python mode or real credentials.
