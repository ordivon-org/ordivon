from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from ordivon_harness.skills.skillspector_adapter import run_skillspector_scan  # noqa: E402


def write_skill(root: Path) -> Path:
    skill = root / "example-skill"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\nname: example-skill\ndescription: Example.\n---\n\n# Example\nSafe procedure.\n",
        encoding="utf-8",
    )
    return skill


def write_fake_scanner(root: Path, *, report: dict | None = None, exit_code: int = 0, raw: str | None = None) -> Path:
    scanner = root / "skillspector"
    payload = raw if raw is not None else json.dumps(report or {})
    scanner.write_text(
        "#!/usr/bin/env python3\n"
        "import sys\n"
        f"sys.stdout.write({payload!r})\n"
        f"raise SystemExit({exit_code})\n",
        encoding="utf-8",
    )
    scanner.chmod(scanner.stat().st_mode | 0o111)
    return scanner


class SkillSpectorAdapterTests(unittest.TestCase):
    def fixture(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        base = Path(td.name)
        return base, write_skill(base)

    def test_clean_complete_report_normalizes_without_granting_trust(self):
        base, skill = self.fixture()
        scanner = write_fake_scanner(
            base,
            report={
                "risk_assessment": {"score": 0, "severity": "LOW", "recommendation": "SAFE", "max_issue_severity": "NONE"},
                "issues": [],
                "metadata": {"skillspector_version": "2.11.2", "llm_requested": False, "llm_available": False},
                "execution_successful": True,
                "analysis_completeness": {"status": "complete", "coverage_percent": 100.0, "is_complete": True},
            },
        )
        evidence = run_skillspector_scan(skill, scanner)
        self.assertEqual(evidence["kind"], "ordivon.skillspector-evidence")
        self.assertEqual(evidence["truthRole"], "scanner-evidence-not-trust-or-authorization")
        self.assertEqual(evidence["assessment"]["evidenceState"], "CLEAN_EVIDENCE")
        self.assertEqual(evidence["scanner"]["processExit"], 0)
        self.assertEqual(evidence["analysis"]["coveragePercent"], 100.0)
        self.assertTrue(evidence["target"]["packageRevision"].startswith("sha256:"))
        self.assertNotIn("trustState", evidence)
        self.assertNotIn("authorized", evidence)

    def test_high_findings_with_exit_one_are_block_signal_not_scanner_error(self):
        base, skill = self.fixture()
        scanner = write_fake_scanner(
            base,
            exit_code=1,
            report={
                "risk_assessment": {"score": 51, "severity": "HIGH", "recommendation": "DO_NOT_INSTALL", "max_issue_severity": "HIGH"},
                "issues": [{"severity": "HIGH", "category": "Prompt Injection"}],
                "metadata": {"skillspector_version": "2.11.2", "llm_requested": False, "llm_available": False},
                "execution_successful": True,
                "analysis_completeness": {"status": "complete", "coverage_percent": 100.0, "is_complete": True},
            },
        )
        evidence = run_skillspector_scan(skill, scanner)
        self.assertEqual(evidence["assessment"]["evidenceState"], "BLOCK_SIGNAL")
        self.assertEqual(evidence["assessment"]["issueCount"], 1)
        self.assertEqual(evidence["scanner"]["processExit"], 1)

    def test_incomplete_report_never_normalizes_as_clean(self):
        base, skill = self.fixture()
        scanner = write_fake_scanner(
            base,
            report={
                "risk_assessment": {"score": 0, "severity": "LOW", "recommendation": "SAFE", "max_issue_severity": "NONE"},
                "issues": [],
                "metadata": {"skillspector_version": "2.11.2", "llm_requested": False, "llm_available": False},
                "execution_successful": True,
                "analysis_completeness": {"status": "partial", "coverage_percent": 100.0, "is_complete": False},
            },
        )
        evidence = run_skillspector_scan(skill, scanner)
        self.assertEqual(evidence["assessment"]["evidenceState"], "INCOMPLETE")
        self.assertFalse(evidence["analysis"]["isComplete"])

    def test_invalid_json_is_explicit_scanner_error(self):
        base, skill = self.fixture()
        scanner = write_fake_scanner(base, raw="not-json", exit_code=0)
        evidence = run_skillspector_scan(skill, scanner)
        self.assertEqual(evidence["assessment"]["evidenceState"], "SCANNER_ERROR")
        self.assertEqual(evidence["scanner"]["processExit"], 0)
        self.assertIn("invalid JSON", evidence["diagnostics"][0])

    def test_exit_two_is_scanner_error_even_with_json(self):
        base, skill = self.fixture()
        scanner = write_fake_scanner(base, report={"error": "bad input"}, exit_code=2)
        evidence = run_skillspector_scan(skill, scanner)
        self.assertEqual(evidence["assessment"]["evidenceState"], "SCANNER_ERROR")
        self.assertEqual(evidence["scanner"]["processExit"], 2)


if __name__ == "__main__":
    unittest.main()
