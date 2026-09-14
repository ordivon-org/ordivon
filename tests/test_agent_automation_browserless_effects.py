from __future__ import annotations
import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class WorkerOnlyEffectAdapterContractTests(unittest.TestCase):
    def test_effect_adapter_is_not_imported_by_public_entrypoints(self):
        for owner in ("agent_automation_mcp.py", "agent_automation_browserless.py"):
            self.assertNotIn(
                "agent_automation_browserless_effects",
                (ROOT / "scripts" / owner).read_text(),
                owner,
            )
        self.assertIn(
            "agent_automation_browserless_effects",
            (ROOT / "scripts/temporal_agent_automation.py").read_text(),
        )

    def test_public_facade_has_no_raw_effect_methods(self):
        tree = ast.parse((ROOT / "scripts/agent_automation_browserless.py").read_text())
        cls = next(
            n
            for n in tree.body
            if isinstance(n, ast.ClassDef) and n.name == "BrowserlessAutomationService"
        )
        methods = {
            n.name for n in cls.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        self.assertFalse(
            methods
            & {
                "birth",
                "reconcile",
                "continue_occurrence",
                "materialize_birth",
                "reconcile_birth",
                "send_turn",
            }
        )


if __name__ == "__main__":
    unittest.main()
