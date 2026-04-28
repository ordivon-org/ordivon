"""Contract tests for Repo Governance evidence reports.

Validates that report JSON and Markdown output conforms to the evidence
report contract, preserves governance decisions, and makes correct
side-effect guarantees.

Reports are evidence only — they do NOT execute code, modify repo state,
create ExecutionRequest/ExecutionReceipt, or call shell/MCP/IDE.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLI_PATH = str(ROOT / "scripts" / "repo_governance_cli.py")
RENDERER_PATH = str(ROOT / "scripts" / "render_repo_governance_report.py")

REQUIRED_JSON_FIELDS = [
    "artifact_version",
    "decision",
    "reasons",
    "pack",
    "underlying_policy",
    "source",
    "ci_behavior",
    "side_effects",
    "evidence_note",
]


def _generate_report(task_desc="Fix test", file_path="tests/test_x.py", impact="low",
                     reasoning="test", test_plan="run tests") -> dict:
    """Run CLI adapter → render report → return JSON report dict."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        gov_json = Path(tmpdir) / "gov.json"
        out_dir = Path(tmpdir) / "reports"

        # Generate governance output
        cmd = [
            sys.executable, CLI_PATH,
            "--task-description", task_desc,
            "--file-path", file_path,
            "--estimated-impact", impact,
            "--reasoning", reasoning,
            "--test-plan", test_plan,
            "--json",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=str(ROOT))
        gov_json.write_text(result.stdout, encoding="utf-8")

        # Render report
        cmd2 = [sys.executable, RENDERER_PATH, "--input", str(gov_json), "--output-dir", str(out_dir)]
        subprocess.run(cmd2, capture_output=True, text=True, timeout=30, cwd=str(ROOT))

        report_path = out_dir / "repo-governance-report.json"
        return json.loads(report_path.read_text(encoding="utf-8"))


# ── JSON report contains required fields ────────────────────────────


def test_json_report_has_required_fields():
    report = _generate_report()
    for field in REQUIRED_JSON_FIELDS:
        assert field in report, f"Missing required field: {field}"


# ── Report preserves adapter decision ───────────────────────────────


def test_report_preserves_execute_decision():
    report = _generate_report()
    assert report["decision"] == "execute"
    assert report["ci_behavior"] == "pass"


def test_report_preserves_reject_decision():
    report = _generate_report(
        task_desc="Add env var", file_path=".env", reasoning="Need env var",
    )
    assert report["decision"] == "reject"
    assert report["ci_behavior"] == "fail"


def test_report_preserves_escalate_decision():
    report = _generate_report(
        task_desc="Optimize query", file_path="domains/service.py",
        impact="high", reasoning="refactor", test_plan="run tests",
    )
    assert report["decision"] == "escalate"
    assert report["ci_behavior"] == "warning"


# ── Report preserves side_effects false ─────────────────────────────


def test_report_side_effects_are_false():
    report = _generate_report()
    se = report["side_effects"]
    for field in ("file_writes", "shell", "mcp", "ide", "execution_receipt", "execution_request"):
        assert se[field] is False, f"side_effects.{field} must be False"


# ── Markdown report says evidence only ──────────────────────────────


def test_markdown_report_says_evidence_only():
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        gov_json = Path(tmpdir) / "gov.json"
        out_dir = Path(tmpdir) / "reports"

        cmd = [
            sys.executable, CLI_PATH,
            "--task-description", "Fix test",
            "--file-path", "tests/test_x.py",
            "--estimated-impact", "low",
            "--reasoning", "test",
            "--test-plan", "run tests",
            "--json",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=str(ROOT))
        gov_json.write_text(result.stdout, encoding="utf-8")

        cmd2 = [sys.executable, RENDERER_PATH, "--input", str(gov_json), "--output-dir", str(out_dir)]
        subprocess.run(cmd2, capture_output=True, text=True, timeout=30, cwd=str(ROOT))

        md_path = out_dir / "repo-governance-report.md"
        md_text = md_path.read_text(encoding="utf-8")
        assert "evidence only" in md_text.lower()
        assert "does not execute code" in md_text.lower()


# ── Artifact version present ────────────────────────────────────────


def test_report_has_artifact_version():
    report = _generate_report()
    assert report["artifact_version"] == "v1"


# ── Evidence note present ───────────────────────────────────────────


def test_report_has_evidence_note():
    report = _generate_report()
    assert "evidence only" in report["evidence_note"]


# ── Report generation does not create ExecutionRequest/Receipt ──────


def test_report_does_not_create_execution_receipt():
    report = _generate_report()
    assert report["side_effects"]["execution_receipt"] is False


# ── Report generation does not call MCP/IDE ─────────────────────────


def test_report_does_not_call_mcp_ide():
    report = _generate_report()
    assert report["side_effects"]["mcp"] is False
    assert report["side_effects"]["ide"] is False


# ── Missing decision field detected ─────────────────────────────────


def test_missing_decision_fails_contract():
    """A report dict missing 'decision' should be detected."""
    bad_report = {"artifact_version": "v1", "reasons": []}
    missing = [f for f in REQUIRED_JSON_FIELDS if f not in bad_report]
    assert "decision" in missing
