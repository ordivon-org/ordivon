from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text())


def test_generated_current_state_is_rebuildable_and_authority_preserving():
    subprocess.run(
        [str(ROOT / "scripts/build-current-state-r2"), "--check"],
        check=True,
        cwd=ROOT,
    )
    doc = load("generated/current-state-r2.json")
    registry = load("config/capital_lego_registry.json")
    fmap = load("planning/functional-lego-map-r1.json")
    atlas = load("config/investment_model_atlas.json")

    assert doc["truthRole"] == "REBUILDABLE_PROJECTION_NOT_AUTHORITY"
    assert doc["productionAuthorization"] == {
        "state": "BLOCK_NOT_GRANTED",
        "externalFinancialWriteAllowed": False,
        "authority": "contracts/production-authorization.json",
    }
    assert doc["privateReality"]["privateAccountDataAdmission"] == "NOT_ADMITTED"
    assert doc["portfolioRiskBudget"]["standing"] == "UNSET"
    assert doc["execution"]["currentLane"] == "NON_LIVE"
    assert doc["inventory"] == {
        "registryEntries": len(registry["entries"]),
        "canonicalEntries": sum(row["sourceClass"] == "CANONICAL" for row in registry["entries"]),
        "functionalLegos": len(fmap["functionalLegos"]),
    }
    assert doc["investmentDecisionSystem"]["registeredModels"] == len(atlas["models"])
    assert doc["investmentDecisionSystem"]["externalFinancialEffectAllowed"] is False


def test_current_state_does_not_use_git_recency_as_semantic_currentness():
    text = (ROOT / "generated/current-state-r2.json").read_text()
    assert "repositorySourceRevision" not in text
    assert "gitHead" not in text
