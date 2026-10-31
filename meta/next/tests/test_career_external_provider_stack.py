from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RANKING = ROOT / "meta/next/evidence/career/github-career-provider-ranking-20261031.json"
STACK = ROOT / "meta/next/planning/career-external-provider-stack-r1.json"
PLUGIN = ROOT / "extensions/ordivon-career-discovery"
MCP_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"
PLUGIN_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


class CareerExternalProviderStackTest(unittest.TestCase):
    def test_ranking_is_unique_descending_and_current_selection_is_maintained(self) -> None:
        doc = load(RANKING)
        rows = doc["providers"]
        self.assertEqual(doc["observedAtDate"], "2026-10-31")
        self.assertEqual(len(rows), len({row["repository"] for row in rows}))
        self.assertEqual(rows, sorted(rows, key=lambda row: row["stars"], reverse=True))

        by_repo = {row["repository"]: row for row in rows}
        for repo in (
            "career-ops-hq/career-ops",
            "reactive-resume/reactive-resume",
            "srbhr/Resume-Matcher",
            "speedyapply/JobSpy",
        ):
            row = by_repo[repo]
            self.assertFalse(row["archived"], repo)
            self.assertIn(row["license"], {"MIT", "Apache-2.0"}, repo)
            self.assertGreater(row["commits30d"], 0, repo)

        self.assertEqual(
            by_repo["xitanggg/open-resume"]["decision"],
            "NO_NEW_ADOPTION_STALE",
        )
        self.assertEqual(by_repo["xitanggg/open-resume"]["commits90d"], 0)

    def test_stack_reuses_external_owners_without_creating_a_career_runtime(self) -> None:
        stack = load(STACK)
        self.assertTrue(stack["constraints"]["reuseBeforeBuild"])
        self.assertTrue(stack["constraints"]["noCareerRuntime"])
        self.assertTrue(stack["constraints"]["noSecondGlobalRegistry"])
        self.assertTrue(stack["constraints"]["irreversibleEffectsRequireHumanApproval"])
        self.assertTrue(stack["constraints"]["providerCaseStateIsNotExternalTruth"])

        by_id = {layer["id"]: layer for layer in stack["layers"]}
        self.assertEqual(by_id["workflow"]["primary"], "career-ops-hq/career-ops")
        self.assertEqual(
            by_id["product-surface"]["primary"],
            "reactive-resume/reactive-resume",
        )
        self.assertEqual(
            by_id["artifact-compiler"]["primary"],
            "srbhr/Resume-Matcher",
        )
        self.assertEqual(by_id["job-discovery-fallback"]["pin"], "1.4.1")
        self.assertEqual(
            by_id["job-discovery-fallback"]["standing"],
            "SMOKE_VERIFIED_PLUGIN_CANDIDATE",
        )

    def test_jobspy_agent_plugin_is_pinned_and_secret_free(self) -> None:
        plugin = load(PLUGIN / "plugin.json")
        mcp = load(PLUGIN / "mcp.json")
        self.assertEqual(plugin["$schema"], PLUGIN_SCHEMA)
        self.assertEqual(mcp["$schema"], MCP_SCHEMA)
        self.assertEqual(set(mcp["mcpServers"]), {"jobspy"})
        server = mcp["mcpServers"]["jobspy"]
        self.assertEqual(server["type"], "stdio")
        self.assertEqual(server["command"], "uvx")
        self.assertEqual(
            server["args"],
            ["--from", "python-jobspy[mcp]==1.4.1", "mcp-jobspy"],
        )
        self.assertNotIn("@latest", json.dumps(mcp))
        self.assertNotIn("env", server)


if __name__ == "__main__":
    unittest.main()
