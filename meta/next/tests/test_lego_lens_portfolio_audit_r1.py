from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/lego_lens_portfolio_audit_r1.py"

spec = importlib.util.spec_from_file_location("lens_portfolio_audit", SCRIPT)
assert spec and spec.loader
MODULE = importlib.util.module_from_spec(spec)
spec.loader.exec_module(MODULE)


class LegoLensPortfolioAuditR1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = json.loads((ROOT / "knowledge/registries/lego-lens-registry-r1.json").read_text(encoding="utf-8"))
        self.ledger = json.loads((ROOT / "evidence/analysis/lego-lens-portfolio-ledger-r1.json").read_text(encoding="utf-8"))

    def test_current_ledger_passes_and_records_contraction(self):
        summary = MODULE.audit(self.registry, self.ledger)
        self.assertEqual(summary["caseCount"], 4)
        self.assertEqual(summary["maxSelectedLensCount"], 2)
        self.assertEqual(summary["casesOverThreeLenses"], [])
        self.assertEqual(summary["domainMethodUses"], 6)
        self.assertEqual(summary["contractions"], [{"case": "agent-service-readiness-damping", "from": 8, "to": 2}])

    def test_four_lenses_without_exception_fails(self):
        bad = {
            "schemaVersion": 1,
            "cases": [{
                "id": "bad",
                "methods": [
                    {"id": "feedback-control", "role": "LENS", "selected": True},
                    {"id": "stpa", "role": "LENS", "selected": True},
                    {"id": "systems-engineering", "role": "LENS", "selected": True},
                    {"id": "dsm", "role": "LENS", "selected": True}
                ]
            }]
        }
        with self.assertRaisesRegex(ValueError, "requires exceptionalLensCountJustification"):
            MODULE.audit(self.registry, bad)

    def test_domain_method_does_not_need_registry_entry(self):
        value = {
            "schemaVersion": 1,
            "cases": [{
                "id": "domain-method",
                "methods": [
                    {"id": "formal-reachability", "role": "DOMAIN_METHOD", "selected": True}
                ]
            }]
        }
        summary = MODULE.audit(self.registry, value)
        self.assertEqual(summary["domainMethodUses"], 1)
        self.assertEqual(summary["maxSelectedLensCount"], 0)

    def test_unknown_lens_fails_closed(self):
        bad = {
            "schemaVersion": 1,
            "cases": [{
                "id": "unknown",
                "methods": [
                    {"id": "quantum-team-metaphor", "role": "LENS", "selected": True}
                ]
            }]
        }
        with self.assertRaisesRegex(ValueError, "unknown registry lens"):
            MODULE.audit(self.registry, bad)


if __name__ == "__main__":
    unittest.main()
