#!/usr/bin/env python3
"""Effect-free owner receipt for successor observation obligations after post-SEND ambiguity.

This module never mutates the materialization ledger, never relabels an old UNKNOWN effect,
and never authorizes a provider SEND.  It proves only that one archived observation-only
obligation may use a new campaign/effect identity while the old effect remains immutable
historical ambiguity.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import tempfile
from pathlib import Path
from typing import Any

try:
    from campaign_materialization import CampaignLaunchSpec, canonical_digest, compile_campaign
    from materialization_reconciliation_archive import (
        ReconciliationArchiveError,
        build_archive,
        load_archive,
    )
except ModuleNotFoundError:
    from scripts.campaign_materialization import (
        CampaignLaunchSpec,
        canonical_digest,
        compile_campaign,
    )
    from scripts.materialization_reconciliation_archive import (
        ReconciliationArchiveError,
        build_archive,
        load_archive,
    )

DECISION_KIND = "ordivon.observation-obligation-successor-decision"
RECEIPT_KIND = "ordivon.observation-obligation-successor-receipt"
REASON = "POST_SEND_UNKNOWN_EVIDENCE_LIMIT"
LATE_RESULT_DISPOSITION = "PRESERVE_AS_HISTORICAL_DO_NOT_SATISFY_SUCCESSOR"


class ObligationSuccessorError(RuntimeError):
    pass


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as error:
        raise ObligationSuccessorError(
            f"JSON input is unreadable: {type(error).__name__}: {error}"
        ) from error
    if not isinstance(value, dict):
        raise ObligationSuccessorError("JSON input must be an object")
    return value


def _digest_bytes(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _file_digest(path: Path) -> str:
    return _digest_bytes(Path(path).read_bytes())


def _sha(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value.startswith("sha256:")
        or len(value) != 71
        or value[7:] != value[7:].lower()
    ):
        raise ObligationSuccessorError(f"{label} must be canonical sha256:<64 lowercase hex>")
    try:
        int(value[7:], 16)
    except ValueError as error:
        raise ObligationSuccessorError(f"{label} must be hexadecimal") from error
    return value


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ObligationSuccessorError(f"{label} must be non-empty and trimmed")
    return value


def _ledger_row(path: Path, effect_id: str) -> dict[str, Any] | None:
    path = Path(path)
    if not path.is_file():
        raise ObligationSuccessorError("materialization ledger does not exist")
    db = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    try:
        row = db.execute(
            """SELECT request_id,request_digest,standing,provider_coordinate,evidence_digest,
                      detail,effect_generation,updated_at_ms
               FROM requests WHERE request_id=?""",
            (effect_id,),
        ).fetchone()
        return dict(row) if row is not None else None
    finally:
        db.close()


def _selected_role(spec: CampaignLaunchSpec, agent_id: str):
    if len(spec.roster) != 1:
        raise ObligationSuccessorError(
            "observation obligation successor requires a one-agent campaign"
        )
    role = spec.roster[0]
    if role.agent_id != agent_id:
        raise ObligationSuccessorError("decision agentId differs from campaign roster")
    return role


def _validate_decision(value: dict[str, Any]) -> dict[str, Any]:
    required = {
        "schemaVersion",
        "kind",
        "obligationId",
        "agentId",
        "priorEffectId",
        "authorityRef",
        "reason",
        "observationOnly",
        "priorEffectMayHaveOccurred",
        "priorEffectSafeToResend",
        "successorProviderEffectAuthorized",
        "latePriorResultDisposition",
        "expectedPriorCampaignDigest",
        "expectedSuccessorCampaignDigest",
        "expectedArchiveDigest",
    }
    if set(value) != required:
        raise ObligationSuccessorError(
            f"decision fields must be exactly {sorted(required)}"
        )
    if value["schemaVersion"] != 1 or value["kind"] != DECISION_KIND:
        raise ObligationSuccessorError("decision identity is invalid")
    _text(value["obligationId"], "obligationId")
    _text(value["agentId"], "agentId")
    _sha(value["priorEffectId"], "priorEffectId")
    _text(value["authorityRef"], "authorityRef")
    if value["reason"] != REASON:
        raise ObligationSuccessorError("successor reason is unsupported")
    if value["observationOnly"] is not True:
        raise ObligationSuccessorError("successor primitive is restricted to observation-only obligations")
    if value["priorEffectMayHaveOccurred"] is not True:
        raise ObligationSuccessorError("post-SEND successor must preserve possibility that prior effect occurred")
    if value["priorEffectSafeToResend"] is not False:
        raise ObligationSuccessorError("prior effect must remain unsafe to resend")
    if value["successorProviderEffectAuthorized"] is not False:
        raise ObligationSuccessorError("successor decision must not authorize provider SEND")
    if value["latePriorResultDisposition"] != LATE_RESULT_DISPOSITION:
        raise ObligationSuccessorError("late prior result disposition is unsupported")
    _sha(value["expectedPriorCampaignDigest"], "expectedPriorCampaignDigest")
    _sha(value["expectedSuccessorCampaignDigest"], "expectedSuccessorCampaignDigest")
    _sha(value["expectedArchiveDigest"], "expectedArchiveDigest")
    return value


def build_receipt(
    *,
    ledger: Path,
    archive_path: Path,
    prior_spec_path: Path,
    successor_spec_path: Path,
    decision_path: Path,
) -> dict[str, Any]:
    decision = _validate_decision(_read_json(decision_path))
    prior_raw = _read_json(prior_spec_path)
    successor_raw = _read_json(successor_spec_path)
    prior_digest = canonical_digest(prior_raw)
    successor_digest = canonical_digest(successor_raw)
    if prior_digest != decision["expectedPriorCampaignDigest"]:
        raise ObligationSuccessorError("prior campaign digest differs from decision fence")
    if successor_digest != decision["expectedSuccessorCampaignDigest"]:
        raise ObligationSuccessorError("successor campaign digest differs from decision fence")
    archive_digest = _file_digest(archive_path)
    if archive_digest != decision["expectedArchiveDigest"]:
        raise ObligationSuccessorError("reconciliation archive bytes differ from decision fence")

    prior = CampaignLaunchSpec.from_dict(prior_raw)
    successor = CampaignLaunchSpec.from_dict(successor_raw)
    agent_id = decision["agentId"]
    prior_role = _selected_role(prior, agent_id)
    successor_role = _selected_role(successor, agent_id)
    if prior.campaign_id == successor.campaign_id:
        raise ObligationSuccessorError("successor campaignId must be new")
    if prior.shared_prompt != successor.shared_prompt or prior_role.role_card != successor_role.role_card:
        raise ObligationSuccessorError("successor must preserve exact observation task bytes")
    if prior.shared_attachments != successor.shared_attachments:
        raise ObligationSuccessorError("successor must preserve exact attachment set")

    prior_request = compile_campaign(prior)[agent_id]
    successor_request = compile_campaign(successor)[agent_id]
    if prior_request.request_id != decision["priorEffectId"]:
        raise ObligationSuccessorError("decision priorEffectId differs from compiled prior campaign")
    if successor_request.request_id == prior_request.request_id:
        raise ObligationSuccessorError("successor effect identity did not change")

    old_row = _ledger_row(ledger, prior_request.request_id)
    if old_row is None:
        raise ObligationSuccessorError("prior effect is absent from materialization ledger")
    if old_row["standing"] not in {"unknown", "submit-observed"}:
        raise ObligationSuccessorError("prior effect is not post-SEND ambiguous")
    if old_row["provider_coordinate"] is not None:
        raise ObligationSuccessorError("prior ambiguous effect already has a provider coordinate")
    if _ledger_row(ledger, successor_request.request_id) is not None:
        raise ObligationSuccessorError("successor effect identity is already recorded in ledger")

    archive = load_archive(archive_path)
    if archive is None:
        raise ObligationSuccessorError("reconciliation archive is absent")
    entries = [
        row
        for row in archive.get("entries", [])
        if isinstance(row, dict) and row.get("effectId") == prior_request.request_id
    ]
    if len(entries) != 1:
        raise ObligationSuccessorError("prior effect needs exactly one reconciliation archive entry")
    archived = entries[0]
    if archived.get("archiveDisposition") != "OBSERVED_EVIDENCE_LIMIT_RETAIN_STANDING":
        raise ObligationSuccessorError("prior effect has not reached observed evidence limit")
    if archived.get("observationCompleted") is not True:
        raise ObligationSuccessorError("prior effect reconciliation observation is incomplete")
    if archived.get("safeToResend") is not False or archived.get("automaticRetryAuthorized") is not False:
        raise ObligationSuccessorError("archive illegally authorizes prior effect replay")
    try:
        normalized = build_archive(ledger, [archived], archived_at_ms=archive.get("archivedAtMs"))
    except ReconciliationArchiveError as error:
        raise ObligationSuccessorError(str(error)) from error
    normalized_entry = normalized["entries"][0]
    if normalized_entry["standingAtArchive"] != old_row["standing"]:
        raise ObligationSuccessorError("archive standing is stale relative to current ledger")

    return {
        "schemaVersion": 1,
        "kind": RECEIPT_KIND,
        "obligationId": decision["obligationId"],
        "agentId": agent_id,
        "authorityRef": decision["authorityRef"],
        "reason": REASON,
        "observationOnly": True,
        "priorCampaignId": prior.campaign_id,
        "priorCampaignDigest": prior_digest,
        "priorEffectId": prior_request.request_id,
        "priorEffectStanding": old_row["standing"],
        "priorEffectGeneration": int(old_row["effect_generation"]),
        "priorLedgerUpdatedAtMs": int(old_row["updated_at_ms"]),
        "priorEffectMayHaveOccurred": True,
        "priorEffectSafeToResend": False,
        "priorEffectStandingRetained": True,
        "reconciliationArchiveDigest": archive_digest,
        "reconciliationDisposition": archived["archiveDisposition"],
        "reconciliationObservationWorkflowId": archived.get("observationWorkflowId"),
        "latePriorResultDisposition": LATE_RESULT_DISPOSITION,
        "successorCampaignId": successor.campaign_id,
        "successorCampaignDigest": successor_digest,
        "successorEffectId": successor_request.request_id,
        "successorEffectLedgerStanding": "unrecorded",
        "successorTaskBytesPreserved": True,
        "successorProviderEffectAuthorized": False,
        "providerSendPerformed": False,
        "decisionDigest": _file_digest(decision_path),
    }


def _write_atomic(path: Path, value: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(value, sort_keys=True, indent=2) + "\n").encode("utf-8")
    if path.exists():
        if path.read_bytes() == raw:
            return
        raise ObligationSuccessorError("successor receipt path already contains different bytes")
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


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ledger", type=Path, required=True)
    p.add_argument("--archive", type=Path, required=True)
    p.add_argument("--prior-spec", type=Path, required=True)
    p.add_argument("--successor-spec", type=Path, required=True)
    p.add_argument("--decision", type=Path, required=True)
    p.add_argument("--output", type=Path)
    return p


def main() -> int:
    a = parser().parse_args()
    receipt = build_receipt(
        ledger=a.ledger,
        archive_path=a.archive,
        prior_spec_path=a.prior_spec,
        successor_spec_path=a.successor_spec,
        decision_path=a.decision,
    )
    if a.output is not None:
        _write_atomic(a.output, receipt)
    print(json.dumps(receipt, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
