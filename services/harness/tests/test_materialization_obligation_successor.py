from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from campaign_materialization import CampaignLaunchSpec, canonical_digest, compile_campaign  # noqa: E402
from materialization_obligation_successor import (  # noqa: E402
    LATE_RESULT_DISPOSITION,
    ObligationSuccessorError,
    build_receipt,
)
from materialization_reconciliation_archive import write_archive  # noqa: E402


def spec(campaign_id: str, *, prompt: str = "inspect only") -> dict:
    return {
        "campaignId": campaign_id,
        "sharedPrompt": prompt,
        "roster": [{"agentId": "A01", "roleCard": "independent observer"}],
    }


def create_ledger(path: Path, effect_id: str, *, standing: str = "unknown") -> None:
    db = sqlite3.connect(path)
    try:
        db.execute(
            """CREATE TABLE requests (
            request_id TEXT PRIMARY KEY, request_digest TEXT NOT NULL, request_json TEXT NOT NULL,
            standing TEXT NOT NULL, provider_coordinate TEXT, evidence_digest TEXT, detail TEXT,
            effect_generation INTEGER NOT NULL, created_at_ms INTEGER NOT NULL, updated_at_ms INTEGER NOT NULL
            )"""
        )
        db.execute(
            "INSERT INTO requests VALUES(?,?,?,?,?,?,?,?,?,?)",
            (
                effect_id,
                "sha256:" + "1" * 64,
                "{}",
                standing,
                None,
                "sha256:" + "2" * 64,
                "post-send ambiguous",
                2,
                100,
                200,
            ),
        )
        db.commit()
    finally:
        db.close()


def decision(prior: dict, successor: dict, prior_effect: str, archive: Path) -> dict:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.observation-obligation-successor-decision",
        "obligationId": "review:living-view-r7",
        "agentId": "A01",
        "priorEffectId": prior_effect,
        "authorityRef": "work:owner:review-recovery",
        "reason": "POST_SEND_UNKNOWN_EVIDENCE_LIMIT",
        "observationOnly": True,
        "priorEffectMayHaveOccurred": True,
        "priorEffectSafeToResend": False,
        "successorProviderEffectAuthorized": False,
        "latePriorResultDisposition": LATE_RESULT_DISPOSITION,
        "expectedPriorCampaignDigest": canonical_digest(prior),
        "expectedSuccessorCampaignDigest": canonical_digest(successor),
        "expectedArchiveDigest": "sha256:" + __import__("hashlib").sha256(archive.read_bytes()).hexdigest(),
    }


def fixture(tmp_path: Path):
    prior = spec("campaign-r1")
    successor = spec("campaign-r2")
    prior_spec = tmp_path / "prior.json"
    successor_spec = tmp_path / "successor.json"
    prior_spec.write_text(json.dumps(prior))
    successor_spec.write_text(json.dumps(successor))
    prior_effect = compile_campaign(CampaignLaunchSpec.from_dict(prior))["A01"].request_id
    ledger = tmp_path / "ledger.sqlite"
    create_ledger(ledger, prior_effect)
    archive = tmp_path / "archive.json"
    write_archive(
        ledger,
        archive,
        [
            {
                "effectId": prior_effect,
                "standingAtArchive": "unknown",
                "archiveDisposition": "OBSERVED_EVIDENCE_LIMIT_RETAIN_STANDING",
                "safeToResend": False,
                "automaticRetryAuthorized": False,
                "observationWorkflowId": "wf-reconcile-1",
                "observationCompleted": True,
                "observationAction": "reconcile-existing-effect",
                "observationResultStanding": "unknown",
            }
        ],
        archived_at_ms=300,
    )
    decision_path = tmp_path / "decision.json"
    decision_path.write_text(json.dumps(decision(prior, successor, prior_effect, archive)))
    return ledger, archive, prior_spec, successor_spec, decision_path, prior_effect


def test_successor_receipt_preserves_old_unknown_and_does_not_authorize_send(tmp_path: Path) -> None:
    ledger, archive, prior_spec, successor_spec, decision_path, prior_effect = fixture(tmp_path)
    receipt = build_receipt(
        ledger=ledger,
        archive_path=archive,
        prior_spec_path=prior_spec,
        successor_spec_path=successor_spec,
        decision_path=decision_path,
    )
    assert receipt["priorEffectId"] == prior_effect
    assert receipt["priorEffectStanding"] == "unknown"
    assert receipt["priorEffectSafeToResend"] is False
    assert receipt["priorEffectStandingRetained"] is True
    assert receipt["priorEffectMayHaveOccurred"] is True
    assert receipt["successorEffectId"] != prior_effect
    assert receipt["successorEffectLedgerStanding"] == "unrecorded"
    assert receipt["successorTaskBytesPreserved"] is True
    assert receipt["successorProviderEffectAuthorized"] is False
    assert receipt["providerSendPerformed"] is False

    db = sqlite3.connect(ledger)
    try:
        row = db.execute(
            "SELECT standing,effect_generation FROM requests WHERE request_id=?", (prior_effect,)
        ).fetchone()
        count = db.execute("SELECT count(*) FROM requests").fetchone()[0]
    finally:
        db.close()
    assert row == ("unknown", 2)
    assert count == 1


def test_successor_refuses_task_drift(tmp_path: Path) -> None:
    ledger, archive, prior_spec, successor_spec, decision_path, prior_effect = fixture(tmp_path)
    changed = spec("campaign-r2", prompt="different task")
    successor_spec.write_text(json.dumps(changed))
    d = json.loads(decision_path.read_text())
    d["expectedSuccessorCampaignDigest"] = canonical_digest(changed)
    decision_path.write_text(json.dumps(d))
    with pytest.raises(ObligationSuccessorError, match="exact observation task bytes"):
        build_receipt(
            ledger=ledger,
            archive_path=archive,
            prior_spec_path=prior_spec,
            successor_spec_path=successor_spec,
            decision_path=decision_path,
        )


def test_successor_refuses_unarchived_or_replay_authorizing_decision(tmp_path: Path) -> None:
    ledger, archive, prior_spec, successor_spec, decision_path, _ = fixture(tmp_path)
    d = json.loads(decision_path.read_text())
    d["priorEffectSafeToResend"] = True
    decision_path.write_text(json.dumps(d))
    with pytest.raises(ObligationSuccessorError, match="unsafe to resend"):
        build_receipt(
            ledger=ledger,
            archive_path=archive,
            prior_spec_path=prior_spec,
            successor_spec_path=successor_spec,
            decision_path=decision_path,
        )

    d["priorEffectSafeToResend"] = False
    d["successorProviderEffectAuthorized"] = True
    decision_path.write_text(json.dumps(d))
    with pytest.raises(ObligationSuccessorError, match="must not authorize provider SEND"):
        build_receipt(
            ledger=ledger,
            archive_path=archive,
            prior_spec_path=prior_spec,
            successor_spec_path=successor_spec,
            decision_path=decision_path,
        )


def test_successor_refuses_if_new_effect_already_exists(tmp_path: Path) -> None:
    ledger, archive, prior_spec, successor_spec, decision_path, _ = fixture(tmp_path)
    successor = CampaignLaunchSpec.from_dict(json.loads(successor_spec.read_text()))
    successor_effect = compile_campaign(successor)["A01"].request_id
    db = sqlite3.connect(ledger)
    try:
        db.execute(
            "INSERT INTO requests VALUES(?,?,?,?,?,?,?,?,?,?)",
            (
                successor_effect,
                "sha256:" + "3" * 64,
                "{}",
                "prepared",
                None,
                None,
                None,
                1,
                300,
                300,
            ),
        )
        db.commit()
    finally:
        db.close()
    with pytest.raises(ObligationSuccessorError, match="already recorded"):
        build_receipt(
            ledger=ledger,
            archive_path=archive,
            prior_spec_path=prior_spec,
            successor_spec_path=successor_spec,
            decision_path=decision_path,
        )
