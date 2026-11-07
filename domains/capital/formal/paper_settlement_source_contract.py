"""Bounded symbolic refinement probe of the *actual* Paper Accounting Python transition.

This is a CrossHair PEP316 contract over a representative two-fill
settlement shape. It imports the canonical value_session; it does not
reimplement the transition, invent a new ledger or check real PostgreSQL.
CrossHair's bounded search is falsification evidence, not a universal
implementation proof.
"""

from datetime import date

from ordivon_capital.accounting.paper_close import (
    PaperSession,
    PaperValuation,
    value_session,
)


def settled_cash_and_liabilities_match_model(
    cash0: int,
    payable0: int,
    receivable0: int,
    reserve0: int,
    due_payable: int,
    due_receivable: int,
) -> bool:
    """Check source refinement of the two-date, no-trade, no-new-mark subset.

    pre: 0 <= cash0 <= 9223372036854775807
    pre: 0 <= payable0 <= cash0
    pre: 0 <= receivable0 <= 9223372036854775807
    pre: 0 <= reserve0 <= cash0 - payable0
    pre: 0 <= due_payable <= payable0
    pre: 0 <= due_receivable <= receivable0
    pre: cash0 - payable0 + receivable0 <= 9223372036854775807
    pre: cash0 - due_payable + due_receivable <= 9223372036854775807
    post: __return__ is True

    Result True means actual value_session preserved the model for
    THIS constructed session and its symbolic input; the bounded
    analysis makes no completeness guarantee for all Python paths.
    """
    previous_session = date(2026, 1, 9)
    current_session = date(2026, 1, 12)
    pending = {
        "buy-due": due_payable,
        "buy-later": payable0 - due_payable,
    }
    pending_sales = {
        "sale-due": due_receivable,
        "sale-later": receivable0 - due_receivable,
    }
    previous = PaperValuation(
        session=previous_session,
        cash_minor=cash0,
        protected_minor=reserve0,
        positions={},
        pending=pending,
        contribution_minor=0,
        payable_minor=payable0,
        nav_minor=cash0 - payable0 + receivable0,
        settlement_dates={
            "buy-due": "2026-01-12",
            "buy-later": "2026-01-13",
        },
        pending_sales=pending_sales,
        sale_settlement_dates={
            "sale-due": "2026-01-12",
            "sale-later": "2026-01-13",
        },
        receivable_minor=receivable0,
    )
    observed = value_session(
        previous,
        PaperSession(
            session=current_session,
            previous_session=previous_session,
            contribution_minor=0,
            reserve_contribution_minor=0,
            marks={},
            buys=(),
        ),
    )
    return (
        observed.cash_minor == cash0 - due_payable + due_receivable
        and observed.payable_minor == payable0 - due_payable
        and observed.receivable_minor == receivable0 - due_receivable
        and observed.protected_minor == reserve0
        and observed.nav_minor == previous.nav_minor
    )
