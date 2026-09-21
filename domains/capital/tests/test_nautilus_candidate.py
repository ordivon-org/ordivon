import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/nautilus_candidate.json"


class NautilusCandidateBoundaryTests(unittest.TestCase):
    def test_candidate_is_non_live_only(self):
        cfg = json.loads(CONFIG.read_text())
        self.assertEqual(cfg["admissionLane"], "SHADOW_QUALIFICATION_ONLY")
        self.assertFalse(cfg["brokerConnectivityAllowed"])
        self.assertFalse(cfg["brokerCredentialsAllowed"])
        self.assertFalse(cfg["externalFinancialWritesAllowed"])
        self.assertFalse(cfg["productionLiveAdmitted"])

    def test_pinned_candidate_environment_is_available(self):
        out = subprocess.check_output([str(ROOT / "tools/nautilus_rc4/check-candidate")], text=True)
        result = json.loads(out)
        self.assertEqual(result["standing"], "NAUTILUS_CANDIDATE_BOUND_NON_LIVE")
        self.assertEqual(result["version"], "2.0.0rc4")
        self.assertEqual(result["python"], "3.12.13")


if __name__ == "__main__":
    unittest.main()
