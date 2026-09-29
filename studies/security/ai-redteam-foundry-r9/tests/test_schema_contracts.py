from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
for path in (ROOT, REPO_ROOT / "studies" / "security" / "ai-redteam-foundry-r1", REPO_ROOT / "studies" / "security" / "ai-redteam-foundry-r8"):
    sys.path.insert(0, str(path))

from foundry.providers import ProviderArtifactRef  # noqa: E402
from foundry_r8 import SearchCandidateRef, SearchResultRef  # noqa: E402
from foundry_r9 import FamilyAssignment, FamilyHypothesis, build_family_ledger, discovery_frontier  # noqa: E402

D = lambda c: "sha256:" + c * 64


class SchemaContractTests(unittest.TestCase):
    def schema(self, name: str) -> dict[str, object]:
        return json.loads((ROOT / "schemas" / name).read_text())

    def assert_exact_top_level(self, schema: dict[str, object], payload: dict[str, object]) -> None:
        self.assertEqual(set(schema["properties"]), set(payload))
        self.assertTrue(set(schema["required"]).issubset(payload))

    def fixture(self):
        artifact = ProviderArtifactRef("p", "v", "fixture", D("1"), 1, "fixture")
        candidate = SearchCandidateRef(D("a"), 1, "p", "v", "run", "case", "surface", "target", D("2"), D("3"), artifact)
        result = SearchResultRef(candidate, "judge", "signal", True, 1.0, None, None, None)
        hypothesis = FamilyHypothesis("hypothesis:1", "mechanism", "synthetic_agent", D("4"), D("5"))
        assignment = FamilyAssignment(result.digest, hypothesis.hypothesis_id, "manual_analysis", "analysis:test", D("6"))
        ledger = build_family_ledger((result,), (hypothesis,), (assignment,))
        frontier = discovery_frontier(D("a"), (result,), (hypothesis,), (assignment,))
        return ledger, frontier

    def test_ledger_schema_matches_serialization(self) -> None:
        ledger, _ = self.fixture()
        self.assert_exact_top_level(self.schema("vulnerability-family-ledger.schema.json"), ledger.to_dict())

    def test_frontier_schema_matches_serialization(self) -> None:
        _, frontier = self.fixture()
        self.assert_exact_top_level(self.schema("discovery-frontier.schema.json"), frontier.to_dict())


if __name__ == "__main__":
    unittest.main()
