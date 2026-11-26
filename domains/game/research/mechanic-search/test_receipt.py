"""Test the decision consumer, not a parallel game model."""
import copy
import json
from pathlib import Path
import sys
import unittest

from run import validate


class SearchReceipt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = json.loads(Path(sys.argv[1]).read_text())["cases"]

    def test_real_positive(self):
        validate(self.rows)

    def test_actual_observation_mutations(self):
        for fault in ("missing_case", "quotient", "path", "turn", "cycle", "budget", "false_policy"):
            with self.subTest(fault=fault):
                rows = copy.deepcopy(self.rows)
                trial = rows[1]
                if fault == "missing_case":
                    rows.pop()
                elif fault == "quotient":
                    trial["reduced"]["frontier"][0]["health"] -= 1
                elif fault == "path":
                    trial["exact"]["frontier"][0]["path"].pop()
                elif fault == "turn":
                    trial["exact"]["frontier"][0]["turns"] += 1
                elif fault == "cycle":
                    trial["guard_cycle"]["same_quotient"] = not trial["guard_cycle"]["same_quotient"]
                elif fault == "budget":
                    trial["exact"]["states"] = 100001
                else:
                    trial["attack_first"]["health"] = trial["initial_health"]
                with self.assertRaises(ValueError):
                    validate(rows)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: test_receipt.py actual-search-receipt.json")
    unittest.main(argv=[sys.argv[0]], verbosity=2)
