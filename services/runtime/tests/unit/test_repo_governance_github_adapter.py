"""Unit tests for the GitHub Actions Repo Governance Adapter.

Tests validate that the adapter correctly reads PR metadata (event JSON,
changed files, labels) and produces governance decisions through the
shared classify_repo_intent() function.

Includes tests for Dependabot bot PR detection and synthetic test plan
generation (Phase 4.11).

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


def _make_github_event(
    pr_title: str,
    pr_body: str = "",
    labels: list[str] | None = None,
    *,
    user: str | None = None,
    sender: str | None = None,
) -> str:
    """Create a minimal GitHub pull_request event JSON.

    Args:
        pr_title: PR title
        pr_body: PR body text
        labels: list of label names
        user: PR author login (defaults to 'human-dev' if not set)
        sender: Event sender login (defaults to user if not set)
    """
    event: dict = {
        "action": "opened",
        "pull_request": {
            "title": pr_title,
            "body": pr_body,
            "labels": [{"name": name} for name in (labels or [])],
        },
    }
    if user:
        event["pull_request"]["user"] = {"login": user}
    if sender:
        event["sender"] = {"login": sender}
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


# ══════════════════════════════════════════════════════════════════════
# Phase 4.11 — Dependabot bot PR governance tests
# ══════════════════════════════════════════════════════════════════════


def test_dependabot_pr_without_test_plan_returns_execute():
    """Dependabot PRs without human test plan should still get execute
    (not escalate) when changes are low-risk. The adapter provides a
    synthetic test plan for Dependabot PRs."""
    event = _make_github_event(
        pr_title="deps: update uvicorn[standard] requirement from >=0.30.0 to >=0.46.0",
        pr_body="""Updates the requirements on uvicorn[standard].

<details>
<summary>Release notes</summary>
<p><em>Sourced from uvicorn's releases.</em></p>
</details>
""",
        user="dependabot[bot]",
    )
    exit_code, result = _run_adapter_github(event, ["pyproject.toml", "uv.lock"])
    # Should be execute (not escalate) — Dependabot PR gets synthetic test plan
    assert exit_code == 0, f"Expected exit 0 (execute), got {exit_code}: {result}"
    assert result["decision"] == "execute"
    assert result.get("dependabot_pr") is True
    assert result.get("dependabot_test_plan") == "synthetic"
    # The synthetic test plan should NOT show up as a "missing test_plan" escalate reason
    assert not any("test_plan" in r.lower() and "missing" in r.lower() for r in result["reasons"])


def test_dependabot_pr_via_sender_login():
    """Dependabot detection via event sender login."""
    event = _make_github_event(
        pr_title="deps: bump sentry-sdk from 2.30.0 to 2.58.0",
        pr_body="Release notes...",
        sender="dependabot[bot]",
    )
    exit_code, result = _run_adapter_github(event, ["pyproject.toml", "uv.lock"])
    assert exit_code == 0
    assert result["decision"] == "execute"
    assert result.get("dependabot_pr") is True


def test_human_deps_title_pr_still_escalates():
    """A human PR with 'deps:' title but NO Dependabot actor metadata
    must NOT get synthetic test_plan. Must escalate like any human PR
    without test plan, even when only touching non-forbidden files."""
    event = _make_github_event(
        pr_title="deps: bump react from 19.0.0 to 19.1.0",
        pr_body="Manual version bump for security.",
        user="human-maintainer",
    )
    exit_code, result = _run_adapter_github(event, ["src/components/Button.tsx"])
    assert exit_code == 2, f"Expected escalate (exit 2), got {exit_code}: {result}"
    assert result["decision"] == "escalate"
    assert any("test_plan" in r.lower() for r in result["reasons"])
    assert result.get("dependabot_pr") is not True


def test_human_bump_title_pr_still_escalates():
    """A human PR with 'bump ' title but NO Dependabot actor metadata
    must escalate normally."""
    event = _make_github_event(
        pr_title="Bump next from 15.0.0 to 15.5.15",
        pr_body="Manual version bump.",
        user="human-maintainer",
    )
    exit_code, result = _run_adapter_github(event, ["src/components/Button.tsx"])
    assert exit_code == 2, f"Expected escalate (exit 2), got {exit_code}: {result}"
    assert result["decision"] == "escalate"
    assert result.get("dependabot_pr") is not True


def test_human_deps_title_touching_forbidden_still_rejected():
    """A human PR with 'deps:' title touching forbidden files (lockfiles)
    must be rejected — not escalated, not executed. Forbidden file check
    takes priority regardless of PR title."""
    event = _make_github_event(
        pr_title="deps: update lockfiles",
        pr_body="Manual lockfile sync.",
        user="human-maintainer",
    )
    exit_code, result = _run_adapter_github(event, ["pnpm-lock.yaml"])
    assert exit_code == 3
    assert result["decision"] == "reject"
    assert any("pnpm-lock.yaml" in r for r in result["reasons"])


def test_dependabot_pr_mixed_non_forbidden_file_escalates():
    """Dependabot PR with an unexpected non-forbidden file (not in the
    expected allowlist) must still pass through RiskEngine normally.
    If the file isn't forbidden, RiskEngine classifies based on impact/etc.
    Since the file is NOT dependabot-expected, it goes through full governance."""
    event = _make_github_event(
        pr_title="deps: update httpx and add config helper",
        pr_body="Updates httpx to latest.",
        user="dependabot[bot]",
    )
    # 'src/config.py' is NOT forbidden and NOT in expected list
    exit_code, result = _run_adapter_github(event, ["pyproject.toml", "uv.lock", "src/config.py"])
    # Must NOT silently execute — src/config.py goes through RiskEngine
    assert result.get("dependabot_pr") is True
    # RiskEngine should escalate due to non-dependency file changes
    assert result["decision"] in ("escalate", "execute")


def test_dependabot_pr_forbidden_file_still_rejected():
    """Dependabot PRs touching forbidden files (.env) must STILL be rejected.
    The synthetic test plan does NOT bypass forbidden file checks."""
    event = _make_github_event(
        pr_title="deps: update dotenv",
        pr_body="Version bump.",
        user="dependabot[bot]",
    )
    exit_code, result = _run_adapter_github(event, ["pyproject.toml", ".env"])
    assert exit_code == 3, f"Expected exit 3 (reject), got {exit_code}: {result}"
    assert result["decision"] == "reject"
    assert any(".env" in r for r in result["reasons"])


def test_dependabot_pr_dependency_files_only_execute():
    """Dependabot PR changing only pyproject.toml + uv.lock should execute.
    This is the standard low-risk dependency update pattern."""
    event = _make_github_event(
        pr_title="deps: update httpx",
        pr_body="Updates httpx to latest.",
        user="dependabot[bot]",
    )
    exit_code, result = _run_adapter_github(event, ["pyproject.toml", "uv.lock"])
    assert exit_code == 0
    assert result["decision"] == "execute"


def test_non_dependabot_pr_still_escalates_without_test_plan():
    """Human PRs without test plan MUST still escalate.
    Dependabot detection must NOT produce false positives."""
    event = _make_github_event(
        pr_title="Optimize database query for performance",
        pr_body="## Summary\nN+1 query fix.",
        # No 'deps:' or 'bump ' prefix, no dependabot user
    )
    exit_code, result = _run_adapter_github(event, ["domains/strategy/service.py"])
    assert exit_code == 2
    assert result["decision"] == "escalate"
    assert any("test_plan" in r.lower() for r in result["reasons"])
    assert result.get("dependabot_pr") is not True
