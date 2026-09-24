from __future__ import annotations

import copy
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from scripts.social_fabric_commitment_r3 import (
    compile_commitment_projection,
    validate_policy,
)
from scripts.social_fabric_r1 import SocialFabricError

ROOT = Path(__file__).resolve().parents[1]
REGO = ROOT / "policies/social-fabric-commitment-r3/policy.rego"
POLICY_DIR = ROOT / "policies/social-fabric-commitment-r3"
PROFILE = POLICY_DIR / "profile.json"
SINGLE = (
    ROOT / "evidence/acceptance/social-fabric-commitment-r3-single-cut-20260923.json"
)
VHD = ROOT / "evidence/acceptance/social-fabric-coordination-r2-vhd-cut-20260923.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _compile(cut: dict, policy: dict | None = None) -> dict:
    return compile_commitment_projection(
        cut,
        policy or _load(PROFILE),
        rego_path=REGO,
    )


def test_native_opa_policy_suite_passes() -> None:
    opa = shutil.which("opa")
    assert opa is not None
    result = subprocess.run(
        [opa, "test", str(POLICY_DIR), "-v"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_single_explicitly_satisfied_candidate_is_ready_shadow_only() -> None:
    result = _compile(_load(SINGLE))
    commitment = result["commitmentProjection"]
    assert commitment["state"] == "READY_SHADOW"
    assert commitment["soleSatisfiedCandidateEventId"] == "candidate:maintenance:single"
    assert commitment["effectAuthorityGranted"] is False
    assert commitment["externalEffectPerformed"] is False
    assert commitment["requiresOwnerBinding"] is True
    assert result["candidateDecisions"][0]["unmet"] == []


def test_missing_required_role_is_explained_and_not_ready() -> None:
    cut = _load(SINGLE)
    cut["events"] = [
        event for event in cut["events"] if event["id"] != "support:maintenance:storage"
    ]
    result = _compile(cut)
    assert result["commitmentProjection"]["state"] == "NOT_READY"
    assert {
        (row["code"], row["value"]) for row in result["candidateDecisions"][0]["unmet"]
    } == {("MISSING_SUPPORT_ROLE", "storage")}


def test_duplicate_support_for_same_role_cannot_substitute_for_missing_role() -> None:
    cut = _load(SINGLE)
    storage = next(
        event for event in cut["events"] if event["id"] == "support:maintenance:storage"
    )
    storage["data"]["role"] = "operations"
    result = _compile(cut)
    assert result["commitmentProjection"]["state"] == "NOT_READY"
    assert ("MISSING_SUPPORT_ROLE", "storage") in {
        (row["code"], row["value"]) for row in result["candidateDecisions"][0]["unmet"]
    }


def test_explicit_blocking_damage_is_policy_visible_without_scoring() -> None:
    cut = _load(SINGLE)
    cut["events"].append(
        {
            "specversion": "1.0",
            "id": "damage:filesystem-unsafe",
            "source": "urn:ordivon:storage",
            "type": "io.ordivon.social.damage.v1",
            "subject": "resource:windows:maintenance:example",
            "time": "2026-09-23T15:24:00+08:00",
            "datacontenttype": "application/json",
            "ordivonscope": "system",
            "expirytime": "2026-09-23T16:00:00+08:00",
            "data": {
                "reasonCode": "FILESYSTEM_UNSAFE",
                "evidenceRefs": ["evidence:filesystem-unsafe"],
            },
        }
    )
    result = _compile(cut)
    assert result["commitmentProjection"]["state"] == "NOT_READY"
    assert ("BLOCKED_DAMAGE_REASON", "FILESYSTEM_UNSAFE") in {
        (row["code"], row["value"]) for row in result["candidateDecisions"][0]["unmet"]
    }


def test_real_vhd_conflict_never_becomes_commitment() -> None:
    result = _compile(_load(VHD))
    assert result["commitmentProjection"]["state"] == "NOT_READY"
    assert result["commitmentProjection"]["policySatisfiedCandidateIds"] == []
    assert len(result["candidateDecisions"]) == 3
    assert all(not row["satisfied"] for row in result["candidateDecisions"])
    assert all(
        any(item["code"] == "CANDIDATE_NOT_ELIGIBLE_SHADOW" for item in row["unmet"])
        for row in result["candidateDecisions"]
    )


def test_multiple_satisfied_shared_candidates_are_ambiguous_not_ranked() -> None:
    cut = _load(SINGLE)
    first = next(
        event
        for event in cut["events"]
        if event["id"] == "candidate:maintenance:single"
    )
    first["data"]["mode"] = "shared"
    second = copy.deepcopy(first)
    second["id"] = "candidate:maintenance:second"
    second["data"]["holderRef"] = "job:example-maintenance-2"
    second["data"]["evidenceRefs"] = ["job:example-maintenance-2"]
    cut["events"].append(second)

    base_support = [
        event
        for event in cut["events"]
        if event["type"] == "io.ordivon.social.support.v1"
    ]
    for support in base_support:
        duplicate = copy.deepcopy(support)
        duplicate["id"] = support["id"] + ":second"
        duplicate["data"]["candidateEventId"] = second["id"]
        duplicate["data"]["evidenceRefs"] = [
            duplicate["data"]["evidenceRefs"][0] + ":second"
        ]
        cut["events"].append(duplicate)

    result = _compile(cut)
    commitment = result["commitmentProjection"]
    assert commitment["state"] == "AMBIGUOUS_MULTIPLE_READY"
    assert commitment["policySatisfiedCandidateIds"] == [
        "candidate:maintenance:second",
        "candidate:maintenance:single",
    ]
    assert "soleSatisfiedCandidateEventId" not in commitment
    assert all(row["satisfied"] for row in result["candidateDecisions"])


def test_policy_schema_rejects_hidden_numeric_quorum_knobs() -> None:
    policy = _load(PROFILE)
    policy["minSupportCount"] = 2
    with pytest.raises(SocialFabricError, match="fields mismatch"):
        validate_policy(policy)


def test_policy_and_projection_are_deterministic() -> None:
    cut = _load(SINGLE)
    policy = _load(PROFILE)
    first = _compile(cut, policy)
    second = _compile(copy.deepcopy(cut), copy.deepcopy(policy))
    assert first == second
    assert first["projectionDigest"].startswith("sha256:")
