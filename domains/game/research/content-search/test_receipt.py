"""Finite content census consumer; mutate real results, not a parallel simulator."""
import copy
import json
from pathlib import Path
import sys
import unittest
from run import validate, SELECTED

class Receipt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=json.loads(Path(sys.argv[1]).read_text())["rows"]

    def test_actual_census(self):
        self.assertEqual(tuple(validate(self.rows)["rooms"]), SELECTED)

    def test_actual_mutations(self):
        for kind in ("missing","duplicate","wrong_total","over_budget","bad_path","reference_mismatch","impossible_policy"):
            with self.subTest(kind=kind):
                rows=copy.deepcopy(self.rows)
                selected=next(r for r in rows if tuple(r["rooms"])==SELECTED)
                if kind=="missing":
                    rows.pop()
                elif kind=="duplicate":
                    rows[-1]=rows[-2]
                elif kind=="wrong_total":
                    selected["rooms"][0]=2
                elif kind=="over_budget":
                    selected["reduced"]["states"]=100001
                elif kind=="bad_path":
                    selected["reduced"]["frontier"][0]["path"][0]="advance"
                elif kind=="reference_mismatch":
                    selected["exact"]["frontier"][0]["health"]+=1
                else:
                    selected["attack_first"]["health"]=48
                with self.assertRaises(ValueError):
                    validate(rows)

if __name__=="__main__":
    unittest.main(argv=[sys.argv[0]],verbosity=2)
