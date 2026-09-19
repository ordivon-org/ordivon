from __future__ import annotations

import unittest
from pathlib import Path

from agent_service import slice1

ROOT = Path(__file__).resolve().parents[1]


class BirthCoordinatorEliminationR24Tests(unittest.TestCase):
    def test_birth_coordinator_class_and_double_facade_are_deleted(self) -> None:
        self.assertFalse(hasattr(slice1, "BirthCoordinator"))
        self.assertFalse(hasattr(slice1, "AgentServiceSlice1"))
        source = (ROOT / "agent_service" / "slice1.py").read_text(encoding="utf-8")
        self.assertNotIn("self.birth = BirthCoordinator", source)

    def test_old_double_birth_call_shape_is_absent(self) -> None:
        old_shape = "." + "birth.birth" + "("
        for base in ("agent_service", "tests", "scripts"):
            for path in (ROOT / base).rglob("*.py"):
                self.assertNotIn(old_shape, path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
