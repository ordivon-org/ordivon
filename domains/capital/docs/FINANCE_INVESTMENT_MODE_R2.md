# Finance Investment Mode R2 — cash-flow-matched passive benchmark

Canonical implementation remains in Capital Portfolio:
src/ordivon_capital/portfolio/passive_benchmark.py. It is a pure,
read-only, deterministic comparison between a caller-supplied investment
return path and a caller-supplied passive-index benchmark, using exactly
the same capital-contribution schedule. It does not install an optimizer,
access personal financial accounts, create an investment signal, or trade.

## Source-owner module completeness and deletion boundary (2026-11-06)

The current Finance program is implemented inside the canonical Capital
source owner. Its seven directories are responsibility boundaries, not seven
independent agents, duplicate data stores or providers. Under Parnas-style
information hiding and the QuantConnect LEAN Algorithm Framework's division
between research/universe, portfolio, risk and execution, code moves only
when an actual cross-owner consumer requires a new responsibility.

The existing `config/capital_domain_taxonomy.json` `moduleMap` is a complete
source-owner representation, not a partial sample. The native
`test_capital_domain_taxonomy.py` now validates both directions:

- Each declared owner/module must exist on the physical source tree.
- Each importable physical owner/module must be declared exactly once.
- Source owners and declared responsibility names must have the same domain
  identity, without accidental duplicate or orphan modules.

The previously unregistered **seven** modules were the existing source files
for ETF/historical prices, paper replay/passive benchmark, research economic
candidate, and Accounting paper close/PostgreSQL readback. Registration
corrects the representation; it does **not** re-implement, move or certify
their provider-facing behavior. The Markets no-import-from-decision test also
recognizes native Python parent-relative imports, not only absolute syntax.

Consumer-based cleanup retired only two zero-byte empty directory marker
files under `data/raw` and `data/derived`, and their redundant ignore
exceptions. The actual ignore protections remain. `artifacts/.gitkeep`
is retained because frozen external evidence includes its path. Legacy
`accounting/sqlite_ledger.py` is likewise *not* a dead file: the PostgreSQL
migration/oracle qualification tests actively import it and the PG adapter
still uses a read-only SQLite legacy ingest seam. Retire it only with
real consumer substitution and invariant readback, never by age or filename.

This source contract is independent of investor performance and brokerage
execution permissions. CFA Institute's GIPS treatment of external flows and
time-weighted performance is relevant to research comparability; it does
not turn a caller-supplied or synthetic paper close into qualified accounting
truth. The authoritative daily NAV and price-vintage owner remain the
existing Accounting and Markets implementations, not a second Portfolio
NAV engine. New Agent research is subordinate to these naturally owned
sources.

Upstream methodological references:
- https://www.quantconnect.com/docs/v2/writing-algorithms/algorithm-framework/overview
- https://import-linter.readthedocs.io/en/v2.6/contract_types.html
- https://www.gipsstandards.org/standards/gips-standards-for-firms/gips-standards-handbook-for-firms/

## Why this boundary exists

A raw ending-balance comparison is misleading when paths receive
deposits at different times. Matching each start-of-period deposit
removes that specific structural asymmetry. The inputs are not a market
truth or an endorsement of any asset. The result is terminal wealth,
deposited capital and simple economic gain, not an internal rate of
return, time-weighted return, annualized return or max drawdown. Those
require different assumptions and cannot be inferred from balances.

Executable consumer (from domains/capital):

    PYTHONPATH=src uv run --locked --group test python -m ordivon_capital.portfolio.passive_benchmark --input replay.json

JSON input must have the exact root keys:
schemaVersion=1, kind=ordivon.capital.finance.passive-benchmark-input,
openingBalance (decimal-string nonnegative), currency (three-letter
uppercase), periods (nonempty ordered array). Each period has:

- periodEndAt: timezone-aware ISO timestamp, strictly increasing;
- depositAtStart: nonnegative decimal string, shared by both paths;
- strategyGrossReturn / benchmarkGrossReturn: fractional simple period
  returns, at least -1, not annualized percentages;
- strategyExpenseFractionAtStart / benchmarkExpenseFractionAtStart:
  nonnegative fractions up to 1, charged at period start;
- strategyFixedFeeAtStart / benchmarkFixedFeeAtStart: fixed costs in the
  declared currency charged before the period's gross return.

All costs and returns are declared inputs. Fixed fees exceeding
available capital are rejected. Withdrawals, leverage, taxes, FX,
dividends and real corporate-action/rebalancing mechanics are not
inferred. An index's historical constituents, dividends, fee and
licensing assumptions are the responsibility of the consuming dataset.

## R2.1 capability contract

- I: currency, opening balance, ordered periods containing endpoint,
  shared deposit, two returns, two expense fractions and two fixed fees.
- O: descriptive CashflowMatchedBenchmarkSummaryV1 or
  PassiveBenchmarkError.
- S: Unit (pure evaluation).
- pre: valid unique ordered timezone-aware periods, finite decimal strings,
  same deposit schedule, nonnegative capital and nonnegative costs.
- post: deterministic cost- and deposit-matched terminal wealth and simple
  economic gains, or a rejection.
- inv: same deposits across paths, no negative final capital,
  external effects, optimization, asset advice or capital permission.
- eff: empty (no account/order/network/credential effects).
- c: O(n) over n periods with O(n) input parsing; exact limit UNKNOWN
  until consumer supplies an admission bound.
- epsilon: Python Decimal context; financial market/observation error is
  UNKNOWN and not treated as zero.
- prov: caller-supplied observations; independent historical source
  lineage and cost realism UNKNOWN.
- unfold: pure source, executable CLI and dedicated consumer tests;
  no additional Agent process, runtime, experiment engine or ledger.

## Owner semantics and next evidence

This is a passive benchmark replay, not a portfolio construction or
allocation recommendation. Investment Mode still requires authoritative
cashflow/holdings data, validated expense assumptions, compliant historical
benchmark data and independent account reconciliation. Existing Accounting
owns durable balances; Research owns experiments; Risk owns constraints.

Future strategy evaluation may consume this result only as a descriptive
economic baseline. It must separately establish market-source rights,
transaction costs, survivorship, security/portfolio feasibility and
temporal qualification. Output always sets capitalAuthority=NONE.
