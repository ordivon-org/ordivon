from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class LegoLensCompilerR1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.skill = (ROOT / ".agents/skills/lego-lens-compiler/SKILL.md").read_text(encoding="utf-8")
        self.contract = (ROOT / "docs/LEGO_LENS_COMPILER_R1.md").read_text(encoding="utf-8")
        self.template = (ROOT / "templates/LEGO_LENS_CARD_R1.md").read_text(encoding="utf-8")
        self.theory = (ROOT / "docs/LEGO_THEORY_LAYER_R1.md").read_text(encoding="utf-8")
        self.questions = (ROOT / "docs/LEGO_QUESTION_COMPILER_R1.md").read_text(encoding="utf-8")
        self.router_contract = (ROOT / "docs/LEGO_LENS_ROUTER_R1.md").read_text(encoding="utf-8")
        self.router_skill = (ROOT / ".agents/skills/lego-lens-router/SKILL.md").read_text(encoding="utf-8")
        self.registry = json.loads((ROOT / "knowledge/registries/lego-lens-registry-r1.json").read_text(encoding="utf-8"))

    def test_skill_rejects_metaphor_only(self):
        self.assertIn("METAPHOR_ONLY", self.skill)
        self.assertIn("Type-check the mapping", self.skill)
        self.assertIn("More lenses do not imply better reasoning.", self.skill)

    def test_compiler_is_router_fallback_not_parallel_router(self):
        self.assertIn("Router returned NO_LENS", self.skill)
        self.assertIn("Compiler does not maintain a second routing catalog.", self.skill)
        self.assertIn("does **not** own active-lens selection, MSTS, the lens registry", self.contract)
        self.assertIn("NO_LENS_METHOD_GAP", self.router_contract)
        self.assertIn("lego-lens-compiler", self.router_skill)

    def test_contract_keeps_active_set_sparse(self):
        self.assertIn("The candidate theory space may be extremely large. The active lens set must remain small.", self.contract)
        self.assertIn("no Wave 4 created merely to add disciplines", self.contract)
        self.assertIn("no universal cross-discipline ontology", self.contract)
        self.assertIn("no parallel registry", self.contract)

    def test_lifecycle_separates_candidate_from_registry_outcomes(self):
        for state in ("CANDIDATE", "SHADOW", "PROSPECTIVE", "ACTIVE", "MERGE", "RETIRE"):
            self.assertIn(state, self.contract)
        self.assertIn("Compiler cannot self-assign this state.", self.contract)
        self.assertIn("does not mutate the registry", self.contract)

    def test_contract_has_type_check_and_return_path(self):
        for phrase in ("Primitive fit", "Assumption fit", "Operator fit", "Observability fit", "Decision return path"):
            self.assertIn(phrase, self.contract)
        self.assertIn("queueing model", self.contract)
        self.assertIn("METAPHOR_ONLY", self.contract)

    def test_template_is_bounded_adapter_not_new_schema(self):
        for heading in (
            "## Target decision",
            "## Problem signature",
            "## Router handoff / rejected candidates",
            "## Primitive mapping",
            "## Assumptions",
            "## Operators",
            "## Non-claims",
            "## Stop condition",
            "## Lifecycle verdict",
        ):
            self.assertIn(heading, self.template)
        matches = list((ROOT / "schemas").glob("*lens*"))
        self.assertEqual(matches, [])

    def test_registry_tracks_compiler_as_operator_not_lens(self):
        self.assertIn("lego-lens-compiler", self.registry["operators"])
        ids = [x.get("id") for x in self.registry["lenses"]]
        refs = [x.get("skillRef") for x in self.registry["lenses"]]
        self.assertNotIn("lego-lens-compiler", ids)
        self.assertNotIn("lego-lens-compiler", refs)

    def test_question_router_compiler_pipeline_is_explicit(self):
        self.assertIn("Then hand off to `lego-lens-router`.", self.questions)
        self.assertIn("hand that uncovered residue to `lego-lens-compiler`", self.questions)
        self.assertIn("### LEGO Lens Router", self.theory)
        self.assertIn("### LEGO Lens Compiler", self.theory)
        self.assertIn("Question Compiler -> Lens Router", self.theory)


if __name__ == "__main__":
    unittest.main()
