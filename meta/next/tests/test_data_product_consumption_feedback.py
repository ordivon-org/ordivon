import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "evidence/data-lifecycle/data-products-r1"


def load(name):
    return json.loads((BASE / name).read_text())


def test_research_post_registration_binding_does_not_claim_generation():
    a = load("acceptance.json")
    r = a["research"]
    assert r["repositoryRevision"] == "18a8afae92ae2ef3b89d645bbcccf6db51db1b9d"
    assert (
        r["consumerBinding"]
        == "PASS_POST_REGISTRATION_OPENLINEAGE_PRODUCT_AND_EXISTING_RESULT_TO_VERIFICATION"
    )
    assert r["openLineageRunId"] == "b07502e6-b0da-58ba-91e8-6e85043f8f31"
    assert r["generationClaim"] == "EXPLICITLY_NOT_CLAIMED"
    assert len(r["verificationArtifactSha256"]) == 64


def test_finance_post_registration_loop_is_bounded_and_no_effect():
    a = load("acceptance.json")
    f = a["finance"]
    assert f["repositoryRevision"] == "14885beb2b566458123dd9f273a66884fb337017"
    assert (
        f["consumerBinding"]
        == "PASS_POST_REGISTRATION_PRODUCT_TO_DECISION_OUTCOME_FEEDBACK_NO_EXTERNAL_EFFECT"
    )
    assert f["openLineageRunId"] == "db63ce70-d168-5dfd-b76f-55419d25bea6"
    assert f["decisionStanding"] == "NO_EXECUTION_OR_DIRECTIONAL_ACTION_ADMITTED"
    assert f["actionStanding"] == "NO_EXTERNAL_EFFECT"
    assert f["outcomeStanding"] == "PASS_BOUNDARY_PRESERVED"
    assert f["feedbackChangeRequired"] is False
    assert (
        a["feedback"]["standing"]
        == "PASS_SELECTED_FINANCE_EXPLICIT_NO_CHANGE_DISPOSITION"
    )
    assert "non-trivial" in a["feedback"]["claimBoundary"]


def test_semantic_and_operational_provenance_are_separate():
    a = load("acceptance.json")
    p = a["semanticProvenance"]
    assert p["standing"] == "PASS_SELECTED_TWO_DOMAIN_OPENLINEAGE_PLUS_PROV"
    assert p["operationalOwner"] == "openlineage-spec"
    assert p["semanticOwner"] == "w3c-prov-o-2013"
    assert p["researchGenerationOverclaimPrevented"] is True


def test_r5_has_no_selected_p0_but_remains_cross_domain_partial():
    r5 = json.loads((ROOT / "planning/data-lifecycle-census-r5.json").read_text())
    assert r5["standing"] == "PARTIAL_CROSS_DOMAIN_LIFECYCLE_R5_SELECTED_P0_CLOSED"
    assert r5["p0Queue"] == []
    by = {x["name"]: x for x in r5["lifecycle"]}
    assert by["provenance-lineage"]["priority"] == "P1"
    assert by["decision-action"]["priority"] == "P1"
    assert (
        by["feedback-recollection"]["standing"]
        == "PASS_SELECTED_FINANCE_NO_CHANGE_DISPOSITION_NONTRIVIAL_UPDATE_UNPROVEN"
    )
    p1 = {x["id"] for x in r5["p1Queue"]}
    assert {
        "nontrivial-feedback-update",
        "business-value-outcome",
        "broader-domain-data-product-adoption",
    } <= p1
