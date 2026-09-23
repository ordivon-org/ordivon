from __future__ import annotations

import json
from pathlib import Path

import pytest

from ordivon_capital.governance.composition_contract import (
    CompositionContractError,
    compile_composition,
)

ROOT = Path(__file__).resolve().parents[1]


def load(rel: str):
    return json.loads((ROOT / rel).read_text())


def test_contract_catalogs_cover_registry_authority_effect_and_role_enums():
    registry = load("config/capital_lego_registry.json")
    authority = load("contracts/capital-authority-requirement-v1.json")
    effects = load("contracts/capital-effect-class-v1.json")
    evidence = load("contracts/capital-evidence-obligation-v1.json")
    roles = set(load("planning/functional-lego-map-r1.json")["functionalLegos"])
    assert {r["authorityRequirement"] for r in registry["entries"]} <= set(authority["classes"])
    assert {r["effectClass"] for r in registry["entries"]} <= set(effects["classes"])
    assert set(evidence["byFunctionalRole"]) == roles
    assert set(evidence["byEffectClass"]) == set(effects["classes"])


def test_public_readonly_composition_is_admitted_without_effect_authority():
    result = compile_composition(
        lego_ids=[
            "capital.markets.binance-usdm-public-capture",
            "capital.markets.crypto-public-shadow",
            "capital.markets.market-sensors",
        ],
        available_authorities={"PUBLIC_READ"},
        requested_use="public descriptive market monitoring",
    )
    assert result["standing"] == "ADMITTED_COMPOSITION_ONLY"
    assert result["effectClasses"] == []
    assert result["authorityGranted"] is False
    assert result["executionPerformed"] is False
    assert result["semanticCompletionEvaluated"] is False
    assert result["unresolvedEvidenceObligations"]


def test_private_read_source_remains_blocked_even_if_caller_names_private_read():
    with pytest.raises(CompositionContractError, match="blocked by independent authority"):
        compile_composition(
            lego_ids=["capital.trading.okx-readonly-client"],
            available_authorities={"PRIVATE_READ"},
            requested_use="read-only private account observation",
        )


def test_model_use_restriction_survives_composition():
    with pytest.raises(CompositionContractError, match="explicitly prohibited"):
        compile_composition(
            lego_ids=["capital.risk.portfolio-risk"],
            available_authorities=set(),
            requested_use="automatic trade sizing",
        )


def test_challenger_is_not_a_canonical_owner_by_default():
    with pytest.raises(CompositionContractError, match="challenger"):
        compile_composition(
            lego_ids=["capital.candidate.nautilus-nonlive-effect"],
            available_authorities={"SIMULATED_EFFECT"},
            requested_use="differential qualification",
        )


def test_simulated_effect_requires_reserve_reconcile_and_account_when_challenger_is_explicit():
    with pytest.raises(CompositionContractError, match="Reserve LEGO"):
        compile_composition(
            lego_ids=[
                "capital.candidate.nautilus-nonlive-effect",
                "capital.trading.execution-reconciliation",
                "capital.accounting.durable-reconciliation",
            ],
            available_authorities={"SIMULATED_EFFECT", "LOCAL_STATE"},
            requested_use="differential qualification",
            allow_challengers=True,
        )

    result = compile_composition(
        lego_ids=[
            "capital.accounting.sqlite-ledger",
            "capital.candidate.nautilus-nonlive-effect",
            "capital.trading.execution-reconciliation",
            "capital.accounting.durable-reconciliation",
        ],
        available_authorities={"SIMULATED_EFFECT", "LOCAL_STATE"},
        requested_use="differential qualification",
        allow_challengers=True,
    )
    assert result["effectClasses"] == ["SIMULATED_EXCHANGE_ORDER_EFFECT"]
    assert any(
        "authoritative post-effect reality" in x
        for x in result["unresolvedEvidenceObligations"]
    )


def test_production_authority_contract_is_explicitly_not_admitted():
    authority = load("contracts/capital-authority-requirement-v1.json")
    production = load("contracts/production-authorization.json")
    assert authority["classes"]["PRODUCTION_WRITE"]["currentAdmission"] is False
    assert production["state"] == "BLOCK_NOT_GRANTED"
    assert production["externalFinancialWriteAllowed"] is False
