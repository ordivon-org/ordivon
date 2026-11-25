from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ordivon_studio.agent_productions import production_standing
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

    def test_learning_digest_describes_the_exact_parsed_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory)
            expression = root / "research/expression/context.json"
            cognition = root / "productions/p1/cognition.md"
            expected = {path: path.read_bytes() for path in (expression, cognition)}
            replacements = {
                expression: expected[expression].replace(b"artifact-local", b"changed-scope"),
                cognition: expected[cognition].replace(b"rendered-artifact inspection", b"changed learning"),
            }
            original_bytes = Path.read_bytes
            original_text = Path.read_text
            changed = set()

            def mutate(path):
                if path in replacements and path not in changed:
                    changed.add(path)
                    path.write_bytes(replacements[path])

            def read_bytes(path):
                result = original_bytes(path)
                mutate(path)
                return result

            def read_text(path, *args, **kwargs):
                result = original_text(path, *args, **kwargs)
                mutate(path)
                return result

            with patch.object(Path, "read_bytes", read_bytes), patch.object(Path, "read_text", read_text):
                value = build_learning_context(root, current_production_id="p1")
            self.assertEqual(changed, set(expected))
            self.assertEqual(value["promotionPath"][0], "artifact-local")
            self.assertIn("rendered-artifact inspection", value["retainedLearning"][0]["learning"])
            self.assertEqual(value["source"]["expressionContextDigest"], "sha256:" + hashlib.sha256(expected[expression]).hexdigest())
            self.assertEqual(value["retainedLearning"][0]["source"]["digest"], "sha256:" + hashlib.sha256(expected[cognition]).hexdigest())

    def test_production_standing_digest_describes_parsed_descriptor(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory)
            path = root / "productions/p1/production.json"
            expected = path.read_bytes()
            replacement = expected.replace(b'"review"', b'"changed"')
            original_bytes = Path.read_bytes
            original_text = Path.read_text
            changed = False

            def mutate(candidate):
                nonlocal changed
                if candidate == path and not changed:
                    changed = True
                    path.write_bytes(replacement)

            def read_bytes(candidate):
                result = original_bytes(candidate)
                mutate(candidate)
                return result

            def read_text(candidate, *args, **kwargs):
                result = original_text(candidate, *args, **kwargs)
                mutate(candidate)
                return result

            with patch.object(Path, "read_bytes", read_bytes), patch.object(Path, "read_text", read_text):
                value = production_standing(root)["productions"][0]
            self.assertTrue(changed)
            self.assertEqual(value["status"], "review")
            self.assertEqual(value["source"]["digest"], "sha256:" + hashlib.sha256(expected).hexdigest())

    def test_cognition_source_cannot_escape_selected_production(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory)
            production = root / "productions/p1"
            manifest = production / "production.json"
            value = json.loads(manifest.read_text(encoding="utf-8"))
            value["sources"]["cognition"] = "../outside-production.md"
            manifest.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "escapes Production root"):
                build_learning_context(root)

    def test_unknown_current_production_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory)
            with self.assertRaisesRegex(ValueError, "unknown Production"):
                build_learning_context(root, current_production_id="missing")


if __name__ == "__main__":
    unittest.main()
