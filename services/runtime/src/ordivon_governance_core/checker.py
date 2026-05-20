"""BaseChecker — minimal SDK for Ordivon governance checkers.

New checkers inherit from BaseChecker. Existing 40 checkers remain independent.

Usage:
    class MyChecker(BaseChecker):
        name = "my-checker"
        event_classes = ["E2_governance_artifact"]

        def check(self) -> GovernanceResult:
            result = self.new_result()
            # ... scan logic ...
            return result
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from ordivon_governance_core.result import GovernanceResult


class BaseChecker:
    """Minimal base class for governance checkers."""

    name: str = "base-checker"
    description: str = ""
    event_classes: list[str] = []  # E2_governance_artifact, E4_debt_lifecycle, etc.
    required_fixtures: list[str] = []

    def __init__(self, repo_root: Optional[Path] = None):
        self.repo_root = repo_root or Path(__file__).resolve().parents[2] if "__file__" in dir() else Path.cwd()

    def new_result(self, status: str = "PASS") -> GovernanceResult:
        """Create a GovernanceResult with checker name preset."""
        return GovernanceResult(tool=self.name, status=status)

    def check(self) -> GovernanceResult:
        """Override this. Return a GovernanceResult with findings."""
        raise NotImplementedError(f"{self.name}.check() must be implemented")

    def run(self) -> int:
        """Run the checker and exit with appropriate code."""
        result = self.check()
        result.emit()
        return result.exit()

    def load_fixture(self, name: str) -> dict:
        """Load a JSON fixture from the checker's fixture directory."""
        import json

        fixture_dir = self.repo_root / "tests" / "fixtures" / self.name
        path = fixture_dir / name
        if path.exists():
            return json.loads(path.read_text())
        raise FileNotFoundError(f"Fixture not found: {path}")

    @classmethod
    def register(cls):
        """Register this checker. Override for custom registration logic."""
        pass
