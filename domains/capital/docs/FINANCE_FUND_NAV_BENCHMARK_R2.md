# Fund NAV total-return benchmark, R2

## Problem and natural owner

The existing passive benchmark is a mathematical cash-flow comparison.
Legacy schema v1 accepts generic caller gross returns and expenses without
identifying fund-internal fees. The historical adjusted-close paper replay
also applies declared hypothetical annual expenses. It is not evidence that
the original data includes or excludes those fees. Do not rewrite frozen
historical experiments or represent their cost assumptions as qualified.

Portfolio now composes a semantic adapter with the existing passive
benchmark. No second wealth engine, external source collector, database,
execution route or account permission is introduced.

## New input and result

The same passive-benchmark CLI accepts schemaVersion 2. Each period has a
strategy and benchmark observation with explicit instrument identity,
USD, start/end dates, source reference, decimal simple return and basis
`FUND_NAV_TOTAL_RETURN_NET_OF_FUND_EXPENSES`.
Both observations must cover the identical interval; successive periods must
be contiguous, with stable instruments. The return must describe a fund NAV
total return with reinvested distributions and fund expenses already
reflected. Do not use a price-only index, gross index return, unqualified
adjusted close, market midpoint or annualized multi-year figure as this
input. A caller label is not market-source qualification.

Only external investor cost fractions and fixed costs at period start are
accepted, plus the same deposit on both legs. Zero is an explicit
assumption, not a statement that actual brokerage cost is zero. Do not
add distributions or deduct fund expenses again. The transition remains

    V_next = ((V + deposit) * (1 - external_fraction) - external_fixed)
             * (1 + declared_net_fund_total_return)

All observation dates are calendar boundaries, not provider publication
timestamps or historical PIT evidence. No withdrawals or intraperiod
cashflows, taxes, execution slippage, FX, daily rebalancing or real account
reconstruction are modeled. The output retains caller-declared evidence
and has no capital authority.

## Real reported-value witness (retrospective only)

The input `examples/fund_nav_benchmark_202609_r2.json` transcribes the
rounded one-month NAV total returns for September 2026 as published in
issuer performance tables, inspected 2026-11-24:

- SHY: -0.57%; BlackRock SHY Performance, cumulative 1m column,
  as of September 30, 2026.
  https://www.blackrock.com/us/financial-professionals/products/239452/ishares-1-3-year-treasury-bond-etf-shy
- SPY: -0.35%; State Street SPY Fund Performance, NAV 1 Month,
  as of September 30, 2026.
  https://www.ssga.com/us/en/individual/etfs/state-street-spdr-sp-500-etf-trust-spy

Both issuer pages describe reinvested distributions and expenses reflected
in fund performance. These two published rounded figures are a manual
transcription witness, NOT a byte-bound provider capture, licence
qualification, corporate-action reconstruction, intraday vintage or
broker receipt. No claim of active edge or suitability follows.
S&P DJI's published methodology separately distinguishes price and total
return indices:
https://www.spglobal.com/spdji/en/methodology/article/index-mathematics-methodology/

With virtual USD 10,000 on each leg, no deposits and explicitly zero
external fees: SHY USD 9,943, SPY USD 9,965, difference -USD 22.
The published inputs are rounded; do not treat these as exact real
portfolio valuations.

```sh
cd domains/capital
PYTHONPATH=src python -m ordivon_capital.portfolio.passive_benchmark \
  --input examples/fund_nav_benchmark_202609_r2.json
```

## Formal and implementation evidence

The existing exact-real SMT model now proves positive duplicate fund fees
strictly reduce an already-net return under positive wealth and return
factor, and exhibits a satisfiable ranking reversal. The original Lean
arbitrary-period cashflow/identical-path results remain in force for the
abstract transition. Behavioral Python tests exercise same-basis alignment,
continuity, legacy compatibility, unsupported price/index return,
duplicate dividend/fee fields, cost projection and the native CLI.
Neither formal result proves issuer data semantics or arbitrary Python
Decimal/date-parser refinement.
