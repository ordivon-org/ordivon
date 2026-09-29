from __future__ import annotations

import importlib.util
import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location(
    "social_fabric_epistemic_r1", SCRIPTS / "social_fabric_epistemic_r1.py"
)
mod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(mod)
CUT = ROOT / "evidence/acceptance/social-fabric-epistemic-r1-cut-20260923.json"
SINGLE = (
    ROOT
    / "evidence/acceptance/social-fabric-commitment-r3-single-projection-20260923.json"
)
VHD = (
    ROOT
    / "evidence/acceptance/social-fabric-commitment-r3-vhd-projection-20260923.json"
)


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_epistemic_dogfood_preserves_three_distinct_standings():
    result = mod.compile_epistemic(load(CUT))
    standings = {row["claimRef"]: row["standing"] for row in result["claims"]}
    assert standings == {
        "claim:browser-window-placement-local-mechanism": "MECHANISM_EVIDENCE_SUPPORTED",
        "claim:vhd-rpc-mechanism-hypothesis": "MECHANISM_HYPOTHESIS",
        "claim:vhd-sequence": "SEQUENCE_OBSERVED",
    }


def test_sequence_requires_multiple_sequence_refs_and_evidence():
    cut = load(CUT)
    row = next(x for x in cut["claims"] if x["standing"] == "SEQUENCE_OBSERVED")
    row["sequenceRefs"] = ["only:one"]
    with pytest.raises(
        mod.EpistemicProjectionError, match="SEQUENCE_OBSERVED requires"
    ):
        mod.compile_epistemic(cut)


def test_temporal_sequence_cannot_be_upgraded_to_supported_mechanism_without_verifier():
    cut = load(CUT)
    row = next(x for x in cut["claims"] if x["claimRef"] == "claim:vhd-sequence")
    row["standing"] = "MECHANISM_EVIDENCE_SUPPORTED"
    row.pop("observationOwnerRef")
    with pytest.raises(mod.EpistemicProjectionError, match="verificationOwnerRef"):
        mod.compile_epistemic(cut)


def test_supported_mechanism_requires_evidence_and_owner_native_standing():
    cut = load(CUT)
    row = next(
        x for x in cut["claims"] if x["standing"] == "MECHANISM_EVIDENCE_SUPPORTED"
    )
    row["evidenceRefs"] = []
    with pytest.raises(mod.EpistemicProjectionError, match="requires evidenceRefs"):
        mod.compile_epistemic(cut)


def test_local_mechanism_preserves_residual_open_claims():
    result = mod.compile_epistemic(load(CUT))
    row = next(
        x for x in result["claims"] if x["standing"] == "MECHANISM_EVIDENCE_SUPPORTED"
    )
    assert "protected-provider challenge causality" in row["residualOpenClaims"]
    assert row["mechanismAuthorityTransferred"] is False


def test_feasibility_single_ready_is_boolean_not_score():
    result = mod.compile_feasibility(load(SINGLE))
    assert result["feasibleCandidateIds"] == ["candidate:maintenance:single"]
    assert result["candidates"][0]["standing"] == "FEASIBLE_SHADOW"
    raw = json.dumps(result)
    assert '"score"' not in raw and '"rank"' not in raw and '"priority"' not in raw
    assert result["winnerSelected"] is False


def test_vhd_infeasible_candidates_preserve_constraints():
    result = mod.compile_feasibility(load(VHD))
    assert result["feasibleCandidateIds"] == []
    assert all(row["standing"] == "INFEASIBLE_SHADOW" for row in result["candidates"])
    assert all(row["unmetConstraints"] for row in result["candidates"])


def test_multiple_feasible_candidates_never_select_winner():
    source = load(SINGLE)
    second = deepcopy(source["candidateDecisions"][0])
    second["candidateEventId"] = "candidate:maintenance:second"
    second["subject"] = "resource:windows:maintenance:second"
    source["candidateDecisions"].append(second)
    result = mod.compile_feasibility(source)
    assert len(result["feasibleCandidateIds"]) == 2
    assert result["winnerSelected"] is False


def test_numeric_or_ranking_semantics_fail_closed():
    for field in (
        "score",
        "rank",
        "weight",
        "voteCount",
        "priority",
        "chemicalPotential",
        "socialPressure",
    ):
        source = load(SINGLE)
        source["candidateDecisions"][0][field] = 1
        with pytest.raises(
            mod.EpistemicProjectionError, match="numeric/ranking semantics forbidden"
        ):
            mod.compile_feasibility(source)


def test_inconsistent_policy_decision_fails_closed():
    source = load(SINGLE)
    source["candidateDecisions"][0]["unmet"] = [{"code": "X", "value": "Y"}]
    with pytest.raises(mod.EpistemicProjectionError, match="satisfied=true with unmet"):
        mod.compile_feasibility(source)


def test_feasibility_requires_no_effect_authority():
    source = load(SINGLE)
    source["commitmentProjection"]["effectAuthorityGranted"] = True
    with pytest.raises(
        mod.EpistemicProjectionError, match="must not grant EffectAuthority"
    ):
        mod.compile_feasibility(source)


def test_deterministic_projections():
    cut = load(CUT)
    assert mod.compile_epistemic(cut) == mod.compile_epistemic(deepcopy(cut))
    commitment = load(SINGLE)
    assert mod.compile_feasibility(commitment) == mod.compile_feasibility(
        deepcopy(commitment)
    )
