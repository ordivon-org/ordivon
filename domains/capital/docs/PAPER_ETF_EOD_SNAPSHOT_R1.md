# Paper ETF end-of-day snapshots (Markets R1)

Markets can admit an offline, operator-supplied snapshot of unadjusted US ETF
closes for a paper decision. This is a data boundary, with no provider account,
network calls, raw data fixture, scheduler, or trading authority. The result
only qualifies the supplied bytes against the operator's evidence and decision
scope; it does not independently prove the operator's rights, market calendar,
data provenance, or correction claims.

Use `ordivon_capital.markets.etf_eod_snapshot.admit_etf_eod_snapshot`. Supply
the original UTF-8 JSON bytes and, separately, the expected SHA-256, source ID,
rights reference, corporate-action evidence reference, expected instrument IDs,
official exchange session closes, and UTC decision timestamp. Those bindings
come from the operator's trusted evidence, rather than from a copy of the
snapshot's own claims. Match ETF identity to stable instrument IDs before
constructing the input. The expected session map must represent the venue's
actual calendar, including holidays and early closes, for the entire intended
window. The rights evidence must cover private retention and paper replay in
the actual environment and for the operator's actual use.

The wire shape below uses invented data:

```json
{
  "schemaVersion": 1,
  "kind": "ordivon.finance.markets.etf-eod-snapshot",
  "sourceId": "example-source",
  "currency": "USD",
  "priceBasis": "RAW_UNADJUSTED_CLOSE",
  "rights": {
    "status": "AUTHORIZED_PRIVATE_PAPER_USE",
    "evidenceRef": "operator-record:rights-1"
  },
  "corporateActions": {
    "coverage": "COMPLETE",
    "evidenceRef": "operator-record:actions-1",
    "events": []
  },
  "capturedAt": "2026-04-02T21:00:00Z",
  "supersedesSha256": null,
  "marks": [
    {
      "sessionDate": "2026-04-02",
      "instrumentId": "TEST",
      "priceMinor": 18342,
      "availableAt": "2026-04-02T21:00:00Z",
      "availabilityBasis": "FIRST_OBSERVED"
    }
  ]
}
```

For each instrument and session there must be exactly one positive integer USD
cent mark. A missing mark on an expected open session blocks admission. No
fill-forward, price adjustments, NAV substitution, rounding, or conversion is
done here. `prices_for(session_date)` exposes only that admitted session's
marks. Admission currently requires verified operator evidence of **no relevant
corporate actions** for every instrument in the window, including distributions
that could create cash or receivables and splits that change share count. An
empty provider response on its own does not prove this.

Availability must be at or after the bound session close, and cannot be later
than capture. Use `SOURCE_REPORTED` only with evidence of actual provider
availability; an advertised update cadence or a trading date cannot supply it.
If the exact source publication time is unknown, `FIRST_OBSERVED` means the
capture time. A snapshot captured after the decision always fails, so querying
today's historical API cannot make yesterday's decision point in time. For a
correction, retain the original bytes in authorized storage, use a new
committed digest and capture time, and record the predecessor in
`supersedesSha256`. Markets never chooses the revision or verifies a revision
chain; the operator must bind the proper digest for each decision.

### Opening fills and clearing dates

For a paper close with supplied opening fills, pass `--fill-calendar FILE`
and `--fill-calendar-sha256 HASH` to the Accounting CLI. The UTF-8 object has
`market_source`, `clearing_source`, and `days`. Give independent evidence
references and one row for every date in the window. Each row has `date`
(ISO date), `open` and `close` (UTC times such as `14:30:00Z`, both null
on a closed market day), and a separate boolean `clears`. Include the
previous session, current session, and next eligible clearing date for any fill.

Trading validates the prior close, the next scheduled open, and the next
clearing day. Accounting binds the calendar evidence to the same committed
request and receipt. When an admitted mark snapshot is also supplied, both
inputs must agree on overlapping session closes. Successive bound calendars
must agree on overlapping dates and with booked clearing dates. The operator is responsible for the
calendar versions, source authenticity, correct venue, and fill prices.
This path models on-time opening fills only.

### Provider qualification, 2026-11-06

The installed Linux developer egress profile reached the EODHD public demo
with no private account. The documented VTI daily endpoint returned nine
sessions in a ten-weekday window spanning Good Friday, and no rows for the
closed dates alone. The raw and adjusted fields differed. The distributions
endpoint supplied its documented ex, declaration, record, and payment date
fields plus an unadjusted cash field; the split endpoint returned no events for
the requested window. SPY returned 403 on the public demo. Two reads of the
same VTI price window matched byte for byte; this tests a repeat download only
and does not establish the absence of revisions. The probe retained no vendor
data in the repository. Runtime evidence: `job-01a1af4d-bc77-7231-864e-96e1417f7d58`.

[EODHD's API](https://eodhd.com/financial-apis/api-for-historical-data-and-volumes)
documents vendor-reported as-traded OHLC, split-adjusted volume, recomputed
adjusted closes, and typical US update timing. It does not supply an as-known
vintage or a publication/correction timestamp per bar. The source's disclaimer
and composite provenance prevent treating its closes as verified primary
exchange prints. Its [corporate actions API](https://eodhd.com/financial-apis/api-splits-dividends)
distinguishes adjusted from historical cash amounts. The [NYSE calendar](https://www.nyse.com/trade/hours-calendars)
independently identifies April 3, 2026 as closed. The
[personal use](https://eodhd.com/help/personal-use),
[storage](https://eodhd.com/help/storage), and
[automation](https://eodhd.com/help/ai-tools) rules describe private paper use
and retention on personal plans and disallow sharing data or results. The
documented public demo is a test path, and its successful response is not
license evidence for recurring use. The no-card personal free tier currently
documents one year of history and 20 calls per day; exact API and intended-use
entitlements must be verified before use.

The [Cboe Equity EOD Summary](https://datashop.cboe.com/equity-eod-summary)
specification separates the last regular-hours trade from the official
primary-listing exchange print. The public sample downloaded successfully but
did not contain the ETFs checked; it provides neither ETF replay data nor an
ongoing entitlement. [Massive Stocks Basic](https://www.massive.com/stocks)
offers documented unadjusted closes on a free individual account with two years
of history; a no-key SPY probe returned 401. Its
[market-data terms](https://massive.com/legal/market-data-terms-of-service)
restrict use to personal use and require deletion when entitlement ends.
Neither EODHD nor these alternatives has an admitted ETF source here. Developer
egress was used for one-off public probes. The existing managed Finance routes
only admit their named exchange and macro hosts, and this change does not
extend that allowlist.
