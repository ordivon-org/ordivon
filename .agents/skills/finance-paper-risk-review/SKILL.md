---
name: finance-paper-risk-review
description: Use for read-only exposure, liquidity and risk-budget review after a durable simulated-account PostgreSQL close with separately admitted ETF market prices.
compatibility: Ordivon domains/capital; original Markets, Accounting, Risk and Governance owners; locked mise/uv Python.
metadata:
  source-authority: Ordivon Finance natural source-owner contracts
---

# Finance Paper Risk Review

Do not confuse a retrospective adjusted-close investment replay with a
simulated brokerage-account fill. The two are distinct representations,
and converting one to the other would invent order execution.

The original Markets owner admits raw unadjusted ETF marks through
`markets.etf_eod_snapshot.admit_etf_eod_snapshot`. Source SHA-256,
source rights and corporate-action evidence references, exchange
session close map, instrument IDs and decision clock must be separately
supplied by the operator. A snapshot's own labels are insufficient.

The original Accounting owner `PostgresPaperClose` durably records
paper-only buys, cash and unsettled payables inside the dedicated
`ordivon_paper` database and returns a daily close receipt. Once
the receipt is persisted, run this existing Capital Python toolchain:

    domains/capital/scripts/run-capability-python -m ordivon_capital.risk.paper_close_risk --receipt receipt.json --snapshot market-snapshot.json --binding market-binding.json

The native Risk consumer verifies exact source identity and book-value
conservation, then delegates exposure and portfolio risk-budget evaluation
to `risk.portfolio_risk` and Governance. It never imports a new trading
engine or invents a risk limit. The owner principal's current registered
budget is UNSET: the proper result is `RISK_BUDGET_INCOMPLETE`, not
a license to increase a position.

For native tests run `mise run //domains/capital:verify`. To
qualify actual durable effects, set
`ORDIVON_CAPITAL_PAPER_PG_TEST_DSN` to a disposable PostgreSQL database
**named ordivon_paper** and run `tests/test_paper_close.py` together
with `tests/test_paper_close_risk.py`. Do not use a production DSN.
Data provider truth, rights, historical timestamps, independent database
provenance, execution fill realism and capital permissions remain UNKNOWN
in this pure source consumer.

Natural owner: Risk; existing source LEGO: CA03. No second Agent,
workflow scheduler, ledger, risk algorithm or publishing registry.
