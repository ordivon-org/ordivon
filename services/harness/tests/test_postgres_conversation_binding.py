"""Real PostgreSQL 18 conversation-binding adoption/cutover evidence."""
from __future__ import annotations

import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

psycopg = pytest.importorskip("psycopg")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from postgres_conversation_binding import PostgresConversationBindingStore, ConversationBindingConflict  # noqa: E402
from sqlite_conversation_binding import SQLiteConversationBindingStore  # noqa: E402

DSN = os.environ.get("ORDIVON_PG_CONVERSATION_TEST_DSN")
pytestmark = pytest.mark.skipif(not DSN, reason="isolated physical PostgreSQL owner not present")
CAMPAIGN = "sha256:"+"a"*64
EVIDENCE = "sha256:"+"b"*64
SESSION = "019a9af0-7b00-7000-8000-000000000001"


@pytest.fixture
def pg():
    assert DSN
    owner = PostgresConversationBindingStore(DSN)
    with psycopg.connect(DSN) as db:
        db.execute("DROP TRIGGER IF EXISTS corrupt_conversation ON ordivon_harness.conversation_bindings")
        db.execute("DROP FUNCTION IF EXISTS ordivon_harness.corrupt_conversation()")
        db.execute("TRUNCATE TABLE ordivon_harness.conversation_bindings")
    return owner


def adopt(owner, **changes):
    args = dict(
        campaign_ref=CAMPAIGN, agent_id="A01",
        provider_resource="https://chatgpt.com/c/conversation-1",
        session_id=SESSION, evidence_digest=EVIDENCE, request_id="adoption:1",
        now_ms=1_800_000_000_000,
    )
    args.update(changes)
    return owner.adopt_binding(**args)


def test_concurrent_fresh_pg_schema_admission_with_existing_wake_owner():
    from postgres_wake_turn_map import PostgresWakeTurnMap
    with psycopg.connect(DSN, autocommit=True) as db:
        db.execute("DROP SCHEMA IF EXISTS ordivon_harness CASCADE")
    from threading import Barrier
    barrier = Barrier(12)
    def start(i):
        barrier.wait(timeout=15)
        if i % 2:
            PostgresWakeTurnMap(DSN)
        else:
            PostgresConversationBindingStore(DSN)
    with ThreadPoolExecutor(max_workers=12) as pool:
        list(pool.map(start, range(12)))
    with psycopg.connect(DSN) as db:
        n = db.execute(
            "SELECT count(*) FROM information_schema.tables "
            "WHERE table_schema='ordivon_harness' AND table_name IN "
            "('conversation_bindings','wake_turn_map')"
        ).fetchone()[0]
    assert n == 2


def test_atomic_exact_replay_and_role_uniqueness(pg):
    result = adopt(pg)
    assert result["bindingStanding"] == "ADOPTED"
    assert adopt(pg) == result
    assert pg.get_binding(CAMPAIGN, "A01") == result
    with pytest.raises(ConversationBindingConflict, match="request identity"):
        adopt(pg, session_id="019a9af0-7b00-7000-8000-000000000002")
    with pytest.raises(ConversationBindingConflict, match="role already"):
        adopt(pg, request_id="adoption:2")
    with psycopg.connect(DSN) as db:
        assert db.execute("SELECT count(*) FROM ordivon_harness.conversation_bindings").fetchone()[0] == 1


def test_real_concurrent_same_request_has_one_verified_identity(pg):
    with ThreadPoolExecutor(max_workers=8) as pool:
        rows = list(pool.map(lambda _: adopt(pg), range(8)))
    assert rows == [rows[0]]*8


def test_legacy_source_cutover_requires_writer_retirement_and_exact_parity(pg, tmp_path):
    path = tmp_path / "ledger.sqlite"
    old = SQLiteConversationBindingStore(path)
    expected = adopt(old)
    with pytest.raises(ConversationBindingConflict, match="not sealed"):
        pg.assert_legacy_sealed(path)
    receipt = pg.retire_legacy_and_import(path)
    assert receipt["sourceRows"] == 1 and receipt["postgresRows"] == 1
    pg.assert_legacy_sealed(path)
    assert pg.get_binding(CAMPAIGN,"A01") == expected
    import sqlite3
    with pytest.raises(sqlite3.DatabaseError):
        adopt(old, request_id="new-request", campaign_ref="sha256:"+"c"*64)
    # PG may continue after cutover; source remains immutable and is a subset.
    adopt(pg, request_id="new-request", campaign_ref="sha256:"+"c"*64)
    pg.assert_legacy_sealed(path)


def test_missing_legacy_source_needs_explicit_fresh_pg_bootstrap(pg, tmp_path):
    missing = tmp_path / "none.sqlite"
    with pytest.raises(ConversationBindingConflict, match="source absent"):
        pg.assert_legacy_sealed(missing)
    pg.assert_legacy_sealed(missing, fresh_bootstrap=True)
    adopt(pg)


def test_legacy_drift_after_retirement_blocks_pg_consumer(pg, tmp_path):
    path = tmp_path / "ledger.sqlite"
    old = SQLiteConversationBindingStore(path)
    adopt(old)
    pg.retire_legacy_and_import(path)
    import sqlite3
    with sqlite3.connect(path) as db:
        db.execute("DROP TRIGGER conversation_pg_retired_update")
        db.execute("UPDATE conversation_bindings SET session_id='FORGED'")
    with pytest.raises(ConversationBindingConflict):
        pg.assert_legacy_sealed(path)


def test_real_pg_before_insert_trigger_forgery_fails_before_commit(pg):
    with psycopg.connect(DSN) as db:
        db.execute("""
            CREATE FUNCTION ordivon_harness.corrupt_conversation() RETURNS trigger
            LANGUAGE plpgsql AS $$ BEGIN NEW.session_id = 'FORGED'; RETURN NEW; END $$
        """)
        db.execute("""
            CREATE TRIGGER corrupt_conversation BEFORE INSERT ON ordivon_harness.conversation_bindings
            FOR EACH ROW EXECUTE FUNCTION ordivon_harness.corrupt_conversation()
        """)
    with pytest.raises((ConversationBindingConflict, psycopg.errors.CheckViolation)):
        adopt(pg)
    with psycopg.connect(DSN) as db:
        assert db.execute("SELECT count(*) FROM ordivon_harness.conversation_bindings").fetchone()[0] == 0


def test_post_insert_timestamp_forgery_is_rolled_back(pg):
    with psycopg.connect(DSN) as db:
        db.execute("""
            CREATE FUNCTION ordivon_harness.corrupt_conversation() RETURNS trigger
            LANGUAGE plpgsql AS $$ BEGIN NEW.created_at_ms = NEW.created_at_ms + 1; RETURN NEW; END $$
        """)
        db.execute("""
            CREATE TRIGGER corrupt_conversation BEFORE INSERT ON ordivon_harness.conversation_bindings
            FOR EACH ROW EXECUTE FUNCTION ordivon_harness.corrupt_conversation()
        """)
    with pytest.raises(ConversationBindingConflict, match="differs before commit"):
        adopt(pg)
    with psycopg.connect(DSN) as db:
        assert db.execute("SELECT count(*) FROM ordivon_harness.conversation_bindings").fetchone()[0] == 0


def test_persistent_pg_digest_tampering_rejected_on_read(pg):
    adopt(pg)
    with pytest.raises(psycopg.errors.CheckViolation):
        with psycopg.connect(DSN) as db:
            db.execute("UPDATE ordivon_harness.conversation_bindings SET session_id='FORGED'")
    assert pg.get_binding(CAMPAIGN, "A01") is not None



def test_counterfeit_pg_schema_is_rejected_before_any_binding_admission():
    with psycopg.connect(DSN, autocommit=True) as db:
        db.execute("DROP SCHEMA IF EXISTS ordivon_harness CASCADE")
        db.execute("CREATE SCHEMA ordivon_harness")
        db.execute("""
            CREATE TABLE ordivon_harness.conversation_bindings(
                campaign_ref TEXT NOT NULL,agent_id TEXT NOT NULL,
                provider_resource TEXT NOT NULL,session_id TEXT NOT NULL,
                evidence_digest TEXT NOT NULL,request_id TEXT NOT NULL,
                binding_digest TEXT NOT NULL,created_at_ms BIGINT NOT NULL
            )
        """)
    try:
        with pytest.raises(ConversationBindingConflict,match="unique/check contract"):
            PostgresConversationBindingStore(DSN)
    finally:
        with psycopg.connect(DSN, autocommit=True) as db:
            db.execute("DROP SCHEMA ordivon_harness CASCADE")
