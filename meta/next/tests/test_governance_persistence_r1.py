from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_governance_persistence_r1.py"


def _load_checker():
    spec = importlib.util.spec_from_file_location("governance_persistence_r1", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load governance persistence checker")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GovernancePersistenceR1Tests(unittest.TestCase):
    def test_repository_satisfies_persistence_ratchet(self) -> None:
        checker = _load_checker()
        self.assertEqual(checker.audit(), [])

    def test_ratchet_is_explicitly_disposable(self) -> None:
        checker = _load_checker()
        profile = checker.load_json(checker.PROFILE)
        self.assertEqual(
            profile["sunsetCondition"]["kind"],
            "DELETE_RATCHET_WHEN_REDUNDANT",
        )

    def test_r21_source_projection_is_not_retired_planning_engine(self) -> None:
        import json

        checker = _load_checker()
        profile = checker.load_json(checker.PROFILE)
        forbidden = profile["growthRatchets"]["forbiddenLocalPlanningInfrastructure"]
        assert "planning/lego-plan-r1.json" not in forbidden
        assert checker.audit() == []

        for old in (
            "schemas/project-lego-plan-r1.schema.json",
            "scripts/check_project_lego_plan_r1.py",
            ".agents/skills/lego-project-planning",
            ".agents/skills/lego-question-compiler",
        ):
            assert old in forbidden
            assert not (ROOT / old).exists()

        replacement = profile["sourceProjectionReplacement"]
        assert replacement["current"] == "planning/lego-plan-r1.json"
        plan = json.loads((ROOT / replacement["current"]).read_text())
        assert plan["kind"] == replacement["kind"]
        assert plan["truthRole"] == "planning-projection-not-project-truth"
        for node in plan["nodes"]:
            for key in (
                "id",
                "responsibility",
                "inputs",
                "outputs",
                "behavioralContract",
                "acceptance",
                "consumerBindings",
            ):
                assert node.get(key), (node.get("id"), key)

    def test_retired_local_method_infrastructure_stays_absent(self) -> None:
        checker = _load_checker()
        profile = checker.load_json(checker.PROFILE)
        retired = profile["growthRatchets"]["forbiddenLocalMethodInfrastructure"]
        self.assertTrue(retired)
        for relative in retired:
            self.assertFalse((ROOT / relative).exists(), relative)


if __name__ == "__main__":
    unittest.main()
