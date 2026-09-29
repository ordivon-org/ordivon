from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from agent_automation_pre_effect_repair import load_and_validate_evidence  # noqa: E402
from conversation_relay_carrier import (  # noqa: E402
    CarrierConflict,
    CarrierMaterializationRequest,
    MaterializationStanding,
)
from sqlite_conversation_materializer import (  # noqa: E402
    SQLiteConversationMaterializer,
    TargetMaterializationObservation,
)
from ordivon_harness.user_browser_gateway import UserBrowserGatewayController  # noqa: E402


class UnknownTarget:
    def materialize(self, request):
        return TargetMaterializationObservation(
            standing=MaterializationStanding.UNKNOWN,
            detail="transport response lost",
        )

    def reconcile(self, request):
        return self.materialize(request)

    def resume_after_human(self, request):
        raise AssertionError("not expected")


def request() -> CarrierMaterializationRequest:
    return CarrierMaterializationRequest(
        request_id="effect-repair",
        preparation_digest="sha256:" + "1" * 64,
        bootstrap_prompt="fixed repair bootstrap",
    )


def row(path: Path) -> sqlite3.Row:
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    try:
        value = db.execute("SELECT * FROM requests WHERE request_id='effect-repair'").fetchone()
        assert value is not None
        return value
    finally:
        db.close()


def test_owner_repair_unknown_to_pre_effect_failed_is_generation_preserving(tmp_path: Path):
    path = tmp_path / "ledger.sqlite"
    materializer = SQLiteConversationMaterializer(path, UnknownTarget())
    req = request()
    first = materializer.materialize(req, now_ms=10)
    assert first.standing is MaterializationStanding.UNKNOWN
    before = row(path)
    repaired = materializer.repair_unknown_as_pre_effect_failed(
        req,
        expected_effect_generation=1,
        expected_updated_at_ms=10,
        expected_evidence_digest=None,
        evidence_digest="sha256:" + "2" * 64,
        detail="owner-native admission absent",
        now_ms=20,
    )
    after = row(path)
    assert repaired.standing is MaterializationStanding.PRE_EFFECT_FAILED
    assert int(after["effect_generation"]) == int(before["effect_generation"]) == 1
    assert after["evidence_digest"] == "sha256:" + "2" * 64
    assert int(after["updated_at_ms"]) == 20


def test_owner_repair_fails_closed_on_generation_or_version_drift(tmp_path: Path):
    path = tmp_path / "ledger.sqlite"
    materializer = SQLiteConversationMaterializer(path, UnknownTarget())
    req = request()
    materializer.materialize(req, now_ms=10)
    with pytest.raises(CarrierConflict, match="generation changed"):
        materializer.repair_unknown_as_pre_effect_failed(
            req,
            expected_effect_generation=2,
            expected_updated_at_ms=10,
            expected_evidence_digest=None,
            evidence_digest="sha256:" + "2" * 64,
            detail="owner-native admission absent",
            now_ms=20,
        )
    with pytest.raises(CarrierConflict, match="ledger version changed"):
        materializer.repair_unknown_as_pre_effect_failed(
            req,
            expected_effect_generation=1,
            expected_updated_at_ms=11,
            expected_evidence_digest=None,
            evidence_digest="sha256:" + "2" * 64,
            detail="owner-native admission absent",
            now_ms=20,
        )
    assert row(path)["standing"] == "unknown"


def test_owner_repair_never_regresses_submit_observed_or_bound(tmp_path: Path):
    path = tmp_path / "ledger.sqlite"
    materializer = SQLiteConversationMaterializer(path, UnknownTarget())
    req = request()
    materializer.materialize(req, now_ms=10)
    db = sqlite3.connect(path)
    try:
        db.execute(
            "UPDATE requests SET standing='submit-observed',evidence_digest=?,updated_at_ms=11 WHERE request_id=?",
            ("sha256:" + "3" * 64, req.request_id),
        )
        db.commit()
    finally:
        db.close()
    with pytest.raises(CarrierConflict, match="requires current UNKNOWN"):
        materializer.repair_unknown_as_pre_effect_failed(
            req,
            expected_effect_generation=1,
            expected_updated_at_ms=11,
            expected_evidence_digest="sha256:" + "3" * 64,
            evidence_digest="sha256:" + "2" * 64,
            detail="owner-native admission absent",
            now_ms=20,
        )
    assert row(path)["standing"] == "submit-observed"


def test_repair_evidence_binds_exact_generation_request_identity(tmp_path: Path):
    req = request()
    ledger = tmp_path / "ledger.sqlite"
    materializer = SQLiteConversationMaterializer(ledger, UnknownTarget())
    materializer.materialize(req, now_ms=10)
    current = dict(row(ledger))
    prompt_digest = "sha256:" + hashlib.sha256(req.bootstrap_prompt.encode()).hexdigest()
    request_id = UserBrowserGatewayController._request_id(
        "materialize", req.request_id, req.request_digest, prompt_digest, None, 1
    )
    evidence = {
        "schemaVersion": 1,
        "kind": "ordivon.user-browser-owner-native-pre-effect-repair-evidence",
        "effectId": req.request_id,
        "expectedStanding": "unknown",
        "expectedEffectGeneration": 1,
        "requestDigest": req.request_digest,
        "promptDigest": prompt_digest,
        "generation2": {
            "deterministicRequestId": request_id,
            "windowsRuntimeExactClientRequestQueryCount": 0,
        },
        "safeToResendAfterRepairOnly": True,
        "repairConclusion": "exact owner request absent",
        "observedAtMs": 20,
    }
    path = tmp_path / "evidence.json"
    raw = (json.dumps(evidence, sort_keys=True) + "\n").encode()
    path.write_bytes(raw)
    digest = "sha256:" + hashlib.sha256(raw).hexdigest()
    observed = load_and_validate_evidence(
        path, expected_digest=digest, request=req, current_row=current
    )
    assert observed["generation2"]["deterministicRequestId"] == request_id


def test_repair_evidence_rejects_nonzero_owner_query_or_stale_observation(tmp_path: Path):
    req = request()
    ledger = tmp_path / "ledger.sqlite"
    materializer = SQLiteConversationMaterializer(ledger, UnknownTarget())
    materializer.materialize(req, now_ms=10)
    current = dict(row(ledger))
    prompt_digest = "sha256:" + hashlib.sha256(req.bootstrap_prompt.encode()).hexdigest()
    request_id = UserBrowserGatewayController._request_id(
        "materialize", req.request_id, req.request_digest, prompt_digest, None, 1
    )
    evidence = {
        "schemaVersion": 1,
        "kind": "ordivon.user-browser-owner-native-pre-effect-repair-evidence",
        "effectId": req.request_id,
        "expectedStanding": "unknown",
        "expectedEffectGeneration": 1,
        "requestDigest": req.request_digest,
        "promptDigest": prompt_digest,
        "generation2": {
            "deterministicRequestId": request_id,
            "windowsRuntimeExactClientRequestQueryCount": 1,
        },
        "safeToResendAfterRepairOnly": True,
        "repairConclusion": "not absent",
        "observedAtMs": 20,
    }
    path = tmp_path / "bad.json"
    raw = (json.dumps(evidence, sort_keys=True) + "\n").encode(); path.write_bytes(raw)
    digest = "sha256:" + hashlib.sha256(raw).hexdigest()
    with pytest.raises(ValueError, match="does not prove exact Windows Runtime request absence"):
        load_and_validate_evidence(path, expected_digest=digest, request=req, current_row=current)
    evidence["generation2"]["windowsRuntimeExactClientRequestQueryCount"] = 0
    evidence["observedAtMs"] = 9
    raw = (json.dumps(evidence, sort_keys=True) + "\n").encode(); path.write_bytes(raw)
    digest = "sha256:" + hashlib.sha256(raw).hexdigest()
    with pytest.raises(ValueError, match="predates the current ledger version"):
        load_and_validate_evidence(path, expected_digest=digest, request=req, current_row=current)
