from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class LegoLensCompilerPilotR1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.lesson = (ROOT / "knowledge/lessons/lego-lens-compiler-queueing-pilot-r1.md").read_text(encoding="utf-8")
        self.acceptance = json.loads((ROOT / "evidence/acceptance/lego-lens-compiler-shadow-pilot-r1.json").read_text(encoding="utf-8"))

    def test_pilot_has_valid_mapping_but_refuses_premature_model(self):
        self.assertIn("PARTIAL PASS", self.lesson)
        self.assertIn("M/M/1 or M/M/c assumptions", self.lesson)
        self.assertIn("permanent skill          NOT_CREATED", self.lesson)
        self.assertEqual(
            self.acceptance["lensCompilerOutcome"],
            "PASS_DISCOVERED_VALID_METHOD_AND_REJECTED_PREMATURE_ACTIVATION",
        )

    def test_queueing_skill_was_not_created(self):
        self.assertFalse((ROOT / ".agents/skills/lego-queueing").exists())
        self.assertFalse((ROOT / ".agents/skills/lego-queueing-theory").exists())

    def test_semantic_acceptance_is_not_collapsed_into_service_completion(self):
        self.assertIn("worker completion is not the same as provider/domain semantic acceptance", self.lesson)
        self.assertIn("semantic acceptance latency", self.lesson)


if __name__ == "__main__":
    unittest.main()
