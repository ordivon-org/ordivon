from __future__ import annotations

import sys
import unittest
from pathlib import Path

STUDY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STUDY / "scripts"))

from computational_lift_r3 import lift_pilot  # noqa: E402
from mcrl2_equivalence_adapter_r3 import parse_ltscompare_boolean  # noqa: E402


class FormalBackendsR3Tests(unittest.TestCase):
    def test_ltscompare_parser_uses_boolean_not_return_code(self):
        self.assertTrue(parse_ltscompare_boolean("true\n"))
        self.assertFalse(parse_ltscompare_boolean("false\n"))
        with self.assertRaises(ValueError):
            parse_ltscompare_boolean("LTSs are not equal\n")

    def test_l0_to_l1_history_witness(self):
        result = lift_pilot()
        cert = result["certificate"]
        witness = result["historyDependenceWitness"]
        self.assertEqual(cert["standing"], "CERTIFIED_LIFT")
        self.assertEqual(cert["lowerModelClass"], "L0_STATELESS_RELATION")
        self.assertEqual(cert["higherModelClass"], "L1_FINITE_STATE_TRANSDUCER")
        self.assertEqual(witness["sameExplicitInput"], "read")
        self.assertNotEqual(witness["observationA"], witness["observationB"])
        self.assertEqual(cert["bounds"]["constructedStateCount"], 2)
        self.assertFalse(cert["universalDecisionProcedureClaimed"])


if __name__ == "__main__":
    unittest.main()
