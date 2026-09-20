from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class OccurrenceRuntimeRetirementTests(unittest.TestCase):
    def test_runtime_surface_uses_materialization_and_conversation_capabilities(self) -> None:
        paths = (
            "scripts/agent_automation_mcp.py",
            "scripts/agent_automation_browserless.py",
            "scripts/agent_automation_browserless_effects.py",
            "scripts/campaign_materialization.py",
            "scripts/temporal_agent_automation.py",
            "scripts/temporal_agent_automation_launch.py",
        )
        source = "\n".join((ROOT / path).read_text() for path in paths)
        for retired in (
            'name="occurrence.',
            '"occurrences"',
            '"occurrence"',
            "_occurrence_dir",
            "temporal-occurrence",
            "Occurrence",
            "occurrence ",
        ):
            self.assertNotIn(retired, source)
        mcp = (ROOT / "scripts/agent_automation_mcp.py").read_text()
        for current in (
            'name="materialization.reconcile"',
            'name="materialization.humanHandoff"',
            'name="materialization.humanResume"',
            'name="conversation.continue"',
        ):
            self.assertIn(current, mcp)


class MaterializationStateDirectoryMigrationTests(unittest.TestCase):
    def test_prepare_finalize_atomically_retires_occurrence_state_root(self) -> None:
        import sys
        sys.path.insert(0, str(ROOT / "scripts"))
        import agent_automation_release as release

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            legacy = root / "occurrences"
            nested = legacy / "effect-a" / "turns"
            nested.mkdir(parents=True)
            (nested / "turn.json").write_bytes(b'{"ok":true}\n')
            before = release._state_tree_snapshot(legacy)

            receipt = release.prepare_materialization_state_migration(root)
            current = root / "materializations"
            self.assertFalse(legacy.exists())
            self.assertTrue(current.is_dir())
            self.assertEqual(receipt["standing"], "PREPARED")
            self.assertEqual(receipt["treeDigest"], before["treeDigest"])

            final = release.finalize_materialization_state_migration(receipt)
            self.assertEqual(final["standing"], "FINALIZED")
            self.assertEqual(release._state_tree_snapshot(current), before)

    def test_rollback_restores_legacy_directory_after_candidate_failure(self) -> None:
        import sys
        sys.path.insert(0, str(ROOT / "scripts"))
        import agent_automation_release as release

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            legacy = root / "occurrences"
            legacy.mkdir()
            (legacy / "evidence.json").write_text('{"standing":"unknown"}\n')
            receipt = release.prepare_materialization_state_migration(root)
            release.rollback_materialization_state_migration(receipt)
            self.assertTrue(legacy.is_dir())
            self.assertFalse((root / "materializations").exists())


if __name__ == "__main__":
    unittest.main()
