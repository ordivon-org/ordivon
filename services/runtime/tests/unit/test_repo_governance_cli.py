"""Unit tests for Repo Governance CLI.

Tests validate that the CLI correctly classifies AI coding intents through
the governance pipeline.  The CLI does NOT execute code, modify files, call
shell/MCP/IDE, or create ExecutionRequest/ExecutionReceipt.

Tests use subprocess to invoke the CLI script and parse JSON output.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLI_PATH = str(ROOT / "scripts" / "repo_governance_cli.py")


def _run_cli(*args: str) -> tuple[int, dict]:
    """Run the CLI script and return (exit_code, parsed_json_output)."""
    cmd = [sys.executable, CLI_PATH, *args]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(ROOT),
    )
    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError:
        output = {"error": "json_parse_failed", "stdout": result.stdout, "stderr": result.stderr}
    return result.returncode, output


# ── Valid test fix returns execute ──────────────────────────────────────


def test_valid_test_fix_returns_execute():
    exit_code, result = _run_cli(
        "--task-description",
        "Fix flaky assertion in test_user_auth.py",
        "--file-path",
        "tests/unit/test_user_auth.py",
        "--estimated-impact",
        "low",
        "--reasoning",
        "The assertion compares timestamps without tolerance.",
        "--test-plan",
        "uv run pytest tests/unit/test_user_auth.py -x 10 times.",
        "--json",
    )
    assert exit_code == 0
    assert result["decision"] == "execute"
    assert len(result["reasons"]) >= 1
    assert "Passed all governance gates" in " ".join(result["reasons"])


# ── Doc change with plan returns execute ──────────────────────────────


def test_doc_change_with_plan_returns_execute():
    exit_code, result = _run_cli(
        "--task-description",
        "Update README with new setup instructions",
        "--file-path",
        "README.md",
        "--file-path",
        "docs/setup.md",
        "--estimated-impact",
        "low",
        "--reasoning",
        "Outdated instructions since uv migration.",
        "--test-plan",
        "Manual review of rendered markdown.",
        "--json",
    )
    assert exit_code == 0
    assert result["decision"] == "execute"


# ── Missing task_description returns reject ───────────────────────────


def test_missing_task_description_returns_reject():
    exit_code, result = _run_cli(
        "--task-description",
        "",
        "--file-path",
        "apps/api/app/main.py",
        "--estimated-impact",
        "low",
        "--reasoning",
        "Need to refactor.",
        "--test-plan",
        "Run unit tests.",
        "--json",
    )
    assert exit_code == 3
    assert result["decision"] == "reject"
    assert any("task_description" in r.lower() for r in result["reasons"])


# ── Missing file_paths returns reject ─────────────────────────────────


def test_missing_file_paths_returns_reject():
    exit_code, result = _run_cli(
        "--task-description",
        "Refactor the authentication middleware",
        "--estimated-impact",
        "medium",
        "--reasoning",
        "Extract duplicate logic.",
        "--test-plan",
        "Run auth test suite.",
        "--json",
    )
    assert exit_code == 3
    assert result["decision"] == "reject"
    assert any("file" in r.lower() for r in result["reasons"])


# ── Forbidden .env returns reject ─────────────────────────────────────


def test_forbidden_env_returns_reject():
    exit_code, result = _run_cli(
        "--task-description",
        "Add new environment variable",
        "--file-path",
        ".env",
        "--estimated-impact",
        "medium",
        "--reasoning",
        "Need DB_REPLICA_URL for read replica.",
        "--test-plan",
        "Verify app starts with new env var.",
        "--json",
    )
    assert exit_code == 3
    assert result["decision"] == "reject"
    assert any(".env" in r for r in result["reasons"])


# ── Forbidden uv.lock returns reject ──────────────────────────────────


def test_forbidden_uv_lock_returns_reject():
    exit_code, result = _run_cli(
        "--task-description",
        "Update dependency version",
        "--file-path",
        "uv.lock",
        "--estimated-impact",
        "low",
        "--reasoning",
        "Patch version bump.",
        "--test-plan",
        "Run pip-audit after update.",
        "--json",
    )
    assert exit_code == 3
    assert result["decision"] == "reject"
    assert any("uv.lock" in r for r in result["reasons"])


# ── High impact returns escalate ──────────────────────────────────────


def test_high_impact_returns_escalate():
    exit_code, result = _run_cli(
        "--task-description",
        "Rewrite risk engine validation logic",
        "--file-path",
        "governance/risk_engine/engine.py",
        "--estimated-impact",
        "high",
        "--reasoning",
        "Need to support streaming validation.",
        "--test-plan",
        "Run full governance test suite.",
        "--json",
    )
    assert exit_code == 2
    assert result["decision"] == "escalate"
    assert any("high" in r.lower() for r in result["reasons"])


# ── Missing test_plan returns escalate ─────────────────────────────────


def test_missing_test_plan_returns_escalate():
    exit_code, result = _run_cli(
        "--task-description",
        "Optimize database query in recommendation service",
        "--file-path",
        "domains/strategy/service.py",
        "--estimated-impact",
        "medium",
        "--reasoning",
        "N+1 query detected.",
        "--json",
    )
    assert exit_code == 2
    assert result["decision"] == "escalate"
    assert any("test_plan" in r.lower() for r in result["reasons"])


# ── Multi-file medium change with plan returns execute ────────────────


def test_multi_file_with_plan_returns_execute():
    exit_code, result = _run_cli(
        "--task-description",
        "Extract shared validation helpers",
        "--file-path",
        "shared/validation.py",
        "--file-path",
        "capabilities/domain/finance_decisions.py",
        "--estimated-impact",
        "medium",
        "--reasoning",
        "Duplicate validation logic across capability files.",
        "--test-plan",
        "Run pytest tests/unit/capabilities/ -v.",
        "--json",
    )
    assert exit_code == 0
    assert result["decision"] == "execute"


# ── JSON output structure tests ────────────────────────────────────────


def test_json_output_has_decision():
    _, result = _run_cli(
        "--task-description",
        "Fix test",
        "--file-path",
        "tests/test_x.py",
        "--estimated-impact",
        "low",
        "--reasoning",
        "Fixing test.",
        "--test-plan",
        "Run tests.",
        "--json",
    )
    assert "decision" in result


def test_json_output_has_reasons():
    _, result = _run_cli(
        "--task-description",
        "Fix test",
        "--file-path",
        "tests/test_x.py",
        "--estimated-impact",
        "low",
        "--reasoning",
        "Fixing test.",
        "--test-plan",
        "Run tests.",
        "--json",
    )
    assert isinstance(result["reasons"], list)


def test_json_output_has_side_effects():
    _, result = _run_cli(
        "--task-description",
        "Fix test",
        "--file-path",
        "tests/test_x.py",
        "--estimated-impact",
        "low",
        "--reasoning",
        "Fixing test.",
        "--test-plan",
        "Run tests.",
        "--json",
    )
    side_effects = result["side_effects"]
    assert side_effects["file_writes"] is False
    assert side_effects["shell"] is False
    assert side_effects["mcp"] is False
    assert side_effects["ide"] is False
    assert side_effects["execution_receipt"] is False
    assert side_effects["execution_request"] is False


def test_json_output_has_pack_and_policy():
    _, result = _run_cli(
        "--task-description",
        "Fix test",
        "--file-path",
        "tests/test_x.py",
        "--estimated-impact",
        "low",
        "--reasoning",
        "Fixing test.",
        "--test-plan",
        "Run tests.",
        "--json",
    )
    assert result["pack"] == "repo_governance"
    assert result["underlying_policy"] == "coding"


# ── CLI side-effect safety tests (no execution / no writes) ───────────


def test_cli_does_not_create_execution_request():
    """CLI must never create an ExecutionRequest."""
    _, result = _run_cli(
        "--task-description",
        "Fix test",
        "--file-path",
        "tests/test_x.py",
        "--estimated-impact",
        "low",
        "--reasoning",
        "Fixing test.",
        "--test-plan",
        "Run tests.",
        "--json",
    )
    assert "execution_request" not in result.get("actual_side_effects", {})
    assert result["side_effects"]["execution_request"] is False


def test_cli_does_not_create_execution_receipt():
    """CLI must never create an ExecutionReceipt."""
    _, result = _run_cli(
        "--task-description",
        "Fix test",
        "--file-path",
        "tests/test_x.py",
        "--estimated-impact",
        "low",
        "--reasoning",
        "Fixing test.",
        "--test-plan",
        "Run tests.",
        "--json",
    )
    assert "execution_receipt" not in result.get("actual_side_effects", {})
    assert result["side_effects"]["execution_receipt"] is False


def test_cli_does_not_shell():
    """CLI must never invoke a shell (beyond its own process)."""
    _, result = _run_cli(
        "--task-description",
        "Fix test",
        "--file-path",
        "tests/test_x.py",
        "--estimated-impact",
        "low",
        "--reasoning",
        "Fixing test.",
        "--test-plan",
        "Run tests.",
        "--json",
    )
    assert result["side_effects"]["shell"] is False


def test_cli_does_not_mcp():
    """CLI must never invoke MCP."""
    _, result = _run_cli(
        "--task-description",
        "Fix test",
        "--file-path",
        "tests/test_x.py",
        "--estimated-impact",
        "low",
        "--reasoning",
        "Fixing test.",
        "--test-plan",
        "Run tests.",
        "--json",
    )
    assert result["side_effects"]["mcp"] is False


def test_cli_does_not_ide():
    """CLI must never invoke IDE."""
    _, result = _run_cli(
        "--task-description",
        "Fix test",
        "--file-path",
        "tests/test_x.py",
        "--estimated-impact",
        "low",
        "--reasoning",
        "Fixing test.",
        "--test-plan",
        "Run tests.",
        "--json",
    )
    assert result["side_effects"]["ide"] is False


def test_cli_does_not_write_files():
    """CLI must never write files."""
    _, result = _run_cli(
        "--task-description",
        "Fix test",
        "--file-path",
        "tests/test_x.py",
        "--estimated-impact",
        "low",
        "--reasoning",
        "Fixing test.",
        "--test-plan",
        "Run tests.",
        "--json",
    )
    assert result["side_effects"]["file_writes"] is False


# ── Forbidden migration runner returns reject ─────────────────────────


def test_forbidden_migration_runner_returns_reject():
    exit_code, result = _run_cli(
        "--task-description",
        "Add idempotent migration",
        "--file-path",
        "state/db/migrations/runner.py",
        "--estimated-impact",
        "high",
        "--reasoning",
        "New ORM column needs migration.",
        "--test-plan",
        "Run schema drift check.",
        "--json",
    )
    assert exit_code == 3
    assert result["decision"] == "reject"
    assert any("migrations" in r.lower() for r in result["reasons"])
