#!/usr/bin/env python3
"""Administrative archive overlay for historical unresolved materializations.

The effect ledger remains the truth owner for provider-effect standing. This overlay only
records that an unresolved historical effect has been investigated to the current evidence
boundary. It never authorizes retry/resend and never mutates ledger standing.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import tempfile
import time
from pathlib import Path
from typing import Any, Iterable

KIND = "ordivon.materialization-reconciliation-archive"
SCHEMA_VERSION = 1
ARCHIVABLE_STANDINGS = frozenset({"unknown", "submit-observed", "human-required"})
AMBIGUOUS_STANDINGS = frozenset({"unknown", "submit-observed"})
DISPOSITIONS = frozenset(
    {
        "OBSERVED_EVIDENCE_LIMIT_RETAIN_STANDING",
        "OBSERVATION_UNAVAILABLE_IDENTITY_ABSENT",
        "LEGACY_HUMAN_HANDOFF_INACTIVE",
    }
)


class ReconciliationArchiveError(RuntimeError):
    pass


def _ledger_rows(path: Path) -> dict[str, dict[str, Any]]:
    path = Path(path)
    if not path.is_file():
        raise ReconciliationArchiveError("materialization ledger does not exist")
    db = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    try:
        exists = db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='requests'"
        ).fetchone()
        if exists is None:
            raise ReconciliationArchiveError("materialization ledger has no requests table")
        return {
            str(row["request_id"]): {
                "standing": str(row["standing"]),
                "effectGeneration": int(row["effect_generation"]),
                "updatedAtMs": int(row["updated_at_ms"]),
            }
            for row in db.execute(
                "SELECT request_id,standing,effect_generation,updated_at_ms FROM requests"
            )
        }
    finally:
        db.close()


def _semantic_digest(rows: dict[str, dict[str, Any]]) -> str:
    raw = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _normalize_entry(value: dict[str, Any], rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ReconciliationArchiveError("archive entry must be an object")
    effect_id = value.get("effectId")
    standing = value.get("standingAtArchive")
    disposition = value.get("archiveDisposition")
    if (
        not isinstance(effect_id, str)
        or not effect_id.startswith("sha256:")
        or len(effect_id) != 71
    ):
        raise ReconciliationArchiveError("archive entry requires exact SHA-256 effectId")
    row = rows.get(effect_id)
    if row is None:
        raise ReconciliationArchiveError(f"archive effect is absent from ledger: {effect_id}")
    if standing not in ARCHIVABLE_STANDINGS:
        raise ReconciliationArchiveError(
            f"standing {standing!r} is not administratively archivable"
        )
    if row["standing"] != standing:
        raise ReconciliationArchiveError(
            f"archive standing differs from current ledger standing for {effect_id}"
        )
    if disposition not in DISPOSITIONS:
        raise ReconciliationArchiveError("unsupported archive disposition")
    if value.get("safeToResend") is not False:
        raise ReconciliationArchiveError("archived unresolved effect must remain unsafe to resend")
    if value.get("automaticRetryAuthorized") is not False:
        raise ReconciliationArchiveError("archive cannot authorize automatic retry")

    if disposition == "OBSERVED_EVIDENCE_LIMIT_RETAIN_STANDING":
        if standing not in AMBIGUOUS_STANDINGS:
            raise ReconciliationArchiveError("observation archive requires ambiguous standing")
        workflow_id = value.get("observationWorkflowId")
        if not isinstance(workflow_id, str) or not workflow_id:
            raise ReconciliationArchiveError("observation archive requires workflow identity")
        if value.get("observationCompleted") is not True:
            raise ReconciliationArchiveError("observation archive requires completed observation")
    elif disposition == "OBSERVATION_UNAVAILABLE_IDENTITY_ABSENT":
        if standing != "unknown":
            raise ReconciliationArchiveError("identity-absent archive is valid only for UNKNOWN")
        if value.get("campaignIdentityAvailable") is not False:
            raise ReconciliationArchiveError("identity-absent archive must prove identity absence")
    elif disposition == "LEGACY_HUMAN_HANDOFF_INACTIVE":
        if standing != "human-required":
            raise ReconciliationArchiveError("legacy handoff archive requires HUMAN_REQUIRED")
        if value.get("handoffStanding") != "INACTIVE":
            raise ReconciliationArchiveError("legacy handoff archive requires INACTIVE handoff")

    normalized = {
        "effectId": effect_id,
        "standingAtArchive": standing,
        "effectGenerationAtArchive": row["effectGeneration"],
        "ledgerUpdatedAtMsAtArchive": row["updatedAtMs"],
        "archiveDisposition": disposition,
        "safeToResend": False,
        "automaticRetryAuthorized": False,
    }
    for key in (
        "campaignRef",
        "campaignId",
        "agentId",
        "observationWorkflowId",
        "observationAction",
        "observationResultStanding",
        "observationUnavailableReason",
        "handoffStanding",
        "detail",
    ):
        val = value.get(key)
        if isinstance(val, str) and val:
            normalized[key] = val
    for key in ("observationCompleted", "campaignIdentityAvailable"):
        if isinstance(value.get(key), bool):
            normalized[key] = value[key]
    return normalized


def build_archive(
    ledger: Path, entries: Iterable[dict[str, Any]], *, archived_at_ms: int | None = None
) -> dict[str, Any]:
    rows = _ledger_rows(ledger)
    normalized = [_normalize_entry(value, rows) for value in entries]
    ids = [value["effectId"] for value in normalized]
    if len(ids) != len(set(ids)):
        raise ReconciliationArchiveError("archive contains duplicate effect identity")
    normalized.sort(key=lambda row: row["effectId"])
    return {
        "schemaVersion": SCHEMA_VERSION,
        "kind": KIND,
        "archivedAtMs": int(time.time() * 1000) if archived_at_ms is None else int(archived_at_ms),
        "ledgerSemanticDigestAtArchive": _semantic_digest(rows),
        "entryCount": len(normalized),
        "entries": normalized,
    }


def _write_private_atomic(path: Path, value: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(value, sort_keys=True, indent=2) + "\n").encode("utf-8")
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def write_archive(
    ledger: Path,
    path: Path,
    entries: Iterable[dict[str, Any]],
    *,
    archived_at_ms: int | None = None,
) -> dict[str, Any]:
    value = build_archive(ledger, entries, archived_at_ms=archived_at_ms)
    _write_private_atomic(path, value)
    return value


def load_archive(path: Path) -> dict[str, Any] | None:
    path = Path(path)
    if not path.exists():
        return None
    if not path.is_file() or path.is_symlink():
        raise ReconciliationArchiveError("reconciliation archive must be a regular file")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as error:
        raise ReconciliationArchiveError(
            f"reconciliation archive is unreadable: {type(error).__name__}: {error}"
        ) from error
    if (
        not isinstance(value, dict)
        or value.get("schemaVersion") != SCHEMA_VERSION
        or value.get("kind") != KIND
    ):
        raise ReconciliationArchiveError("reconciliation archive identity is invalid")
    entries = value.get("entries")
    if not isinstance(entries, list) or value.get("entryCount") != len(entries):
        raise ReconciliationArchiveError("reconciliation archive entry count is invalid")
    return value


def project_archive(ledger: Path, path: Path) -> dict[str, Any]:
    rows = _ledger_rows(ledger)
    unresolved = {
        effect_id: row
        for effect_id, row in rows.items()
        if row["standing"] in {"prepared", "unknown", "submit-observed", "human-required"}
    }
    raw_unresolved = len(unresolved)
    raw_ambiguous = sum(row["standing"] in AMBIGUOUS_STANDINGS for row in unresolved.values())
    raw_human = sum(row["standing"] == "human-required" for row in unresolved.values())
    try:
        archive = load_archive(path)
    except ReconciliationArchiveError as error:
        return {
            "healthy": False,
            "present": True,
            "archiveEntries": 0,
            "activeArchivedUnresolved": 0,
            "staleArchiveEntries": 0,
            "actionableUnresolved": raw_unresolved,
            "actionableEffectOutcomeAmbiguous": raw_ambiguous,
            "actionableHumanRequired": raw_human,
            "issues": [str(error)],
        }
    if archive is None:
        return {
            "healthy": True,
            "present": False,
            "archiveEntries": 0,
            "activeArchivedUnresolved": 0,
            "staleArchiveEntries": 0,
            "actionableUnresolved": raw_unresolved,
            "actionableEffectOutcomeAmbiguous": raw_ambiguous,
            "actionableHumanRequired": raw_human,
            "issues": [],
        }

    active = []
    stale = []
    issues = []
    seen: set[str] = set()
    for raw in archive["entries"]:
        if not isinstance(raw, dict):
            issues.append("archive entry is not an object")
            continue
        effect_id = raw.get("effectId")
        if not isinstance(effect_id, str) or effect_id in seen:
            issues.append("archive contains invalid or duplicate effect identity")
            continue
        seen.add(effect_id)
        row = unresolved.get(effect_id)
        if row is None or row["standing"] != raw.get("standingAtArchive"):
            stale.append(effect_id)
            continue
        try:
            _normalize_entry(raw, rows)
        except ReconciliationArchiveError as error:
            issues.append(str(error))
            continue
        active.append(raw)

    archived_ids = {row["effectId"] for row in active}
    actionable = {k: v for k, v in unresolved.items() if k not in archived_ids}
    return {
        "healthy": not issues,
        "present": True,
        "archiveEntries": len(archive["entries"]),
        "activeArchivedUnresolved": len(active),
        "archivedEffectOutcomeAmbiguous": sum(
            row["standingAtArchive"] in AMBIGUOUS_STANDINGS for row in active
        ),
        "archivedHumanRequired": sum(
            row["standingAtArchive"] == "human-required" for row in active
        ),
        "staleArchiveEntries": len(stale),
        "actionableUnresolved": len(actionable),
        "actionableEffectOutcomeAmbiguous": sum(
            row["standing"] in AMBIGUOUS_STANDINGS for row in actionable.values()
        ),
        "actionableHumanRequired": sum(
            row["standing"] == "human-required" for row in actionable.values()
        ),
        "issues": issues,
    }
