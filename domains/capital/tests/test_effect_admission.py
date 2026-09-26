from __future__ import annotations

import pytest

from ordivon_capital.governance.nonlive_effect_circuit import (
    NonLiveEffectCircuitError,
    compile_nonlive_effect_circuit,
)

INTENT = {
    "protocol": "FIX.4.4",
    "msgType": "D",
    "clOrdId": "SIM-C1",
    "exDestination": "BINANCE",
    "symbol": "BTCUSDT",
    "orderQty": "1",
}


def test_nonlive_compiler_binds_only_simulated_effect_and_preserves_production_block():
    circuit = compile_nonlive_effect_circuit(scenario="FILL", intent=INTENT)
    assert circuit["effectClass"] == "SIMULATED_EXCHANGE_ORDER_EFFECT"
    assert circuit["externalFinancialWriteAllowed"] is False
    assert circuit["realMoney"] is False
    assert circuit["productionAuthorization"] == "BLOCK_NOT_GRANTED"


def test_nonlive_compiler_rejects_non_admitted_scenario():
    with pytest.raises(NonLiveEffectCircuitError, match="unsupported"):
        compile_nonlive_effect_circuit(scenario="PRODUCTION", intent=INTENT)
