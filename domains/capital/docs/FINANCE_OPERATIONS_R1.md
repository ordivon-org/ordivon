# Finance Operating Guide R1 — Human and Agent

Source of truth: domains/capital and planning/lego-plan-r1.json for
Recursive LEGO R2.1. This guide is a current **consumer** of implemented
natural owners, not a new Finance engine or approval authority.

## For Human operators

### Investment Mode

Choose an investment horizon, benchmark, protected cash balance, target
weights, maximum tolerable drawdown and contribution amount **yourself**.
The contribution-only planning CLI is:

    cd domains/capital
    scripts/run-strategic-contribution-brief < examples/strategic_contribution_r1.json

The separate cash-flow-matched passive benchmark measures descriptive
relative wealth; it does not promise returns. The owner principal's
config/portfolio_risk_budget.json is currently UNSET; do not confuse
RISK_BUDGET_INCOMPLETE with risk approval. A strategy/Agent never writes
your capital limits on your behalf.

### Research Mode

Define a finite trial family, estimated costs, hypothesis, source
availability and untouched prospective holdout **before** looking at the
test returns. Use the existing run-finance-lego operations in order:
fingerprint-policy, freeze-experiment, and after the holdout exists,
review-candidate with committed source bytes. If no independent proof of
source publication or multiple-testing correction exists, the scientific
standing remains UNKNOWN even if the arithmetic replays. Compare
against a simple passive benchmark.

### Paper Account Mode

A retrospective *adjusted-close* ETF portfolio simulation using
scripts/run-paper-etf-replay-r1 does not generate broker fills. For an
actual simulated brokerage account, Markets admits original raw USD-cent
session closes through markets/etf_eod_snapshot.py; Accounting posts
simulated buys, sells, cash contributions and settlement claims into an
isolated PostgreSQL database **named ordivon_paper**. Never equate
adjusted total-return data with a raw instrument cashbook.

To review a **previously committed** paper account by direct, read-only
PostgreSQL source readback, set the approved paper-only DSN outside the
command line and invoke the existing native Risk CLI:

    export ORDIVON_CAPITAL_PAPER_PG_DSN='...paper-only DSN...'
    cd domains/capital
    scripts/run-capability-python -m ordivon_capital.risk.paper_close_risk       --account paper-account-key --session 2026-01-13       --snapshot /private/etf-raw-marks.json       --binding /private/operator-market-binding.json

The separate operator-market-binding.json supplies the expected SHA-256,
source/rights/corporate-action refs, exact official session closes,
instrument IDs and decision clock. The snapshot cannot certify its
own provenance. The SQL readback binds the actual stored request SHA-256
and receipt identity before Risk evaluation. The alternative
--receipt /private/offline-receipt.json is a weaker, **unattested**
file-only diagnostic and should be labeled accordingly.

Interpret cash, protected cash, unsettled purchase payables, unsettled
sale receivables, invested positions and net asset value **separately**.
An unsettled sale increases receivables and NAV but not spendable cash.
The Risk available-equity ratio is a paper *unencumbered cash*
projection, never real broker buying power. Even SATISFIED risk status
alone does not authorize real financial transactions.

## For Agent operators

Do not spawn another Finance Agent platform, broker, risk engine,
database or credential manager. Use existing Harness, Runtime, Host,
Markets, Research, Portfolio, Risk, Accounting and Governance. For
each proposed analysis report: economic mode, natural owner, exact
data snapshot digest, source availability and rights standing, strategy
version, fees, trial count, benchmark, Risk status and independently
verified parts. UNKNOWN is not REJECTED, and neither is permission
to place an order.

Prefer an actual Accounting readback (--account and --session) to
unattested JSON (--receipt). Do not promote the persistence flag unless
SQL readback succeeded. Reject point-in-time mismatches, mixed raw vs
adjusted price bases, source identity drift, invented purchases, and
any claim that incomplete risk limits were satisfied. Reuse the
existing Decimal Risk engine and the existing passive benchmark rather
than writing another financial formula.

For source qualification, use mise run //domains/capital:verify.
For real stateful correctness, run tests/test_paper_close.py and
tests/test_paper_close_risk.py with
ORDIVON_CAPITAL_PAPER_PG_TEST_DSN pointing **only to a disposable**
PostgreSQL ordivon_paper database. Verify committed receipt readback,
cash-flow conservation and transaction restart, not just test booleans.
No production database or real brokerage API is needed.

## LEGO consumer guide — natural owner first

| LEGO | Human decision | Agent source consumer |
|---|---|---|
| CA01 Markets observation | Select allowed source, instrument, source time, rights | markets/crypto_public_streaming.py and Markets ETF admission; no broker rights |
| CA02 Factor proxy | Choose hypotheses and time horizon, question stability | risk/portfolio_risk.py factor observatory; correlation is not causal truth |
| CA03 Portfolio exposure | Set actual capital limits and inspect payable/receivable/cash | risk/paper_close_risk.py to existing Risk and Governance; UNSET is INCOMPLETE |
| CA04 Portfolio counterfactual | Choose HOLD, DE_RISK or HEDGE question | scripts/run-portfolio-scenario-brief, no unseen optimization |
| CA05 Nonlive policy | Identify external-effect class and capital owner | governance/policy_decision.py; NON_LIVE is not trading authority |
| CA06 Reconciliation | Demand authoritative order/fill observations | trading/execution_reconciliation.py; ambiguity stays unresolved |
| CA07 Durable accounting | Inspect exact committed/post/void identity | accounting/postgres_ledger.py and postgres_paper_close.py, atomic paper state |
| CA08 Prospective validation | Freeze time boundary before observing results | research/prospective_validation.py, reject future leakage |
| CA09 Strategic contribution | Choose reserve, amounts, weights | scripts/run-strategic-contribution-brief; no orders |
| CA10 Frozen experiments | Predeclare trial family, fees, holdout | scripts/run-finance-lego fingerprint-policy/freeze/review |

The table describes *existing* source-capability LEGO, not independent
proof that all providers, optimizers and broker integrations are admitted.
Paper replay, passive benchmark and data-vintage sensitivity reuse their
Portfolio/Markets owners. They are not second Accounting or Agent platforms.

## Mature methods: reuse without duplicating them

- QuantConnect LEAN's RAW and ADJUSTED/TOTAL_RETURN corporate-action modes
  have distinct split, dividend and cashbook semantics:
  https://www.quantconnect.com/docs/v2/writing-algorithms/securities/asset-classes/us-equity/corporate-actions
- CFA/GIPS recommends valuations at external cash flows and qualified
  independent valuations: useful for reliable benchmark comparisons
  without claiming GIPS accreditation:
  https://www.gipsstandards.org/standards/gips-standards-for-firms/gips-standards-handbook-for-firms/
- NIST AI RMF Govern/Map/Measure/Manage provides adaptable evidence and
  evaluation framing, not a mandate for another checklist platform:
  https://www.nist.gov/itl/ai-risk-management-framework/nist-ai-rmf-playbook
- Bailey et al. PBO/CSCV and Deflated Sharpe address overfitting and
  selection bias only when a meaningful complete trial family is known:
  https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2326253
  https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551

Delete duplicate algorithms and unused wrapper documents once their real
consumers have migrated. Preserve source data rights, evidence and shared
consumer continuity. No new real-money approval, database or scheduler.
