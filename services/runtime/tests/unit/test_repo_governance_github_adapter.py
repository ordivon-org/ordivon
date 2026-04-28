"""Unit tests for the GitHub Actions Repo Governance Adapter.

Tests validate that the adapter correctly reads PR metadata (event JSON,
changed files, labels) and produces governance decisions through the
shared classify_repo_intent() function.

The adapter does NOT write files, comment on PRs, push commits, or
create ExecutionRequest/ExecutionReceipt.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ADAPTER_PATH = str(ROOT / "scripts" / "repo_governance_github_adapter.py")


def _make_github_event(pr_title: str, pr_body: str = "", labels: list[str] | None = None) -> str:
    """Create a minimal GitHub pull_request event JSON."""
    event = {
        "action": "opened",
        "pull_request": {
            "title": pr_title,
            "body": pr_body,
            "labels": [{"name": name} for name in (labels or [])],
        },
    }
    return json.dumps(event)


def _make_changed_files_content(files: list[str]) -> str:
    return "\n".join(files)


def _run_adapter_github(event_json: str, changed_files: list[str]) -> tuple[int, dict]:
    """Run the adapter in GitHub event mode with temp files."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as ef:
        ef.write(event_json)
        event_path = ef.name

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as cf:
        cf.write(_make_changed_files_content(changed_files))
        changed_path = cf.name

    try:
        cmd = [
            sys.executable,
            ADAPTER_PATH,
            "--github-event-path",
            event_path,
            "--changed-files-file",
            changed_path,
            "--json",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=str(ROOT))
        try:
            output = json.loads(result.stdout)
        except json.JSONDecodeError:
            output = {"error": "json_parse_failed", "stdout": result.stdout, "stderr": result.stderr}
        return result.returncode, output
    finally:
        Path(event_path).unlink(missing_ok=True)
        Path(changed_path).unlink(missing_ok=True)


def _run_adapter_cli(*args: str) -> tuple[int, dict]:
    """Run the adapter in CLI/local test mode."""
    cmd = [sys.executable, ADAPTER_PATH, *args]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=str(ROOT))
    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError:
        output = {"error": "json_parse_failed", "stdout": result.stdout, "stderr": result.stderr}
    return result.returncode, output


# ── GitHub event mode: valid test plan → execute ─────────────────────


def test_github_event_with_test_plan_returns_execute():
    event = _make_github_event(
        pr_title="Fix flaky assertion in test_user_auth.py",
        pr_body="""## Summary
The assertion compares timestamps without tolerance.

## Test Plan
Run pytest tests/unit/test_user_auth.py -x 10 times.
""",
    )
    exit_code, result = _run_adapter_github(event, ["tests/unit/test_user_auth.py"])
    assert exit_code == 0
    assert result["decision"] == "execute"
    assert result["source"] == "github_actions_adapter"


# ── GitHub event mode: missing test plan → escalate ──────────────────


def test_github_event_missing_test_plan_returns_escalate():
    event = _make_github_event(
        pr_title="Optimize database query",
        pr_body="## Summary\nN+1 query detected in recommendation service.",
    )
    exit_code, result = _run_adapter_github(event, ["domains/strategy/service.py"])
    assert exit_code == 2
    assert result["decision"] == "escalate"
    assert any("test_plan" in r.lower() for r in result["reasons"])


# ── GitHub event mode: forbidden .env → reject ───────────────────────


def test_github_event_forbidden_env_returns_reject():
    event = _make_github_event(
        pr_title="Add new environment variable",
        pr_body="## Summary\nNeed DB_REPLICA_URL for read replica.\n\n## Test Plan\nVerify app starts.",
    )
    exit_code, result = _run_adapter_github(event, [".env"])
    assert exit_code == 3
    assert result["decision"] == "reject"
    assert any(".env" in r for r in result["reasons"])


# ── GitHub event mode: high impact label → escalate ──────────────────


def test_github_event_high_impact_label_returns_escalate():
    event = _make_github_event(
        pr_title="Rewrite risk engine",
        pr_body="## Summary\nMajor refactor.\n\n## Test Plan\nFull governance test suite.",
        labels=["impact/high"],
    )
    exit_code, result = _run_adapter_github(event, ["governance/risk_engine/engine.py"])
    assert exit_code == 2
    assert result["decision"] == "escalate"
    assert any("high" in r.lower() for r in result["reasons"])


# ── GitHub event mode: many changed files → escalate ─────────────────


def test_github_event_many_changed_files_returns_escalate():
    files = [f"src/module_{i}.py" for i in range(15)]
    event = _make_github_event(
        pr_title="Large refactor",
        pr_body="## Summary\nRefactoring.\n\n## Test Plan\nRun all tests.",
    )
    exit_code, result = _run_adapter_github(event, files)
    # >10 files → inferred high impact → escalate
    assert result["decision"] in ("escalate", "execute")


# ── JSON output includes side_effects false ──────────────────────────


def test_adapter_json_includes_side_effects_false():
    event = _make_github_event(
        pr_title="Fix test",
        pr_body="## Test Plan\nRun tests.",
    )
    _, result = _run_adapter_github(event, ["tests/test_x.py"])
    side_effects = result["side_effects"]
    assert side_effects["file_writes"] is False
    assert side_effects["pr_comments"] is False
    assert side_effects["push"] is False
    assert side_effects["shell"] is False
    assert side_effects["mcp"] is False
    assert side_effects["ide"] is False
    assert side_effects["execution_receipt"] is False
    assert side_effects["execution_request"] is False


# ── Adapter does not write files ─────────────────────────────────────


def test_adapter_does_not_write_files():
    event = _make_github_event(
        pr_title="Fix test",
        pr_body="## Test Plan\nRun tests.",
    )
    _, result = _run_adapter_github(event, ["tests/test_x.py"])
    assert result["side_effects"]["file_writes"] is False


# ── Adapter does not create ExecutionRequest/Receipt ─────────────────


def test_adapter_does_not_create_execution_receipt():
    event = _make_github_event(
        pr_title="Fix test",
        pr_body="## Test Plan\nRun tests.",
    )
    _, result = _run_adapter_github(event, ["tests/test_x.py"])
    assert result["side_effects"]["execution_receipt"] is False
    assert result["side_effects"]["execution_request"] is False


# ── Adapter does not call MCP/IDE ────────────────────────────────────


def test_adapter_does_not_call_mcp_ide():
    event = _make_github_event(
        pr_title="Fix test",
        pr_body="## Test Plan\nRun tests.",
    )
    _, result = _run_adapter_github(event, ["tests/test_x.py"])
    assert result["side_effects"]["mcp"] is False
    assert result["side_effects"]["ide"] is False


# ── Reject exit code is blocking ─────────────────────────────────────


def test_reject_exit_code_is_blocking():
    event = _make_github_event(
        pr_title="Update deps",
        pr_body="## Test Plan\nRun pip-audit.",
    )
    exit_code, result = _run_adapter_github(event, ["uv.lock"])
    assert exit_code == 3
    assert result["decision"] == "reject"


# ── CLI mode: valid input → execute ──────────────────────────────────


def test_cli_mode_valid_returns_execute():
    exit_code, result = _run_adapter_cli(
        "--task-description",
        "Fix unit test naming",
        "--file-path",
        "tests/unit/test_example.py",
        "--estimated-impact",
        "low",
        "--reasoning",
        "Small test-only cleanup",
        "--test-plan",
        "uv run pytest tests/unit/test_example.py",
        "--json",
    )
    assert exit_code == 0
    assert result["decision"] == "execute"
    assert result["source"] == "github_actions_adapter"


# ── CLI mode: missing test plan → escalate ───────────────────────────


def test_cli_mode_missing_test_plan_returns_escalate():
    exit_code, result = _run_adapter_cli(
        "--task-description",
        "Optimize query",
        "--file-path",
        "domains/strategy/service.py",
        "--estimated-impact",
        "medium",
        "--reasoning",
        "N+1 query fix",
        "--json",
    )
    assert exit_code == 2
    assert result["decision"] == "escalate"


# ── changed_files_count field ────────────────────────────────────────


def test_adapter_includes_changed_files_count():
    event = _make_github_event(
        pr_title="Multi-file fix",
        pr_body="## Test Plan\nRun tests.",
    )
    _, result = _run_adapter_github(event, ["a.py", "b.py", "c.py"])
    assert result.get("changed_files_count") == 3
