from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ordivon_studio.learning_context import build_learning_context


class LearningContextTests(unittest.TestCase):
    def _root(self, directory: str) -> Path:
        root = Path(directory)
        (root / "research/expression").mkdir(parents=True)
        (root / "research/expression/context.json").write_text(json.dumps({
            "creativeSystem": {
                "learningPromotion": ["artifact-local", "medium-profile-candidate", "cross-medium-core-candidate"],
                "twoSpeedLearning": {"boundary": "do not collapse human experience"},
                "culturalObservatory": {
                    "creativeAlphaResearch": {
                        "authority": "research/expression/experiments/r6-creative-alpha.md",
                        "researchInstitutions": ["search-is-data", "pristine-holdout"],
                        "oosDimensions": ["artifact-content", "observer-class", "human-population"],
                        "boundary": "agent evidence is not human truth",
                    }
                },
            }
        }), encoding="utf-8")
        production = root / "productions/p1"
        production.mkdir(parents=True)
        (production / "production.json").write_text(json.dumps({
            "id": "p1",
            "status": "review",
            "audiences": ["technical-reader"],
            "outputs": [{"profile": "writing"}],
            "sources": {"claims": "claims.json", "cognition": "cognition.md"},
        }), encoding="utf-8")
        (production / "claims.json").write_text(json.dumps({"productionId": "p1", "claims": []}), encoding="utf-8")
        (production / "cognition.md").write_text("# P1\n\n## FRAME\nx\n\n## LEARNING\n\nRetain rendered-artifact inspection.\n\n### Scope\nArtifact-local until replicated.\n", encoding="utf-8")
        return root

    def test_learning_context_hydrates_scoped_sources_and_oos_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory)
            value = build_learning_context(root, current_production_id="p1")
        self.assertEqual(value["kind"], "ordivon.studio.learning-context")
        self.assertEqual(value["promotionPath"][0], "artifact-local")
        self.assertIn("observer-class", value["researchValidity"]["oosDimensions"] )
        self.assertEqual(value["retainedLearning"][0]["productionId"], "p1")
        self.assertIn("rendered-artifact inspection", value["retainedLearning"][0]["learning"] )
        self.assertIn("One observer is one observation", value["humanBoundary"] )

    def test_unknown_current_production_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory)
            with self.assertRaisesRegex(ValueError, "unknown Production"):
                build_learning_context(root, current_production_id="missing")


if __name__ == "__main__":
    unittest.main()
