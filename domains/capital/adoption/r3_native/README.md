# Finance R3 - OpenBB V5 + Qlib + PyPortfolioOpt (read-only research)

Native Python 3.11 consumer: OpenBB Cboe SPY/QQQ/IWM historical OHLCV ->
Qlib StaticDataLoader/DataHandlerLP/DatasetH -> LGBModel.fit / Recorder
/ SignalRecord -> independent PyPortfolioOpt min_volatility math example.

Reproduce inside this directory in an isolated Windows Python 3.11 env:
  uv venv .venv --python 3.11
  uv pip sync --python .venv/Scripts/python.exe requirements.lock
  .venv/Scripts/python.exe etf_qlib_consumer.py

First invocation captures normalized provider CSVs under output/ and
a capture receipt in output/native_study_result.json. This data is not
committed: provider redistribution rights remain UNKNOWN.
To reproducibly replay without network, copy the three CSVs and JSON
into a separate private local directory and set environment variable
ORDIVON_FINANCE_R3_CAPTURE_DIR to that directory. The consumer verifies
each normalized CSV SHA-256 from the receipt BEFORE computing features.
Tampered or incomplete captures must fail closed.

The Qlib session timestamp index is explicitly canonical datetime64[ns].
On the recorded Windows Python3.11 pandas3.1.1/pyarrow26.0.1 setup,
independent live provider fetch and hash-verified offline replay of
identical input bytes produced identical parquet SHA-256. Without this
explicit unit, pandas3 inferred millisecond timestamps for native date
objects and microseconds for CSV strings, changing parquet bytes even
though DataFrames had equal values. This is a representation proof,
not provider accuracy or retrospective PIT proof.

2026-11-14 native source-quality refinement: the existing HILO feature
depends on actual high-low bars, but source SHA and correct XNYS dates do
not certify internal OHLC shape. Natural Markets
equity_ohlcv_shape.require_ohlcv_shape_for_hilo now rejects contradictory
OHLCV bars BEFORE training or generating HILO features. The original
private Cboe snapshot has QQQ 2026-05-20 high 713.13 below close 713.15
(2 cents / ~0.28bp) and IWM 2023-06-05 high 180.82 below open 181.37
(55 cents / ~30.63bp); SPY had no such anomaly. It rejects BOTH despite
different magnitudes: no feature is silently repaired, truncated,
forward-filled, or declared independently source-authenticated. Historical
models remain descriptive at original SourceCut; requalification and a
separate new-source study are required before new native HILO training.
This is only an OHLC shape obligation, not licensed provider rights, PIT
or a proof of adjusted/dividend total-return economics.

Features RET1/MOM5/HILO/VOL5 are EOD-close-derived; LABEL0 is next
TRADING SESSION open-to-close fractional return (for new entries). These predictions are
UNCALIBRATED research scores, NOT a conditional return distribution or
an admitted expected-return vector. The independent covariance-only
PyPortfolioOpt min-volatility calculation is MATH ONLY; the machine
result explicitly carries portfolio_target=null and optimizer_policy_eligible=false.

Source historical_available_at/corporate_actions/adjustment/rights remain
UNKNOWN; backfill today != knowable then. The Cboe V5 native daily endpoint
does not provide adj_close/dividend/split_ratio in its Cboe-specific model.
No broker, real paper, capital, PG posting, or actual financial result.

Qlib 0.9.7 includes MLflow3.18: this isolated experiment explicitly
uses MLFLOW_ALLOW_FILE_STORE=true while production should reuse existing
qualified PostgreSQL tracking. Output ignored by Git. No new OMS,
hypothesis engine, optimizer, or platform abstraction is introduced.
The JSON audited_capital_source_cut names the original baseline audit, NOT
the current consumer Git commit; obtain current HEAD from Runtime workspace.get
or git rev-parse at execution. Recorder ID is an MLflow run identity.


## R3 native consumer proof — 2026-11-11 round 3

The P0 source hash/parse/copy TOCTOU is fixed in the consumer. Pinned CSV
is read ONCE as immutable pinned_bytes, both pandas BytesIO parsing and
emitted CSV snapshot derive from the admitted bytes. A concurrent source
path replacement after the initial read cannot alter consumed model rows.

The focused real-Qlib probe mutates a private SPY source immediately
after the committed source byte read, verifies Qlib Recorder succeeds
and snapshot SHA still equals originally checked bytes; a pre-admission
mutation is rejected with Capture hash mismatch.

Qlib LABEL0[t] = close[t+1]/open[t+1]-1, the new-position next-session
OPEN-to-CLOSE fractional return, not previous CLOSE-to-next CLOSE.
The latter includes an overnight gap that a next-open new entry cannot
capture. For QQQ 2024-08-05, captured priorclose-to-close -2.981616%,
new-entry open-to-close +2.517189%; Qlib label equals the latter.
These inputs are backfilled and have UNKNOWN historical availableAt,
corporate actions and adjusted total return. No calibrated expected
return, portfolio target, actual order or PG cash/position posting.

From here (isolated Windows Python3.11, private capture in environment):
  set ORDIVON_FINANCE_R3_TEST_CAPTURE_DIR=<private-capture-folder>
  .venv/Scripts/python.exe tests/probe_native_capture_admission.py

The source test runs actual Qlib LGBModel.fit and native Recorder;
it is not a replacement engine or test framework.
MLflow tracking URI is assigned before importing Qlib/MLflow. This avoids
the unconsumed default root-level ./mlruns scratch side effect; the
research-only file store remains confined to ignored ./output/mlruns.

## Independent simulated Paper batch consumer (Q1 R3, 2026-11-13)

After the existing native test-producer generates native_holding_result.json
and paper_sessions.json, Capital accounting.paper_simulation_run consumes
those exact-by-digest outputs and the Qlib study/predictions in another
process, without re-running native Nautilus. Its stable r3sim_... key is
simulation-run-specific, not a real customer mapping. The original
PostgreSQL Paper accounting ledger owns all financial daily effects.
The original native fill-report-derived native_fill_claims in the outcome
is reconciled to Paper fills including mature account-scoped trade ID,
price, fee, quantity and timestamp. Terminal cash equality alone is
insufficient: balancing buy/sell price or fee errors is explicitly refused.
See docs/FINANCE_PAPER_INVESTMENT_R1.md for invocation, PIT/rights limits,
physical PG acceptance and replay. Never promote this producer or
retrospective study to an authorized live strategy.


## Frozen SPY/SHY forward consumer (2026-11-13)

The existing Research plan `evidence/finance-research/spy-shy-forward-20261108/frozen-plan.json`
precommits to 60% SPY / 40% SHY against 100% SPY before the planned
2026-11-09 to 2027-03-31 holdout. Its `configDigest` binds the exact existing
`examples/paper_fixed_mix_etf_20261106.json` policy bytes.

The small `frozen_spy_shy_holdout.py` is an actual private consumer of
the native OpenBB V5 Cboe provider, `research.experiment_protocol` and
`portfolio.passive_benchmark`. It does not duplicate provider HTTP, Qlib,
the benchmark engine, Risk, accounting, broker, or scheduler. It checks
the frozen plan and refuses altered weights/costs, missing matched
sessions, future rows and wrong provider identity. It emits normalized
Cboe CSV data and one partial research receipt **only** into a fresh
operator-selected private directory outside Git.

Example from the Ordivon repository root in the existing native Python3.11
environment with `openbb-core==2.0.1` / `openbb-cboe==2.0.0`:

```sh
export PYTHONPATH="$PWD/domains/capital/src"
python domains/capital/adoption/r3_native/frozen_spy_shy_holdout.py \
  --frozen domains/capital/evidence/finance-research/spy-shy-forward-20261108/frozen-plan.json \
  --policy domains/capital/examples/paper_fixed_mix_etf_20261106.json \
  --through 2026-11-13 \
  --private-output /root/projects/ordivon-private/finance/spy-shy-forward-20261113
```

This is **price-only** partial-forward observation. The original
retrospective study used adjusted closes; this Cboe close-price proxy
is NOT yet verified equivalent to that frozen economic metric. It is NOT
a completed 2027 holdout, authenticated data rights, total-return economic proof,
PIT historical investability, reliable alpha, or execution grant.
Source raw-wire bytes and independently signed publisher timestamps are
not present; historic and prospective claims remain UNKNOWN. Keep the
vendor CSV private; do not commit it or put it in a Host message. Use
the existing `finance-experiment-review` Skill for any later review.

For a concise Human research status, pass `--format markdown` to the same
CLI. It renders the exact existing Portfolio comparison with mandatory data
and risk unknowns; it is not an additional pricing, accounting or risk engine.
