from __future__ import annotations

import ast
from pathlib import Path
import unittest

from ordivon_harness import api
from tests.test_public_api import EXPECTED_API as PUBLIC_TEST_API

ROOT = Path(__file__).resolve().parents[1]
RETIRED_LOOP_DRIVER_EXPORTS = {
    "HarnessLoopDriverRef",
    "DELIBERATE_THEN_ACT_LOOP_DRIVER",
    "SEQUENTIAL_LOOP_DRIVER",
}
RETIRED_MANDATE_EXPORTS = {
    "CompiledHarnessAttempt",
    "HarnessExecutionMandate",
    "HarnessMandateConsumption",
    "HarnessExecutionProfile",
    "HarnessExecutionStrategy",
    "compile_harness_attempt",
}
RETIRED_STRATEGY_SELECTION_EXPORTS = {
    "HarnessAgentStrategySelection",
    "HarnessPriorAttemptEvidence",
    "HarnessStrategyEvidence",
    "HarnessStrategySelectionContext",
    "admit_harness_agent_strategy",
    "build_harness_strategy_selection_context",
    "compile_harness_selected_attempt",
    "derive_harness_mandate_consumption",
}
RETIRED_CLAIM_STANDING_EXPORTS = {
    "OperationalClaimEvidenceRole",
    "OperationalClaimRef",
    "OperationalClaimStandingView",
    "project_operational_claim_standing_view",
}


def _literal_set(path: Path, name: str) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(target, ast.Name) and target.id == name for target in targets):
                value = ast.literal_eval(node.value)
                return set(value)
    raise AssertionError(f"{name} not found in {path}")


class WheelPublicApiContractTests(unittest.TestCase):
    def test_all_existing_public_api_projections_agree(self) -> None:
        source = set(api.__all__)
        docs = _literal_set(ROOT / "scripts" / "check_docs.py", "STABLE_API")
        wheel = _literal_set(ROOT / "scripts" / "check_wheel.py", "EXPECTED_API")
        self.assertEqual(source, set(PUBLIC_TEST_API))
        self.assertEqual(source, docs)
        self.assertEqual(source, wheel)

    def test_extracted_skills_namespace_is_forbidden_from_harness_wheel(self) -> None:
        prefixes = _literal_set(ROOT / "scripts" / "check_wheel.py", "FORBIDDEN_PREFIXES")
        self.assertEqual(prefixes, {"ordivon_harness/skills/"})

    def test_retired_loop_driver_exports_do_not_resurrect(self) -> None:
        projections = (
            set(api.__all__),
            set(PUBLIC_TEST_API),
            _literal_set(ROOT / "scripts" / "check_docs.py", "STABLE_API"),
            _literal_set(ROOT / "scripts" / "check_wheel.py", "EXPECTED_API"),
        )
        for projection in projections:
            self.assertTrue(RETIRED_LOOP_DRIVER_EXPORTS.isdisjoint(projection))

    def test_retired_mandate_exports_do_not_resurrect(self) -> None:
        projections = (
            set(api.__all__),
            set(PUBLIC_TEST_API),
            _literal_set(ROOT / "scripts" / "check_docs.py", "STABLE_API"),
            _literal_set(ROOT / "scripts" / "check_wheel.py", "EXPECTED_API"),
        )
        for projection in projections:
            self.assertTrue(RETIRED_MANDATE_EXPORTS.isdisjoint(projection))

    def test_retired_strategy_selection_exports_do_not_resurrect(self) -> None:
        projections = (
            set(api.__all__),
            set(PUBLIC_TEST_API),
            _literal_set(ROOT / "scripts" / "check_docs.py", "STABLE_API"),
            _literal_set(ROOT / "scripts" / "check_wheel.py", "EXPECTED_API"),
        )
        for projection in projections:
            self.assertTrue(RETIRED_STRATEGY_SELECTION_EXPORTS.isdisjoint(projection))

    def test_retired_claim_standing_exports_do_not_resurrect(self) -> None:
        source = set(api.__all__)
        self.assertTrue(RETIRED_CLAIM_STANDING_EXPORTS.isdisjoint(source))
        self.assertTrue(RETIRED_CLAIM_STANDING_EXPORTS.isdisjoint(set(PUBLIC_TEST_API)))
        self.assertTrue(
            RETIRED_CLAIM_STANDING_EXPORTS.isdisjoint(
                _literal_set(ROOT / "scripts" / "check_docs.py", "STABLE_API")
            )
        )
        self.assertTrue(
            RETIRED_CLAIM_STANDING_EXPORTS.isdisjoint(
                _literal_set(ROOT / "scripts" / "check_wheel.py", "EXPECTED_API")
            )
        )


if __name__ == "__main__":
    unittest.main()
