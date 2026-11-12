# Finance R3 · Investment horizon and economic-baseline consumer (2026-11-12)

## First-principles contract

**Problem (L0–L4):** Native Qlib successfully predicts a test signal, but that does not imply incremental investor wealth or compatibility with the actual Capital Paper position lifecycle. Before implementing more agents, order bridges or optimizers, compare the **same prediction-date, execution-date, return horizon and cash envelope** against simple policies.

**Reuse (capability LEGO):** Real earlier OpenBB Cboe source capture and Qlib DatasetH/LightGBM/Recorder; existing Capital `portfolio.passive_benchmark.replay_passive_benchmark` and `portfolio.strategic_contribution.plan_strategic_contribution`. No new forecasting/optimization/backtest engine, broker, account ledger, runtime or CI platform.

**Native run:** `domains/capital/adoption/r3_native/tests/probe_qlib_paper_horizon.py` within the existing *research Python 3.11* environment after `etf_qlib_consumer.py` generated its original Qlib dataset, test predictions and source-capture outputs. It verifies the actual Qlib label against next-session open/close, evaluates 272 successive test decisions (2025-10-01–2026-10-29; economic trades through 2026-10-30), and reuses the existing passive replay with the same 272 session cashflows and assumed gross returns. The test has no network, PostgreSQL, trading or external effects; generated raw provider data is not committed.

**Capital envelope:** Simulated initial account $10,000; $9,000 protected cash; $1,000 hypothetical investment sleeve from the existing read-only Portfolio contribution projection. Fractions of shares are assumed, so this is **not** a whole-lot Paper execution backtest. Daily ETF switching requires same-day sale, which the current Paper account does not support. The fixed QQQ vs fixed SPY cross-session holding comparison is separately shown as a different, more Paper-compatible economic horizon; its exact lot-size execution is also not qualified.

**Measured OOS outcome:** Source Qlib regressor MSE `7.5134035533e-05` vs zero `7.4997825689e-05`, train-mean `7.5008494272e-05`; no dominance. For fixed research test-window signals, hypothetical highest-score daily ETF selection chooses IWM 165, QQQ 71, SPY 36 times. At zero assumed daily transaction cost, the $1,000 sleeve underperforms SPY same-day intraday by **$21.2409**, and three-ETF same-day equal weight by **$25.0593**. At hypothetical symmetric daily roundtrip fee fraction 0.001 applied equally to model and SPY, difference is **-$16.1803**. In the different fixed open-once, hold-through-test-window exposure, QQQ outperforms SPY by $10.2141, a descriptive result **not produced by the Qlib predictor**. All figures omit actual fills, tax, dividends, corporate actions and real friction.

**Standing:** `RETROSPECTIVE_NON_EXECUTABLE_HYPOTHETICAL_ONLY`, `PortfolioIntent=NONE`, `PIT=UNKNOWN`, `real economic effect=NONE`. This is direct evidence **against** promoting the current signal to live investment or native order generation; it is not proof that a different signal or strategy cannot work.

## PR-level review: complete business and engineering checklist

| Dimension | Evidence and decision |
| --- | --- |
| Business objective / measurable acceptance | Cross-horizon actual Qlib OOS signals measured against same-period passive alternatives; negative economic comparison established, model not admitted. PASS for scoped experiment. |
| Consumer chain and boundaries | Qlib test predictions + DatasetH LABEL0 + original Cboe EOD → existing passive benchmark + existing Portfolio capital envelope. No new portfolio mandate or OMS. PASS. |
| Data quality and economic correctness | Verified T→T+1 open-close label and separate multi-session hold. Historical source availability, corporate actions, dividends, raw vendor rights and realistic costs UNKNOWN. |
| Native vs custom reuse | Existing Qlib, pandas/pyarrow, Portfolio and PassiveBenchmark algorithms; one bounded test-only composition, no new production service. PASS. |
| Performance and memory/resource budget | 816 Qlib prediction rows, 272 economic periods, no persistent processes or new workspaces; one observed bounded Runtime execution. Production memory/throughput/leak UNKNOWN. |
| Reliability / recovery / observability | Fail-fast for missing/unaligned labels, nonfinite scores, mixed dates and optimized Python; output JSON to ignored test artifacts, reproducible with original private capture. Production retry/recovery N/A. |
| Audit and provenance | Exact source producer receipts and run-specific model skill embedded in aggregate evidence, all model effects remain NONE. Original data not redistributed. Historical PIT UNKNOWN. |
| Supply chain/security/external standards | Existing locked research environment, no added dependency, no keys, order, broker or PG. Financial compliance/market-data redistribution qualifications UNKNOWN, not claimed. |
| Formal/refinement and negative cases | Positive next-session label equality; same-day shift differs materially; model fails simple OOS MSE baselines and economic alternatives; consumer horizon cannot be refined to same-day Paper liquidation. PASS scoped, complete strategy proof NOT_DONE. |
| Long-term evolution / technical debt / cross-agent review | Keep until another genuine Agent checks measurable consumer value; prefer DELETE if baseline test becomes redundant. Another Agent review **REQUESTED**, not approved. No fictional owner. |

**Independent review request:** Inspect the actual committed consumer + evidence, challenge assumptions that may exaggerate/invert relative wealth, test at least one contrary data or return-horizon case, and state exact `PASS/FAIL/UNKNOWN` in the Finance R3 Host Topic. An author self-review is not peer approval.

## Native replay and test limitations

- Actual Qlib-to-PassiveBenchmark economic consumer: Windows Runtime job-01a1cf15-f883-7371-9652-60cf1bd67947, exit 0, 272 dates, 816 predictions, zero orders and PG effects.
- Existing Portfolio PassiveBenchmark and StrategicContribution regression: 82 native Windows pure-Python cases passed. Two legacy cases require a POSIX shell launcher and fail Windows WinError 193; they are not counted as passed, and require supported Linux integration replay.
- Optimized interpreter negative: the new economic probe rejects Python -O before model/data evaluation, verified via a separate native Windows Runtime job. This does not confer economic authority.
- Independent agent acceptance still PENDING.

## R8: native Qlib holding horizon and economic-consumer independent review

Agent A independently reviewed Agent B's exact source commit 93c052eebd089a07d8f5c4e401c712c28f897f2f, cherry-picked with original B author as 33e10ca9d6ec236cbd7d92bc8ac85b869a0156d3. The native H1/H5/H20 Qlib experiment, existing Portfolio budget and passive-benchmark consumers were re-executed, without new ML/OMS/ledger/strategy dependency.

Actual RED: B H1 changed a pre-existing signal_quality.horizon string while preserving 816 prediction rows/MSE; the previous test-only Portfolio economic consumer rejected it in job-01a1cf3c-c6fb-75b0-b0fa-0be326e92de6. A restored exactly the H1 previous consumer contract and retained new H5/H20 horizons. Native Qlib H1 and all three economic consumers then passed in job-01a1cf3d-e31d-7661-a63a-f74f0c13dfaa.

Predeclared strategy: at every Hth test decision date, select the ETF with maximum native Qlib OOS score, enter at next-session OPEN, exit at T+H CLOSE. Horizons H5/H20 are separate fixed experiments, not selected after their test P&L is seen. Each comparison uses the same disjoint entry/exit windows, $1000 hypothetical fractional-share capital and $9000 protected cash. SPY/QQQ/IWM baselines are fixed-symbol exposures within exactly those windows, NOT uninterrupted buy-and-hold. Both sides use identical zero costs or hypothetical symmetric 10bps per window.

| Economic result on $1000 investment sleeve | 5-session (54 windows) | 20-session (13 windows) |
| --- | ---: | ---: |
| Model - same-window SPY | -$74.405879 | -$35.674754 |
| Model - same-window 3 ETF equal weights | -$107.796963 | -$47.286237 |
| Model - same-window fixed IWM | -$94.504420 | exactly $0.00 |
| Model - same-window fixed QQQ | -$146.768972 | -$101.685896 |
| Model - SPY with both assumed 10bps/window | -$70.492614 | -$35.213754 |
| Model-selected ETFs | IWM36, QQQ14, SPY4 | IWM13, QQQ0, SPY0 |

The H20 policy never changes its selected instrument. Its economic outcome exactly equals the fixed IWM policy on all 13 nonoverlapping windows, so no conditional allocation advantage is demonstrated. These outcomes use retrospective unadjusted market OHLCV and assumed fractional shares, not realizable fills. Model MSE improves vs train-mean by only 0.1654% (H5) / 0.2332% (H20), with negative cross-asset IC and low independent sample count. NO model-driven PortfolioIntent or trading is justified.

| PR required dimension | Status and evidence |
| --- | --- |
| Business outcome | PASS scoped negative result: model does not beat simple economic baselines; reject promotion |
| Core consumers/boundaries | Native Qlib -> same existing Portfolio PassiveBenchmark and StrategicContribution; no orders/PG |
| Financial correctness & input data | H dates use T+1 OPEN to T+H CLOSE and no overlap; PIT, price adjustment, rights, dividends UNKNOWN |
| Reuse vs custom | Qlib native TimeAdjuster and segments; existing Portfolio replay; no duplicated optimization or execution engine |
| Performance/memory/disk | 3 native Qlib modes ~19s; each generated 333-343KB ignored output; 853MB free RAM snapshot, zero remaining test Python processes; sustained RSS/leak UNKNOWN |
| Reliability/recovery/observability | Actual H1 contract break caught and repaired with independent native rerun; label equality and no-overlap checked; no external effects |
| Supply chain/security/standards | No new packages, credentials, licensing or real investor authority; existing locked Python research components used, vendor redistribution UNKNOWN |
| Formal/refinement | Future-label purge from B; T+H labels matched actual bars, disjoint exposure; H20 model/fixed-IWM economic identity established |
| Long-term evolution/technical debt | One existing experimental consumer extended; no new service/MLflow manager/OMS; retain test only while used as regression |
| Real other-Agent audit | A audited B 93c and found H1 break; A final integrated fix and economic extension still need another real Agent review, PENDING |

Reproduction: set ORDIVON_FINANCE_R3_RESEARCH_HOLD_SESSIONS=1/5/20 and distinct ORDIVON_FINANCE_R3_RESEARCH_OUT_DIR; run native etf_qlib_consumer.py with the original private capture; then run existing tests/probe_qlib_paper_horizon.py against each output. Machine result: qlib_disjoint_horizon.evidence.json. Standing: RETROSPECTIVE_NON_EXECUTABLE_HYPOTHETICAL_ONLY. Historical PIT, true order cost, corporate actions, dividend treatment, integer lot and capital authorization not admitted.
