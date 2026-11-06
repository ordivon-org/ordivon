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
4. Prefer SQL read-only Accounting readback:

       export ORDIVON_CAPITAL_PAPER_PG_DSN='...paper-only DSN...'
       cd domains/capital
       scripts/run-capability-python -m ordivon_capital.risk.paper_close_risk --account ACCOUNT --session YYYY-MM-DD --snapshot snapshot.json --binding binding.json

   The alternative --receipt FILE reads a caller-provided JSON file
   and leaves accountingPersistenceReverified=false. Never claim
   database proof from an offline receipt.
5. Risk checks NAV conservation with pending purchase payables, sale
   receivables, protected cash and marked positions, then delegates
   exposure and budget decisions to the existing Risk/Governance.
   Unsettled sale receivables cannot fund new buys.
   UNSET principal budget means RISK_BUDGET_INCOMPLETE, not approval.

Qualification: mise run //domains/capital:verify plus actual isolated
PostgreSQL paper receipt readback under disposable
ORDIVON_CAPITAL_PAPER_PG_TEST_DSN against database ordivon_paper.
The source does not independently attest provider licence, historical
point-in-time source, model profit, or real-money broker authority.
