from state.db.bootstrap import init_db as legacy_init_db
from state.db.session import SessionLocal as legacy_session_local
from state.db.bootstrap import init_db
from state.db.session import SessionLocal


def test_root_state_imports_are_available():
    assert SessionLocal is not None
    assert init_db is not None


def test_legacy_state_imports_still_resolve():
    assert legacy_session_local is not None
    assert legacy_init_db is not None
