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

    def test_retired_local_method_infrastructure_stays_absent(self) -> None:
        checker = _load_checker()
        profile = checker.load_json(checker.PROFILE)
        retired = profile["growthRatchets"]["forbiddenLocalMethodInfrastructure"]
        self.assertTrue(retired)
        for relative in retired:
            self.assertFalse((ROOT / relative).exists(), relative)


if __name__ == "__main__":
    unittest.main()
