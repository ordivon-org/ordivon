import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTEXT = ROOT / "research" / "expression" / "context.json"


class ExpressionContextTests(unittest.TestCase):
    def test_expression_context_is_agent_usable(self) -> None:
        data = json.loads(CONTEXT.read_text(encoding="utf-8"))
        self.assertEqual(data["schemaVersion"], 1)
        self.assertEqual(data["id"], "studio.expression-context")
        self.assertGreaterEqual(len(data["outcomes"]), 8)
        self.assertGreaterEqual(len(data["tensions"]), 6)
        self.assertEqual(len({item["id"] for item in data["tensions"]}), len(data["tensions"]))
        for item in data["tensions"]:
            self.assertTrue(item["a"])
            self.assertTrue(item["b"])
            self.assertNotEqual(item["a"], item["b"])
            self.assertTrue(item["prior"])
        for required in ("web", "film-video", "still-graphic", "article-essay", "audio-music", "interactive"):
            self.assertIn(required, data["mediumProfiles"])
            profile = data["mediumProfiles"][required]
            self.assertTrue(profile["primaryOutcomes"])
            self.assertTrue(profile["constraints"])
        self.assertIn("local_experiment", data["evidenceClasses"])
        self.assertIn("calibrate-only-where-uncertain", data["agentLoop"])


if __name__ == "__main__":
    unittest.main()
