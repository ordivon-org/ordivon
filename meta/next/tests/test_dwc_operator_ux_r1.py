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
SCRIPT = SCRIPTS / "dwc_operator_ux_r1.py"
SPEC = importlib.util.spec_from_file_location("dwc_operator_ux_r1", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
ux = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ux)
FIXTURE = ROOT / "evidence/acceptance/dwc-operator-ux-r1-reentry-fixture-20261001.json"


def bundle():
    return json.loads(FIXTURE.read_text())


def keys_recursive(value):
    if isinstance(value, dict):
        yield from value.keys()
        for item in value.values():
            yield from keys_recursive(item)
    elif isinstance(value, list):
        for item in value:
            yield from keys_recursive(item)


def test_compact_preserves_five_independent_axes_without_global_green():
    view = ux.compile_view(bundle(), "compact")
    assert list(view["securityStanding"]["axes"]) == list(ux.AXIS_ORDER)
    assert view["securityStanding"]["globalSecurityVerdictIncluded"] is False
    assert view["securityStanding"]["unresolvedAxes"] == [
        "protection",
        "compromise",
        "recovery",
    ]
    assert view["workflowProgress"]["separateFromSecurityStanding"] is True
    assert view["projectionSemantics"]["authorizationDecisionIncluded"] is False


def test_mixed_horizons_remain_explicit():
    view = ux.compile_view(bundle(), "compact")
    assert view["coherentObservationHorizon"] is False
    assert view["observationStanding"] == "MIXED_HORIZONS"
    assert len(view["sourceHorizons"]) > 1


def test_deadline_is_policy_grounded_and_missing_policy_means_no_deadline():
    view = ux.compile_view(bundle(), "compact")
    assert view["policyClock"]["deadlineProjectionStanding"] == "POLICY_GROUNDED"
    assert view["policyClock"]["policyRef"] == "policy:dwc:ssvc-inspired:synthetic-r1"

    changed = copy.deepcopy(bundle())
    changed["policy"] = None
    view = ux.compile_view(changed, "compact")
    assert view["policyClock"] is None
    assert "DEADLINE: not projected" in ux.render_text(view)


def test_policy_source_must_exist_in_owner_source_index():
    changed = copy.deepcopy(bundle())
    changed["policy"]["sourceRef"] = "source:missing"
    with pytest.raises(ux.DwcOperatorUxError, match="unknown sourceRefs"):
        ux.compile_view(changed)


def test_attention_deduplicates_case_subject_update_without_ranking():
    view = ux.compile_view(bundle(), "evidence")
    assert view["attentionSummary"]["inputEventCount"] == 3
    assert view["attentionSummary"]["deduplicatedUpdateGroupCount"] == 2
    assert view["attentionSummary"]["collapsedDuplicateCount"] == 1
    assert view["attentionSummary"]["rankingApplied"] is False
    first = next(
        row
        for row in view["attentionGroups"]
        if row["updateRef"] == "update:authority-needed-r1"
    )
    assert first["inputEventCount"] == 2
    assert first["uniqueVariantCount"] == 1
    assert first["variantStanding"] == "DEDUPLICATED_SINGLE_UPDATE"


def test_attention_same_key_with_conflicting_variant_is_preserved_not_suppressed():
    changed = copy.deepcopy(bundle())
    extra = copy.deepcopy(changed["attentionEvents"][0])
    extra["summary"] = "Independent owner emitted a materially different explanation."
    changed["attentionEvents"].append(extra)
    view = ux.compile_view(changed, "evidence")
    group = next(
        row
        for row in view["attentionGroups"]
        if row["updateRef"] == "update:authority-needed-r1"
    )
    assert group["uniqueVariantCount"] == 2
    assert group["variantStanding"] == "MULTIPLE_VARIANTS"


def test_progressive_disclosure_keeps_same_source_basis():
    views = {
        level: ux.compile_view(bundle(), level)
        for level in ux.DISCLOSURES
    }
    assert len({view["sourceSetDigest"] for view in views.values()}) == 1
    assert "nextSafeActions" not in views["compact"]
    assert "nextSafeActions" in views["plan"]
    assert "sourceIndex" not in views["plan"]
    assert "sourceIndex" in views["evidence"]
    assert "rawArtifactRefs" not in views["evidence"]
    assert "rawArtifactRefs" in views["raw"]


def test_next_safe_actions_are_explicitly_unranked():
    view = ux.compile_view(bundle(), "plan")
    assert view["nextSafeActions"]["orderingSemantics"] == "NONE_UNRANKED"
    assert all("priority" not in row for row in view["nextSafeActions"]["actions"])
    assert view["projectionSemantics"]["schedulerDecisionIncluded"] is False


def test_effect_review_exposes_owner_standing_without_authorizing():
    view = ux.compile_view(bundle(), "plan")
    row = view["effectReviews"][0]
    assert row["authorityStanding"] == "MISSING"
    assert row["authorityBindingRef"] == "authority:synthetic-exchange-mitigation"
    assert row["commitPoint"] == "provider-apply"
    assert row["reversibility"] == "rollback-available"
    assert row["verifierRef"] == "verifier:synthetic-protection-check"
    assert view["effectReviewSummary"]["authorizationDecisionIncluded"] is False


def test_effect_review_requires_full_preapproval_surface():
    changed = copy.deepcopy(bundle())
    del changed["effectReviews"][0]["commitPoint"]
    with pytest.raises(ux.DwcOperatorUxError, match="commitPoint"):
        ux.compile_view(changed, "plan")


def test_text_cli_surface_separates_axes_workflow_and_actions():
    text = ux.render_text(ux.compile_view(bundle(), "plan"))
    assert "SECURITY AXES (independent; no global verdict):" in text
    assert "WORKFLOW (separate):" in text
    assert "NEXT SAFE ACTIONS (unranked):" in text
    assert "EFFECT REVIEW:" in text
    assert "global green" not in text.lower()


def test_invalid_attention_subject_fails_closed():
    changed = copy.deepcopy(bundle())
    changed["attentionEvents"][0]["subjectRef"] = "subject:not-in-case"
    with pytest.raises(ux.DwcOperatorUxError, match="is not in subjectRefs"):
        ux.compile_view(changed)


def test_axes_must_be_exact_and_unknown_remains_explicit():
    changed = copy.deepcopy(bundle())
    del changed["axes"]["compromise"]
    with pytest.raises(ux.DwcOperatorUxError, match="axes must be exactly"):
        ux.compile_view(changed)

    changed = copy.deepcopy(bundle())
    changed["axes"]["compromise"]["state"] = "UNKNOWN"
    changed["axes"]["compromise"]["closureStanding"] = "UNKNOWN"
    view = ux.compile_view(changed)
    assert view["securityStanding"]["axes"]["compromise"] == {
        "state": "UNKNOWN",
        "closureStanding": "UNKNOWN",
    }
