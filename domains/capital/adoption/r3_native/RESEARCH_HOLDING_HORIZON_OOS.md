# Finance R3 — economic holding horizons and Qlib OOS evidence

Date: 2026-11-12. Research source baseline: 681add9e7df0fce573f3367605b08504d26dc307.
Status: RETROSPECTIVE_BACKFILL_RESEARCH_ONLY. No capital policy, approved portfolio target, paper-PG writes, real orders or historical point-in-time proof.

## Logic module: economic objective and holding period

The original model predicts T+1 open to SAME-DAY close, but PaperSession cannot sell shares bought on that same day. Thus an intraday IC cannot establish value for its actual multi-day holding consumer.

The same Qlib/LightGBM source now supports an opt-in T+H close / T+1 open - 1 research target, for H in 1, 5, 20 exchange sessions. The default H=1 is unchanged. Multi-session sales can be represented in the existing Paper state machine, but research-driven exit orders remain absent and execution eligibility stays FALSE.

Long labels can overlap training/validation/test windows. Reuse Qlib TimeAdjuster and trunc_segments with the PINNED offline session calendar; enforce two runtime refinements:

1. Last TRAIN decision + H exchange sessions STRICTLY PRECEDES first VALIDATION date.
2. Last VALIDATION decision + H exchange sessions STRICTLY PRECEDES first TEST date.

The offline Qlib StaticDataLoader has no D.calendar and therefore attaches its same observed session calendar to the existing Qlib TimeAdjuster; this is a research-only adaptation, not a new calendar engine.

## Measured native Qlib 0.9.7 / LightGBM outcome

Same actual OpenBB/Cboe captured 3 ETF normalized raw price histories: 962 sessions each. Three independently separated native experiment outputs, Qlib's official SigAnaRecord, actual held-out labels, train-only baselines.

| OOS measurement | 1-session default | 5-session hold | 20-session hold |
| --- | ---: | ---: | ---: |
| Samples / test decision sessions | 816 / 272 | 804 / 268 | 759 / 253 |
| Last train decision | 2024-12-30 | 2024-12-23 | 2024-12-02 |
| Last validation decision | 2025-09-29 | 2025-09-23 | 2025-09-02 |
| Model MSE | 0.0000751340 | 0.0004501636 | 0.0019577161 |
| Improvement over predicting ZERO | -0.182% | +1.211% | +5.963% |
| Improvement over train-only mean | -0.167% | +0.165% | +0.233% |
| Improvement over train-only per-ETF means | -0.008% | +0.638% | +1.081% |
| Qlib IC / Rank IC | -0.086 / -0.099 | -0.099 / -0.091 | -0.070 / -0.097 |
| Approx. disjoint H-session blocks | 272 | 54 | 13 |

H=20 average forecast 0.0165819 versus training-sample mean 0.0165801; its forecast standard deviation is only 0.000438 versus realized label standard deviation around 0.044. This is almost an unconditional prediction. The model exhibits NO demonstrated investment-management or cross-asset selection advantage; negative IC is an independent warning. Small MSE differences do not imply economic alpha or authorization.

Separate seeded descriptive block resampling of loss difference (train-mean baseline minus model) gives approximate 95% ranges: H5 [-2.76e-7,+1.80e-6], H20 [+4.12e-7,+1.08e-5]. These are not robust formal confidence guarantees: SPY/QQQ/IWM are correlated, outcomes overlap, 20-session results have only ~13 disjoint blocks, and several horizons were inspected on the same test set. No winner selection is admitted.

## Native Accounting consumer refinement: real 5/20-session positions

A separate independent REAL Python test reused the existing Capital paper_close.py / PaperSession / value_session, with actual captured SPY OPEN/CLOSE dates, 1 share, no invented broker fees and no PG financial writes. It applied every daily state transition, T+1 settlement of buys, actual later sale and final settlement. Native Job: job-01a1cf22-7bd9-72d1-9568-ded0cc34ebe4, exit 0.

| Pre-fixed holding | Entry | Exit | Retrospective label | Pure Paper cash gain |
| --- | --- | --- | ---: | ---: |
| 5 exchange sessions | 2025-10-02 OPEN $670.44 | 2025-10-08 CLOSE $673.11 | +0.3982459% | +$2.67 |
| 20 exchange sessions | 2025-10-02 OPEN $670.44 | 2025-10-29 CLOSE $687.39 | +2.5281904% | +$16.95 |

The position gain from Paper equals the corresponding target within cent rounding, and terminal receivables settle to cash. Reusing the same Paper state on a buy and sell in ONE session yields the actual rejection: paper sell exceeds held shares. The Paper sale date still requires a **previous-session** decision timestamp; no pre-committed policy schedule exists to issue that future sale automatically. The closing-price fills here are synthetic retrospective price proxies, not true historical Nautilus executions or certified vendor data.
## PR acceptance across natural consumers

| Dimension | Actual evidence / unresolved |
| --- | --- |
| Business value | Research target matches expressible investment holding duration. No improvement in ACTUAL portfolio wealth is demonstrated. |
| Core consumer and authority | Same OpenBB capture to Qlib to separate score. Trading, Portfolio decision, Risk and Accounting receive NO new authorized action; Paper can represent a later sell but no live sell policy was added. |
| Correctness and data | Exact default H1 dataset SHA e14deedead6efe85f0c460466cffd965d78d23c66b6a1704912e13c8b2113435 and old 816 rows/MSE independently match before change. H5/H20 use real exchange-session purge and fail on overlaps. Vendor PIT, adjusted total returns, rights, corporate actions remain UNKNOWN. |
| Performance, RAM, storage | One Windows native job ran all three modes in 34.6 s, EXIT0. Windows free RAM observed roughly 0.66–0.75 GiB during the experiments, but process peak RSS and production stress budget remain UNKNOWN. Full private experiment output staged outside Git occupied 2.25 MiB. Full monorepo CI was NOT_RUN because the observed host had less than 1 GiB free memory; no throughput, stress, or leak conclusion. |
| Reliability / recovery | Bad hold settings or missing forecast/test rows fail closed. Crash while writing MLflow/file output is not an economic transaction; no PG/broker activity. |
| Observability | Existing Qlib SigAnaRecord, MLflow recorder and machine-readable forecast scores; run's selected horizon and test sample count are explicit. |
| Architecture / evolution | One existing Python research script extended. No new ML framework, strategy, optimizer, order manager, ledger, background agent or registry. |
| Reuse / supply chain / compliance | Existing locked Qlib/LightGBM/pandas/OpenBB; upstream Qlib TimeAdjuster and trunc_segments, no added dependencies. Source licensing and historical PIT still UNKNOWN; no regulatory approval implied. |
| Formal refinement | TRAIN label endpoint before VALID start; VALID label endpoint before TEST start. Both enforced at the consumer boundary. Unknown cannot become false or pass. |
| Independent review | Await separate actual Agent review of final candidate Git SHA. A review request alone is NOT approval. |

## Reproduce without modifying the frozen capture

Use the already installed Qlib/LightGBM research environment, the existing etf_qlib_consumer.py, and set ORDIVON_FINANCE_R3_CAPTURE_DIR to the user-private captured OpenBB dataset. Specify separate ORDIVON_FINANCE_R3_RESEARCH_OUT_DIR locations and ORDIVON_FINANCE_R3_RESEARCH_HOLD_SESSIONS=1, 5 or 20. Omitting the holding setting preserves the original 1-session experiment. Do not use these test results to choose a production horizon or promote forecast.usable_as_optimizer_expected_return.

Mature upstream: https://github.com/microsoft/qlib/blob/main/qlib/workflow/task/gen.py

## R10: executable next-open exit target, actual economic stress, no alpha admission

Date 2026-11-12. Parent baseline c0c1947df56a5a2b9719e312fa4a202002df209a.

### Core problem and mature solution

Earlier H5/H20 Qlib research modeled entry T+1 OPEN to exit T+H CLOSE. The
already-verified NautilusTrader Strategy plus the existing next-open Paper
consumer actually buys T+1 OPEN, HOLDS H full exchange sessions, and SELLS
T+H+1 OPEN. The difference is an overnight gap, not a JSON/interface bug.

The single existing Qlib research consumer now accepts opt-in
ORDIVON_FINANCE_R3_RESEARCH_EXIT_PRICE=next_open with H=5 or 20; omitted
value remains close for every legacy 1/5/20 replay. Label is future
OPEN[T+H+1]/OPEN[T+1]-1. Qlib native TimeAdjuster/trunc_segments use the
source's actual session calendar and prune one MORE session than the earlier
T+H CLOSE research before training and validation. Both economic label
endpoints must STRICTLY precede the next segment's first decision session.

The already-existing independent Portfolio test consumer
probe_qlib_paper_horizon.py now reuses the SAME PassiveBenchmark for either
exit price, on the same entry/exit schedule for model, SPY, QQQ, IWM and
equal-weight alternatives. No new engine, policy scheduler, optimizer,
backtester, production order manager, SQL/PG writer or external dependency.

### Actual unchanged old and new Qlib ML results

Real Qlib 0.9.7, existing LightGBM, OpenBB/Cboe frozen SPY/QQQ/IWM
captures. Five sequential REAL native runs, total 52.88 s, Job
job-01a1cf87-f543-7c81-96c3-1b76ef59e3af, all exit 0.
Legacy H1 816 OOS rows / exact same dataset SHA / MSE as before;
legacy H5 CLOSE 804 rows and H20 CLOSE 759 rows also exactly reproduced.

| NEW executable target | H5 NEXT OPEN | H20 NEXT OPEN |
| --- | ---: | ---: |
| OOS rows / decision dates | 801 / 267 | 756 / 252 |
| Model MSE | 0.00047976648 | 0.00200204381 |
| ZERO MSE | 0.00048778328 | 0.00213405919 |
| TRAIN-only unconditional mean MSE | 0.00048063893 | 0.00200466582 |
| MSE improvement vs TRAIN mean | +0.1815% | +0.1308% |
| Native Qlib IC / Rank IC | +0.0337 / +0.0528 | -0.0114 / -0.0299 |
| Approx. disjoint H-session periods | 54 | 13 |

Both new models still show tiny gains over a cheap training-only
unconditional mean. Neither can be treated as validated alpha or as a
forecast entitled to generate PortfolioIntent or real orders.

### The actual existing Portfolio consumer and native effect

The four H5/H20 CLOSE and NEXT OPEN replay combinations in the existing
Portfolio PassiveBenchmark/StrategicContribution consumer all exit 0
(Job job-01a1cf8f-4c73-7ea0-a4c6-78e05d2e231a).
CLOSE results precisely reproduce Agent A's previous model-minus-SPY:
H5 -74.41 USD, H20 -35.67 USD for the 1000 USD investment sleeve.

For the revised, TRUE native opening exit (same fractional-share,
nonoverlapping entry/exit periods, zero illustrative costs):

| Economic comparator | H5, 54 periods | H20, 13 periods |
| --- | ---: | ---: |
| Model minus same-window SPY (1000 USD sleeve) | +88.63 USD | +73.16 USD |
| Model minus same-window ETF equal-weight | +69.09 USD | +66.43 USD |
| Model minus SPY if BOTH pay illustrative 10bps per period | +83.97 USD | +72.22 USD |

A separate, independent, read-only actual-price test on the SPY
2025-10-01 decision proved the new Qlib LABEL equals the corresponding
source OPEN-to-OPEN price change and refines the earlier real
NautilusTrader BacktestNode + PaperSession run, Job
job-01a1cf92-11cd-7591-b6b5-3fc0751f0aaa:

- H5 entry 2025-10-02 OPEN $670.44, exit 2025-10-09 OPEN $673.52:
  gross one-share price gain $3.08; original native BUY $670.45,
  SELL $673.51, simulation fee $0.02, final Paper cash gain **$3.04**.
- H20 exit 2025-10-30 OPEN $683.84: gross one-share price gain
  $13.40; native BID/ASK + fees give final Paper gain **$13.36**.

Thus the specific OPEN exit *economic event* now matches, not a
historical real quote or admitted financial authority. The Portfolio
comparator assumes fractional shares, perfect gross historical opens,
and a simplified symmetric cost scenario, not continuous SPY buy/hold.
There is still no automatic Research score -> authorized Target -> Order.

### Independent economic falsification: decision start-date fragility

A fixed H-period rebalancing cadence is not justified merely because
the earliest OOS date produced a gain. The same existing Portfolio
consumer was replayed at EVERY offset 0..H-1 without changing forecasts,
cost conventions or source data (same read-only Job as above).

- H5: original offset 0 +$88.63 versus SPY, but the five offsets span
  **-$37.41 to +$135.84**; four positive, one negative.
- H20: original offset 0 +$73.16 versus SPY, but twenty offsets span
  **-$210.59 to +$119.88**; only seven positive, thirteen negative.
- Descriptive paired resampling of original-offset period log excess
  returns gives H5 95% percentile interval [-0.0030,+0.0056],
  H20 [-0.0073,+0.0168]. Both include zero; bootstrap periods are
  NOT independent market regimes. This is NOT a valid significance test
  because OOS was repeatedly inspected, horizons and offsets correlated,
  data is not PIT and labels cover only a few independent long windows.

The correct outcome is **DO_NOT_PROMOTE**, regardless of the positive
after-the-fact offset-0 result. This is an example where replacing a
logical representation changes economic results without changing any
existing mature execution engine.

### Formal counterexample and failure boundary

Deliberately mutating only the new Qlib purge back to the OLD
H-only number of exchange sessions caused the ACTUAL native Python/Qlib
H20-NEXT-OPEN process to exit 1 before model fitting:
Research target leaks future labels across train/valid.
Experiment Job job-01a1cf93-d5e5-7382-a902-83af42a4dc3f (driver
succeeded by detecting this expected failure). Correct script all
five modes exit 0. The original H1 Portfolio result, checked with
Job job-01a1cf95-d35e-7312-a5af-8b6ac491faf7, remains unchanged.

### R10 engineering / PR review, with actual standing

| Required dimension | Observed and unresolved |
| --- | --- |
| Business target | PASS scoped: research now tests the same open exit clock event as native holding; no demonstrated investable advantage |
| Full consumer path | OPEN price capture -> Qlib/TimeAdjuster/MLflow -> unchanged Portfolio PassiveBenchmark; native cross-check for one actual Paper case; no admitted PortfolioIntent or broker |
| Correctness and data quality | PASS source-scoped labels and red/green leakage; historic PIT/adjustment/dividends/rights/real L1 order fill all UNKNOWN |
| Performance and resources | Five real Qlib runs 52.88s, four existing Portfolio replays completed; isolated total scratch 2.51MiB. Host free RAM 0.42GiB before and 0.83GiB after ML batch; peak RSS, concurrent budget and leak trend UNKNOWN |
| Reliability / recovery | Extra-session label leakage mutant fails before fit; no real financial side effects; file/MLflow restart behavior not proven as durable transaction |
| Observability and audit | Native recorder/test predictions, Portfolio economic result, logged exact exit price/horizon and prices; external venue receipts UNKNOWN |
| Architecture and evolution | Two existing Python consumers enhanced, one existing Research evidence page extended; DELETE-CUSTOM: no new framework / scheduler / storage / OMS |
| Mature reuse / supply chain / compliance | Pinned Qlib/LightGBM/OpenBB/Portfolio; no new package, regulatory standing or redistribution rights invented |
| Formal tests / negative examples | Two segment nonoverlap invariants, genuine Qlib old-purge mutation, H1 unchanged, matched native cash and phase offsets |
| Agent collaboration | Actual Host cross-Agent communication, independent audit of final SHA PENDING. Review request is NOT approval |

Use a fresh output directory (ORDIVON_FINANCE_R3_RESEARCH_OUT_DIR),
the pinned local capture directory and existing Qlib Python environment.
For the new actual OPEN exit, set both
ORDIVON_FINANCE_R3_RESEARCH_HOLD_SESSIONS=5 or 20 and
ORDIVON_FINANCE_R3_RESEARCH_EXIT_PRICE=next_open. Default CLOSE mode
preserves previous experiments. Do NOT choose an investment horizon or
deploy a policy using this already-inspected historical test set.

## R11: Historical XNYS session qualification and native consumer revalidation (2026-11-14)

Observed counterexample: originally retained Windows Finance R3 SPY/QQQ/IWM
962-row Cboe normalized inputs match original Git receipt SHA-256 values.
Each contains 2025-05-26, when XNYS was closed (Memorial Day).
Vendor calendar labels do not establish a genuine trading event.

Controlled revalidation: existing native Qlib 0.9.7/LightGBM,
Riskfolio-Lib 7.4.1 and native Capital passive_benchmark and
strategic_contribution under the same code revision per pair:

- A: preserve the original 962-row input receipt and results.
- B: remove only that one invalid session from each original SHA-matched
  issuer source (961 rows), no synthetic fill or forecast tuning.
- Five Qlib labels: H1 CLOSE, H5 CLOSE, H20 CLOSE, H5 NEXT_OPEN,
  H20 NEXT_OPEN. Same time windows and cost conventions.
- This CURRENT Qlib source revision: A/B predictions identical across
  816/804/759/801/756 rows respectively; all five Portfolio economic
  comparisons also identical, although five Qlib dataset byte digests change.
  Riskfolio last-252-row CVaR/minimum-variance outputs are unchanged.
- OLDER Qlib source revision had a separate A/B experiment whose H1
  scores changed. Different code revisions confound the interpretation:
  never equate cross-revision results with a single-input causal experiment.
- Evidence in user-private Windows:
  FinanceR3AgentA/calendar-requalification-20261114/economic-revalidation-r2/
  native_5mode_calendar_requalification_matrix.json.
  Private captured bytes, exact source SHA, model snapshots, MLflow recorders
  and Portfolio results remain outside Git.

Natural-owner source fix: reuse pinned exchange_calendars XNYS in Markets
equity_session_calendar.require_xnys_session_grid, BEFORE Qlib feature,
label/TimeAdjuster construction and before Riskfolio returns. The source
provider cannot declare its own actual exchange sessions. The standing
EXCHANGE_SESSION_ALIGNED_SOURCE_UNVERIFIED explicitly does NOT grant
historical PIT, split/dividend/total-return, issuer licensing, PortfolioIntent,
Paper PostgreSQL authorization or live orders.

The Markets guard now checks the declared request window, not merely
the earliest and latest observed date. Otherwise, a stale issuer source
missing only the first/last requested XNYS session would falsely PASS.
The current fixed R3 experiment requests 2023-01-01 through 2026-10-31,
and the qualifying XNYS sequence must cover every true exchange
session in that exact request interval. This still does not attest
first-observed provider publication time or historical PIT.

The fake Memorial Day and missing-session negative controls now belong to
tests/test_market_xnys_source_session_calendar.py, consumed by the existing
Capital verify task. This is native behavior falsification; not a new formally
proved Lean/Z3 implementation refinement. Formal obligations remaining:
the actual date-index equality and Qlib label-horizon TimeAdjuster refinement,
and independent external calendar vintage and publication-time evidence.

Pure Accounting Paper consumer was also run on exact SHA-matched original
and corrected SPY sources with the existing PaperSession/value_session
transition code, without Postgres or broker calls. H5 BUY on 2025-10-02 OPEN,
SELL on 2025-10-09 OPEN and settle after 8 successive XNYS sessions:
both sources end with +USD 3.04 after synthetic fees, zero shares, payables
and receivables. H20 SELL on 2025-10-30 OPEN and settle after 23 sessions:
both end with +USD 13.36, no pending positions or liabilities. The
replayed trading dates are AFTER the observed fake 2025-05-26 date and do
not authenticate fills or retrospective source availability. Private
evidence: economic-revalidation-r2/
native_paper_h5h20_session_calendar_revalidation.json. No Paper
PostgreSQL or external account state was touched.

This scoped revalidation does not rehabilitate synthetic economic results,
historical price PIT, corporate actions, volume, market fills or adjusted price
basis. It settles calendar sensitivity for five current-source model/Portfolio
combinations plus two pure Paper transition paths. It does NOT prove
correctness of original market prices, durable PostgreSQL paper accounting
replay, real broker execution or predictive alpha.
