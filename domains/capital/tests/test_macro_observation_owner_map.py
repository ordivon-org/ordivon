from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_macro_owner_map_prefers_official_sources_and_fails_closed_on_credentials():
    doc = json.loads((ROOT / "config/macro_observation_owners.json").read_text())
    obs = doc["observations"]
    assert obs["usTreasuryNominalCurve"]["owner"] == "U.S. Department of the Treasury"
    assert obs["usTreasuryNominalCurve"]["transportAuthority"] == "usTreasuryRest"
    assert obs["usTreasuryRealCurve"]["credentialRequired"] is False
    assert obs["brentWti"]["standing"] == "ACTIVE_EIA_ORIGIN_FRED_PUBLIC_MIRROR"
    assert obs["brentWti"]["originOwner"] == "U.S. Energy Information Administration"
    assert obs["brentWti"]["activeAggregator"] == "Federal Reserve Bank of St. Louis FRED"
    assert obs["brentWti"]["credentialRequired"] is False
    assert obs["brentWti"]["directEiaCredentialRequired"] is True
    assert obs["fedPolicyRepricing"]["standing"] == "EXTERNAL_SUBSCRIPTION_REQUIRED_NOT_INTEGRATED"
    assert "do not scrape" in obs["fedPolicyRepricing"]["credentialPolicy"]
    assert obs["fedPolicyRepricing"]["derivedChallenger"]["standing"] == "UNQUALIFIED_NEW_DERIVED_CHALLENGER"


def test_soxl_identity_separates_benchmark_cash_and_derivative_truth():
    doc = json.loads((ROOT / "config/soxl_instrument_identity.json").read_text())
    assert doc["benchmark"]["name"] == "NYSE Semiconductor Index"
    assert doc["benchmark"]["symbol"] == "ICESEMIT"
    assert doc["dailyTargetMultiple"] == "3.0"
    assert all("NOT_CASH_OR_BENCHMARK_TRUTH" in row["role"] for row in doc["derivativeObservations"])
