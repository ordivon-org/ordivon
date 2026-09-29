from __future__ import annotations

import json
from pathlib import Path

CAPITAL = Path(__file__).resolve().parents[1]


def load(rel: str):
    return json.loads((CAPITAL / rel).read_text())


def test_private_reality_keeps_observer_and_effect_authority_separate():
    policy = load("config/private_reality_policy.json")
    assert policy["secretDiscoveryAllowed"] is False
    assert policy["orderCapableCredentialsAllowed"] is False
    assert policy["withdrawalCredentialsAllowed"] is False
    assert policy["privateAccountDataAdmission"] == "NOT_ADMITTED"
    assert policy["externalFinancialWritesAllowed"] is False
    for row in policy["credentialBindings"].values():
        assert row["copyIntoRepository"] is False


def test_current_capital_contracts_and_acceptance_do_not_embed_secret_paths():
    paths = [
        CAPITAL / "contracts/capital-skill-boundary-v1.json",
        CAPITAL / "acceptance/capital-circuit-readonly-r1.json",
        CAPITAL / "acceptance/capital-nonlive-circuit-r1.json",
        CAPITAL / "acceptance/capital-lego-architecture-r1.json",
    ]
    for path in paths:
        text = path.read_text()
        assert "/root/.config/ordivon/secrets/" not in text
        assert "executor/config.toml" not in text


def test_information_flow_plan_never_transfers_effect_authority():
    doc = load("planning/information-flow-r1.json")
    for row in doc["flows"]:
        if "effectAuthorityTransferred" in row:
            assert row["effectAuthorityTransferred"] is False
