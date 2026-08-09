import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTEXT = ROOT / "research" / "expression" / "context.json"
SOURCES = ROOT / "research" / "expression" / "sources.json"


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
        self.assertNotIn("mediumProfiles", data)
        self.assertNotIn("agentLoop", data)
        self.assertIn("local_experiment", data["evidenceClasses"])
        creative = data["creativeSystem"]
        self.assertEqual(creative["authority"], "research/expression/creative-system.md")
        self.assertEqual(creative["coreLoop"], ["frame", "bind", "express", "render", "audit", "decide"])
        self.assertEqual(creative["protocolAuthority"], "research/expression/protocol.md")
        self.assertEqual(creative["knowledgeModel"], "research/expression/knowledge-model.md")
        self.assertIn("medium", creative["variableProfiles"])
        self.assertIn("encounter-mode", creative["variableProfiles"])
        self.assertEqual(creative["learningPromotion"][0], "artifact-local")
        self.assertIn("human experience", creative["twoSpeedLearning"]["boundary"])

        expected_layers = {"hard_constraint", "durable_prior", "medium_prior", "context_signal", "local_observation"}
        self.assertEqual(set(data["knowledgeLayers"]), expected_layers)
        profile_registry = ROOT / data["profileRegistry"]
        self.assertTrue(profile_registry.is_file())
        profiles = json.loads(profile_registry.read_text(encoding="utf-8"))
        for required in ("web", "film-video", "still-graphic", "article-essay", "audio-music", "interactive"):
            self.assertIn(required, profiles["profiles"])
            self.assertTrue(profiles["profiles"][required]["constraints"])

    def test_aesthetic_dimensions_and_sources_are_consistent(self) -> None:
        data = json.loads(CONTEXT.read_text(encoding="utf-8"))
        sources = json.loads(SOURCES.read_text(encoding="utf-8"))

        dimensions = {item["id"] for item in data["aestheticDimensions"]}
        tensions = {item["id"] for item in data["tensions"]}
        self.assertGreaterEqual(len(dimensions), 8)
        self.assertEqual(len(dimensions), len(data["aestheticDimensions"]))
        self.assertEqual(data["sourceLedger"], "research/expression/sources.json")
        self.assertEqual(len(data["causalLayers"]), len(set(data["causalLayers"])))

        known_concepts = dimensions | tensions | {"comparative-judgment"}
        source_ids = [item["id"] for item in sources["sources"]]
        self.assertEqual(len(source_ids), len(set(source_ids)))
        for source in sources["sources"]:
            self.assertIn(source["evidenceClass"], data["evidenceClasses"])
            self.assertTrue(source.get("doi") or source.get("arxiv"))
            self.assertTrue(source["concepts"])
            self.assertTrue(set(source["concepts"]).issubset(known_concepts))


if __name__ == "__main__":
    unittest.main()
