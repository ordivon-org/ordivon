"""Physical PostgreSQL effect ownership tests; use isolated disposable PG DSN."""

from __future__ import annotations

from contextlib import closing
import os
import sqlite3
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

psycopg = pytest.importorskip("psycopg")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from postgres_turn_effects import PostgresTurnEffects, TurnEffectConflict  # noqa: E402

DSN = os.environ.get("ORDIVON_PG_EFFECT_TEST_DSN")
pytestmark = pytest.mark.skipif(not DSN, reason="disposable PG authority not provided")


@pytest.fixture
def owner() -> PostgresTurnEffects:
    assert DSN is not None
    store = PostgresTurnEffects(DSN)
    with psycopg.connect(DSN) as pg:
        pg.execute("TRUNCATE ordivon_harness.turn_effects")
        pg.execute("DELETE FROM ordivon_harness.turn_effect_cutover")
    return store


def _claim(store: PostgresTurnEffects, identity: str = "turn:1"):
    return store.claim_before_send(
        identity, "sha256:" + "a" * 64, "https://chatgpt.com/c/existing", now_ms=1234
    )


def test_no_unqualified_pg_claim(owner: PostgresTurnEffects):
    with pytest.raises(TurnEffectConflict, match="PENDING|not certified"):
        _claim(owner)


def test_pg_fresh_cannot_shadow_existing_source(owner: PostgresTurnEffects, tmp_path: Path):
    source = tmp_path / "existing.sqlite"
    source.touch()
    with pytest.raises(TurnEffectConflict, match="legacy source exists"):
        owner.activate_empty_fresh(source)
    with pytest.raises(TurnEffectConflict, match="PENDING"):
        _claim(owner)


def test_claim_persists_unknown_before_send_and_replay_never_resends(
    owner: PostgresTurnEffects, tmp_path: Path
):
    owner.activate_empty_fresh(tmp_path / "absent.sqlite")
    first = _claim(owner)
    assert first["admittedToSend"] is True and first["state"] == "UNKNOWN"
    replay = _claim(owner)
    assert replay["admittedToSend"] is False and replay["state"] == "UNKNOWN"
    assert owner.get("turn:1")["receipt_json"] is None


def test_concurrent_claim_one_provider_admission(owner: PostgresTurnEffects, tmp_path: Path):
    owner.activate_empty_fresh(tmp_path / "absent.sqlite")
    with ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(lambda _: _claim(owner), range(24)))
    assert sum(row["admittedToSend"] for row in results) == 1
    assert all(row["state"] == "UNKNOWN" for row in results)


def test_conflicting_identity_cannot_rebind(owner: PostgresTurnEffects, tmp_path: Path):
    owner.activate_empty_fresh(tmp_path / "absent.sqlite")
    _claim(owner)
    with pytest.raises(TurnEffectConflict, match="identity conflict"):
        owner.claim_before_send("turn:1", "sha256:" + "b" * 64, "target")


def test_after_send_receipt_monotonic_and_replay(owner: PostgresTurnEffects, tmp_path: Path):
    owner.activate_empty_fresh(tmp_path / "absent.sqlite")
    _claim(owner)
    values = ("turn:1", "sha256:" + "a" * 64, "https://chatgpt.com/c/existing")
    expected = owner.record_after_send(*values, "COMPLETED", {"ok": True}, now_ms=4567)
    assert expected["safeToResend"] is False
    owner.record_after_send(*values, "COMPLETED", {"ok": True}, now_ms=4567)
    with pytest.raises(TurnEffectConflict, match="cannot be rebound"):
        owner.record_after_send(*values, "UNKNOWN", {"ok": False}, now_ms=7890)


def test_unclaimed_result_refused(owner: PostgresTurnEffects, tmp_path: Path):
    owner.activate_empty_fresh(tmp_path / "absent.sqlite")
    with pytest.raises(TurnEffectConflict, match="unclaimed"):
        owner.record_after_send("missing", "digest", "target", "COMPLETED", {"ok": True})


def test_stage_historical_data_never_activates_pg(owner: PostgresTurnEffects, tmp_path: Path):
    path = tmp_path / "turn?origin.sqlite"
    with closing(sqlite3.connect(path)) as db, db:
        db.execute(
            "CREATE TABLE turn_effects(turn_request_id TEXT PRIMARY KEY,prompt_digest TEXT,target_coordinate TEXT,state TEXT,receipt_json TEXT,updated_at_ms INTEGER)"
        )
        db.execute(
            "INSERT INTO turn_effects VALUES (?,?,?,?,?,?)",
            ("t-1", "digest", "coordinate", "UNKNOWN", None, 13),
        )
    before = path.read_bytes()
    receipt = owner.stage_legacy(path)
    assert receipt["standing"] == "PENDING" and receipt["rows"] == 1
    assert path.read_bytes() == before
    with pytest.raises(TurnEffectConflict, match="PENDING"):
        _claim(owner)
    assert owner.stage_legacy(path) == receipt
    with psycopg.connect(DSN) as db:
        assert db.execute("SELECT COUNT(*) FROM ordivon_harness.turn_effects").fetchone()[0] == 1


def test_stage_divergent_pg_fails_without_source_mutation(
    owner: PostgresTurnEffects, tmp_path: Path
):
    path = tmp_path / "source.sqlite"
    with closing(sqlite3.connect(path)) as db, db:
        db.execute(
            "CREATE TABLE turn_effects(turn_request_id TEXT PRIMARY KEY,prompt_digest TEXT,target_coordinate TEXT,state TEXT,receipt_json TEXT,updated_at_ms INTEGER)"
        )
        db.execute(
            "INSERT INTO turn_effects VALUES ('t-1','digest','coordinate','UNKNOWN',NULL,13)"
        )
    with psycopg.connect(DSN) as db:
        db.execute(
            "INSERT INTO ordivon_harness.turn_effects VALUES ('t-1','FORGED','coordinate','UNKNOWN',NULL,13)"
        )
    before = path.read_bytes()
    with pytest.raises(TurnEffectConflict, match="differs"):
        owner.stage_legacy(path)
    assert path.read_bytes() == before
    with pytest.raises(TurnEffectConflict, match="PENDING"):
        _claim(owner)


def test_browserless_reader_routes_to_pg_without_touching_legacy(
    owner: PostgresTurnEffects, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    from types import SimpleNamespace
    from agent_automation_browserless import BrowserlessAutomationService

    owner.activate_empty_fresh(tmp_path / "no-legacy.sqlite")
    _claim(owner)
    owner.record_after_send(
        "turn:1",
        "sha256:" + "a" * 64,
        "https://chatgpt.com/c/existing",
        "COMPLETED",
        {"accepted": True},
        now_ms=4567,
    )
    monkeypatch.setenv("ORDIVON_TURN_EFFECT_POSTGRES_DSN", DSN)
    service = object.__new__(BrowserlessAutomationService)
    source = tmp_path / "legacy-must-not-be-created.sqlite"
    service.config = SimpleNamespace(turn_ledger=source)
    projected = service._turn_effect_row("turn:1")
    assert projected == {
        "promptDigest": "sha256:" + "a" * 64,
        "targetCoordinate": "https://chatgpt.com/c/existing",
        "state": "COMPLETED",
        "receipt": {"accepted": True},
        "updatedAtMs": 4567,
    }
    assert not source.exists()


def test_pending_pg_sender_never_initializes_legacy_or_browser(
    owner: PostgresTurnEffects, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    import playwright_browserless_turn_once as sender

    prompt = tmp_path / "prompt.txt"
    prompt.write_text("never send this", encoding="utf-8")
    legacy = tmp_path / "legacy-must-not-be-created.sqlite"
    monkeypatch.setenv("ORDIVON_TURN_EFFECT_POSTGRES_DSN", DSN)
    monkeypatch.setattr(sender, "connector_spec", lambda _: {"connectionEndpoint": "unused"})
    monkeypatch.setattr(sender, "canonical_chatgpt_resource", lambda v: v)
    monkeypatch.setattr(sender, "sync_playwright", lambda: pytest.fail("provider connected"))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "sender",
            "--target-resource",
            "exact:resource",
            "--prompt-file",
            str(prompt),
            "--turn-request-id",
            "turn:1",
            "--ledger",
            str(legacy),
            "--receipt-out",
            str(tmp_path / "receipt.json"),
        ],
    )
    with pytest.raises(TurnEffectConflict, match="PENDING|not certified"):
        sender.main()
    assert not legacy.exists()


def test_pg_receipt_corruption_rolls_back_entire_outcome(
    owner: PostgresTurnEffects, tmp_path: Path
):
    owner.activate_empty_fresh(tmp_path / "absent.sqlite")
    _claim(owner)
    with psycopg.connect(DSN) as pg:
        pg.execute("""
            CREATE FUNCTION ordivon_harness.forge_effect() RETURNS trigger
            LANGUAGE plpgsql AS $$
            BEGIN
                UPDATE ordivon_harness.turn_effects
                SET receipt_json='{"forged":true}' WHERE turn_request_id=NEW.turn_request_id;
                RETURN NEW;
            END $$""")
        pg.execute("""
            CREATE TRIGGER forge_effect_after_update AFTER UPDATE
            ON ordivon_harness.turn_effects FOR EACH ROW
            WHEN (NEW.receipt_json IS NOT NULL AND OLD.receipt_json IS NULL)
            EXECUTE FUNCTION ordivon_harness.forge_effect()""")
    values = ("turn:1", "sha256:" + "a" * 64, "https://chatgpt.com/c/existing")
    with pytest.raises(TurnEffectConflict, match="durable readback differs"):
        owner.record_after_send(*values, "COMPLETED", {"accepted": True})
    assert owner.get("turn:1")["receipt_json"] is None
    with psycopg.connect(DSN) as pg:
        pg.execute("DROP TRIGGER forge_effect_after_update ON ordivon_harness.turn_effects")
        pg.execute("DROP FUNCTION ordivon_harness.forge_effect()")


def test_persisted_pg_unknown_outcome_never_resends(owner: PostgresTurnEffects, tmp_path: Path):
    owner.activate_empty_fresh(tmp_path / "absent.sqlite")
    _claim(owner)
    values = ("turn:1", "sha256:" + "a" * 64, "https://chatgpt.com/c/existing")
    owner.record_after_send(*values, "UNKNOWN", {"providerAccepted": "uncertain"})
    repeat = _claim(owner)
    assert repeat["admittedToSend"] is False
    assert owner.get("turn:1")["state"] == "UNKNOWN"
    with pytest.raises(TurnEffectConflict, match="cannot be rebound"):
        owner.record_after_send(*values, "COMPLETED", {"providerAccepted": "yes"})


def test_legacy_pg_effect_activation_requires_quiescence_and_source_retirement(
    owner: PostgresTurnEffects,
    tmp_path: Path,
):
    """Promote a nonempty immutable source exactly once; PG becomes sole writer."""
    source = tmp_path / "legacy-with-send.sqlite"
    with closing(sqlite3.connect(source)) as db, db:
        db.execute(
            "CREATE TABLE turn_effects(turn_request_id TEXT PRIMARY KEY,"
            "prompt_digest TEXT,target_coordinate TEXT,state TEXT,"
            "receipt_json TEXT,updated_at_ms INTEGER)"
        )
        db.execute(
            "INSERT INTO turn_effects VALUES(?,?,?,?,?,?)",
            (
                "turn:prior",
                "sha256:" + "a" * 64,
                "https://chatgpt.com/c/existing",
                "COMPLETED",
                '{"providerAccepted":true}',
                1234,
            ),
        )
    before = owner.stage_legacy(source)
    assert before["standing"] == "PENDING"
    with pytest.raises(TurnEffectConflict, match="quiesced"):
        owner.activate_staged_legacy(source, old_writers_quiesced=False)
    with pytest.raises(TurnEffectConflict, match="PENDING"):
        _claim(owner, "turn:new")
    result = owner.activate_staged_legacy(source, old_writers_quiesced=True)
    assert result["standing"] == "ACTIVE"
    assert result["rows"] == 1
    assert result["sourceDigest"] == before["sourceDigest"]
    assert owner.get("turn:prior")["receipt_json"] == '{"providerAccepted":true}'
    with pytest.raises(sqlite3.IntegrityError, match="retired to PostgreSQL"):
        with closing(sqlite3.connect(source)) as db, db:
            db.execute(
                "INSERT INTO turn_effects VALUES ('old:new','digest','target','UNKNOWN',NULL,2)"
            )
    fresh = _claim(owner, "turn:new")
    assert fresh["admittedToSend"] is True
    assert _claim(owner, "turn:new")["admittedToSend"] is False
    assert owner.activate_staged_legacy(source, old_writers_quiesced=True) == result


def test_pg_effect_activation_refuses_changed_source_without_retirement(
    owner: PostgresTurnEffects,
    tmp_path: Path,
):
    source = tmp_path / "changed.sqlite"
    with closing(sqlite3.connect(source)) as db, db:
        db.execute(
            "CREATE TABLE turn_effects(turn_request_id TEXT PRIMARY KEY,"
            "prompt_digest TEXT,target_coordinate TEXT,state TEXT,"
            "receipt_json TEXT,updated_at_ms INTEGER)"
        )
        db.execute("INSERT INTO turn_effects VALUES('turn:1','digest','target','UNKNOWN',NULL,1)")
    owner.stage_legacy(source)
    with closing(sqlite3.connect(source)) as db, db:
        db.execute("INSERT INTO turn_effects VALUES('turn:2','digest','target','UNKNOWN',NULL,2)")
    with pytest.raises(TurnEffectConflict, match="source.*changed|differs"):
        owner.activate_staged_legacy(source, old_writers_quiesced=True)
    # Rejected promotion must not install the legacy retirement barrier.
    with closing(sqlite3.connect(source)) as db, db:
        db.execute("INSERT INTO turn_effects VALUES('turn:3','digest','target','UNKNOWN',NULL,3)")
    with pytest.raises(TurnEffectConflict, match="PENDING"):
        _claim(owner, "turn:new")


def test_pg_effect_activation_rejects_forged_target_row_before_source_retirement(
    owner: PostgresTurnEffects,
    tmp_path: Path,
):
    source = tmp_path / "divergent.sqlite"
    with closing(sqlite3.connect(source)) as db, db:
        db.execute(
            "CREATE TABLE turn_effects(turn_request_id TEXT PRIMARY KEY,"
            "prompt_digest TEXT,target_coordinate TEXT,state TEXT,"
            "receipt_json TEXT,updated_at_ms INTEGER)"
        )
        db.execute("INSERT INTO turn_effects VALUES('turn:1','digest','target','UNKNOWN',NULL,1)")
    owner.stage_legacy(source)
    with psycopg.connect(DSN) as pg:
        pg.execute(
            "UPDATE ordivon_harness.turn_effects SET prompt_digest='forged' WHERE turn_request_id='turn:1'"
        )
    with pytest.raises(TurnEffectConflict, match="differ"):
        owner.activate_staged_legacy(source, old_writers_quiesced=True)
    with closing(sqlite3.connect(source)) as db, db:
        db.execute("INSERT INTO turn_effects VALUES('turn:2','digest','target','UNKNOWN',NULL,2)")
    with pytest.raises(TurnEffectConflict, match="PENDING"):
        _claim(owner, "turn:new")


def test_pg_effect_cutover_resumes_after_source_sealed_but_pg_still_pending(
    owner: PostgresTurnEffects, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Crash window between two database commits leaves no live writer or SEND."""
    source = tmp_path / "crash-window.sqlite"
    with closing(sqlite3.connect(source)) as db, db:
        db.execute(
            "CREATE TABLE turn_effects(turn_request_id TEXT PRIMARY KEY,"
            "prompt_digest TEXT,target_coordinate TEXT,state TEXT,"
            "receipt_json TEXT,updated_at_ms INTEGER)"
        )
        db.execute(
            "INSERT INTO turn_effects VALUES('turn:prior','digest','target','UNKNOWN',NULL,10)"
        )
    owner.stage_legacy(source)
    original = PostgresTurnEffects._legacy_rows

    def simulate_crash_after_source_commit(path: Path):
        raise TurnEffectConflict("injected interruption after durable source retirement")

    with monkeypatch.context() as context:
        context.setattr(
            PostgresTurnEffects, "_legacy_rows", staticmethod(simulate_crash_after_source_commit)
        )
        with pytest.raises(TurnEffectConflict, match="injected interruption"):
            owner.activate_staged_legacy(source, old_writers_quiesced=True)
    assert PostgresTurnEffects._legacy_rows is original
    with psycopg.connect(DSN) as pg:
        assert (
            pg.execute(
                "SELECT state FROM ordivon_harness.turn_effect_cutover WHERE cutover_id='legacy'"
            ).fetchone()[0]
            == "PENDING"
        )
    with closing(sqlite3.connect(source)) as db, db:
        with pytest.raises(sqlite3.IntegrityError, match="retired to PostgreSQL"):
            db.execute(
                "INSERT INTO turn_effects VALUES('turn:forbidden','d','t','UNKNOWN',NULL,20)"
            )
    with pytest.raises(TurnEffectConflict, match="PENDING"):
        _claim(owner, "turn:should-not-send")
    receipt = owner.activate_staged_legacy(source, old_writers_quiesced=True)
    assert receipt["standing"] == "ACTIVE" and receipt["rows"] == 1
    assert owner.get("turn:prior")["state"] == "UNKNOWN"
    assert _claim(owner, "turn:after")["admittedToSend"] is True


def test_pg_effect_cli_refuses_unsafe_cutover_before_any_source_access(
    owner: PostgresTurnEffects,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    from postgres_turn_effects import main

    missing = tmp_path / "no-owned-source.sqlite"
    monkeypatch.setenv("ORDIVON_TURN_EFFECT_POSTGRES_DSN", DSN)
    with pytest.raises(SystemExit) as exit_error:
        main(["--legacy-ledger", str(missing)])
    assert exit_error.value.code == 2
    assert not missing.exists()
    with pytest.raises(TurnEffectConflict, match="PENDING"):
        _claim(owner)


def test_pg_effect_cli_promotes_real_history_only_after_confirmation(
    owner: PostgresTurnEffects,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    from postgres_turn_effects import main

    path = tmp_path / "production-shaped-legacy.sqlite"
    with closing(sqlite3.connect(path)) as db, db:
        db.execute(
            "CREATE TABLE turn_effects(turn_request_id TEXT PRIMARY KEY,"
            "prompt_digest TEXT,target_coordinate TEXT,state TEXT,"
            "receipt_json TEXT,updated_at_ms INTEGER)"
        )
        db.execute("INSERT INTO turn_effects VALUES('turn:old','digest','target','UNKNOWN',NULL,5)")
    monkeypatch.setenv("ORDIVON_TURN_EFFECT_POSTGRES_DSN", DSN)
    assert main(["--legacy-ledger", str(path), "--confirm-old-writers-quiesced"]) == 0
    receipt = __import__("json").loads(capsys.readouterr().out)
    assert receipt["standing"] == "ACTIVE"
    assert receipt["rows"] == 1
    assert receipt["sourceDigest"].startswith("sha256:")
    assert owner.get("turn:old")["updated_at_ms"] == 5
    assert _claim(owner, "turn:new")["admittedToSend"] is True
