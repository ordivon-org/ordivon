from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from scripts.evaluation_boundary_r1 import (
    EvaluationBoundaryError,
    compile_profile,
    validate_binding,
    validate_profile,
)

NEXT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = NEXT_ROOT.parents[1]
BINDING = NEXT_ROOT / "evidence/acceptance/evaluation-boundary-rw6-bindings.json"


def _binding() -> dict:
    return json.loads(BINDING.read_text(encoding="utf-8"))


def test_binding_and_profile_validate_with_two_natural_donors() -> None:
    binding = _binding()
    validate_binding(binding)
    profile = compile_profile(REPO_ROOT, binding)
    validate_profile(profile)

    assert profile["closure"] == {
        "distinctOwnerCount": 2,
        "executedDonorPresent": True,
        "mechanicalClosure": True,
        "empiricalClosure": False,
    }
    assert {donor["standing"] for donor in profile["donors"]} == {
        "EXECUTED",
        "FROZEN_PROTOCOL_ONLY",
    }


def test_common_boundary_laws_do_not_create_evaluator_authority() -> None:
    profile = compile_profile(REPO_ROOT, _binding())
    assert profile["laws"]["freezePrecedesHoldoutExposure"] is True
    assert profile["laws"]["postExposureMutationPreservesStanding"] is False
    assert profile["laws"]["thresholdRetuningAfterUnblindingAllowed"] is False
    assert profile["laws"]["holdoutEvidenceSeparateFromDevelopmentEvidence"] is True
    assert profile["laws"]["evaluatorSemanticsRemainOwnerNative"] is True
    assert any("universal evaluator" in item for item in profile["nonClaims"])


def test_source_digest_drift_fails_closed() -> None:
    binding = _binding()
    binding["donors"][0]["sources"][0]["sha256"] = "sha256:" + "0" * 64
    with pytest.raises(EvaluationBoundaryError, match="source digest mismatch"):
        compile_profile(REPO_ROOT, binding)


def test_owner_native_assertion_drift_fails_closed() -> None:
    binding = _binding()
    game = binding["donors"][1]["sources"][0]
    for assertion in game["jsonAssertions"]:
        if assertion["pointer"] == "/state/protocolFrozen":
            assertion["expected"] = False
            break
    with pytest.raises(EvaluationBoundaryError, match="JSON assertion failed"):
        compile_profile(REPO_ROOT, binding)


def test_one_owner_cannot_establish_cross_owner_profile() -> None:
    binding = _binding()
    binding["donors"][1]["ownerId"] = binding["donors"][0]["ownerId"]
    with pytest.raises(EvaluationBoundaryError, match="two distinct natural owners"):
        compile_profile(REPO_ROOT, binding)


def test_protocol_only_donors_cannot_claim_executed_evidence() -> None:
    binding = copy.deepcopy(_binding())
    for donor in binding["donors"]:
        donor["standing"] = "FROZEN_PROTOCOL_ONLY"
    with pytest.raises(EvaluationBoundaryError, match="one executed donor"):
        compile_profile(REPO_ROOT, binding)
