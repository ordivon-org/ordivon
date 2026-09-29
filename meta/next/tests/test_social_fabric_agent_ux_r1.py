from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
SCRIPT = SCRIPTS / "social_fabric_agent_ux_r1.py"
SPEC = importlib.util.spec_from_file_location("social_fabric_agent_ux_r1", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
ux = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ux)
MANIFEST = ROOT / "evidence/acceptance/social-fabric-agent-ux-r1-manifest-20260923.json"


def bundle():
    return ux.load_manifest(MANIFEST)


def keys_recursive(value):
    if isinstance(value, dict):
        yield from value.keys()
        for item in value.values():
            yield from keys_recursive(item)
    elif isinstance(value, list):
        for item in value:
            yield from keys_recursive(item)


def test_four_compact_views_share_exact_source_basis_without_authority():
    b = bundle()
    views = {name: ux.compile_view(b, name) for name in ux.VIEW_KINDS}
    assert {v["view"] for v in views.values()} == {
        "CURRENT",
        "ATTENTION",
        "COORDINATION",
        "AUTHORITY",
    }
    assert len({v["sourceSetDigest"] for v in views.values()}) == 1
    assert all(
        v["truthRole"] == "agent-facing-projection-only-no-owner-authority"
        for v in views.values()
    )
    forbidden = ux.FORBIDDEN_CONTROL_FIELDS
    assert not (forbidden & set(k for v in views.values() for k in keys_recursive(v)))


def test_compact_and_detail_preserve_source_basis_but_not_same_view_digest():
    b = bundle()
    compact = ux.compile_view(b, "authority")
    detail = ux.compile_view(b, "authority", detail=True)
    assert compact["sourceSetDigest"] == detail["sourceSetDigest"]
    assert compact["viewDigest"] != detail["viewDigest"]
    assert "evidenceRefs" not in compact["summary"]["bindings"][0]
    assert detail["detail"]["ownerAndVerifierLocators"][0]["evidenceRefs"]


def test_current_preserves_mixed_horizons_and_unknown_currentness():
    b = bundle()
    b = copy.deepcopy(b)
    b["inputs"]["freshness"]["ownerViews"][0]["standing"] = "CURRENTNESS_UNKNOWN"
    view = ux.compile_view(b, "current", detail=True)
    assert view["coherentObservationHorizon"] is False
    assert view["summary"]["freshnessStandingCounts"]["CURRENTNESS_UNKNOWN"] >= 1
    assert any(
        row["standing"] == "CURRENTNESS_UNKNOWN"
        for row in view["detail"]["freshnessOwnerViews"]
    )


def test_attention_is_source_grouped_and_preserves_host_exact_reentry():
    view = ux.compile_view(bundle(), "attention", detail=True)
    assert view["summary"]["grouping"] == "source-preserving-unranked"
    task = next(
        row
        for row in view["detail"]["hostRoutedTasks"]
        if row["taskId"].startswith("task:social-fabric")
    )
    assert task["reentry"]["requiredBeforeActing"] is True
    assert task["reentry"]["operation"] == "task.resume"
    assert task["reentry"]["expectedRevision"] == 5


def test_coordination_compartment_filter_is_presentation_only():
    b = bundle()
    full = ux.compile_view(b, "coordination", detail=True)
    filtered = ux.compile_view(
        b,
        "coordination",
        detail=True,
        compartment_prefixes=("resource:windows:drive:D",),
    )
    assert full["summary"]["candidateRefs"] == filtered["summary"]["candidateRefs"]
    assert (
        filtered["summary"]["visibleSignalCount"]
        < full["summary"]["visibleSignalCount"]
    )
    assert filtered["visibility"]["presentationFilterOnly"] is True
    assert filtered["visibility"]["authorizationEffect"] is False
    assert filtered["visibility"]["aclEffect"] is False


def test_authority_is_locator_not_authorization():
    view = ux.compile_view(bundle(), "authority", detail=True)
    assert view["summary"]["authorizationDecisionIncluded"] is False
    assert view["summary"]["requiresOwnerBinding"] is True
    assert view["summary"]["candidateEffectOwnerRefs"]
    assert all(
        "evidenceRefs" in row and "sourceRef" in row
        for row in view["detail"]["ownerAndVerifierLocators"]
    )


def test_bundle_rejects_wrong_projection_kind():
    b = bundle()
    b = copy.deepcopy(b)
    b["inputs"]["memory"]["kind"] = "ordivon.fake"
    with pytest.raises(ux.AgentUxProjectionError, match="inputs.memory.kind"):
        ux.compile_view(b, "authority")


def test_bundle_rejects_authority_grant_in_commitment_source():
    b = bundle()
    b = copy.deepcopy(b)
    b["inputs"]["commitment"]["commitmentProjection"]["effectAuthorityGranted"] = True
    with pytest.raises(ux.AgentUxProjectionError, match="must not grant authority"):
        ux.compile_view(b, "current")


def test_manifest_rejects_path_escape(tmp_path: Path):
    manifest = json.loads(MANIFEST.read_text())
    manifest["inputs"]["current"] = "../escape.json"
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest))
    with pytest.raises(ux.AgentUxProjectionError, match="local relative path"):
        ux.load_manifest(path)


def test_forbidden_control_fields_fail_closed_even_if_nested():
    b = bundle()
    b = copy.deepcopy(b)
    b["inputs"]["hostAttention"]["routedTasks"][0]["priority"] = 1
    with pytest.raises(ux.AgentUxProjectionError, match="forbidden control fields"):
        ux.compile_view(b, "attention", detail=True)


def test_preflight_recommends_all_four_views_for_explicit_vhd_maintenance_traits():
    request = json.loads(
        (
            ROOT
            / "evidence/acceptance/social-fabric-agent-ux-r1-preflight-vhd-20260923.json"
        ).read_text()
    )
    advice = ux.compile_preflight(request)
    assert advice["standing"] == "SOCIAL_READ_RECOMMENDED"
    assert advice["recommendedViews"] == [
        "CURRENT",
        "ATTENTION",
        "COORDINATION",
        "AUTHORITY",
    ]
    assert advice["effectAuthorizationIncluded"] is False
    assert advice["executionAdmissionIncluded"] is False
    assert not (ux.FORBIDDEN_CONTROL_FIELDS & set(keys_recursive(advice)))


def test_preflight_is_optional_for_explicitly_local_cheap_read():
    request = json.loads(
        (
            ROOT
            / "evidence/acceptance/social-fabric-agent-ux-r1-preflight-cheap-read-20260923.json"
        ).read_text()
    )
    advice = ux.compile_preflight(request)
    assert advice["standing"] == "SOCIAL_READ_OPTIONAL"
    assert advice["recommendedViews"] == []


def test_preflight_fails_closed_on_implicit_or_nonboolean_traits():
    request = {
        "schemaVersion": 1,
        "kind": ux.PREFLIGHT_KIND,
        "operationRef": "op:x",
        "traits": {"durable": True},
    }
    with pytest.raises(ux.AgentUxProjectionError, match="traits must be exactly"):
        ux.compile_preflight(request)
    request["traits"] = {
        "durable": True,
        "shared": False,
        "effectful": "yes",
        "scarce": False,
    }
    with pytest.raises(ux.AgentUxProjectionError, match="effectful must be boolean"):
        ux.compile_preflight(request)


def test_preflight_recommended_read_requires_explicit_subject():
    request = {
        "schemaVersion": 1,
        "kind": ux.PREFLIGHT_KIND,
        "operationRef": "op:x",
        "traits": {
            "durable": False,
            "shared": True,
            "effectful": False,
            "scarce": False,
        },
        "subjectRefs": [],
        "compartmentRefs": [],
    }
    with pytest.raises(
        ux.AgentUxProjectionError, match="requires at least one explicit subjectRef"
    ):
        ux.compile_preflight(request)
