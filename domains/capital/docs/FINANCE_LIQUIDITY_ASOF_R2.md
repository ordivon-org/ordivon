# Finance Liquidity R2 — official multi-frequency as-of state

**2026-11-20 real Finance Research delivery. No investment authority.**

## Business question and actual economic result

At a specific New York decision instant, which published balance-sheet
stocks and repo-market observations could an investor have seen?
Can two original official publications corroborate their accounting
values without confusing observation dates with release times?

Using official H.4.1 archived dated HTML releases 2026-10-29,
2026-11-05, 2026-11-12, 2026-11-19; FiscalData Treasury DTS JSON
2026-10-28, 2026-11-04, 2026-11-18; and official NY Fed SOFR CSV
2026-10-01 through 2026-11-19, actual native Runtime produced:

| H41 release | Observed Wednesday | Bank reserves (USD millions) | H41 Treasury TGA | Same-date Treasury DTS |
|---|---|---:|---:|---:|
| 2026-10-29 | 2026-10-28 | 2,895,236 | 1,015,632 | 1,015,632 |
| 2026-11-05 | 2026-11-04 | 2,962,804 | 936,248 | 936,248 |
| 2026-11-12 | 2026-11-11 | 2,969,977 | 912,134 | NO SAME-DATE DTS (federal holiday) |
| 2026-11-19 | 2026-11-18 | 3,001,790 | 892,310 | 892,310 |

H.4.1 Table 1 reserve supply minus Table 2 all non-reserve
absorption equals Table 2 reserve stock in all four downloaded
original dated reports. On Nov 18 specifically:
6,793,431 - 3,791,641 = 3,001,790 million USD.

**Critical RRP definition counterexample:** H.4.1 Table 2 reports
a total Reverse Repurchase Agreements stock, NOT the stand-alone
ON RRP facility balance. On 2026-11-18, the Wednesday value is
317,043 USD million, decomposed into **316,712** million for Foreign
official and international accounts and **331** million for Others.
Both report series reconcile exactly. For each of the four dates
the source reverse-repo total equals its explicit two subclasses.
Do not insert 317 billion into a market model as an ON RRP balance.
The H.4.1 Others subtotal by itself is likewise NOT independent
proof of the ON RRP facility's full outstanding balance.

The three observed same-day TGA balances exactly match the
other official publication, but the two publications share
related accounting inputs: this is a cross-publication check,
not independent physical financial measurement.

## Critical time truth

- Thursday 2026-11-19 16:00 EST, at the regular US stock close:
  the newest H.4.1 permitted by its stated publication schedule
  is the 2026-11-12 archive, using November 11 Wednesday stock.
- Thursday 2026-11-19 17:00 EST: the 2026-11-19 archive is past
  its expected 16:30 EST release time, using November 18 stock.
- Thursday 2026-11-19 16:00 EST: the Nov 18 Treasury DTS is not yet
  schedule-qualified; Treasury documents publication by 16:00 on the
  *next US federal business day*. This consumer adds a 30-minute
  buffer, so the first eligible scheduled time is Thu 16:30 EST.
- Thursday 2026-11-19 17:00 EST: both H41 Nov 19 and DTS Nov 18
  are eligible by their documented schedules; the TGA balances match.
  Friday 2026-11-20 10:00 EST retains that qualified comparison.
- SOFR effective dates are held back by two *XNYS exchange sessions*,
  and kept as exact decimal strings. NY Fed normally publishes SOFR
  around 08:00 Eastern on the next repo business day; this exchange
  lag is a defensive approximation, not a true repo calendar or
  independent first-release timestamp.

The source-time boundary is still only
RELEASE_CALENDAR_ALIGNED_SOURCE_HISTORY_UNATTESTED. An official
dated webpage is not an external authenticated original HTTP
capture; current FiscalData and SOFR endpoints are latest-series
views, not complete historical original vintages. Historical
publication minute, corrections and rights are not proven by a
current SHA-256 file identity.

**No weekend/holiday future data:** The old +2 calendar day convention
was NOT conservative on Friday, since Sunday is earlier than the actual
following Federal business day. The source reader now uses pandas'
existing USFederalHolidayCalendar/CustomBusinessDay and a 16:30 New
York scheduled deadline on the **next federal business day**. For
Friday 2026-11-13 the next scheduled release is Monday 11-16;
Wednesday 11-11 Veterans Day is NOT an ordinary Treasury business
day. This reproduces the official Treasury next-business-day
publication rule. The actual historical first HTTP capture remains
unattested; no timestamp is fabricated or silently promoted.

**Actual DTS accounting layout after 2022-04-18:** the
close_today_bal field contains the literal null sentinel.
Take the amount from open_today_bal in the row whose account_type
is Treasury General Account (TGA) Closing Balance. Public
USD millions are separately rounded; accept four-part
opening+deposits-withdrawals-closing equality only within a
two-million rounding tolerance. The code rejects other unknown
fields rather than substituting zero.

**When days differ, do not join.** The Wednesday 2026-11-11
TGA has no same-day FiscalData DTS from the queried API. The
consumer reports DIFFERENT_OBSERVATION_DAY, not an invented
accounting match. A same-day numerical disagreement instead
reports CONFLICT_DO_NOT_COMBINE, with the two distinct published
values retained. There is NO blended daily liquidity index and
NO financial effect.

## Direct reproduction through existing tools

Place captured official files into a Git-ignored local folder
(domains/capital/.artifacts/liquidity-asof-r1); do not commit
or redistribute third-party raw data.

- https://www.federalreserve.gov/releases/h41/20261119/default.htm
  (also 20261112, 20261105, 20261029); save the
  full UTF-8 HTML as h41-YYYYMMDD.html
- https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/dts/operating_cash_balance?filter=record_date:eq:2026-11-18&page[size]=100
  (also substitute 2026-11-04, 2026-10-28); save full
  JSON as dts-YYYYMMDD.json
- https://markets.newyorkfed.org/api/rates/secured/sofr/search.csv?startDate=2026-10-01&endDate=2026-11-19
  save as sofr-20261001-20261119.csv

From domains/capital, with existing pinned mise, uv and test dependencies:

    mise exec -- uv run --locked --group test \
      python scripts/research/finance_liquidity_asof.py \
      --h41 .artifacts/liquidity-asof-r1/h41-20261112.html \
      --h41 .artifacts/liquidity-asof-r1/h41-20261119.html \
      --dts .artifacts/liquidity-asof-r1/dts-20261118.json \
      --sofr .artifacts/liquidity-asof-r1/sofr-20261001-20261119.csv \
      --at 2026-11-19T21:00:00+00:00 \
      --at 2026-11-19T22:00:00+00:00 \
      --at 2026-11-20T15:00:00+00:00

Provide additional same-format --h41 and --dts arguments
for the other weeks. The output contains source SHA-256,
release and observed dates, financial stock amounts, exact
SOFR decimals, source standing and conflict status. No
network or broker write is performed by the research script.

## Thought, logic, capabilities and stop rule

- Positive Thought LEGO: monetary economics, reserve accounting,
  economic conservation, market microstructure, calendar-based
  information sets, observed-versus-available time, reproducible science.
- Inverse Thought LEGO: a same-date financial observation may not
  yet be published; Thanksgiving/Veterans Day and other closures
  can create missing sources; two independent publications may
  share an underlying balance; a hash proves file bytes now, not
  historical availability; a latest database is not an original vintage.
- Logic LEGO: original provider observation -> native unit and
  table semantics -> chronological release eligibility -> as-of
  state -> reserve conservation + same-day TGA comparison ->
  qualified research-only output or explicit conflict/unknown.
- Capability LEGO: official Fed dated HTML, FiscalData JSON,
  NY Fed SOFR CSV; built-in Python HTMLParser, Decimal, zoneinfo;
  pinned exchange_calendars:XNYS; existing Capital Research and
  Runtime. No new dependency, Owner, broker, OMS, database,
  experiment scheduler or Agent-role framework.
- Consumer: Agent researchers can recover *what could have been
  eligible at an explicit time* without creating false daily
  liquidity signals. 12 pure/source-native falsification tests
  exercise accounting, date, DST, revisions, future SOFR and
  wrong-column cases.

## Next phase (not performed by this reader)

P0: independently timestamped first-release archive / true
historical vintages; source-qualified Treasury issuance, primary
dealer financing, credit conditions and quarterly BIS dollar credit.
BIS quarterly data cannot be forward-filled into new daily
observations. Its historical values may be revised.

P1: freeze a new untouched prospective macro hypothesis, verify
signal significance and matched benchmark economics on truly
new data. Do not refit the old R1 SOFR/SPX experiment after looking
at its negative result. Portfolio/Risk can evaluate a candidate
only after genuine incremental economic evidence; no live write.
P2: refine formal proofs/interfaces only when a real consumer
exposes a correctness need.

Official field and release guidance:
- https://www.federalreserve.gov/releases/h41/
- https://www.federalreserve.gov/monetarypolicy/bst_fedsbalancesheet.htm
- https://fiscaldata.treasury.gov/datasets/daily-treasury-statement/operating-cash-balance
- https://fiscaldata.treasury.gov/api-documentation/
- https://fiscaldata.treasury.gov/release-calendar/
- https://www.newyorkfed.org/markets/reference-rates/sofr
