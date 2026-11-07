# Paper Accounting cash / settlement formal boundary R1

Natural Owner: Capital / Accounting. This is a proof carrier for an existing
Paper Accounting responsibility. It does not create a new LEGO, registry, verifier,
agent service, ledger, broker permission or independent Risk Owner.

## Specification to model

PaperCashSettlementR1.smt2 is a Z3 QF_LIA model using exact integer USD minor
units. It abstracts a single daily-close step. The declared amounts are:

- previous cash, protected cash, pending buy payable and pending sale receivable;
- due buy payable and due sale receivable for the current settlement date;
- new cash contribution and its protected portion;
- new buy gross cost and new sale net proceeds;
- previous and current marked-holdings values.

The concrete source is
src/ordivon_capital/accounting/paper_close.py::value_session. The previous
money fields map to PaperValuation; contributions to PaperSession;
due amounts to payable_due_on and receivable_due_on; and buy/sale amounts to
PaperBuy.cost_minor / PaperSell.proceeds_minor. These are assumptions about the
mapping, not mechanically proved source refinement.

Preconditions: nonnegative monetary amounts; each due payable/receivable
is at most the corresponding outstanding amount; reserves do not exceed
cash available after previous obligations; and protected new contribution
does not exceed total new contribution.

Postconditions, with C = contribution, B = new buy cost, S = new sale proceeds,
and deltaM = new marked holdings value minus previous marked holdings value:

- cashNext = cash + C - duePayable + dueReceivable;
- payableNext = payable - duePayable + B;
- receivableNext = receivable - dueReceivable + S;
- protectedNext = protected + reserveContribution;
- NAVNext - NAV = C - B + S + deltaM;
- cashNext - payableNext - dueReceivable >= protectedNext, whenever the
  source's intraday purchase guard admits the session.

The last guard is equivalent to cash - payable + C - B >= protectedNext,
so settling sale proceeds never count as intraday purchase capacity. Pure
settlement with no contribution/new fills/mark changes cannot create NAV.

## Mature tool and scoped results

From repository root, run:

    mise run //domains/capital:verify:formal

This delegates to the pinned upstream Z3 from tools/formal/mise.toml. The
verifier requires UNSAT for negated universal arithmetic obligations, SAT
for a nonvacuous legal transition, and SAT for two faulty-model probes:
counting unsettled/intraday sale proceeds as buying power and failing to
remove a settled receivable. An unexpected solver result or UNKNOWN fails.

PASS means **ABSTRACT_QF_LIA_MODEL_ONLY**. Z3 is the adopted SMT solver;
its correctness and the chosen abstraction are trusted assumptions. No
claim of unbounded Python program correctness, time/order validity,
corporate-action accuracy, database SERIALIZABLE correctness or
PostgreSQL installed/prod behavior is made by this arithmetic result.

## Concrete implementation and terminal consumers

The existing test_paper_close.py consumer runs the actual value_session;
the targeted mixed buy/sell and due settlement witness checks the field
mapping for one concrete path. It is implementation evidence, not a
universal forward-simulation theorem.

Further Accounting/Risk/PostgreSQL verification is in the existing:
- tests/test_paper_close.py
- tests/test_paper_close_risk.py
- tests/test_paper_fill_calendar.py

Database tests require an independently created disposable ordivon_paper
PostgreSQL instance via ORDIVON_CAPITAL_PAPER_PG_TEST_DSN. Ordinary owner
unit checks do not run those tests if no DSN is supplied. Do not delete
these native consumer tests based on an abstract model PASS.

Unknown remains: complete Python/SQL model refinement; corporate actions
and provider reality; live settlement timing; deployed state; investor
risk preferences; financial permissions. The model grants no external effect.
