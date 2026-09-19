from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class LegoQuestionCompilerR1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.skill = (ROOT / ".agents/skills/lego-question-compiler/SKILL.md").read_text(encoding="utf-8")
        self.contract = (ROOT / "docs/LEGO_QUESTION_COMPILER_R1.md").read_text(encoding="utf-8")
        self.pilot = (ROOT / "knowledge/lessons/poker-ai-lego-question-compiler-pilot-r1.md").read_text(encoding="utf-8")

    def test_skill_declares_analysis_not_truth(self):
        self.assertIn("Generated questions are derived analysis artifacts, not truth.", self.skill)
        self.assertIn("A question never updates project truth by itself.", self.skill)
        self.assertIn("## Stop condition", self.skill)

    def test_skill_has_bounded_compile_and_prune_pipeline(self):
        for family in (
            "STATE",
            "OBSERVABILITY",
            "ACTION/SEARCH",
            "OBJECTIVE",
            "POLICY/ADAPTATION",
            "FEEDBACK",
            "EXPLOITABILITY/ROBUSTNESS",
            "INFORMATION FLOW",
            "EMERGENCE",
            "CONTROL",
            "COUNTERFACTUAL",
            "FALSIFICATION",
        ):
            self.assertIn(family, self.skill)
        self.assertIn("Prune aggressively", self.skill)
        self.assertIn("Default to 3-7 primary questions", self.skill)

    def test_contract_preserves_thin_core(self):
        self.assertIn("no universal 12- or 17-question checklist", self.contract)
        self.assertIn("No machine-readable schema is introduced in R1.", self.contract)
        self.assertIn("Question Compiler does not own or maintain a theory catalog.", self.contract)
        self.assertNotIn("lego-lens-router", self.contract)
        self.assertNotIn("lego-lens-compiler", self.contract)

    def test_contract_ends_in_real_handoff(self):
        for mode in ("INVESTIGATE", "EXPERIMENT", "METHOD", "PLAN"):
            self.assertIn(mode, self.contract)
        self.assertIn("Question generation itself is not a permanent work mode.", self.contract)

    def test_poker_pilot_is_bounded_and_falsifiable(self):
        primary = re.findall(r"^### PQ\d+\s+—", self.pilot, flags=re.MULTILINE)
        self.assertGreaterEqual(len(primary), 3)
        self.assertLessEqual(len(primary), 7)
        self.assertIn("Questions pruned in R1", self.pilot)
        self.assertIn("Discriminating outcomes", self.pilot)
        self.assertIn("**EXPERIMENT**, not PLAN.", self.pilot)
        self.assertIn("CANDIDATE ONLY", self.pilot)

    def test_no_question_compiler_schema_was_added(self):
        matches = list((ROOT / "schemas").glob("*question*"))
        self.assertEqual(matches, [])


if __name__ == "__main__":
    unittest.main()
