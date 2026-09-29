from __future__ import annotations

from copy import deepcopy

import pytest

from ordivon_capital.governance.nonlive_effect_circuit import (
    NonLiveEffectCircuitError,
    compile_nonlive_effect_circuit,
    run_nonlive_effect_circuit,
)


def intent(scenario: str):
    return {
        "protocol": "FIX.4.4",
        "msgType": "D",
        "clOrdId": f"SIM-{scenario}",
        "exDestination": "BINANCE",
        "symbol": "BTCUSDT",
        "orderQty": "1",
    }


@pytest.mark.parametrize(
    ("scenario", "resolution", "pending", "posted"),
    [
        ("FILL", "POST_PENDING_TRANSFER", 0, 1000),
        ("PARTIAL_FILL_SLICES", "POST_PENDING_TRANSFER", 0, 1000),
        ("CANCEL", "VOID_PENDING_TRANSFER", 0, 0),
        ("DENY", "VOID_PENDING_TRANSFER", 0, 0),
        ("UNKNOWN_AFTER_SUBMISSION", "NO_MUTATION", 1000, 0),
    ],
)
def test_nonlive_circuit_closes_reservation_by_reconciliation(tmp_path, scenario, resolution, pending, posted):
    circuit = compile_nonlive_effect_circuit(scenario=scenario, intent=intent(scenario))
    result = run_nonlive_effect_circuit(
        circuit=circuit,
        ledger_path=tmp_path / f"{scenario}.sqlite3",
    )
    assert result["accountingResolution"] == resolution
    assert result["availableAccount"]["debitsPending"] == pending
    assert result["availableAccount"]["debitsPosted"] == posted
    assert result["durableLedgerReconciliation"] == "MATCH"
    assert result["externalFinancialWritesAttempted"] is False


def test_tampered_effect_circuit_fails_before_mechanics(tmp_path):
    circuit = compile_nonlive_effect_circuit(scenario="FILL", intent=intent("FILL"))
    bad = deepcopy(circuit)
    bad["scenario"] = "UNKNOWN_AFTER_SUBMISSION"
    with pytest.raises(NonLiveEffectCircuitError, match="digest mismatch"):
        run_nonlive_effect_circuit(circuit=bad, ledger_path=tmp_path / "bad.sqlite3")
