"""PostgreSQL 18 one-way conversation role binding consumer tests.

No live external provider SEND; all database effects stay in an explicit
disposable PostgreSQL test database and per-test temporary legacy fixtures.
"""

from __future__ import annotations

import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

psycopg = pytest.importorskip("psycopg")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from postgres_conversation_binding import (  # noqa: E402
    ConversationBindingConflict,
    PostgresConversationBindingStore,
)
from sqlite_conversation_binding import SQLiteConversationBindingStore  # noqa: E402

DSN = os.environ.get("ORDIVON_PG_BINDING_TEST_DSN")
pytestmark = pytest.mark.skipif(not DSN, reason="disposable PG binding database required")
SESSION_ID = "019a9af0-7b00-7000-8000-000000000001"
EVIDENCE = "sha256:" + "f" * 64


def payload(role="A01", request="adopt-1") -> dict:
    return {
        "campaign_ref": "sha256:" + "a" * 64,
        "agent_id": role,
        "provider_resource": "https://chatgpt.com/c/existing-1",
        "session_id": SESSION_ID,
        "evidence_digest": EVIDENCE,
        "request_id": request,
        "now_ms": 1_800_000_000_000,
    }


@pytest.fixture
def owner(tmp_path: Path) -> PostgresConversationBindingStore:
    assert DSN
    store = PostgresConversationBindingStore(
        DSN,
        legacy_source=tmp_path / "legacy-bindings.sqlite",
        fresh_bootstrap=True,
    )
    with psycopg.connect(DSN) as pg:
        pg.execute(
            "DROP TRIGGER IF EXISTS corrupt_binding_insert ON ordivon_harness.conversation_bindings"
        )
        pg.execute("DROP FUNCTION IF EXISTS ordivon_harness.corrupt_binding_insert()")
        pg.execute("TRUNCATE TABLE ordivon_harness.conversation_bindings")
    return store


def test_pg_binding_first_admission_replay_and_unique_role(owner) -> None:
    first = owner.adopt_binding(**payload())
    assert first["bindingStanding"] == "ADOPTED"
    assert owner.adopt_binding(**payload()) == first
    assert owner.get_binding(first["campaignRef"], "A01") == first
    with pytest.raises(ConversationBindingConflict):
        owner.adopt_binding(**payload(request="other"))
    with pytest.raises(ConversationBindingConflict):
        owner.adopt_binding(**payload(role="A02", request="adopt-1"))
    assert owner.get_binding(first["campaignRef"], "A02") is None


def test_pg_concurrent_same_role_exact_request_has_one_identity(owner) -> None:
    with ThreadPoolExecutor(max_workers=8) as workers:
        results = list(workers.map(lambda _: owner.adopt_binding(**payload()), range(8)))
    assert len({x["bindingDigest"] for x in results}) == 1
    with psycopg.connect(owner.dsn) as pg:
        assert (
            pg.execute("SELECT COUNT(*) FROM ordivon_harness.conversation_bindings").fetchone()[0]
            == 1
        )


def test_pg_post_write_identity_mutation_rolls_back(owner) -> None:
    with psycopg.connect(owner.dsn) as pg:
        pg.execute(
            """
            CREATE FUNCTION ordivon_harness.corrupt_binding_insert()
            RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN
              UPDATE ordivon_harness.conversation_bindings
              SET provider_resource='https://chatgpt.com/c/forged'
              WHERE campaign_ref=NEW.campaign_ref AND agent_id=NEW.agent_id;
              RETURN NULL;
            END;
            $$
            """
        )
        pg.execute(
            "CREATE TRIGGER corrupt_binding_insert AFTER INSERT ON "
            "ordivon_harness.conversation_bindings FOR EACH ROW "
            "EXECUTE FUNCTION ordivon_harness.corrupt_binding_insert()"
        )
    with pytest.raises(ConversationBindingConflict, match="digest|binding"):
        owner.adopt_binding(**payload())
    with psycopg.connect(owner.dsn) as pg:
        assert (
            pg.execute("SELECT COUNT(*) FROM ordivon_harness.conversation_bindings").fetchone()[0]
            == 0
        )


def test_legacy_import_seals_old_writer_and_pg_accepts_new_role(owner, tmp_path: Path) -> None:
    path = owner.legacy_source
    old = SQLiteConversationBindingStore(path)
    before = old.adopt_binding(**payload())
    receipt = owner.retire_legacy_and_import(path)
    assert receipt["standing"] == "source-sealed"
    assert receipt["sourceRows"] == receipt["postgresRows"] == 1
    owner.assert_legacy_sealed(path)
    assert owner.get_binding(before["campaignRef"], "A01") == before
    with pytest.raises(Exception, match="retired to PostgreSQL"):
        old.adopt_binding(**payload(role="A02", request="adopt-2"))
    added = owner.adopt_binding(**payload(role="A02", request="adopt-2"))
    assert added["agentId"] == "A02"
    owner.assert_legacy_sealed(path)
    assert owner.retire_legacy_and_import(path)["standing"] == "source-sealed"


def test_import_divergence_does_not_retire_old_writer(owner, tmp_path: Path) -> None:
    path = owner.legacy_source
    # A previously admitted PG-only row before old-source migration is
    # forbidden to silently override the legacy same-role identity.
    owner.adopt_binding(**payload(role="A01", request="different"))
    old = SQLiteConversationBindingStore(path)
    old.adopt_binding(**payload())
    with pytest.raises(ConversationBindingConflict, match="differs"):
        owner.retire_legacy_and_import(path)
    with pytest.raises(ConversationBindingConflict, match="not retired"):
        owner.assert_legacy_sealed(path)
    # Migration failure did NOT patch the legacy writer, so old source stays
    # authoritative pending an explicit operator reconciliation.
    assert old.adopt_binding(**payload(role="A02", request="adopt-2"))["agentId"] == "A02"


def test_absent_legacy_never_silently_bootstraps_pg(owner, tmp_path: Path) -> None:
    missing = tmp_path / "missing.sqlite"
    with pytest.raises(ConversationBindingConflict, match="absent"):
        owner.assert_legacy_sealed(missing)
    owner.assert_legacy_sealed(missing, fresh_bootstrap=True)
    assert not missing.exists()


def test_pg_store_refuses_direct_admission_with_unsealed_legacy(owner) -> None:
    old = SQLiteConversationBindingStore(owner.legacy_source)
    old.adopt_binding(**payload())
    with pytest.raises(ConversationBindingConflict, match="not retired"):
        owner.get_binding(payload()["campaign_ref"], "A01")
    with pytest.raises(ConversationBindingConflict, match="not retired"):
        owner.adopt_binding(**payload(role="A02", request="new"))
    with psycopg.connect(owner.dsn) as pg:
        assert (
            pg.execute("SELECT COUNT(*) FROM ordivon_harness.conversation_bindings").fetchone()[0]
            == 0
        )


def test_tampered_pg_row_rejected_on_get(owner) -> None:
    owner.adopt_binding(**payload())
    with psycopg.connect(owner.dsn) as pg:
        pg.execute(
            "UPDATE ordivon_harness.conversation_bindings SET evidence_digest=%s",
            ("sha256:" + "a" * 64,),
        )
    with pytest.raises(ConversationBindingConflict, match="digest"):
        owner.get_binding(payload()["campaign_ref"], "A01")
