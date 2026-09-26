from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FOUNDRY = ROOT / "catalogs" / "knowledge" / "model-foundry"


def load(name: str):
    return json.loads((FOUNDRY / name).read_text(encoding="utf-8"))


def test_model_foundry_catalog_keeps_cognition_and_authority_separate() -> None:
    catalog = load("model-foundry-r2.json")
    operators = set(catalog["operators"])
    non_model = set(catalog["nonModelAuthorities"])

    assert "DECIDE" in operators
    assert "VERIFY" in operators
    assert {"AUTHORIZE", "EXECUTE", "WITNESS", "COMMIT"} <= non_model
    assert operators.isdisjoint(non_model)
    assert "provider_diversity_does_not_establish_failure_diversity" in catalog["hardLaws"]
    assert "benchmark_score_does_not_transfer_outside_its_measurement_boundary" in catalog["hardLaws"]


def test_decision_provider_catalog_is_discovery_not_ranking() -> None:
    catalog = load("decision-provider-catalog-r2.json")
    assert catalog["truthRole"] == "discovery_and_evidence_mapping_only"
    providers = catalog["providers"]
    assert len(providers) >= 5
    assert all(p["operator"] == "DECIDE" for p in providers)
    assert not any("rank" in p or "score" in p for p in providers)
    assert any(p["providerId"] == "deterministic.rule" for p in providers)


def test_benchmark_observations_forbid_global_winner_collapse() -> None:
    observations = load("benchmark-observations-r2.json")
    assert observations["truthRole"] == "external_reported_observations_not_global_ranking"
    assert "BEST_PROVIDER" in observations["admissionRule"]
    ids = {item["observationId"] for item in observations["observations"]}
    assert "sysone-bench-triage-laya-vs-jev" in ids
    assert "sysone-bench-agnews-laya-vs-jev" in ids
    assert "anyjev-qwen3-8b-banking77-calibration-ablation" in ids


def test_schema_documents_are_draft_2020_12_and_non_authoritative() -> None:
    schemas = [
        FOUNDRY / "schemas" / "cognitive-operator-v1.schema.json",
        FOUNDRY / "schemas" / "qualification-envelope-v1.schema.json",
    ]
    for path in schemas:
        value = json.loads(path.read_text(encoding="utf-8"))
        assert value["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert value["type"] == "object"
        assert value["additionalProperties"] is False

    operator_schema = json.loads(schemas[0].read_text(encoding="utf-8"))
    authority_values = operator_schema["properties"]["authorityClass"]["enum"]
    assert "ADVISORY" in authority_values
    assert "EVIDENCE_PRODUCING" in authority_values
    assert "AUTHORIZED_EFFECT" not in authority_values
