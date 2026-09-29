from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "agent-plugins-1.0.0"
PLUGIN = ROOT / "plugins" / "ordivon-skills-bridge"


class AgentPluginsConformanceTests(unittest.TestCase):
    def test_vendored_schema_bytes_match_recorded_official_hashes(self) -> None:
        provenance = json.loads((FIXTURE / "PROVENANCE.json").read_text(encoding="utf-8"))
        for name, row in provenance["schemas"].items():
            digest = hashlib.sha256((FIXTURE / name).read_bytes()).hexdigest()
            self.assertEqual(digest, row["sha256"])

    def test_bridge_plugin_manifest_conforms_to_agent_plugins_1_0(self) -> None:
        schema = json.loads((FIXTURE / "plugin.schema.json").read_text(encoding="utf-8"))
        instance = json.loads((PLUGIN / "plugin.json").read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(schema).validate(instance)
        self.assertEqual(instance["$schema"], "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json")

    def test_bridge_mcp_config_conforms_and_contains_no_portable_secret(self) -> None:
        schema = json.loads((FIXTURE / "mcp.schema.json").read_text(encoding="utf-8"))
        instance = json.loads((PLUGIN / "mcp.json").read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(schema).validate(instance)
        server = instance["mcpServers"]["skills"]
        self.assertEqual(server["type"], "streamable-http")
        self.assertEqual(server["url"], "https://skills-mcp.ordivon.com/mcp")
        self.assertNotIn("headers", server)

    def test_portable_plugin_has_only_standard_core_component_locations(self) -> None:
        names = {path.name for path in PLUGIN.iterdir()}
        self.assertEqual(names, {"plugin.json", "mcp.json"})


if __name__ == "__main__":
    unittest.main()
