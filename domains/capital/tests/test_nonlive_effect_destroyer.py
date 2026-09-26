from __future__ import annotations

from ordivon_capital.governance.nonlive_effect_circuit import (
    compile_nonlive_effect_circuit,
    run_nonlive_effect_circuit,
)


def intent(name: str):
    return {
        "protocol": "FIX.4.4",
        "msgType": "D",
        "clOrdId": f"DESTROY-{name}",
        "exDestination": "BINANCE",
        "symbol": "BTCUSDT",
        "orderQty": "1",
    }


def test_response_loss_unknown_preserves_pending_and_never_posts(tmp_path):
    circuit = compile_nonlive_effect_circuit(
        scenario="UNKNOWN_AFTER_SUBMISSION",
        intent=intent("UNKNOWN"),
    )
    result = run_nonlive_effect_circuit(circuit=circuit, ledger_path=tmp_path / "unknown.sqlite3")
    assert result["reconciliation"]["standing"] == "UNKNOWN"
    assert result["accountingResolution"] == "NO_MUTATION"
    assert result["availableAccount"]["debitsPending"] == 1000
    assert result["availableAccount"]["debitsPosted"] == 0


def test_terminal_replay_is_idempotent_and_does_not_double_consume(tmp_path):
    circuit = compile_nonlive_effect_circuit(scenario="FILL", intent=intent("FILL"))
    path = tmp_path / "replay.sqlite3"
    first = run_nonlive_effect_circuit(circuit=circuit, ledger_path=path)
    second = run_nonlive_effect_circuit(circuit=circuit, ledger_path=path)
    assert first["availableAccount"]["debitsPosted"] == 1000
    assert second["availableAccount"]["debitsPosted"] == 1000
    assert second["reservationStatus"] == "EXISTS"
    assert second["resolutionApplyStatus"] == "EXISTS"
