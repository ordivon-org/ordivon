from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/check_adaptive_edit_r2_benchmark.py"
spec = importlib.util.spec_from_file_location("adaptive_edit_r2_benchmark", SCRIPT)
assert spec and spec.loader
benchmark = importlib.util.module_from_spec(spec)
spec.loader.exec_module(benchmark)


class AdaptiveEditR2BenchmarkTests(unittest.TestCase):
    def test_all_predeclared_mechanical_checks_pass(self) -> None:
        report = benchmark.build_report()
        self.assertTrue(report["allChecksPassed"])
        self.assertTrue(all(report["checks"].values()))
        self.assertIn("mechanical ACI benchmark only", report["scope"])

    def test_repository_repair_codecs_lower_to_same_runtime_patch(self) -> None:
        case = benchmark.repository_repair_case()
        self.assertTrue(case["exactReplacement"]["matchesTarget"])
        self.assertTrue(case["anchoredLine"]["matchesTarget"])
        self.assertTrue(case["sameRuntimePatch"])

    def test_adaptive_choice_has_a_real_mechanical_reason(self) -> None:
        case = benchmark.duplicate_text_case()
        self.assertFalse(case["exactReplacement"]["compiled"])
        self.assertTrue(case["exactReplacement"]["expectedFailure"])
        self.assertTrue(case["anchoredLine"]["matchesTarget"])


if __name__ == "__main__":
    unittest.main()
