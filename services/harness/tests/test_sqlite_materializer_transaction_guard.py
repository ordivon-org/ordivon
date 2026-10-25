"""A committed effect-ledger transition requires its durable receipt readback.

SQLite is the real verifier: DELETE triggers simulate a valid SQL statement whose
postcondition unexpectedly stops providing a receipt. They must not commit.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from conversation_relay_carrier import CarrierConflict, CarrierMaterializationRequest, MaterializationStanding
from sqlite_conversation_materializer import SQLiteConversationMaterializer, TargetMaterializationObservation


def _request() -> CarrierMaterializationRequest:
    return CarrierMaterializationRequest(
        request_id="request:atomic-readback-001",
        preparation_digest="sha256:" + "a" * 64,
        bootstrap_prompt="Fixed bootstrap.",
    )


def _install_receipt_erasing_trigger(path: Path, operation: str) -> None:
    with sqlite3.connect(path) as db:
        db.executescript(
            f"""
            CREATE TABLE adversarial_commit_witness (marker INTEGER);
            CREATE TRIGGER erase_receipt AFTER {operation} ON requests BEGIN
                INSERT INTO adversarial_commit_witness VALUES (1);
                DELETE FROM requests WHERE request_id = NEW.request_id;
            END;
            """
        )


def _assert_no_effect_committed(path: Path, expected_rows: int) -> None:
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT count(*) FROM adversarial_commit_witness").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM requests").fetchone()[0] == expected_rows


def test_durable_intent_never_commits_without_post_insert_receipt(tmp_path: Path) -> None:
    db_path = tmp_path / "ledger.sqlite3"
    store = SQLiteConversationMaterializer(db_path, target=object())
    _install_receipt_erasing_trigger(db_path, "INSERT")
    with pytest.raises(CarrierConflict, match="receipt.*missing"):
        store._record_intent(_request(), now_ms=1)
    _assert_no_effect_committed(db_path, 0)


@pytest.mark.parametrize("transition", ["apply", "claim"])
def test_durable_transition_never_commits_without_readback(tmp_path: Path, transition: str) -> None:
    db_path = tmp_path / "ledger.sqlite3"
    store = SQLiteConversationMaterializer(db_path, target=object())
    request = _request()
    store._record_intent(request, now_ms=1)
    _install_receipt_erasing_trigger(db_path, "UPDATE")
    with pytest.raises(CarrierConflict, match="receipt.*missing"):
        if transition == "apply":
            store._apply(
                request,
                TargetMaterializationObservation(standing=MaterializationStanding.PRE_EFFECT_FAILED, evidence_digest="sha256:" + "b" * 64),
                now_ms=2,
            )
        else:
            store._claim_effect_attempt(request, now_ms=2)
    _assert_no_effect_committed(db_path, 1)
    with sqlite3.connect(db_path) as db:
        assert db.execute("SELECT standing FROM requests").fetchone()[0] == MaterializationStanding.PREPARED.value


def test_human_resume_claim_cannot_commit_without_receipt(tmp_path: Path) -> None:
    db_path = tmp_path / "ledger.sqlite3"
    store = SQLiteConversationMaterializer(db_path, target=object())
    request = _request()
    store._record_intent(request, now_ms=1)
    with sqlite3.connect(db_path) as db:
        db.execute(
            "UPDATE requests SET standing=?,evidence_digest=? WHERE request_id=?",
            (MaterializationStanding.HUMAN_REQUIRED.value, "sha256:" + "c" * 64, request.request_id),
        )
    _install_receipt_erasing_trigger(db_path, "UPDATE")
    with pytest.raises(CarrierConflict, match="receipt.*missing"):
        store._claim_human_resume(request, now_ms=3)
    _assert_no_effect_committed(db_path, 1)
    with sqlite3.connect(db_path) as db:
        assert db.execute("SELECT standing FROM requests").fetchone()[0] == MaterializationStanding.HUMAN_REQUIRED.value


def test_post_update_invalid_receipt_cannot_be_committed(tmp_path: Path) -> None:
    db_path = tmp_path / "ledger.sqlite3"
    store = SQLiteConversationMaterializer(db_path, target=object())
    request = _request()
    store._record_intent(request, now_ms=1)
    with sqlite3.connect(db_path) as db:
        db.executescript(
            """
            CREATE TABLE adversarial_commit_witness (marker INTEGER);
            CREATE TRIGGER corrupt_receipt AFTER UPDATE ON requests BEGIN
                INSERT INTO adversarial_commit_witness VALUES (1);
                UPDATE requests SET standing='FORGED_TERMINAL' WHERE request_id=NEW.request_id;
            END;
            """
        )
    with pytest.raises(CarrierConflict, match="receipt.*invalid"):
        store._claim_effect_attempt(request, now_ms=2)
    _assert_no_effect_committed(db_path, 1)
    with sqlite3.connect(db_path) as db:
        assert db.execute("SELECT standing FROM requests").fetchone()[0] == MaterializationStanding.PREPARED.value
