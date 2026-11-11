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
  .venv/Scripts/python.exe tests/test_native_capture_admission.py

The source test runs actual Qlib LGBModel.fit and native Recorder;
it is not a replacement engine or test framework.
MLflow tracking URI is assigned before importing Qlib/MLflow. This avoids
the unconsumed default root-level ./mlruns scratch side effect; the
research-only file store remains confined to ignored ./output/mlruns.
