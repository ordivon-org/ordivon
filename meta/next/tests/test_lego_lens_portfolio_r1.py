from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class LegoLensPortfolioR1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.skill = (ROOT / ".agents/skills/lego-lens-portfolio/SKILL.md").read_text(encoding="utf-8")
        self.contract = (ROOT / "docs/LEGO_LENS_PORTFOLIO_R1.md").read_text(encoding="utf-8")
        self.lesson = (ROOT / "knowledge/lessons/lego-lens-portfolio-readiness-pressure-test-r1.md").read_text(encoding="utf-8")
        self.evidence = json.loads((ROOT / "evidence/acceptance/lego-lens-portfolio-pressure-test-r1.json").read_text(encoding="utf-8"))
        self.registry = json.loads((ROOT / "knowledge/registries/lego-lens-registry-r1.json").read_text(encoding="utf-8"))
        self.acceptance = json.loads((ROOT / "evidence/acceptance/lego-lens-portfolio-r1.json").read_text(encoding="utf-8"))

    def test_distinguishes_lens_method_operator(self):
        for role in ("LENS", "DOMAIN_METHOD", "OPERATOR"):
            self.assertIn(role, self.skill)
            self.assertIn(role, self.contract)
        self.assertIn("many invoked methods != many active lenses", self.skill)

    def test_pressure_audit_contracts_overcounted_case(self):
        self.assertEqual(self.evidence["sourceCase"]["originalActiveCount"], 8)
        self.assertEqual(self.evidence["normalized"]["lensCount"], 2)
        self.assertEqual(self.evidence["normalized"]["domainMethodCount"], 6)
        self.assertEqual(self.evidence["normalized"]["selectedMsts"], ["feedback-control", "stpa"])
        self.assertFalse(self.evidence["projectTruthChanged"])
        self.assertEqual(self.evidence["registryMutation"], "NONE")

    def test_pressure_test_preserves_material_outputs(self):
        for phrase in (
            "freshness filtering survives",
            "negative-edge immediate loss survives",
            "positive-edge damping survives",
            "benchmark correction survives",
            "production no-change survives",
        ):
            self.assertIn(phrase, self.lesson)

    def test_portfolio_is_operator_not_lens(self):
        self.assertIn("lego-lens-portfolio", self.registry["operators"])
        ids = [x.get("id") for x in self.registry["lenses"]]
        refs = [x.get("skillRef") for x in self.registry["lenses"]]
        self.assertNotIn("lego-lens-portfolio", ids)
        self.assertNotIn("lego-lens-portfolio", refs)

    def test_no_universal_scalar_fitness(self):
        self.assertIn("does not collapse these into a universal numeric score", self.contract)
        self.assertIn("no universal scalar lens score", self.contract)

    def test_acceptance_keeps_registry_sparse_without_core_change(self):
        self.assertEqual(self.acceptance["standing"], "PASS_INITIAL_CROSS_DOMAIN_PORTFOLIO_GOVERNANCE")
        self.assertFalse(self.acceptance["registry"]["lensCountChangedByPortfolio"])
        self.assertFalse(self.acceptance["registry"]["coreSchemaChanged"])
        self.assertEqual(self.acceptance["registry"]["reservePoolCount"], 23)
        self.assertIn("LEGO_LENS_UNIVERSE_R1.md", self.acceptance["registry"]["canonicalReserveOwner"])
        self.assertIn("reservePool", self.contract)
        self.assertEqual(self.acceptance["validation"]["executableAudit"]["maxSelectedLensCount"], 2)


if __name__ == "__main__":
    unittest.main()
