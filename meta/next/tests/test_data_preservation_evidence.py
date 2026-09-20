from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRES = ROOT / "evidence/data-lifecycle/preservation-r1"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_exact_preservation_falsifier_is_retained() -> None:
    a = load(PRES / "acceptance.json")
    f = a["falsifier"]
    assert f["standing"] == "REJECTED_FOR_EXACT_PRESERVATION_CLAIM"
    assert f["sourceFileChecks"]["expected"] == 49
    assert f["sourceFileChecks"]["exact"] == 47
    assert sorted(f["sourceFileChecks"]["missing"]) == [
        "evidence/github-pilot-r1/.gitignore",
        "evidence/temporal-evolution-r1/.gitignore",
    ]


def test_accepted_preservation_is_exact_and_replicated() -> None:
    a = load(PRES / "acceptance.json")
    ok = a["accepted"]
    assert a["standing"] == "PASS_WITH_LOCAL_FAILURE_DOMAIN_BOUNDARY"
    assert ok["standing"] == "PASS_LOCAL_DURABLE_PRESERVATION"
    assert ok["payloadExactFiles"] == {
        "expected": 49,
        "verified": 49,
        "standing": "PASS",
    }
    assert ok["masterReplicaByteEqual"] is True
    assert ok["aipSha256"] == "43cd27dc86634fa64be4b56cf0d4720e81c7ee73c214be588cf6ce54eb2dfc15"
    assert ok["metsXml"] == "PASS"
    assert ok["premisNamespace"] == "PASS"
    assert ok["aipBagItValidation"] == "PASS"
    assert ok["fixity"]["masterPassed"] is True
    assert ok["fixity"]["replicaPassed"] is True


def test_preservation_does_not_overclaim_failure_domains() -> None:
    a = load(PRES / "acceptance.json")
    boundary = a["operationalBoundary"]
    assert boundary["independentFailureDomain"] is False
    assert "same machine/WSL failure domain" in boundary["note"]


def test_bagit_adapter_does_not_claim_rfc8493() -> None:
    a = load(PRES / "acceptance.json")
    adapter = a["submission"]["archivematicaAdapter"]
    assert adapter["bagItVersion"] == "0.97"
    assert adapter["standing"] == "PROVIDER_ADAPTER_ONLY_NOT_RFC8493_CONFORMANCE"
    canonical = a["submission"]["canonicalInterchange"]
    assert canonical["format"] == "E-ARK SIP / CSIP"
    assert canonical["version"] == "2.2.0"
    assert canonical["validation"]["failedMust"] == 0


def test_ndsa_projection_is_gap_based_not_a_score() -> None:
    d = load(PRES / "ndsa-2.1-assessment.json")
    assert "No aggregate level is claimed" in d["scoringPolicy"]
    assert d["dimensions"]["storage"]["standing"] == "PARTIAL"
    assert d["dimensions"]["integrity"]["standing"] == "STRONG_LOCAL"
    assert d["dimensions"]["sustainability"]["standing"] == "NOT_ASSESSED"


def test_census_r2_promotes_preservation_but_keeps_cross_domain_p0s() -> None:
    d = load(ROOT / "planning/data-lifecycle-census-r2.json")
    by_name = {x["name"]: x for x in d["lifecycle"]}
    assert by_name["raw-preservation"]["standing"] == "PASS_LOCAL_DURABLE_PRESERVATION"
    assert by_name["raw-preservation"]["priority"] == "P1"
    assert by_name["metadata-catalog"]["priority"] == "P0"
    assert by_name["provenance-lineage"]["priority"] == "P0"
    assert by_name["data-contract-product"]["standing"] == "ODCS_PILOT_PROVEN_ODPS_MISSING"
    assert by_name["feedback-recollection"]["standing"] == "MISSING"

    p0 = {x["id"] for x in d["p0Queue"]}
    assert p0 == {
        "catalog-products",
        "domain-adoption",
        "semantic-provenance",
        "rights-privacy-retention",
        "decision-outcome-feedback",
    }


def test_heavy_substrates_stay_workload_gated() -> None:
    d = load(ROOT / "planning/data-lifecycle-census-r2.json")
    gated = set(d["workloadGated"])
    assert {"Apache Iceberg", "Debezium", "Kafka/Redpanda", "Dagster", "OCFL"} <= gated


def test_data_capability_standing_is_split() -> None:
    text = (ROOT / "capabilities/packages/data-analytics.md").read_text(encoding="utf-8")
    assert "Project-scoped data work: **READY_FOR_REAL_WORK**" in text
    assert "Cross-domain data lifecycle: **PARTIAL**" in text
    assert "CrossDomainDataLifecycle = PARTIAL" in text
