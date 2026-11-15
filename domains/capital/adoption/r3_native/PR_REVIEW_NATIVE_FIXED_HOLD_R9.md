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

## R10 · Actual Qlib-score-driven executable Paper simulation (Agent A)

Acceptance was changed by the user: **execution now matters, research outperformance does not**. Never reject a simulation merely because its predicted return is poor or a test strategy loses money. Continue to distinguish SIMULATION_ONLY from live authority, and preserve economic source/PIT uncertainty.

Original fully native scenario source is B exact Git 46f8c46051ea9ac9c9379eef282198e20f70d79c, independently replayed by another actual Agent A in Windows Job job-01a1cf97-01bc-7f80-b452-015353972898 exit0: native SPY BUY1 $670.45, SELL1 $673.51, fee $0.02, existing Paper cash $10,003.04, zero native open positions. It remains a test-only fixed SPY policy; the A integration below reuses that source directly rather than creating a new OMS, ledger or strategy runner.

Agent A's actual compositional change: use the output of the real existing Qlib0.9.7 DatasetH/LightGBM OOS prediction for a requested historical decision date, select the maximum-score ETF with fixed alphabetical tie-breaking, feed that symbol to the **existing** Capital Portfolio strategic contribution sleeve ($1000 available, $9000 protected), and execute the already existing NautilusTrader Strategy/BacktestNode/LimitIOC BUY/HOLD/SELL with mature `next_open_paper_session` + `value_session` for each historical session. The actual symbol/cost/Paper holdings change with Qlib's input; quantity remains fixed at exactly one whole share. No alpha/market-performance threshold applies.

| Native true-model decision (no score intervention) | Selected instrument | Native buy -> sell | Pure Paper final cash |
| --- | --- | --- | ---: |
| 2025-10-01 / H5 | IWM | 242.99 -> 246.23, fee 0.00 | $10,003.24 |
| 2025-10-15 / H5 | QQQ | 605.11 -> 604.87, fee 0.02 | $9,999.74 |
| 2025-12-11 / H5 | SPY | 688.18 -> 676.56, fee 0.02 | $9,988.36 |
| 2025-10-01 / H20 | IWM | 242.99 -> 245.29, fee 0.00 | $10,002.30 |

Actual Windows Runtime Jobs: H5 IWM job-01a1cf88-a8bd-7241-9d9e-6acbc450ee37 (also final re-test job-01a1cf9a-5590-7320-a610-67a62864d8da), H20 IWM job-01a1cf89-fa32-70f1-94d3-6539cf071cd8, natural H5 QQQ job-01a1cf94-a599-7a13-ab25-de9e69f20861, natural H5 SPY job-01a1cf95-702b-7e90-8fe8-b91e046e0998; all exit0, two native filled orders, no native or Paper open positions, reserve9000 retained and Paper receivable settled. Losing scenarios intentionally still execute.

Independent intervention/cancellation counterexamples: `ORDIVON_FINANCE_R3_TEST_FORCE_ASSET=SPY/QQQ` clearly marks a *test intervention*, not real Qlib output, and changes the native instrument/fill and Paper cash (jobs job-01a1cf8a-d0d1-70d2-b202-7a94406ec5bb and job-01a1cf8c-15b7-7423-b184-ac30bdad9515, exit0). Native BUY IOC canceled -> 0 fills/no SELL/cash unchanged $10000 (job-01a1cf8d-4da2-7930-8db4-21eb7075ca9a, exit0). Native SELL IOC canceled -> original position remains and source raises, exit1, NO successful result (job-01a1cf8e-74ae-75f3-aad1-fb6e50bafe07). A real duplicate run to a pre-existing successful output directory explicitly fails *before running native effects* (job-01a1cf9a-d847-7920-a78a-05c323e7d50b, exit1).

| Required PR dimension | Evidence / standing |
| --- | --- |
| Business goal | PASS scoped: real Qlib scores determine symbol, native OrderFilled/OrderCanceled and existing Paper cash; no alpha prerequisite. |
| Core consumer/authority | Existing Qlib -> existing Portfolio allocation -> existing Nautilus BacktestNode -> Trading bridge -> pure Paper. No broker/PG/live capital. |
| Economic correctness/data | Valid native quote simulation, real event/cash reconciliation, reserve intact and exit-failure not accepted. Historical capture PIT, dividends, corporate actions, true L1 and full costs UNKNOWN. |
| Mature external reuse | Qlib0.9.7, NautilusTrader2.0rc9, Portfolio, bridge and Paper; selective cherry-pick B exact source. No new optimizer, execution engine, registry or dependency. |
| Performance/memory/resource | Small bounded one-share replay, isolated outputs, no persistent service; long-term peak RSS, throughput SLA, workspace leak and GC UNKNOWN. |
| Reliability and observability | Native orders/fills/cache and Paper output, fresh-run output guard, entry cancellation and failed exit tests. No false terminal success. |
| Security/supply chain/standards | Private capture, simulation only, no new dependencies, no credentials/production DSN; vendor use license, broker and regulatory obligations UNKNOWN. |
| Formal/refinement | Native fills must imply recorded Portfolio symbol, whole-share budget, matching Paper positions/cash, canceled order cannot produce imaginary fill; Qlib historical PIT unqualified. |
| Long-term evolution/technical debt | Extend existing B 349LOC test-only Native driver with a narrow model selection, no second Strategy/OMS. Long-running multi-day event streaming into production PG not yet implemented. |
| Other real-Agent review | A independently reviewed B original exact46f8; this modified A source requires actual B/Coordinator new commit audit and has NOT YET PASSED independent review. |

**Important economic target gap:** the original Qlib 5/20-session label is next OPEN to T+H CLOSE, while the native executable policy exits at T+H+1 OPEN; this code uses the forecasts only as symbol selection, not as correctly calibrated returns. This semantic difference must not be called prediction-to-return equivalence. Another Agent B independently is building an opt-in native Qlib NEXT_OPEN-target with upstream Qlib TimeAdjuster; reuse that existing commit when verified, rather than implementing new research training here.

Machine evidence: `native_qlib_signal_execution.evidence.json`. All economic effects are retrospective SYNTHETIC Paper; real orders, actual PG writes and capital authorization NONE. The original model on 2025-10-01 ties all three symbols; IWM is the deterministic alphabetical tie break, not a demonstrated dynamic edge. Historical model decisions were not actually deployed in 2025.

## R10 · Final time-matched real Qlib → native order → Paper economic execution

Supersedes the earlier H5/H20 CLOSE-vs-NEXT_OPEN qualification only for the **new opt-in matched research source**. Agent B supplied and was credited for the real additional Qlib `NEXT_OPEN` producer in original Git commit `3487d4203bc2216de2b692017b852799e971b7f1`, cherry-picked preserving its Git author as `abfced59d79f05089a2319b861197eeafc35eb89`. Qlib default historical CLOSE research mode remains unchanged. The existing native execution consumer now **requires** Qlib signal_quality.exit_price_kind=next_open and both source claims that its T+H+1 OPEN label matches the actual native sale; old CLOSE-source research is rejected BEFORE native order admission (real Runtime job-01a1cfa3-d365-7960-a1a2-9dcf3cc2a8d8 exit0 for deliberately expected negative case). This requirement is economic target correctness, NEVER a predictive profit/alpha gate.

True native Qlib 0.9.7 retraining on independent frozen private OpenBB Cboe capture in Job job-01a1cf9f-f215-7903-a6df-3bf896b7015a exit0: H5 NEXT_OPEN 801 OOS rows and H20 NEXT_OPEN 756 rows, both Qlib native train→valid/test purged. The resulting actual scores are consumed by the existing native Strategy/BacktestNode/Limit IOC and PaperSession/value_session (NOT synthetic JSON-only orders) in Job job-01a1cfa1-5395-7a91-a652-1c4d384bc63e exit0:

| Actual Qlib decision / matching native exit | Real model-selected ETF | Native simulated fills | Paper final cash |
| --- | --- | --- | ---: |
| 2025-10-01; H5, exit 2025-10-09 OPEN | IWM | buy242.99, sell246.23, 2 fills | $10,003.24 |
| 2025-10-03; H5, exit T+6 OPEN | QQQ | 2 filled native orders | $9,991.25 |
| 2025-10-14; H5, exit T+6 OPEN | SPY | 2 filled native orders | $10,005.17 |
| 2025-10-01; H20, exit 2025-10-30 OPEN | IWM | buy242.99, sell245.29, 2 fills | $10,002.30 |

True Qlib QQQ and SPY distinct-date branches independently verified in job-01a1cfa2-dca3-7fa0-84c5-929e7bdb1cd5 exit0, each 2 Native OrderFilled and 0 Native cache positions_open. The model has no demonstrated alpha, **but the exact same maturity/matched economic machine does execute both positive and negative outcomes**. Allocation is existing `plan_strategic_contribution` whole-share example: $10000 pure Paper start, $9000 protected, $1000 available, 1 share per open order. This is not a general multi-asset portfolio target or true production account binding.

Matched-mode cancellation and negative verification: native IOC BUY canceled → 1 order/0 fills, $10000 unchanged, 0 native positions (job-01a1cfa4-3ae8-7503-9d46-e9e312c455b2 exit0). Native SELL canceled → 1 position remains, economic success receipt absent, native job-01a1cfa4-bc71-7bd0-a9f3-572c41b65abd exit1 as expected. Deliberately reusing prior finished output is denied before a new native execution (job-01a1cf9a-d847-7920-a78a-05c323e7d50b exit1). The older unaligned model exit was rejected before native orders; the new matched label and execution were observed and independently linked by existing Qlib/Portfolio/Nautilus/Paper consumers.

Ten-dimensional PR check in final state: business deliverable PASS simulation execution without profit gate; consumers PASS for Native Qlib→Portfolio sleeve→Native engine→pure Paper (no PG or broker); financial semantics PASS for matched OPEN-exit event, but PIT, real market quotes, dividends, corporate actions, vendor rights and capital identity remain UNKNOWN; mature modules reused, no new Rust/TS/Python dependency/OMS/ledger/scheduler; actual native bounded runs completed, but sustained RSS, Workspace GC/lifetime and service throughput UNKNOWN; retries/canceled exit fail closed, no incorrect paid-out success; native order/cache/cash/recorded source evidence available; exact formal counterexamples prove no fill on failed buy and no success on failed sell, but no full strategy theorem; long-term reduce test-only 349LOC after an actual supported production consumer supersedes it; independent Agent B or Coordinator review of this new A source still PENDING, and no Github PR/production CI pass is claimed. This work never touches a production PG DSN, broker adapter or real capital.

Full machine summary updated in `native_qlib_signal_execution.evidence.json`. Previous CLOSE label tests preserved as legacy evidence but are **not** accepted as current qualified economic contract. User explicitly removed a profitability prerequisite, not requirements to preserve source/capital truth.

## 2026-11-13 prediction output authority falsifier (P0 repaired, SIMULATION_ONLY)

The R10 model-to-order consumer checked market source hashes but accepted a
rewritten Qlib prediction CSV as genuine OOS score. Actual negative input:
on 2025-10-14 one private copied IWM score was changed to 1.5, with original
model manifest and Cboe captures unchanged. The PRE-FIX native consumer
selected IWM (rather than natural SPY), produced two native SIM fills, and
still stated native_Qlib_0.9.7_OOS_score; Windows Runtime Job
job-01a1d09c-a955-71d3-ac47-38bb5bdfb77e exit0. This falsified
the consumer's model-score-source authority, not its simulated fills.

Minimal repair: Qlib's own producer records the sha256 of the exact
qlib_test_predictions.csv beside its native study; existing native consumer
pins that file once, checks the study's matching prediction digest before
any success receipt or native order, and parses the pinned bytes. No new
framework/OMS/ledger/data provider. A focused existing native_nonlive
pytest lane checks an isolated rewritten prediction is refused.

After exact cross-host source synchronization the installed Qlib0.9.7 native
producer reran H5=801 and H20=756 OOS rows, Job
job-01a1d0a1-2b92-7843-a139-069d7f9db750 exit0. Unmodified genuine
model scores selected QQQ, SPY and IWM in Nautilus/Paper, Job
job-01a1d0a2-dcb6-7ce0-8e54-2ecca05b0b4a exit0. The rewritten CSV
was now explicitly rejected before a native successful receipt, Job
job-01a1d0a3-778a-77c2-b5d1-b1652ef081c4 exit0. Actual native/PG18
full financial consumer was replayed under exactly patched source for
H5/SPY, H20/IWM and H5 canceled entry, 8/23/8 daily committed receipts,
physical PG stop/restart and exact readback PASS, Job
job-01a1d0a4-5f19-7913-9be9-293c7afdb2e0 exit0. PG stopped.
Native CI regression Job job-01a1d0a6-5294-75c9-a2c5-0b377f6b4e9d exit0.

Scope: LOCAL STUDY CO-ARTIFACT CONSISTENCY, not independent authentication
against jointly forged study+CSV, verified vendor PIT, model alpha, real
capital mandate, broker permissions or production PG effects. Older local
studies missing the new field are rejected for native execution until rerun
through the same mature Qlib producer.
