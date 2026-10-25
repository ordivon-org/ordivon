from __future__ import annotations

from contextlib import closing

import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from sqlite_wake_turn_map import SQLiteWakeTurnMap, WakeTurnConflict  # noqa: E402

TURN_ID = "019a9af0-7b00-7000-8000-000000000011"
CAMPAIGN_REF = "sha256:" + "a" * 64
PROMPT_DIGEST = "sha256:" + "1" * 64


def mapping(tmp_path: Path, ids=None) -> SQLiteWakeTurnMap:
    iterator = iter(ids or [TURN_ID])
    return SQLiteWakeTurnMap(
        tmp_path / "turn-ledger.sqlite",
        uuid7_factory=lambda: next(iterator),
        now_ms=lambda: 1_800_000_000_000,
    )


def allocate(m: SQLiteWakeTurnMap, **overrides):
    args = {
        "campaign_ref": CAMPAIGN_REF,
        "agent_id": "A01",
        "wake_intent_id": "wake:task-123:rev-7",
        "prompt_digest": PROMPT_DIGEST,
    }
    args.update(overrides)
    return m.allocate(**args)


def test_first_wake_allocates_uuid7_turn_identity(tmp_path: Path) -> None:
    value = allocate(mapping(tmp_path))
    assert value["turnRequestId"] == TURN_ID
    assert value["disposition"] == "created"
    assert value["wakeIntentId"] == "wake:task-123:rev-7"


def test_exact_wake_replay_returns_same_turn_identity(tmp_path: Path) -> None:
    m = mapping(tmp_path, [TURN_ID])
    first = allocate(m)
    second = allocate(m)
    assert second["turnRequestId"] == first["turnRequestId"]
    assert second["disposition"] == "existing"


@pytest.mark.parametrize(
    "field,value",
    [
        ("campaign_ref", "sha256:" + "b" * 64),
        ("agent_id", "A02"),
        ("prompt_digest", "sha256:" + "2" * 64),
    ],
)
def test_same_wake_intent_changed_semantics_conflicts(
    tmp_path: Path, field: str, value: str
) -> None:
    m = mapping(tmp_path)
    allocate(m)
    with pytest.raises(WakeTurnConflict, match="wake intent identity"):
        allocate(m, **{field: value})


def test_distinct_wakes_receive_distinct_turn_ids(tmp_path: Path) -> None:
    second = "019a9af0-7b00-7000-8000-000000000012"
    m = mapping(tmp_path, [TURN_ID, second])
    first = allocate(m)
    other = allocate(m, wake_intent_id="wake:task-123:rev-8")
    assert first["turnRequestId"] != other["turnRequestId"]


def test_map_coexists_with_existing_turn_effect_table(tmp_path: Path) -> None:
    ledger = tmp_path / "turn-ledger.sqlite"
    db = sqlite3.connect(ledger)
    db.execute("CREATE TABLE turn_effects (turn_request_id TEXT PRIMARY KEY)")
    db.execute("INSERT INTO turn_effects VALUES ('existing-effect')")
    db.commit()
    db.close()
    m = SQLiteWakeTurnMap(ledger, uuid7_factory=lambda: TURN_ID, now_ms=lambda: 1_800_000_000_000)
    allocate(m)
    db = sqlite3.connect(ledger)
    try:
        assert (
            db.execute("SELECT turn_request_id FROM turn_effects").fetchone()[0]
            == "existing-effect"
        )
        assert db.execute("SELECT turn_request_id FROM wake_turn_map").fetchone()[0] == TURN_ID
    finally:
        db.close()


@pytest.mark.parametrize(
    "field,value",
    [
        ("campaign_ref", ""),
        ("agent_id", " A01"),
        ("wake_intent_id", ""),
        ("prompt_digest", "sha256:abc"),
    ],
)
def test_invalid_inputs_fail_closed(tmp_path: Path, field: str, value: str) -> None:
    m = mapping(tmp_path)
    with pytest.raises(ValueError):
        allocate(m, **{field: value})



@pytest.mark.parametrize("basename", ["turn?shadow.sqlite", "turn#shadow.sqlite", "turn%23shadow.sqlite"])
def test_wake_readback_targets_exact_sqlite_file(tmp_path: Path, basename: str) -> None:
    """URI control characters must never redirect an actual wake ledger read."""
    ledger = tmp_path / basename
    m = SQLiteWakeTurnMap(
        ledger,
        uuid7_factory=lambda: TURN_ID,
        now_ms=lambda: 1_800_000_000_000,
    )
    created = allocate(m)
    assert m.get("wake:task-123:rev-7") == {**created, "disposition": "existing"}
    with closing(m._connect(read_only=True)) as db:
        assert db.execute("SELECT count(*) FROM wake_turn_map").fetchone()[0] == 1

def test_read_does_not_create_missing_ledger(tmp_path: Path) -> None:
    ledger = tmp_path / "missing.sqlite"
    m = SQLiteWakeTurnMap.__new__(SQLiteWakeTurnMap)
    m.path = ledger
    assert m.get("wake:missing") is None
    assert not ledger.exists()


def test_module_has_no_provider_or_temporal_effects() -> None:
    text = (ROOT / "scripts/sqlite_wake_turn_map.py").read_text().lower()
    for forbidden in ("playwright", "browserless", "send.click", "temporalclient", "composer.fill"):
        assert forbidden not in text


@pytest.mark.parametrize("fault", ["erase", "forge"])
def test_wake_allocation_is_atomic_with_verified_turn_identity(tmp_path: Path, fault: str) -> None:
    """Turn identity cannot be committed without exact post-write readback."""
    m = mapping(tmp_path)
    with closing(sqlite3.connect(m.path)) as db, db:
        if fault == "erase":
            fault_sql = "DELETE FROM wake_turn_map WHERE wake_intent_id=NEW.wake_intent_id;"
        else:
            fault_sql = "UPDATE wake_turn_map SET turn_request_id='FORGED' WHERE wake_intent_id=NEW.wake_intent_id;"
        db.executescript(
            f"""
            CREATE TABLE corruption_witness (mark INTEGER);
            CREATE TRIGGER wake_corrupt AFTER INSERT ON wake_turn_map BEGIN
                INSERT INTO corruption_witness VALUES (1);
                {fault_sql}
            END;
            """
        )
    with pytest.raises(WakeTurnConflict, match="receipt"):
        allocate(m)
    with closing(sqlite3.connect(m.path)) as db, db:
        assert db.execute("SELECT count(*) FROM wake_turn_map").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM corruption_witness").fetchone()[0] == 0


def test_replay_rejects_existing_row_with_invalid_turn_identity(tmp_path: Path) -> None:
    m = mapping(tmp_path)
    allocate(m)
    with closing(sqlite3.connect(m.path)) as db, db:
        db.execute("UPDATE wake_turn_map SET turn_request_id='FORGED' WHERE wake_intent_id='wake:task-123:rev-7'")
    with pytest.raises(WakeTurnConflict, match="receipt"):
        allocate(m)
