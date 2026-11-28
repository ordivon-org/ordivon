from __future__ import annotations

import sqlite3
import sys
from contextlib import closing
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



@pytest.mark.parametrize("basename", ["effect?ledger.sqlite", "effect#ledger.sqlite", "effect%23ledger.sqlite"])
def test_archive_uses_exact_physical_sqlite_filename(tmp_path: Path, basename: str) -> None:
    ledger = tmp_path / basename
    archive = tmp_path / "archive.json"
    effect = "sha256:" + "f" * 64
    create_ledger(ledger, [(effect, "unknown")])
    write_archive(ledger, archive, [observed(effect)], archived_at_ms=300)
    assert project_archive(ledger, archive)["activeArchivedUnresolved"] == 1
    assert project_archive(ledger, archive)["actionableUnresolved"] == 0

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


@pytest.mark.parametrize(
    "assignment",
    [
        "effect_generation=effect_generation+1",
        "updated_at_ms=updated_at_ms+1",
        "request_digest='changed-request'",
        "request_json='{\"changed\":true}'",
        "provider_coordinate='changed-provider'",
        "evidence_digest='changed-evidence'",
        "detail='changed-observation'",
    ],
)
def test_same_standing_does_not_preserve_archive_currentness(
    tmp_path: Path, assignment: str
) -> None:
    ledger = tmp_path / "ledger.sqlite"
    archive = tmp_path / "archive.json"
    effect = "sha256:" + "a" * 64
    create_ledger(ledger, [(effect, "unknown")])
    write_archive(ledger, archive, [observed(effect)], archived_at_ms=300)
    with closing(sqlite3.connect(ledger)) as db, db:
        db.execute(f"UPDATE requests SET {assignment} WHERE request_id=?", (effect,))
    value = project_archive(ledger, archive)
    assert value["activeArchivedUnresolved"] == 0
    assert value["staleArchiveEntries"] == 1
    assert value["actionableUnresolved"] == 1


def test_unrelated_row_change_does_not_invalidate_exact_archive_subject(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.sqlite"
    archive = tmp_path / "archive.json"
    one, two = "sha256:" + "a" * 64, "sha256:" + "b" * 64
    create_ledger(ledger, [(one, "unknown"), (two, "unknown")])
    write_archive(ledger, archive, [observed(one)], archived_at_ms=300)
    with closing(sqlite3.connect(ledger)) as db, db:
        db.execute("UPDATE requests SET evidence_digest='new' WHERE request_id=?", (two,))
    value = project_archive(ledger, archive)
    assert value["activeArchivedUnresolved"] == 1
    assert value["actionableUnresolved"] == 1


def test_legacy_tuple_only_archive_is_not_exact_or_data_release(tmp_path: Path) -> None:
    import json

    ledger = tmp_path / "ledger.sqlite"
    archive = tmp_path / "archive.json"
    effect = "sha256:" + "a" * 64
    create_ledger(ledger, [(effect, "unknown")])
    value = write_archive(ledger, archive, [observed(effect)], archived_at_ms=300)
    assert value["schemaVersion"] == 2
    value["schemaVersion"] = 1
    value["entries"][0].pop("ledgerRowDigestAtArchive")
    archive.write_text(json.dumps(value))
    projection = project_archive(ledger, archive)
    assert projection["activeArchivedUnresolved"] == 1
    assert projection["legacyTupleOnlyArchivedUnresolved"] == 1
    assert projection["exactRowArchivedUnresolved"] == 0
    assert projection["archiveAuthorizesDataRelease"] is False
    with closing(sqlite3.connect(ledger)) as db, db:
        db.execute("UPDATE requests SET effect_generation=effect_generation+1")
    projection = project_archive(ledger, archive)
    assert projection["actionableUnresolved"] == 1
    assert projection["legacyTupleOnlyArchivedUnresolved"] == 0


@pytest.mark.parametrize("mutation", ["missing-row-digest", "duplicate-subject", "coerced-generation"])
def test_invalid_archival_evidence_cannot_mask_unresolved(tmp_path: Path, mutation: str) -> None:
    import json

    ledger = tmp_path / "ledger.sqlite"
    archive = tmp_path / "archive.json"
    effect = "sha256:" + "b" * 64
    create_ledger(ledger, [(effect, "unknown")])
    value = write_archive(ledger, archive, [observed(effect)], archived_at_ms=300)
    if mutation == "missing-row-digest":
        value["entries"][0].pop("ledgerRowDigestAtArchive")
    elif mutation == "coerced-generation":
        value["entries"][0]["effectGenerationAtArchive"] = True
    else:
        value["entries"].append(dict(value["entries"][0]))
        value["entryCount"] += 1
    archive.write_text(json.dumps(value))
    projection = project_archive(ledger, archive)
    assert projection["activeArchivedUnresolved"] == 0
    assert projection["actionableUnresolved"] == 1
    assert projection["archiveAuthorizesDataRelease"] is False
