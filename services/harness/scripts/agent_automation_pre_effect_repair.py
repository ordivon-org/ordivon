#!/usr/bin/env python3
"""Digest-bound administrative repair for proven pre-effect UNKNOWN materializations.

This command never contacts a provider and never retries an effect.  It consumes an exact
owner-native evidence document, validates it against the current campaign request, and performs
one transactional UNKNOWN -> PRE_EFFECT_FAILED compare-and-set through the ledger owner.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

from ordivon_harness.user_browser_gateway import UserBrowserGatewayController

try:
    from campaign_materialization import CampaignLaunchSpec, compile_campaign
    from sqlite_conversation_materializer import SQLiteConversationMaterializer
except ModuleNotFoundError:
    from scripts.campaign_materialization import CampaignLaunchSpec, compile_campaign
    from scripts.sqlite_conversation_materializer import SQLiteConversationMaterializer


EVIDENCE_KIND = "ordivon.user-browser-owner-native-pre-effect-repair-evidence"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def read_current_row(ledger: Path, effect_id: str) -> dict[str, Any]:
    db = sqlite3.connect(f"file:{Path(ledger)}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    try:
        row = db.execute(
            """
            SELECT request_id,request_digest,request_json,standing,provider_coordinate,
                   evidence_digest,detail,effect_generation,created_at_ms,updated_at_ms
            FROM requests WHERE request_id=?
            """,
            (effect_id,),
        ).fetchone()
        if row is None:
            raise ValueError("repair effect is absent from materialization ledger")
        return dict(row)
    finally:
        db.close()


def load_and_validate_evidence(
    path: Path,
    *,
    expected_digest: str,
    request,
    current_row: dict[str, Any],
) -> dict[str, Any]:
    observed_digest = sha256_file(path)
    if observed_digest != expected_digest:
        raise ValueError("repair evidence digest mismatch")
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if value.get("schemaVersion") != 1 or value.get("kind") != EVIDENCE_KIND:
        raise ValueError("repair evidence identity is invalid")
    if value.get("effectId") != request.request_id:
        raise ValueError("repair evidence effect identity differs from campaign request")
    if value.get("requestDigest") != request.request_digest:
        raise ValueError("repair evidence request digest differs from campaign request")
    if value.get("promptDigest") != sha256_text(request.bootstrap_prompt):
        raise ValueError("repair evidence prompt digest differs from campaign request")
    if value.get("expectedStanding") != "unknown":
        raise ValueError("repair evidence must bind UNKNOWN standing")
    generation = value.get("expectedEffectGeneration")
    if type(generation) is not int or generation < 1:
        raise ValueError("repair evidence effect generation is invalid")
    if current_row.get("standing") != "unknown":
        raise ValueError("current ledger standing is no longer UNKNOWN")
    if current_row.get("provider_coordinate") is not None:
        raise ValueError("current ledger row already has provider binding")
    if current_row.get("request_digest") != request.request_digest:
        raise ValueError("current ledger request digest differs from campaign request")
    if int(current_row.get("effect_generation")) != generation:
        raise ValueError("current ledger generation differs from repair evidence")
    observed_at = value.get("observedAtMs")
    if type(observed_at) is not int or observed_at < int(current_row.get("updated_at_ms")):
        raise ValueError("repair evidence predates the current ledger version")
    generation2 = value.get("generation2")
    if not isinstance(generation2, dict):
        raise ValueError("repair evidence lacks generation2 owner observation")
    if generation2.get("windowsRuntimeExactClientRequestQueryCount") != 0:
        raise ValueError("repair evidence does not prove exact Windows Runtime request absence")
    expected_request_id = UserBrowserGatewayController._request_id(
        "materialize",
        request.request_id,
        request.request_digest,
        sha256_text(request.bootstrap_prompt),
        request.attachment_digest,
        generation,
    )
    if generation2.get("deterministicRequestId") != expected_request_id:
        raise ValueError("repair evidence deterministic Windows request identity mismatch")
    if value.get("safeToResendAfterRepairOnly") is not True:
        raise ValueError("repair evidence does not preserve resend fence")
    conclusion = value.get("repairConclusion")
    if not isinstance(conclusion, str) or not conclusion.strip():
        raise ValueError("repair evidence lacks a conclusion")
    return value


class _RepairOnlyTarget:
    def materialize(self, request):  # pragma: no cover - repair must never call target
        raise AssertionError("repair unexpectedly invoked materialize target")

    def reconcile(self, request):  # pragma: no cover
        raise AssertionError("repair unexpectedly invoked reconcile target")

    def resume_after_human(self, request):  # pragma: no cover
        raise AssertionError("repair unexpectedly invoked human-resume target")


def repair(
    *,
    ledger: Path,
    spec_path: Path,
    agent_id: str,
    evidence_path: Path,
    evidence_digest: str,
    execute: bool,
    now_ms: int | None = None,
) -> dict[str, Any]:
    raw_spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    spec = CampaignLaunchSpec.from_dict(raw_spec)
    try:
        request = compile_campaign(spec)[agent_id]
    except KeyError as error:
        raise ValueError("agent id is absent from campaign roster") from error
    row = read_current_row(ledger, request.request_id)
    evidence = load_and_validate_evidence(
        evidence_path,
        expected_digest=evidence_digest,
        request=request,
        current_row=row,
    )
    base = {
        "schemaVersion": 1,
        "kind": "ordivon.materialization-pre-effect-administrative-repair",
        "effectId": request.request_id,
        "requestDigest": request.request_digest,
        "evidenceDigest": evidence_digest,
        "standingBefore": row["standing"],
        "effectGeneration": int(row["effect_generation"]),
        "ledgerUpdatedAtMsBefore": int(row["updated_at_ms"]),
        "safeToResendBeforeRepair": False,
        "dryRun": not execute,
    }
    if not execute:
        return {**base, "standingAfter": None, "repairEligible": True}
    materializer = SQLiteConversationMaterializer(Path(ledger), _RepairOnlyTarget())
    receipt = materializer.repair_unknown_as_pre_effect_failed(
        request,
        expected_effect_generation=int(row["effect_generation"]),
        expected_updated_at_ms=int(row["updated_at_ms"]),
        expected_evidence_digest=row["evidence_digest"],
        evidence_digest=evidence_digest,
        detail=(
            "owner-native Windows Runtime admission absent for exact materialize attempt; "
            f"repair evidence {evidence_digest}"
        ),
        now_ms=now_ms,
    )
    after = read_current_row(ledger, request.request_id)
    return {
        **base,
        "dryRun": False,
        "standingAfter": receipt.standing.value,
        "effectGenerationAfter": int(after["effect_generation"]),
        "ledgerUpdatedAtMsAfter": int(after["updated_at_ms"]),
        "repairEligible": True,
        "safeToResendAfterRepair": receipt.standing.value == "pre-effect-failed",
        "receiptDigest": receipt.receipt_digest,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--agent-id", required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--evidence-digest", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    value = repair(
        ledger=args.ledger,
        spec_path=args.spec,
        agent_id=args.agent_id,
        evidence_path=args.evidence,
        evidence_digest=args.evidence_digest,
        execute=args.execute,
    )
    print(json.dumps(value, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
