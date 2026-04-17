from sqlalchemy import inspect

from pfios.core.db.bootstrap import init_db
from pfios.core.db.session import engine


def test_db_bootstrap_creates_core_tables():
    init_db()
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    expected = {
        "analyses",
        "recommendations",
        "outcome_snapshots",
        "reviews",
        "audit_events",
        "usage_snapshots",
    }

    assert expected.issubset(tables)
