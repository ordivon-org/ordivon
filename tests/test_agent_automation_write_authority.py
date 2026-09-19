from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


class AgentAutomationWriteAuthorityTests(unittest.TestCase):
    def test_raw_provider_effect_adapter_calls_are_temporal_activity_only(self):
        pattern = re.compile(
            r"\b(?:effects|_effects\(\))\.(materialize|reconcile|send_turn)\("
        )
        hits = []
        for path in sorted(SCRIPTS.glob("*.py")):
            for lineno, line in enumerate(path.read_text().splitlines(), 1):
                if pattern.search(line):
                    hits.append((path.name, lineno, line.strip()))
        self.assertEqual([x[0] for x in hits], ["temporal_agent_automation.py"] * 3, hits)
        self.assertEqual(
            [re.search(pattern, x[2]).group(1) for x in hits],
            ["materialize", "reconcile", "send_turn"],
        )

    def test_public_browserless_facade_has_no_raw_provider_writer_methods(self):
        def methods(path: Path, class_name: str) -> set[str]:
            tree = ast.parse(path.read_text())
            cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name)
            return {
                n.name for n in cls.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            }

        public = methods(
            SCRIPTS / "agent_automation_browserless.py", "BrowserlessAutomationService"
        )
        raw = {
            "birth",
            "reconcile",
            "continue_occurrence",
            "materialize",
            "reconcile",
            "send_turn",
        }
        self.assertFalse(public & raw, public & raw)
        effects = methods(
            SCRIPTS / "agent_automation_browserless_effects.py", "BrowserlessEffectAdapter"
        )
        self.assertTrue({"materialize", "reconcile", "send_turn"} <= effects)

    def test_mcp_and_cli_provider_effect_actions_are_temporal_admissions(self):
        mcp = (SCRIPTS / "agent_automation_mcp.py").read_text()
        facade = (SCRIPTS / "agent_automation_browserless.py").read_text()
        for direct in (
            "_invoke(service.birth",
            "_invoke(service.reconcile",
            "_invoke(service.continue_occurrence",
            "_invoke(current_service().birth",
            "_invoke(current_service().reconcile",
            "_invoke(current_service().continue_occurrence",
        ):
            self.assertNotIn(direct, mcp)
        for admitted in (
            "current_service().launch_reconcile",
            "current_service().launch_continue",
        ):
            self.assertIn(admitted, mcp)
        self.assertNotIn('a.action == "birth":', facade)
        self.assertNotIn('r = svc.launch_occurrence(a.spec, a.agent_id)', facade)
        self.assertIn('a.action == "reconcile":', facade)
        self.assertIn('r = svc.launch_reconcile(a.spec, a.agent_id)', facade)
        self.assertIn('a.action == "continue":', facade)
        self.assertIn('r = svc.launch_continue(', facade)
        self.assertNotRegex(
            facade,
            r'a\.action=="(?:birth|reconcile|continue)".*svc\.(?:birth|reconcile|continue_occurrence)\(',
        )

    def test_birth_ledger_mutator_is_single_materializer_module(self):
        tokens = ("INSERT INTO requests", "UPDATE requests")
        writers = []
        for path in sorted(SCRIPTS.glob("*.py")):
            text = path.read_text()
            if any(token in text for token in tokens):
                writers.append(path.name)
        self.assertEqual(writers, ["sqlite_conversation_materializer.py"])

    def test_turn_ledger_mutator_is_single_provider_effect_script(self):
        tokens = ("INSERT INTO turn_effects", "UPDATE turn_effects")
        writers = []
        for path in sorted(SCRIPTS.glob("*.py")):
            text = path.read_text()
            if any(token in text for token in tokens):
                writers.append(path.name)
        self.assertEqual(writers, ["playwright_browserless_turn_once.py"])

    def test_browserless_materialization_target_has_one_constructor_owner(self):
        hits = []
        for path in sorted(SCRIPTS.glob("*.py")):
            text = path.read_text()
            # Ignore the class definition itself; count instantiation syntax only.
            if (
                path.name != "browserless_materialization_target.py"
                and "BrowserlessMaterializationTarget(" in text
            ):
                hits.append(path.name)
        self.assertEqual(hits, ["agent_automation_browserless_effects.py"])

    def test_provider_send_scripts_are_not_invoked_by_mcp_cli_or_local_bridge(self):
        forbidden = (
            "playwright_browserless_chatgpt_submit.py",
            "playwright_browserless_turn_once.py",
            "playwright_browserless_binding_reconcile.py",
        )
        for owner in ("agent_automation_mcp.py",):
            text = (SCRIPTS / owner).read_text()
            for script in forbidden:
                self.assertNotIn(script, text, (owner, script))


if __name__ == "__main__":
    unittest.main()
