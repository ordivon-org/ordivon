# Finance liquidity R1: actual SOFR funding signal ablation

## Business question and result

Does observable US Treasury repo funding information add predictive value over
a cheap SPX price-only baseline on future 5-session price-index changes?

**Observed on 2026-11-20: NO for this exact exploratory experiment.**
Using the official New York Fed SOFR latest-history CSV and Cboe SPX
price-only history, the funding-enhanced model had **higher** walk-forward
MSE across all five staggered, nonoverlapping decision phase offsets.

| Phase | Independent windows in phase | MSE degradation vs price-only | Funding sleeve ($1,000 start) | Always long SPX index proxy |
|---|---:|---:|---:|---:|
| 0 | 328 | +1.82% | $2,123.02 | $2,652.04 |
| 1 | 328 | +2.31% | $1,985.37 | $2,571.57 |
| 2 | 328 | +2.58% | $2,035.99 | $2,502.97 |
| 3 | 328 | +2.58% | $2,087.58 | $2,496.76 |
| 4 | 328 | +2.43% | $2,189.18 | $2,497.69 |

**The five phases are correlated reuses of the same source history, not
five independent experiments.** A negative result does NOT prove that
all monetary liquidity information is irrelevant, and the synthetic
index-price sleeve is NOT a tradable or dividend-qualified ETF account.

This result justifies stopping expansion of **this specific simple
SOFR -> SPX strategy**, not reinterpreting the research as a live signal.

## True data inputs and native consumers

- New York Fed official SOFR: effective-date, rate, repo daily volume,
  1st/99th percentile rates. At source download two records had missing
  numeric fields: 2019-05-31 and 2021-08-05; they were explicitly excluded.
  During 2020-2022, some actual repo percentile rates were **negative**
  and must NOT be discarded as invalid. All remaining 2,154 rate rows
  were parsed.
- Cboe public SPX price index history: 2,173 XNYS sessions within
  the experiment's frozen 2018-04-02 through 2026-11-19 range.
  The existing Markets XNYS session-grid checker independently rejects
  invented exchange sessions and missing sessions.
- Native skills used: monetary economics, point-in-time causal reasoning,
  forecast ablation, investment cash-flow comparison, reverse falsification.
- Existing capabilities used: Markets exchange_calendars, Python CSV,
  scikit-learn StandardScaler and Ridge, native PostgreSQL Runtime Jobs.
  No duplicate financial authority, data warehouse, OMS, ledger,
  broker, scheduler or new dependency.
- Private source identities captured 2026-11-20, not historical PIT:
  New York Fed CSV SHA-256 d98bf73e87e43a2eb03d0842c67676da45d826e9db09b71459a29c579432b1c9;
  Cboe SPX CSV SHA-256 a441124b04c0cde717ab8edaef25c82c22a78ef3981025e10f3f8a6254342ec1.
  A future provider download with different bytes is a new snapshot.
- Exact downloaded source bytes were retained ONLY in an ignored private
  workspace directory, not distributed in Git. The output contains SHA256
  input identities and aggregated metric results only.

## Fixed experiment design and evidence limits

- Decision: **after** Cboe daily SPX close at session t.
- Funding features are drawn from the most recent SOFR *effective date*
  at least TWO XNYS sessions earlier; next-day publication near
  08:00 Eastern is an official general rule, but this conservative
  offset does NOT certify the exact original historical publication.
- Outcome: SPX_CLOSE[t+6]/SPX_CLOSE[t+1] - 1, an illustrative
  5-session holding interval beginning at the next session's close.
- Price-only baseline: log return from t-20 through t.
- Additional funding inputs: SOFR rate level, five-record log volume
  change and percentile spread (99th - 1st), none pulled from the
  future relative to the conservative source cutoff.
- Models: StandardScaler + Ridge(alpha=10); expanding walk-forward
  training with at least 500 previously **matured** labels.
- Five different 5-session staggered evaluation phases; the outcome
  of every train sample must be observable at the current decision
  close. No target look-ahead.
- Economic *illustration*: $1,000 index-price-only hypothetical
  long/cash sleeve, 5bps turnover per entry or exit, compared to
  continuously long SPX price-index proxy with equivalent initial
  and terminal turnover charges. No dividends, actual ETF fills,
  market impact, taxes, live trade permission or investor welfare.
- **Standing**:
  RETROSPECTIVE_LATEST_SNAPSHOT_ONLY_NOT_PIT_OR_ALPHA.
  New York Fed observations are the latest downloaded series, not
  certified original release vintages. Revision Indicator blanks
  are not a proof of historical first publication.
- No statistical claim of alpha; no preregistered prospective
  sample, multiple-testing corrected confidence, credit-cycle
  robustness or total-return accounting. Cboe index data may be
  copyrighted. Do not redistribute the raw price series.

## Direct rerun without extra platform

From domains/capital, with existing pinned mise and uv:

    mkdir -p .artifacts/liquidity-r1-private
    curl -fsSL \
      'https://markets.newyorkfed.org/api/rates/secured/sofr/search.csv?startDate=2018-01-01&endDate=2026-11-19' \
      -o .artifacts/liquidity-r1-private/sofr.csv
    curl -fsSL \
      'https://cdn.cboe.com/api/global/us_indices/daily_prices/SPX_History.csv' \
      -o .artifacts/liquidity-r1-private/spx.csv
    PYTHONPATH=src mise exec -- uv run --locked --group test \
      python scripts/research/liquidity_sofr_spx_ablation.py \
      --sofr .artifacts/liquidity-r1-private/sofr.csv \
      --spx .artifacts/liquidity-r1-private/spx.csv \
      --output .artifacts/liquidity-r1-private/result.json

The output explicitly records input SHA-256 digests, first and last
observations, omission dates and all five offset comparisons.
A rerun downloaded on a later date is a **new snapshot** and may change
the sample or historic corrections. Use original SHA identities for
exact reproduction; keep raw source private, never push it.

## Evidence-based follow-ups

1. **Source hardness:** Secure original historical availability/vintages
   via authorized ALFRED API or independently timestamped original
   publications. Verify fund corporate actions and tradeable
   price/fee assumptions separately. Do not invent first-vintage truth.
2. **Broader monetary-credit mechanism:** Predeclare a *new* study of
   bank credit, Treasury/dealer balance-sheet capacity, fiscal cash,
   repo basis and global dollar financing. A single SOFR series is
   NOT "all market liquidity"; avoid optimizing the already inspected
   historical test set.
3. **Forward scientific evidence:** Freeze a new hypothesis BEFORE
   unseen observations, record data at actual capture times and let
   a true independent analyst or agent falsify the economic conclusion.
4. **Investment economics:** Only after demonstrated incremental
   predictive value should Portfolio and Risk evaluate net economics.
   Existing Governance NON_LIVE restrictions remain in force.

Thought LEGO: positive monetary and asset-pricing mechanism; inverse
funding stress vs risk-on, missing-value semantics, selection effects.
Logic LEGO: verified observable funding -> lagged information set ->
forecast vs cheap baseline -> economic comparison -> retire or continue.
Capability LEGO: only official CSV, existing Markets calendar, sklearn,
existing Research consumer and native Runtime; **no new general abstraction**.

Official sources:
- https://www.newyorkfed.org/markets/reference-rates/sofr
- https://www.newyorkfed.org/markets/reference-rates/additional-information-about-reference-rates
- https://cdn.cboe.com/api/global/us_indices/daily_prices/SPX_History.csv
- https://fred.stlouisfed.org/docs/api/fred/series_observations.html
