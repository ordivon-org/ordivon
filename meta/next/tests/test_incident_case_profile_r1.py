import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(rel: str):
    return json.loads((ROOT / rel).read_text())


def dogfood_case(case_id: str):
    analysis = load("evidence/analysis/incident-case-profile-r1-dogfood-20260923.json")
    return next(case for case in analysis["cases"] if case["id"] == case_id)


def test_incident_profile_preserves_owner_boundaries():
    profile = load("planning/incident-case-profile-r1.json")
    assert profile["standing"] == "EXTRACTED_PROFILE_NO_INCIDENT_SERVICE"
    laws = set(profile["separationLaws"])
    assert "damage signal != incident admission" in laws
    assert "detection != containment authority" in laws
    assert "execution receipt != consequence truth" in laws
    assert "hypothesis != root cause" in laws
    assert "global incident registry" in profile["doNotOwn"]
    assert "EffectAuthority" in profile["doNotOwn"]


def test_vhd_damage_signal_is_evidence_bound_but_non_authoritative():
    cut = load(
        "evidence/acceptance/social-fabric-coordination-r2-vhd-cut-20260923.json"
    )
    damage = next(
        e for e in cut["events"] if e["id"] == "damage:diskpart-rpc-unavailable"
    )
    assert damage["type"] == "io.ordivon.social.damage.v1"
    assert len(damage["data"]["evidenceRefs"]) == 2
    assert any("not a live owner lease" in x for x in cut["nonClaims"])


def test_runtime_recovery_projection_preserves_reconcile_without_redispatch_claims():
    recovery = dogfood_case("windows-native-recovery")
    observed = recovery["observed"]
    assert observed["finalAcceptance"] == "passed"
    assert observed["exactReplayNeverRedispatchesInterruptedEffect"] is True
    assert observed["runtimeCoreReconstructionReattachesWithoutRedispatch"] is True
    assert observed["wslRestartRecoveryUsesSameJobAttempt"] is True
    assert observed["reservationReleased"] is True
    assert (
        "Runtime recovery does not establish domain semantic closure."
        in recovery["nonClaims"]
    )


def test_harness_incident_projection_keeps_hypotheses_and_unknowns_explicit():
    incident = dogfood_case("browserless-engineering-incident")
    observed = incident["observed"]
    standings = set(observed["hypothesisStandings"])
    assert {"FALSIFIED", "SUPPORTED", "UNRESOLVED"} <= standings
    assert observed["explicitUnknownCount"] >= 1
    assert observed["serviceBlocked"] is True
    assert (
        "Provider-authoritative root cause remains unresolved." in incident["nonClaims"]
    )


def test_profile_dogfood_has_four_distinct_owner_pressures():
    analysis = load("evidence/analysis/incident-case-profile-r1-dogfood-20260923.json")
    assert analysis["extractionDecision"] == "EXTRACT_PROFILE_ONLY"
    assert len(analysis["cases"]) == 4
    acceptance = load(
        "evidence/acceptance/incident-case-profile-r1-acceptance-20260923.json"
    )
    assert acceptance["pressure"]["materiallyDifferentOwnerClasses"] == 4
    assert acceptance["standing"] == "PASS_PROFILE_EXTRACTION_NO_INCIDENT_SERVICE"
