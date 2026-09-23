from __future__ import annotations

import pytest

from ordivon_capital.trading.execution_reconciliation import reconcile_fix_intent
from ordivon_capital.trading.simulated_effect import SimulatedEffectError, simulate_exchange_episode

INTENT = {
    "protocol": "FIX.4.4",
    "msgType": "D",
    "clOrdId": "SIM-C1",
    "exDestination": "BINANCE",
    "symbol": "BTCUSDT",
    "orderQty": "1",
}


@pytest.mark.parametrize(
    ("scenario", "expected"),
    [
        ("FILL", "POST_PENDING_TRANSFER"),
        ("PARTIAL_FILL_SLICES", "POST_PENDING_TRANSFER"),
        ("CANCEL", "VOID_PENDING_TRANSFER"),
        ("DENY", "VOID_PENDING_TRANSFER"),
        ("UNKNOWN_AFTER_SUBMISSION", "NO_MUTATION"),
    ],
)
def test_simulated_episode_reconciles_through_current_owner(scenario, expected):
    episode = simulate_exchange_episode(intent=INTENT, scenario=scenario)
    result = reconcile_fix_intent(
        intent=INTENT,
        reality=episode["reality"],
        exact_lookup=episode["exactLookup"],
    )
    assert result["reservationResolution"] == expected
    assert episode["externalFinancialWritesAttempted"] is False
    assert episode["realMoney"] is False


def test_simulated_effect_rejects_unknown_scenario():
    with pytest.raises(SimulatedEffectError, match="unsupported scenario"):
        simulate_exchange_episode(intent=INTENT, scenario="LIVE")
