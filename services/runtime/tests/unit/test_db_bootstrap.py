from sqlalchemy import inspect

from state.db.bootstrap import init_db
from state.db.session import engine


def test_db_bootstrap_creates_core_tables():
    init_db()
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    expected = {
        "agent_actions",
        "intelligence_runs",
        "analyses",
        "decision_intakes",
        "recommendations",
        "outcome_snapshots",
        "reviews",
        "audit_events",
        "usage_snapshots",
    }

    assert expected.issubset(tables)
