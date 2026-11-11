import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "tools/nautilus_rc4/config/nautilus_candidate.json"


class NautilusCandidateBoundaryTests(unittest.TestCase):
    def test_candidate_is_non_live_only(self):
        cfg = json.loads(CONFIG.read_text())
        self.assertEqual(cfg["admissionLane"], "SHADOW_QUALIFICATION_ONLY")
        self.assertFalse(cfg["brokerConnectivityAllowed"])
        self.assertFalse(cfg["brokerCredentialsAllowed"])
        self.assertFalse(cfg["externalFinancialWritesAllowed"])
        self.assertFalse(cfg["productionLiveAdmitted"])

    @pytest.mark.provider_qualification
    def test_pinned_candidate_environment_is_available(self):
        out = subprocess.check_output([str(ROOT / "tools/nautilus_rc4/check-candidate")], text=True)
        result = json.loads(out)
        self.assertEqual(result["standing"], "NAUTILUS_CANDIDATE_BOUND_NON_LIVE")
        self.assertEqual(result["version"], "2.0.0rc4")
        self.assertEqual(result["python"], "3.12.13")


@pytest.mark.provider_qualification
def test_python315_rc9_native_nonlive_reconciliation() -> None:
    # This is a real upstream BacktestEngine-to-Capital consumer, not a mock or
    # proof of external venue execution. The optional nonlive group is required.
    assert sys.version_info[:2] == (3, 15)
    from nautilus_trader import __version__ as upstream_version

    assert upstream_version == "2.0.0rc9"
    result = subprocess.check_output(
        [sys.executable, str(ROOT / "tools/nautilus_rc4/nonlive_effect_matrix.py")],
        cwd=ROOT,
        env=os.environ | {"PYTHONPATH": str(ROOT / "src")},
        text=True,
    )
    payload = json.loads(result)
    assert payload["providerVersion"] == "2.0.0rc9"
    assert payload["standing"] == "PASS_NAUTILUS_NONLIVE_EFFECT_RECONCILIATION_MATRIX"
    assert payload["observedResolutions"] == {
        "FILL": "POST_PENDING_TRANSFER",
        "PARTIAL_FILL_SLICES": "POST_PENDING_TRANSFER",
        "CANCEL": "VOID_PENDING_TRANSFER",
        "DENY": "VOID_PENDING_TRANSFER",
        "UNKNOWN_AFTER_SUBMISSION": "NO_MUTATION",
    }
    assert payload["partialFillSliceCount"] >= 2
    assert payload["externalFinancialWriteAttempted"] is False
    assert payload["realMoney"] is False


if __name__ == "__main__":
    unittest.main()


@pytest.mark.provider_qualification
def test_rc9_synthetic_equity_paper_consumer(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "tools/nautilus_rc4"))
    import equity_paper_qualification as eq
    from nautilus_trader.model import ClientOrderId, OrderFilled

    for fee, nav in (("0.00", 100396), ("1.23", 100273)):
        result = eq.run_episode(fee)
        assert result["nativeNavMinor"] == result["paper"]["nav_minor"] == nav
        assert result["paper"]["cash_minor"] == 100000
        assert result["paper"]["payable_minor"] == 100000 - result["nativeCashMinor"]
        assert result["holidayPayableMinor"] == result["paper"]["payable_minor"]
        assert result["settlementCashMinor"] == result["nativeCashMinor"]
        assert result["settlementDate"] == eq.SETTLEMENT.isoformat()
        fill, event = result["fills"][0], result["events"][0]
        assert (fill["shares"], fill["price_minor"], fill["fee_minor"]) == (2, 11002, eq.minor(fee))
        assert fill["fill_id"] == event["trade_id"]
        assert fill["filled_at"] == eq.OPEN
        assert event["ts_event"] == eq.ns(eq.OPEN)
    # Same frozen target under a different opening price: no future-price sizing.
    assert eq.run_episode(ask="111.00")["fills"][0]["shares"] == 2
    for kwargs in ({"opening": False}, {"cash": "100.00"}):
        with pytest.raises(ValueError):
            eq.run_episode(**kwargs)
    for amount in ("1.001", "-1", "NaN", "Infinity"):
        with pytest.raises(ValueError):
            eq.minor(amount)
    intent = eq.Intent(eq.InstrumentId.from_str(event["instrument_id"]))
    order_id = ClientOrderId(event["client_order_id"])
    real = OrderFilled.from_dict(event)
    with pytest.raises(ValueError, match="duplicate"):
        eq.project([real, real], intent, order_id)
    # Explicitly corrupted copies of observed native events test admission only.
    for change in ({"commission": "1.23 EUR"}, {"last_qty": "0.5"},
                   {"last_qty": "3"}, {"last_px": "110.021"},
                   {"ts_event": eq.ns(eq.OPEN) + 1}, {"client_order_id": "wrong"}):
        with pytest.raises(ValueError):
            eq.project([OrderFilled.from_dict(event | change)], intent, order_id)
