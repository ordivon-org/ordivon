from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from materialization_reconciliation_archive import (  # noqa: E402
    ReconciliationArchiveError,
    project_archive,
    write_archive,
)


def create_ledger(path: Path, rows: list[tuple[str, str]]) -> None:
    db = sqlite3.connect(path)
    try:
        db.execute(
            """CREATE TABLE requests (
            request_id TEXT PRIMARY KEY, request_digest TEXT NOT NULL, request_json TEXT NOT NULL,
            standing TEXT NOT NULL, provider_coordinate TEXT, evidence_digest TEXT, detail TEXT,
            effect_generation INTEGER NOT NULL, created_at_ms INTEGER NOT NULL, updated_at_ms INTEGER NOT NULL
            )"""
        )
        for index, (effect_id, standing) in enumerate(rows):
            db.execute(
                "INSERT INTO requests VALUES(?,?,?,?,?,?,?,?,?,?)",
                (effect_id, f"d{index}", "{}", standing, None, None, None, 1, 100, 200 + index),
            )
        db.commit()
    finally:
        db.close()


def observed(effect_id: str, standing: str = "unknown") -> dict:
    return {
        "effectId": effect_id,
        "standingAtArchive": standing,
        "archiveDisposition": "OBSERVED_EVIDENCE_LIMIT_RETAIN_STANDING",
        "safeToResend": False,
        "automaticRetryAuthorized": False,
        "observationWorkflowId": "wf-1",
        "observationCompleted": True,
        "observationAction": "current-carrier-reconcile",
        "observationResultStanding": standing,
    }


def test_archive_reduces_actionable_projection_without_mutating_raw_ledger(tmp_path: Path) -> None:
    db = tmp_path / "ledger.sqlite"
    archive = tmp_path / "archive.json"
    e1 = "sha256:" + "1" * 64
    e2 = "sha256:" + "2" * 64
    create_ledger(db, [(e1, "unknown"), (e2, "human-required")])
    before = db.read_bytes()
    write_archive(
        db,
        archive,
        [
            observed(e1),
            {
                "effectId": e2,
                "standingAtArchive": "human-required",
                "archiveDisposition": "LEGACY_HUMAN_HANDOFF_INACTIVE",
                "safeToResend": False,
                "automaticRetryAuthorized": False,
                "handoffStanding": "INACTIVE",
            },
        ],
        archived_at_ms=300,
    )
    value = project_archive(db, archive)
    assert value["healthy"] is True
    assert value["activeArchivedUnresolved"] == 2
    assert value["actionableUnresolved"] == 0
    assert value["archivedEffectOutcomeAmbiguous"] == 1
    assert value["archivedHumanRequired"] == 1
    assert db.read_bytes() == before


def test_standing_change_invalidates_archive_and_restores_actionable_backlog(
    tmp_path: Path,
) -> None:
    db = tmp_path / "ledger.sqlite"
    archive = tmp_path / "archive.json"
    effect = "sha256:" + "3" * 64
    create_ledger(db, [(effect, "unknown")])
    write_archive(db, archive, [observed(effect)], archived_at_ms=300)
    con = sqlite3.connect(db)
    con.execute("UPDATE requests SET standing='prepared' WHERE request_id=?", (effect,))
    con.commit()
    con.close()
    value = project_archive(db, archive)
    assert value["activeArchivedUnresolved"] == 0
    assert value["staleArchiveEntries"] == 1
    assert value["actionableUnresolved"] == 1


def test_corrupt_archive_never_masks_unresolved(tmp_path: Path) -> None:
    db = tmp_path / "ledger.sqlite"
    archive = tmp_path / "archive.json"
    effect = "sha256:" + "4" * 64
    create_ledger(db, [(effect, "unknown")])
    archive.write_text("not-json")
    value = project_archive(db, archive)
    assert value["healthy"] is False
    assert value["activeArchivedUnresolved"] == 0
    assert value["actionableUnresolved"] == 1


def test_archive_cannot_authorize_resend_or_archive_prepared(tmp_path: Path) -> None:
    db = tmp_path / "ledger.sqlite"
    archive = tmp_path / "archive.json"
    effect = "sha256:" + "5" * 64
    create_ledger(db, [(effect, "prepared")])
    row = observed(effect, "prepared")
    row["safeToResend"] = True
    with pytest.raises(ReconciliationArchiveError):
        write_archive(db, archive, [row], archived_at_ms=300)


def test_identity_absent_archive_is_unknown_only(tmp_path: Path) -> None:
    db = tmp_path / "ledger.sqlite"
    archive = tmp_path / "archive.json"
    effect = "sha256:" + "6" * 64
    create_ledger(db, [(effect, "unknown")])
    write_archive(
        db,
        archive,
        [
            {
                "effectId": effect,
                "standingAtArchive": "unknown",
                "archiveDisposition": "OBSERVATION_UNAVAILABLE_IDENTITY_ABSENT",
                "safeToResend": False,
                "automaticRetryAuthorized": False,
                "campaignIdentityAvailable": False,
            }
        ],
        archived_at_ms=300,
    )
    value = project_archive(db, archive)
    assert value["actionableUnresolved"] == 0
