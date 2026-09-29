from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_reservation_contract_matches_current_reconciliation_mapping():
    contract = json.loads((ROOT / "contracts/capital-reservation-v1.json").read_text())
    assert contract["resolutionMap"]["UNKNOWN"] == "NO_MUTATION"
    assert contract["resolutionMap"]["POSITIVE_EXECUTION"] == "POST_PENDING_TRANSFER"
    assert contract["resolutionMap"]["PROVEN_NO_EFFECT"] == "VOID_PENDING_TRANSFER"
