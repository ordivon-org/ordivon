# Finance Paper Lab: Daily Valuation Consumer R1

**Source realized / read-only**, not a live or historical close feed and not a
registered recurring task. Natural owner: Portfolio, physically
`domains/capital`. External broker settlement and the durable Accounting
Owner are distinct authorities.

## Why this is a small LEGO, not a second portfolio engine

LEAN owns fill, fee, margin and corporate-action mechanics when those are
required. Finance `accounting` owns durable capital reservations and balances.
This source only composes caller-supplied *already reconciled* cash, quantities
and one end-of-session price per instrument into a research snapshot. It
separates start-of-period external funding from economic gain. A newer
investment recommendation is not inferred from a valuation receipt.

Output measures **one candidate closing NAV**, not actual settlement,
verified portfolio wealth, shareholder total return, or security performance.
External sources must separately qualify pricing rights, corporate actions,
currency conversion, fee completeness, custodian readback and point-in-time
availability before authoritative daily use.

## Existing consumers, not duplicate frameworks

- `portfolio/strategic_contribution.py`: caller-mandated cash reserve and
  contribution-only allocation, not order authorization.
- `portfolio/passive_benchmark.py`: cashflow-matched comparison over already
  supplied returns, not a data feed or optimized investment policy.
- `research/investment_candidate.py`: frozen source/holdout structural
  evidence; no economic alpha or permissions proven.
- `portfolio/daily_valuation.py`: new read-only source-level daily NAV
  calculation with explicit no-source-verification standing.

Run from the Finance Owner root:

```sh
scripts/run-paper-daily-valuation-brief \
  < examples/paper_daily_valuation_synthetic_r1.json
```

The example is **entirely synthetic**. It intentionally uses `SIM_INDEX`
rather than a real ETF and does not suggest the price ever existed.

## R2.1 LEGO CA11: PaperDailyValuationProjection

- I: explicit prior NAV, start-of-period external cash flow (signed),
  current cash, protected cash, bounded fractional positions, end-of-session
  USD marks and source/availability timestamps, evaluation timestamp.
- O: per-position market values, cash, closing NAV, economic gain,
  period simple return (nullable for zero starting capital), and source
  qualification standing.
- S: pure function, no mutable or durable ledger.
- pre: exact schema, USD, finite decimals, bounded asset identifiers,
  one mark per unique instrument, `priceAsOf == sessionCloseAt`,
  `sessionCloseAt <= availableAt <= evaluatedAt`, covered reserve.
- post: `closing NAV = closing cash + sum(rounded position values)`;
  `gain = closing NAV - (opening NAV + net external start flow)`;
  no false profit from deposits.
- inv: cash never below caller protected reserve; cent precision with
  half-even rounding per position; source remains UNATTESTED; no order,
  provider effect, account change, real capital authorization or history
  rewrite.
- eff: none; stdin-to-stdout JSON receipt only.
- c: O(n log n) deterministic sort, n <= 128.
- epsilon: decimal cents rounding only, with exact Decimal arithmetic; market
  quality/coverage, fees and total return error remain UNKNOWN.
- prov: synthetic or caller-supplied data only; source truth not attested.
- unfold: validating input -> no-lookahead timestamp ordering -> market
  values -> funding-neutral gain/return -> read-only receipt.

No model forecasts, annualization, forward trading signal, tax lot, dividend
accrual or independent source attestation are claimed. The input `cashAtClose`
must already include any charged costs or received payouts; otherwise
reported economic gain is incomplete.

## Daily operating design (not yet activated)

The natural target for the long-running Ordivon Paper Lab is four comparison
accounts (cash-only, passive index, balanced 60/40, reserve-first) and a
separate Research Agent candidate. Each starts with an equal synthetic
$10,000 and receives identical externally scheduled deposits. Only a
verified trade calendar, price provider, account journal and corporate-action
readback can advance an authoritative EOD session receipt. A missing source
means PENDING, never a fabricated mark. U.S. market dates use IANA
`America/New_York`; reports may display `Asia/Taipei`. Do not calculate
close-to-close returns from post-close decisions as though filled before
the close.

Next real qualifying consumer: ingest a provider-qualified EOD snapshot,
bind to a durable paper-only Accounting namespace, apply original
provider/data version and freeze a session receipt; compare that journal
against the passive benchmark. Only then attach a scheduled daily task.
The independent Risk/Governance approval route remains outside this pure
Portfolio function.

## Mature references

- CFA Institute, investment performance and cash flow separation.
- QuantConnect LEAN framework:
  https://www.quantconnect.com/docs/v2/writing-algorithms/algorithm-framework/overview
- LEAN data and portfolio lifecycle:
  https://www.quantconnect.com/docs/v2/writing-algorithms/key-concepts/algorithm-engine
- GitHub native merge queue: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue

Acceptance: dedicated 29-test source/negative-input matrix, actual
`scripts/run-paper-daily-valuation-brief` consumer, native Finance
`mise run verify`, repository CI and independent GitHub checks.
