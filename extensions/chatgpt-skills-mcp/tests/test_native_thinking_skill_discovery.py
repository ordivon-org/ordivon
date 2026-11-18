from __future__ import annotations

import asyncio
import json
import sys
import tempfile
import unittest
from pathlib import Path

OWNER = Path(__file__).resolve().parents[1]
REPO = OWNER.parents[1]
for candidate in (OWNER / "src", OWNER / "scripts"):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from skills_mcp import CatalogProvider, build_server  # noqa: E402


class NativeThinkingSkillDiscoveryTests(unittest.TestCase):
    """Exercise the real project-level Agent Skills consumer, not a mirror registry."""

    METHODS = {
        "evidence-calibrated-dialogue": "Evidence-Calibrated Dialogue",
        "natural-chinese-writing": "Natural Chinese Writing",
        "feedback-grounded-repair": "Feedback-Grounded Repair",
        "research-claim-framing": "Research Claim Framing",
    }

    def test_four_methods_resolve_read_and_remain_scoped(self):
        with tempfile.TemporaryDirectory() as td:
            config = {
                "schemaVersion": 2,
                "ttlMs": 30000,
                "standardDiscovery": {"user": False, "projects": True},
                "workspaces": {"ordivon-thinking": {"path": str(REPO), "trusted": True}},
                "additionalSources": [],
                "compatibilitySources": [],
            }
            path = Path(td) / "skills.json"
            path.write_text(json.dumps(config), encoding="utf-8")
            server = build_server(CatalogProvider(path))
            tools = {tool.name: tool for tool in server._tool_manager.list_tools()}

            global_list = asyncio.run(tools["skills.list"].fn())
            self.assertFalse(global_list.is_error)
            for name in self.METHODS:
                self.assertFalse(
                    any(row["name"] == name for row in global_list.structured_content["skills"]),
                    f"project-local {name} must not leak into global discovery",
                )

            scoped = asyncio.run(tools["skills.list"].fn(workspaceId="ordivon-thinking"))
            self.assertFalse(scoped.is_error, scoped)
            rows = scoped.structured_content["skills"]
            names = {row["name"] for row in rows}
            for name, heading in self.METHODS.items():
                self.assertIn(name, names)
                row = next(item for item in rows if item["name"] == name)
                self.assertEqual(row["scope"], "project")
                self.assertEqual(row["trustState"], "TRUSTED")

                resolved = asyncio.run(
                    tools["skills.resolve"].fn(
                        ref=name, workspaceId="ordivon-thinking", invocationMode="explicit"
                    )
                )
                self.assertFalse(resolved.is_error, resolved)
                value = resolved.structured_content
                resolved_skill = value["resolved"]
                self.assertEqual(resolved_skill["name"], name)

                read = asyncio.run(
                    tools["skills.read"].fn(
                        skillId=resolved_skill["skillId"],
                        workspaceId="ordivon-thinking",
                        expectedInstructionDigest=resolved_skill["instructionDigest"],
                        expectedPackageRevision=resolved_skill["packageRevision"],
                        expectedSnapshotRevision=value["snapshotRevision"],
                    )
                )
                self.assertFalse(read.is_error, read)
                self.assertIn(heading, read.structured_content["content"])
                self.assertIn("Human / Agent contract", read.structured_content["content"])
                self.assertIn("MIT", read.structured_content["content"])


if __name__ == "__main__":
    unittest.main()
