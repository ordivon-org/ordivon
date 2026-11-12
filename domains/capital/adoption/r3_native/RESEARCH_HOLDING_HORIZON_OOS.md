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
