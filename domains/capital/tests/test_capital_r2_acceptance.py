from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: str):
    return json.loads((ROOT / path).read_text())


def test_r2_acceptance_binds_exact_implementation_and_preserves_authority():
    acc = load("acceptance/capital-r2-architecture.json")
    assert acc["standing"] == "PASS_R2_IMPLEMENTATION"
    assert acc["implementation"]["commit"] == "b077c9246bda15f032f7f0c70ba716d34752e2ec"
    assert acc["implementation"]["verificationRuntimeJob"] == "job-01a0cd76-f7d2-7e53-8c9c-f28fb2fa399a"
    assert acc["substitution"]["standing"] == "EQUIVALENT_FOR_CURRENT_CAPITAL_CONTRACT_SPACE"
    assert acc["authorityStanding"] == {
        "executionLane": "NON_LIVE",
        "productionAuthorization": "BLOCK_NOT_GRANTED",
        "externalFinancialWriteAllowed": False,
        "privateAccountDataAdmission": "NOT_ADMITTED",
        "portfolioRiskBudget": "UNSET",
    }


def test_r2_acceptance_does_not_claim_repository_publication_or_domain_truth():
    acc = load("acceptance/capital-r2-architecture.json")
    assert acc["waves"]["repositoryIntegration"] == "PENDING_SEPARATE_REPO_AUTHORITY"
    assert acc["truthRole"] == "IMPLEMENTATION_ACCEPTANCE_NOT_FINANCIAL_OR_PROVIDER_TRUTH"
    assert any("does not make mechanical circuit closure" in item for item in acc["nonClaims"])
