from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "materialize_agent_plugin.py"
SPEC = importlib.util.spec_from_file_location("materialize_agent_plugin", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class AgentPluginMaterializationTests(unittest.TestCase):
    def _plugin(self, root: Path) -> Path:
        plugin = root / "plugin"
        plugin.mkdir()
        (plugin / "plugin.json").write_text(
            json.dumps({"$schema": MODULE.PLUGIN_SCHEMA, "name": "test", "version": "1.0.0"}),
            encoding="utf-8",
        )
        (plugin / "mcp.json").write_text(
            json.dumps({"$schema": MODULE.MCP_SCHEMA, "mcpServers": {}}), encoding="utf-8"
        )
        return plugin

    def _skills(self, root: Path) -> Path:
        skills = root / "skills-source"
        (skills / "alpha" / "references").mkdir(parents=True)
        (skills / "alpha" / "SKILL.md").write_text("---\nname: alpha\ndescription: alpha skill\n---\n", encoding="utf-8")
        (skills / "alpha" / "references" / "one.md").write_text("one\n", encoding="utf-8")
        (skills / "beta").mkdir()
        (skills / "beta" / "SKILL.md").write_text("---\nname: beta\ndescription: beta skill\n---\n", encoding="utf-8")
        return skills

    def test_omits_skills_unless_explicitly_composed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plugin = self._plugin(root)
            output = root / "release" / "test-plugin"
            receipt = root / "receipts" / "test-plugin.json"
            value = MODULE.materialize(plugin, None, output, receipt)
            self.assertEqual(value["skillComposition"], "omitted")
            self.assertEqual(value["skillCount"], 0)
            self.assertIsNone(value["sourceOfTruth"])
            self.assertIsNone(value["skillSource"])
            self.assertFalse((output / "skills").exists())
            self.assertEqual(json.loads(receipt.read_text(encoding="utf-8"))["outputTreeDigest"], MODULE.tree_digest(output))

    def test_cli_defaults_to_omitting_skills_and_requires_explicit_opt_in(self) -> None:
        with patch("sys.argv", ["materialize_agent_plugin.py", "--output", "/tmp/plugin"]):
            args = MODULE.parse_args()
            self.assertFalse(args.include_skills)
        with patch(
            "sys.argv",
            ["materialize_agent_plugin.py", "--output", "/tmp/plugin", "--include-skills"],
        ):
            args = MODULE.parse_args()
            self.assertTrue(args.include_skills)

    def test_materializes_skills_without_receipt_inside_plugin(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plugin = self._plugin(root)
            skills = self._skills(root)
            output = root / "release" / "test-plugin"
            receipt = root / "receipts" / "test-plugin.json"
            value = MODULE.materialize(plugin, skills, output, receipt)
            self.assertEqual(value["skillComposition"], "included")
            self.assertEqual(value["skillCount"], 2)
            self.assertTrue((output / "skills" / "alpha" / "SKILL.md").is_file())
            self.assertTrue((output / "skills" / "alpha" / "references" / "one.md").is_file())
            self.assertTrue((output / "skills" / "beta" / "SKILL.md").is_file())
            self.assertFalse((output / "receipt.json").exists())
            self.assertEqual(json.loads(receipt.read_text(encoding="utf-8"))["outputTreeDigest"], MODULE.tree_digest(output))

    def test_repeated_materialization_is_byte_stable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plugin = self._plugin(root)
            skills = self._skills(root)
            first = MODULE.materialize(plugin, skills, root / "release-a", root / "receipt-a.json")
            second = MODULE.materialize(plugin, skills, root / "release-b", root / "receipt-b.json")
            self.assertEqual(first["outputTreeDigest"], second["outputTreeDigest"])
            self.assertEqual(MODULE.tree_manifest(root / "release-a"), MODULE.tree_manifest(root / "release-b"))

    def test_refuses_receipt_inside_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plugin = self._plugin(root)
            skills = self._skills(root)
            output = root / "release"
            with self.assertRaises(SystemExit):
                MODULE.materialize(plugin, skills, output, output / "receipt.json")

    def test_refuses_existing_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plugin = self._plugin(root)
            skills = self._skills(root)
            output = root / "release"
            output.mkdir()
            with self.assertRaises(SystemExit):
                MODULE.materialize(plugin, skills, output, root / "receipt.json")

    def test_refuses_skill_without_skill_md(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plugin = self._plugin(root)
            skills = self._skills(root)
            (skills / "broken").mkdir()
            with self.assertRaises(SystemExit):
                MODULE.materialize(plugin, skills, root / "release", root / "receipt.json")

    def test_refuses_symlink_in_skill_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plugin = self._plugin(root)
            skills = self._skills(root)
            (skills / "alpha" / "escape").symlink_to(root / "outside")
            with self.assertRaises(SystemExit):
                MODULE.materialize(plugin, skills, root / "release", root / "receipt.json")

    def test_refuses_source_plugin_with_skills_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plugin = self._plugin(root)
            skills = self._skills(root)
            (plugin / "skills").mkdir()
            (plugin / "skills" / "unexpected.txt").write_text("duplicate source\n", encoding="utf-8")
            with self.assertRaises(SystemExit):
                MODULE.materialize(plugin, skills, root / "release", root / "receipt.json")


if __name__ == "__main__":
    unittest.main()
