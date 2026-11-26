"""Finite corruption obligations over actual native route receipts."""
import copy
import json
from pathlib import Path
import sys
import unittest
from run import validate

class Receipt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=json.loads(Path(sys.argv[1]).read_text())["rows"]
    def test_actual(self):
        validate(self.rows)
    def test_negative_axes(self):
        for fault in ("missing","wrong_rooms","bad_reference","bypass","extra_signal",
                      "free_health","duplicate_enabled","wrong_terminal","wrong_prefix"):
            with self.subTest(fault=fault):
                rows=copy.deepcopy(self.rows)
                r=rows[1]
                if fault=="missing": rows.pop()
                elif fault=="wrong_rooms": r["rooms"][1]=3
                elif fault=="bad_reference": r["exact"]["frontier"][0]["health"]+=1
                elif fault=="bypass": r["witness"][r["witness"].index("gradual")]="advance"
                elif fault=="extra_signal": r["fork"]["state_events"]=2
                elif fault=="free_health": r["fork"]["after"]["state"]["player_health"]+=1
                elif fault=="duplicate_enabled": r["fork"]["after"]["enabled"]["direct"]=True
                elif fault=="wrong_terminal": r["terminal"]["state"]["phase"]="cleared"
                else:
                    r["fork"]["before"]["state"]["player_health"]-=1
                    r["fork"]["after"]["state"]["player_health"]-=1
                with self.assertRaises(ValueError): validate(rows)

if __name__=="__main__":
    unittest.main(argv=[sys.argv[0]],verbosity=2)
