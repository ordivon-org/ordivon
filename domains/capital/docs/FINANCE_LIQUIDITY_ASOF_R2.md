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

## Dealer financing: source-native, release-qualified (P0 extension)

The exact SAME Finance Research as-of CLI optionally reads 3 NY Fed
Primary Dealer FR 2004 weekly statistics, not another platform or
separate data authority. The official catalog has 1,539 keys.
Only post-Jul-2024 official structural break SBN2024 observations are
admitted; older series with different definitions are not stitched
together.

| NY Fed series ID | Financial interpretation | 2024-break published weeks |
|---|---|---|
| PDPOSGST-TOT | US Treasuries excluding TIPS: dealer net long-short position | 124 / 124 |
| PDSIOSB-UTSETTOT | Same Treasuries: securities borrowed | 124 / 124 |
| PDSOOS-UTSETTOT | Same Treasuries: securities lent | 49 / 124; **75 withheld** |

Data units: USD millions, according to the official FR 2004 weekly
statistical release. The Fed usually publishes on the FOLLOWING
Thursday at approximately 16:15 New York time. This consumer uses a
16:30 buffered schedule and shifts federal holidays to the next US
federal business day; it does not certify historical first publication.

Official missing token * means data not publicly reported, NOT
a reported zero or proof that no financing occurred. The NY Fed
notes that categories with fewer than 3 dealers reporting are not
published, and that the historical endpoint can contain revisions.
The model retains original week identity and outputs null value with
PUBLISHED_VALUE_WITHHELD rather than zero or a previous valid value.
Before the first released qualified dealer week, the consumer
returns NO_ELIGIBLE_DEALER_WEEK, not the misleading SAME_REPORTED_WEEK.
Duplicate dealer source-key file bindings are rejected before reading
source bytes, so duplicated input cannot hide an omitted series.


Actual official inputs replayed at five decision instants:

| NY decision instant | Eligible dealer week | Net position USD mn | Borrowed USD mn | Lent USD mn |
|---|---|---:|---:|---:|
| 2026-11-05 17:00 | 2026-10-28 | 452,759 | 425,849 | WITHHELD |
| 2026-11-19 16:00 | 2026-11-04 | 467,271 | 423,640 | 120,072 |
| 2026-11-19 16:35 | 2026-11-11 | 456,007 | 411,760 | 123,465 |
| 2026-11-19 17:00 | 2026-11-11 | 456,007 | 411,760 | 123,465 |
| 2026-11-20 10:00 | 2026-11-11 | 456,007 | 411,760 | 123,465 |

The three positions and financing activities are not a conservation
equation and cannot be netted to infer cash flowing into equities.
They describe a reporting subset of dealers and are NOT global
liquidity, SPX Alpha or actual matched ETF total-return economics.

Use optional (all-or-nothing) arguments with provider raw data kept in
an ignored local workspace, in addition to the existing H41/DTS/SOFR
inputs:

    --dealer-catalog .artifacts/liquidity-dealer-r1-private/pd-series-metadata.csv
    --dealer-series .artifacts/liquidity-dealer-r1-private/PDPOSGST-TOT.json
    --dealer-series .artifacts/liquidity-dealer-r1-private/PDSIOSB-UTSETTOT.json
    --dealer-series .artifacts/liquidity-dealer-r1-private/PDSOOS-UTSETTOT.json

Original API endpoints:
- https://markets.newyorkfed.org/api/pd/list/timeseries.csv
- https://markets.newyorkfed.org/api/pd/get/PDPOSGST-TOT.json
- https://markets.newyorkfed.org/api/pd/get/PDSIOSB-UTSETTOT.json
- https://markets.newyorkfed.org/api/pd/get/PDSOOS-UTSETTOT.json
- https://www.newyorkfed.org/markets/counterparties/primary-dealers-statistics

Captured source byte SHA-256 identities (2026-11-21):
- catalog 31776e9749211f25d0e68fb5478f5d5ce9bb88161e4239246acba721fdfe3efe
- position 51b4367f1f22a550327492232717d5b5e8125e224a84c802826a1cfec75307d6
- borrowed d42ced99aec6975b7c3e9ca33699d807b8a7e1a521708ebe36c1c19042b379f5
- lent 03a4257af15a6d0f8bebf6b34433ce44c494c20f8b22911df5987c8f067e18e8

The captured source bytes were kept private and NOT committed.
These hashes prove present bytes, not historical first availability.
New test inputs are synthetic fixtures with actual provider-shaped
field semantics; no real provider data is bundled in Git.

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
  liquidity signals. 23 source-native counterexample tests
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

## Optional historical macro context (ROUTPUT)

The existing consumer may also take the Philadelphia Fed monthly vintage
workbook for quarterly real GDP; see
[RTDSM ROUTPUT R1](FINANCE_RTDSM_ROUTPUT_R1.md). This is separately qualified
historical macro context, not a liquidity stock. Its conservative
month-resolution availability rule must not be applied to daily SOFR,
Treasury or H41 series.
