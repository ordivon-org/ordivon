---
name: finance-paper-risk-review
description: Review committed Ordivon paper Accounting closes against independently admitted ETF marks, Risk and Governance, including unsettled sale receivables.
compatibility: Ordivon Capital, locked Python mise/uv, PostgreSQL paper-only.
metadata:
  source-authority: Ordivon Capital Markets, Accounting, Risk and Governance
---

# Finance Paper Risk Review

Natural source owner is Risk CA03. Human-facing instructions live at
`domains/capital/docs/FINANCE_HUMAN_GUIDE_R1.md`; the authoritative
CA01–CA10 mapping is `domains/capital/planning/lego-plan-r1.json`.
Do not load unrelated Finance procedures unless the task requires them.
Do not create another broker, Finance Agent service, ledger or risk engine.

1. Distinguish retrospective adjusted-close virtual NAV from the
   simulated-paper account requiring actual dated buys/sells.
2. Have Markets admit raw, unadjusted ETF marks against the separate
   operator-supplied SHA256, source rights and corporate-action refs,
   exact session schedule, instrument set and decision clock.
3. Have Accounting commit paper buy/sell sessions, pending payables
   and sale receivables in the dedicated ordivon_paper PostgreSQL DB.
4. Determine the current Paper account head **before** constructing any
   daily-close request. Use the Accounting-native read-only consumer; it
   neither creates an account nor synthesizes a valuation:

       export ORDIVON_CAPITAL_PAPER_PG_DSN='...dedicated paper-only DSN...'
       cd domains/capital
       scripts/run-capability-python -m ordivon_capital.accounting.postgres_paper_close --account ACCOUNT --read-latest

   `COMMITTED_PAPER_HEAD` contains the stored receipt and its latest session.
   `NO_COMMITTED_PAPER_CLOSE` means this account is empty in an initialized
   paper database. A missing database/schema, invalid receipt or absent DSN
   is an error, **not** an empty account or invitation to reset capital.
   The readback checks request digest, immediate predecessor linkage,
   recorded market-evidence equality and a consistent PostgreSQL snapshot;
   it does not independently authenticate publisher data or recalculate NAV.
   `--read-latest` rejects all market/fill/calendar admission options.
5. Prefer SQL read-only Accounting readback for Risk:


       export ORDIVON_CAPITAL_PAPER_PG_DSN='...paper-only DSN...'
       cd domains/capital
       scripts/run-capability-python -m ordivon_capital.risk.paper_close_risk --account ACCOUNT --session YYYY-MM-DD --snapshot snapshot.json --binding binding.json

   The alternative --receipt FILE reads a caller-provided JSON file
   and leaves accountingPersistenceReverified=false. Never claim
   database proof from an offline receipt.
6. Risk checks NAV conservation with pending purchase payables, sale
   receivables, protected cash and marked positions, then delegates
   exposure and budget decisions to the existing Risk/Governance.
   Unsettled sale receivables cannot fund new buys.
   UNSET principal budget means RISK_BUDGET_INCOMPLETE, not approval.

For a separate descriptive tail-risk request, call the existing Risk
`historical_expected_shortfall` consumer. It integrates the empirical loss
quantile over the exact upper probability mass, including fractional boundary
observations; use `effectiveTailObservationWeight` rather than treating
`tailObservationCount` as independent severe events. Do not turn this
statistic into an automated risk-budget approval.

Formal Accounting obligation: reuse the existing owner and the pinned Z3
solver, not a second Finance/Risk verifier. Run
mise run //domains/capital:verify:formal from repository root. The
PaperCashSettlementR1.smt2 QF_LIA model proves aggregate cash, payable,
receivable and NAV conservation plus same-session exclusion of settling
sale proceeds. It must also produce concrete SAT counterexamples for the
wrong liquidity and receivable-retention models. Its source-to-Python
refinement is NOT_FORMALLY_PROVED; preserve owner implementation checks and
isolated PostgreSQL readback for that boundary. See
domains/capital/formal/README.md. This is not trading authorization.

Qualification: mise run //domains/capital:verify plus actual isolated
PostgreSQL paper receipt readback under disposable
ORDIVON_CAPITAL_PAPER_PG_TEST_DSN against database ordivon_paper.
The source does not independently attest provider licence, historical
point-in-time source, model profit, or real-money broker authority.
