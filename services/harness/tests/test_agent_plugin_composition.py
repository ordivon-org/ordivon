from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from anc_canonical import canonical_digest

from ordivon_harness.agent_plugin import (
    AgentPluginComposition,
    AgentPluginCompositionError,
)
from ordivon_harness.ordivon.model import AgentToolCall
from ordivon_harness.plugin_mcp import PluginMcpObservationBridge


class FakeMcpClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []
        self.omit: set[str] = set()

    def list_tools(self):
        def tool(name: str):
            return {
                "name": name,
                "description": name,
                "inputSchema": {"type": "object", "additionalProperties": True},
            }

        return tuple(
            tool(name)
            for name in (
                "system.describe",
                "capability.describe",
                "execution.submit",
                "execution.get",
                "execution.cancel",
                "artifact.read",
                "continuity.get",
                "continuity.list",
            )
            if name not in self.omit
        )

    def call_tool(self, name, arguments):
        self.calls.append((name, dict(arguments)))
        return False, {"tool": name, "arguments": dict(arguments)}


def write_plugin(root: Path) -> None:
    (root / "plugin.json").write_text(
        json.dumps(
            {
                "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
                "name": "ordivon-control-plane",
                "version": "0.2.0",
                "description": "fixture",
                "homepage": "https://ordivon.com",
            }
        ),
        encoding="utf-8",
    )
    (root / "mcp.json").write_text(
        json.dumps(
            {
                "$schema": "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json",
                "mcpServers": {
                    "ordivon-gateway": {
                        "type": "streamable-http",
                        "url": "https://gateway-mcp.ordivon.com/mcp",
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    skill = root / "skills" / "method-router"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\nname: method-router\n---\nUse the smallest useful method set.\n",
        encoding="utf-8",
    )


class AgentPluginCompositionTests(unittest.TestCase):
    def test_loads_standard_plugin_without_claiming_authority(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_plugin(root)
            value = AgentPluginComposition.load(root)
            self.assertEqual(value.name, "ordivon-control-plane")
            self.assertEqual(value.version, "0.2.0")
            self.assertEqual([item.name for item in value.mcp_components], ["ordivon-gateway"])
            self.assertEqual([item.name for item in value.skill_components], ["method-router"])
            projected = value.to_dict()
            self.assertEqual(projected["truthRole"], "derived-portable-composition-projection")
            self.assertIn("grants no Tool", projected["authorityBoundary"])

    def test_skill_projection_is_exact_and_advisory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_plugin(root)
            value = AgentPluginComposition.load(root)
            skill = value.skill("method-router")
            source = skill.to_working_view_source()
            self.assertEqual(source.logical_generation, skill.content_digest)
            self.assertIn("grants no Tool", source.messages[0]["content"])
            self.assertIn("Use the smallest useful method set.", source.messages[0]["content"])
            (root / "skills" / "method-router" / "SKILL.md").write_text(
                "drifted\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(AgentPluginCompositionError, "drifted"):
                skill.to_working_view_source()

    def test_rejects_non_https_or_extended_mcp_definition(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_plugin(root)
            mcp = json.loads((root / "mcp.json").read_text())
            mcp["mcpServers"]["ordivon-gateway"]["url"] = "http://example.test/mcp"
            (root / "mcp.json").write_text(json.dumps(mcp))
            with self.assertRaisesRegex(AgentPluginCompositionError, "canonical HTTPS"):
                AgentPluginComposition.load(root)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_plugin(root)
            mcp = json.loads((root / "mcp.json").read_text())
            mcp["mcpServers"]["ordivon-gateway"]["headers"] = {"Authorization": "secret"}
            (root / "mcp.json").write_text(json.dumps(mcp))
            with self.assertRaisesRegex(AgentPluginCompositionError, "does not admit fields"):
                AgentPluginComposition.load(root)

    def test_observation_bridge_filters_effectful_gateway_tools(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_plugin(root)
            plugin = AgentPluginComposition.load(root)
            client = FakeMcpClient()
            bridge = PluginMcpObservationBridge(plugin.mcp("ordivon-gateway"), client)
            names = tuple(item.name for item in bridge.definitions())
            self.assertEqual(
                names,
                (
                    "capability.describe",
                    "continuity.get",
                    "continuity.list",
                    "system.describe",
                ),
            )
            self.assertNotIn("execution.submit", names)
            self.assertNotIn("execution.cancel", names)
            self.assertEqual(
                bridge.catalog_digest,
                canonical_digest(
                    {
                        "schemaVersion": 1,
                        "kind": "ordivon.plugin-mcp-observation-tool-surface",
                        "component": plugin.mcp("ordivon-gateway").to_dict(),
                        "tools": [item.to_dict() for item in bridge.definitions()],
                    }
                ),
            )

    def test_observation_bridge_detects_catalog_drift(self) -> None:
        from ordivon_harness.ordivon.tool_errors import ToolBridgeError

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_plugin(root)
            plugin = AgentPluginComposition.load(root)
            client = FakeMcpClient()
            bridge = PluginMcpObservationBridge(
                plugin.mcp("ordivon-gateway"),
                client,
                allowed_tools=("system.describe",),
            )
            bridge.validate_runtime_catalog()
            client.omit.add("system.describe")
            with self.assertRaisesRegex(ToolBridgeError, "catalog drifted"):
                bridge.validate_runtime_catalog()

    def test_observation_bridge_restores_model_tool_messages(self) -> None:
        from ordivon_harness.agent_tool_observation import HarnessToolObservation

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_plugin(root)
            plugin = AgentPluginComposition.load(root)
            bridge = PluginMcpObservationBridge(
                plugin.mcp("ordivon-gateway"),
                FakeMcpClient(),
                allowed_tools=("system.describe",),
            )
            observation = HarnessToolObservation(
                tool_call_id="tool-call:restore:1",
                tool_name="system.describe",
                status="observed",
                structured_content={"ok": True},
            )
            restored = bridge.restore_current_attempt_tool_exchanges((observation,))
            self.assertEqual(len(restored), 1)
            self.assertEqual(restored[0]["role"], "tool")
            self.assertEqual(restored[0]["name"], "system.describe")
            self.assertEqual(restored[0]["observation"]["content"], {"ok": True})

    def test_observation_bridge_calls_only_granted_tool(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_plugin(root)
            plugin = AgentPluginComposition.load(root)
            client = FakeMcpClient()
            bridge = PluginMcpObservationBridge(
                plugin.mcp("ordivon-gateway"),
                client,
                allowed_tools=("system.describe",),
            )
            observed = bridge.execute(
                AgentToolCall(
                    tool_call_id="tool-call:plugin:1",
                    name="system.describe",
                    arguments={},
                ),
                step_id="tool-step:1",
            )
            self.assertEqual(observed.status, "observed")
            self.assertEqual(client.calls, [("system.describe", {})])
            with self.assertRaisesRegex(ValueError, "refuses effectful"):
                PluginMcpObservationBridge(
                    plugin.mcp("ordivon-gateway"),
                    client,
                    allowed_tools=("execution.submit",),
                )


if __name__ == "__main__":
    unittest.main()
