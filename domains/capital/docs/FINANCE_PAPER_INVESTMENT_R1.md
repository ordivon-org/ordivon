# Finance Paper Investment R1 — historical data, virtual capital, daily settlement

Decision: an Agent may compute, compare and select a **SIMULATION_ONLY**
allocation. It may not create a broker account, spend real funds or infer
economic skill from a retrospective experiment. Existing Ordivon Harness
and Runtime execute the work; Capital Markets validates external bytes,
Portfolio computes NAV, and the already-qualified passive benchmark owns
the end-to-end return comparison. No new OMS, risk engine or scheduler.

## Evidence from real local/GitHub source inventory (2026-11-06)

- Capital's tracked Git tree and a bounded /root/projects pathname search
  contained no ready-to-use ETF adjusted-close dataset.
- Candidate GitHub source: https://github.com/manisahni/marketdata,
  at full commit 65a079329e379e104495f459e12e76a8f995585a
  (GitHub committer timestamp 2026-08-20T21:41:22Z).
  File daily_adjclose.csv: SHA-256
  361efb287116fc8200582c15fcd315bcce2e218fa1e50b416bacc5acebff37b9;
  Git blob SHA-1 29175a3fd8700cab31762bd72ced772ea5d1c807.
  Actually fetched and verified locally: 1,511,995 bytes, 5,688 data rows,
  original row range 2004-01-02 to 2026-08-11.
- SPY and SHY have no price at 2026-05-25 and 2026-08-11. The former is
  explicitly excluded from daily trading sessions; the latter is NOT a valid
  price for the last session. Last complete pair: 2026-08-10.
- GitHub provenance stops at the *mirror file at this commit*. The
  upstream yfinance data source, its adjustment algorithms, licensing,
  timestamp availability at the historical trade date and publication
  history are not independently established. The repository has no GitHub
  license declaration. Keep the raw CSV locally private, Git-ignored,
  and do not redistribute it in a PR or an artifact.

Other candidates examined: plotly/datasets is MIT and contains an older
AAPL finance example but not the matching ETF portfolio; Setooooo/etf-insight
contains a dated SPY extract and raw-data description; Pubmarks/datasets
has current public market stock CSV samples but no verified licence.
Do not conflate Git repository time with original market as-of time.

## Native reproducible historical simulation

Fetch data by its immutable commit (only for local evaluation):

    cd domains/capital
    curl --fail --location --retry 3 --output data/raw/etf-daily-65a07932.csv \
      https://raw.githubusercontent.com/manisahni/marketdata/65a079329e379e104495f459e12e76a8f995585a/daily_adjclose.csv
    sha256sum data/raw/etf-daily-65a07932.csv
    git hash-object data/raw/etf-daily-65a07932.csv

Compare the digests against the example manifest, then run:

    scripts/run-paper-etf-replay-r1 \
      --request examples/paper_fixed_mix_etf_20261106.json \
      --source data/raw/etf-daily-65a07932.csv \
      --output data/derived/paper-fixed-mix-spy-shy-20261106.json

The example fixes virtual opening wealth at USD 100,000 and an **arbitrary
preselected 60% SPY + 40% SHY, rebalanced daily at adjusted-close-based
hypothetical marks**, against 100% SPY and an idle USD cash balance.
It is not a portfolio optimized on the data. Illustrative hypothetical
annual expense fractions are 0.002 and 0.001 respectively, spread over
252 priced sessions; these are neither issuer-verified ETF fees nor a
brokerage commission/slippage model. No taxes, FX, margin, liquidity or
cash interest are included.

The first session close defines the virtual starting NAV; it is not a
realistic executable first fill. Each subsequent priced session creates
a daily NAV receipt; an all-blank source row is visibly excluded, a
partially priced session is rejected, and a requested unpriced final
date is rejected instead of silently using the previous day's price.
Virtual constant-mix accounting is a deterministic descriptive
projection; it cannot establish an executable strategy or fill quality.

The report is committed to an explicitly requested output path, using
a same-directory temporary file and atomic replacement; a re-run with
different content at the same path is rejected. Git-ignored raw/derived
data are local materializations, not Git branches or new databases.
No real funds are used. No broker credentials are needed.

## Scientific interpretation / R2.1 contract

- I: immutable source CSV bytes, full Git and SHA-256 identity,
  declared virtual-capital PolicyV1 with frozen dates and weights.
- O: immutable DailySettlementReplayV1, cash and SPY benchmarks,
  missing-price evidence, plus typed REJECTED on bad input.
- S: Unit in the pure projection; the optional CLI output file is an
  explicit effect separated from computation.
- pre: selected start/end dates must be exactly priced, ordered,
  instrument columns valid, and all financial calculations Decimal-based.
- post: the final daily virtual NAV equals the existing Portfolio passive
  benchmark terminal NAV under exactly the same return and expense
  conventions.
- inv: no real-money order, no leverage and no authority escalation;
  every dated mark has observed input prices and source-byte identity.
- eff: optionally write one simulation receipt; no broker operations.
- c: O(n*k) over n source dates and k selected instruments.
- epsilon: Python Decimal context arithmetic; true financial/market
  cost error is UNKNOWN and never equated with 0.
- prov: Git blob/SHA bytes verified; original publisher and real
  historical point-in-time data NOT VERIFIED.
- unfold: existing Capital Python runner, Markets CSV admission,
  Portfolio passive benchmark and native pytest/CI.

The 2025-2026 window is retrospective: the mirror commit was published
in August 2026. It cannot be called a precommitted, untouched historical
holdout. One declared trial does not independently prove the absence of
other trials. Virtual NAV differences are an observation about this
specific simulation policy, not evidence of reliable investment alpha.

## Next consumer boundaries

1. To settle **today** or any future day, admit a newer source cut with
   an actual priced session and its Git/source receipt. No stale-data
   rollover. Existing current Market providers can serve this boundary
   when data licences and adjusted-close semantics match.
2. A future calendar-driven Agent run may produce new simulation receipts
   using existing Runtime/Host/Harness scheduling, never a bespoke
   Finance daemon or state store.
3. Only when real portfolio orders become the question should LEAN or
   NautilusTrader's qualified paper brokerage/fill model be used. This
   bounded mark-to-market projection must not grow into a new broker.
