from __future__ import annotations

import hashlib
import json
from pathlib import Path

from market_capital.execution_reconciliation import reservation_resolution_for_standing

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "fixtures" / "r5_legacy_bounded"


def _load(path: Path) -> dict:
    value = json.loads(path.read_text())
    assert isinstance(value, dict)
    return value


def test_frozen_legacy_fixture_digests_are_exact() -> None:
    manifest = _load(FIXTURE_ROOT / "manifest.json")
    for entry in manifest["fixtures"]:
        path = FIXTURE_ROOT / entry["path"]
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual == entry["sha256"]
    assert manifest["legacyCodeImported"] is False


def test_historical_effect_outcomes_map_to_provider_native_resolutions() -> None:
    evidence = _load(
        FIXTURE_ROOT / "market-capital-r27-p21-effect-reconciliation-final-20260908.json"
    )
    contract = evidence["contract"]
    for standing in contract["release"]:
        assert reservation_resolution_for_standing(standing) == "VOID_PENDING_TRANSFER"
    for standing in ("UNKNOWN", "AMBIGUOUS", "PARTIAL_OPEN", "CONTRADICTORY"):
        assert standing in contract["retainHold"]
        assert reservation_resolution_for_standing(standing) == "NO_MUTATION"
    assert reservation_resolution_for_standing("POSITIVE_EXECUTION") == "POST_PENDING_TRANSFER"


def test_historical_authority_fixture_remains_archived_not_reimplemented() -> None:
    evidence = _load(
        FIXTURE_ROOT / "market-capital-r28-p31-effect-authority-v2-final-20260908.json"
    )
    assert evidence["boundedStanding"]["institutionalProduction"] == "NOT_GRANTED"
    assert evidence["externalFinancialWriteAttempted"] is False
