from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_nonlive_circuit_acceptance_is_five_scenario_and_nonfinancial():
    doc = json.loads((ROOT / "acceptance/capital-nonlive-circuit-r1.json").read_text())
    assert doc["standing"] == "PASS"
    assert doc["assertions"]["scenarioCount"] == 5
    assert doc["assertions"]["externalFinancialWritesAttempted"] is False
    assert doc["assertions"]["allDurableLedgerReconciliationsMatch"] is True
    assert doc["assertions"]["productionAuthorizationUnchanged"] == "BLOCK_NOT_GRANTED"
    by = {row["scenario"]: row for row in doc["scenarios"]}
    assert by["FILL"]["accountingResolution"] == "POST_PENDING_TRANSFER"
    assert by["PARTIAL_FILL_SLICES"]["accountingResolution"] == "POST_PENDING_TRANSFER"
    assert by["CANCEL"]["accountingResolution"] == "VOID_PENDING_TRANSFER"
    assert by["DENY"]["accountingResolution"] == "VOID_PENDING_TRANSFER"
    assert by["UNKNOWN_AFTER_SUBMISSION"]["accountingResolution"] == "NO_MUTATION"
