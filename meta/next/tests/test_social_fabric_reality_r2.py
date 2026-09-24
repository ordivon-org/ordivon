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
    "social_fabric_reality_r2", SCRIPTS / "social_fabric_reality_r2.py"
)
mod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(mod)

CUT = ROOT / "evidence/acceptance/social-fabric-reality-r2-owner-cut-20260923.json"
PROV = ROOT / "evidence/data-lifecycle/data-products-r2/product-provenance.prov.jsonld"


def load_cut():
    return json.loads(CUT.read_text(encoding="utf-8"))


def test_prov_adapter_projects_existing_w3c_relations_without_causal_claim():
    document = json.loads(PROV.read_text(encoding="utf-8"))
    result = mod.compile_prov(document, f"file:{PROV.as_posix()}")
    assert result["kind"] == "ordivon.social-fabric-prov-projection"
    assert any(row["provTypes"] == ["prov:Agent"] for row in result["nodes"])
    assert any(row["relation"] == "prov:wasDerivedFrom" for row in result["edges"])
    assert any(row["relation"] == "prov:wasAssociatedWith" for row in result["edges"])
    assert "causal mechanism" in " ".join(result["nonClaims"])


def test_prov_external_target_is_preserved_not_rejected():
    document = {
        "@graph": [
            {
                "@id": "urn:a",
                "@type": "prov:Entity",
                "prov:wasDerivedFrom": {"@id": "urn:external"},
            }
        ]
    }
    result = mod.compile_prov(document, "unit:prov")
    assert result["edges"][0]["target"] == "urn:external"
    assert result["edges"][0]["targetPresentInDocument"] is False


def test_prov_duplicate_identity_fails_closed():
    document = {"@graph": [{"@id": "urn:x"}, {"@id": "urn:x"}]}
    with pytest.raises(mod.RealityProjectionError, match="duplicate PROV node"):
        mod.compile_prov(document, "unit:prov")


def test_transactive_memory_uses_only_explicit_owner_relations():
    result = mod.compile_transactive_memory(load_cut())
    relations = {row["relation"] for row in result["entries"]}
    assert relations == {
        "CONTINUITY_OWNER",
        "EXTERNAL_AUTHORITY_ISSUER",
        "NATURAL_CAPABILITY_OWNER",
    }
    assert not any("expert" in json.dumps(row).lower() for row in result["entries"])
    assert not any(row["relation"] == "EXPLICIT_VERIFIER" for row in result["entries"])


def test_transactive_memory_emits_verifier_only_when_explicitly_bound():
    cut = load_cut()
    cut["verificationBindings"] = [
        {
            "subjectRef": "capability:execution.linux",
            "verifierRef": "verifier:runtime-acceptance",
            "evidenceRefs": ["evidence:runtime-acceptance"],
            "sourceRef": "acceptance:runtime",
        }
    ]
    result = mod.compile_transactive_memory(cut)
    verifier = [
        row for row in result["entries"] if row["relation"] == "EXPLICIT_VERIFIER"
    ]
    assert verifier[0]["principalRef"] == "verifier:runtime-acceptance"


def test_freshness_dogfood_preserves_current_and_historical_versions_for_same_owner():
    result = mod.compile_freshness(load_cut())
    views = {(row["subjectRef"], row["owner"]): row for row in result["ownerViews"]}
    view = views[("authority:network-research-owner", "research-owner:network")]
    assert view["standing"] == "CURRENT_DECLARED"
    assert view["currentVersionRefs"] == [
        "sha256:dbdbb759b2b86b898a343cbb81646b283c589676989e919537f1a6cbc2b1df91"
    ]
    assert view["historicalVersionRefs"] == [
        "sha256:bfadaaaad3b01f9c4388e4e4a75e77c782c2c3111849e5c4598052ec740ee79f"
    ]


def test_two_distinct_current_versions_from_one_owner_conflict():
    cut = load_cut()
    cut["currentnessFacts"].append(
        {
            "subjectRef": "authority:network-research-owner",
            "owner": "research-owner:network",
            "standing": "CURRENT_DECLARED",
            "versionRef": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "sourceRef": "unit:conflicting-current",
        }
    )
    result = mod.compile_freshness(cut)
    view = next(
        row
        for row in result["ownerViews"]
        if row["subjectRef"] == "authority:network-research-owner"
    )
    assert view["standing"] == "CONFLICTED_CURRENT_DECLARATIONS"


def test_authority_catalog_check_is_only_point_in_time():
    result = mod.compile_freshness(load_cut())
    authority_views = [
        row for row in result["ownerViews"] if row["owner"] == "authority-catalog"
    ]
    assert authority_views
    assert all(row["standing"] == "POINT_IN_TIME_OBSERVED" for row in authority_views)


def test_git_recency_does_not_change_owner_currentness_views():
    cut = load_cut()
    baseline = mod.compile_freshness(cut)["ownerViews"]
    with_git = deepcopy(cut)
    with_git["git"] = {
        "mainRevision": "ffffffffffffffffffffffffffffffffffffffff",
        "newerThanOwnerSource": True,
    }
    assert mod.compile_freshness(with_git)["ownerViews"] == baseline


def test_host_open_state_does_not_mint_freshness():
    cut = load_cut()
    result = mod.compile_freshness(cut)
    assert not any(
        row["subjectRef"] == "task:social-fabric-crossdisciplinary-r2-20260923"
        for row in result["ownerViews"]
    )


def test_supersession_is_projected_only_when_explicit():
    cut = load_cut()
    assert mod.compile_freshness(cut)["supersession"] == []
    cut["supersessionFacts"] = [
        {
            "subjectRef": "claim:x",
            "owner": "owner:x",
            "relation": "supersedes",
            "olderRef": "claim:x:v1",
            "newerRef": "claim:x:v2",
            "sourceRef": "owner-evidence:x",
        }
    ]
    assert mod.compile_freshness(cut)["supersession"][0]["olderRef"] == "claim:x:v1"


def test_projections_are_deterministic():
    cut = load_cut()
    assert mod.compile_transactive_memory(cut) == mod.compile_transactive_memory(cut)
    assert mod.compile_freshness(cut) == mod.compile_freshness(cut)
