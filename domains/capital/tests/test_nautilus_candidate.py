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
