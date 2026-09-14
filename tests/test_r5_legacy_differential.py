from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from market_capital.semantic import (
    EffectDisposition,
    ProofObject,
    SemanticViolation,
    classify_effect_disposition,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "fixtures" / "r5_legacy_bounded"


def _load(path: Path) -> dict:
    value = json.loads(path.read_text())
    assert isinstance(value, dict)
    return value


def test_frozen_legacy_fixture_digests_are_exact() -> None:
    manifest = _load(FIXTURE_ROOT / "manifest.json")
    for entry in manifest["fixtures"]:
        path = FIXTURE_ROOT / entry["path"]
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual == entry["sha256"]
    assert manifest["legacyCodeImported"] is False


def test_r26_registry_parcel_outcome_survives_without_legacy_mechanism() -> None:
    evidence = _load(FIXTURE_ROOT / "market-capital-r26-p01-registry-parcel-authority-20260908.json")
    contract = evidence["authorityContract"]
    assert contract["callerMaySupplyParcelTuple"] is False
    assert contract["callerMaySupplyCanonicalParcelResourceRef"] is False
    assert contract["callerMayMintAllocationUniquenessPass"] is False
    assert contract["legalOwnershipCreated"] is False
    assert contract["deploymentAuthorityCreated"] is False
    assert contract["externalEffectAuthorityCreated"] is False

    semantic = _load(ROOT / "contracts" / "semantic-core-v1.json")
    assert "registry_parcel_scarcity_identity" in semantic["ownedSemantics"]
    assert semantic["externalFinancialWriteAdmission"] == "NOT_ADMITTED"


def test_r27_effect_disposition_outcomes_replay_exactly() -> None:
    evidence = _load(FIXTURE_ROOT / "market-capital-r27-p21-effect-reconciliation-final-20260908.json")
    contract = evidence["contract"]

    for standing in contract["release"]:
        assert classify_effect_disposition(standing) is EffectDisposition.RELEASE
    for standing in ("UNKNOWN", "AMBIGUOUS", "PARTIAL_OPEN", "CONTRADICTORY"):
        assert standing in contract["retainHold"]
        assert classify_effect_disposition(standing) is EffectDisposition.RETAIN
    assert classify_effect_disposition("POSITIVE_EXECUTION") is EffectDisposition.CONSUME
    assert evidence["externalFinancialWriteAttempted"] is False


def test_r28_currentness_and_terminal_fail_closed_outcome_survives() -> None:
    evidence = _load(FIXTURE_ROOT / "market-capital-r28-p31-effect-authority-v2-final-20260908.json")
    assert evidence["boundedStanding"]["institutionalProduction"] == "NOT_GRANTED"
    assert evidence["externalFinancialWriteAttempted"] is False

    digest = "sha256:" + "a" * 64
    current = ProofObject(
        issuer="issuer:test",
        subject="subject:test",
        resource_identity="resource:test",
        generation="1",
        source_cut="cut:test",
        digest=digest,
        current=True,
    )
    current.validate_current()

    for kwargs, message in (
        ({"revoked": True}, "revoked proof is terminal"),
        ({"superseded": True}, "superseded proof is not current authority"),
        ({"current": False}, "proof is not current"),
    ):
        values = {
            "issuer": current.issuer,
            "subject": current.subject,
            "resource_identity": current.resource_identity,
            "generation": current.generation,
            "source_cut": current.source_cut,
            "digest": current.digest,
            "current": current.current,
            "superseded": current.superseded,
            "revoked": current.revoked,
        }
        values.update(kwargs)
        with pytest.raises(SemanticViolation, match=message):
            ProofObject(**values).validate_current()
