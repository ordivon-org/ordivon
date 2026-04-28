"""Contract tests for Repo Governance CLI and GitHub adapter JSON output.

Validates that all outputs conform to the repo governance output schema
and that side_effect guarantees are enforced.

Uses the JSON schema at tests/contracts/repo_governance_output.schema.json
as the canonical output contract.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLI_PATH = str(ROOT / "scripts" / "repo_governance_cli.py")
ADAPTER_PATH = str(ROOT / "scripts" / "repo_governance_github_adapter.py")
SCHEMA_PATH = ROOT / "tests" / "contracts" / "repo_governance_output.schema.json"

# Load the JSON schema once
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _validate_against_schema(data: dict) -> list[str]:
    """Validate output dict against the schema. Returns list of violation messages."""
    errors: list[str] = []

    # Check required top-level fields
    for field in SCHEMA.get("required", []):
        if field not in data:
            errors.append(f"Missing required field: {field}")

    # Check decision enum
    decision = data.get("decision")
    valid_decisions = SCHEMA["properties"]["decision"]["enum"]
    if decision not in valid_decisions:
        errors.append(f"decision must be one of {valid_decisions}, got {decision!r}")

    # Check pack + underlying_policy
    if data.get("pack") != "repo_governance":
        errors.append(f"pack must be 'repo_governance', got {data.get('pack')!r}")
    if data.get("underlying_policy") != "coding":
        errors.append(f"underlying_policy must be 'coding', got {data.get('underlying_policy')!r}")

    # Check source enum
    valid_sources = SCHEMA["properties"]["source"]["enum"]
    if data.get("source") not in valid_sources:
        errors.append(f"source must be one of {valid_sources}, got {data.get('source')!r}")

    # Check reasons is non-null list
    reasons = data.get("reasons")
    if not isinstance(reasons, list):
        errors.append(f"reasons must be a list, got {type(reasons).__name__}")

    # Check side_effects required fields are all False
    side_effects = data.get("side_effects", {})
    required_se = SCHEMA["properties"]["side_effects"]["required"]
    for field in required_se:
        if field not in side_effects:
            errors.append(f"side_effects missing required field: {field}")
        elif side_effects[field] is not False:
            errors.append(f"side_effects.{field} must be False, got {side_effects[field]!r}")

    # Check optional side_effects are False if present
    for opt_field in ("pr_comments", "push"):
        if opt_field in side_effects and side_effects[opt_field] is not False:
            errors.append(f"side_effects.{opt_field} must be False if present")

    # changed_files_count: if present, must be integer >= 0
    if "changed_files_count" in data:
        cfc = data["changed_files_count"]
        if not isinstance(cfc, int) or cfc < 0:
            errors.append(f"changed_files_count must be non-negative integer, got {cfc!r}")

    return errors


def _run_cli(*args: str) -> dict:
    cmd = [sys.executable, CLI_PATH, *args]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=str(ROOT))
    return json.loads(result.stdout)


def _run_adapter_github(pr_title: str, pr_body: str, files: list[str], labels: list[str] | None = None) -> dict:
    event = {
        "action": "opened",
        "pull_request": {
            "title": pr_title,
            "body": pr_body,
            "labels": [{"name": n} for n in (labels or [])],
        },
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as ef:
        ef.write(json.dumps(event))
        event_path = ef.name
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as cf:
        cf.write("\n".join(files))
        changed_path = cf.name

    try:
        cmd = [
            sys.executable, ADAPTER_PATH,
            "--github-event-path", event_path,
            "--changed-files-file", changed_path,
            "--json",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=str(ROOT))
        return json.loads(result.stdout)
    finally:
        Path(event_path).unlink(missing_ok=True)
        Path(changed_path).unlink(missing_ok=True)


# ── CLI execute output matches contract ──────────────────────────


def test_cli_execute_matches_contract():
    data = _run_cli(
        "--task-description", "Fix unit test naming",
        "--file-path", "tests/unit/test_example.py",
        "--estimated-impact", "low",
        "--reasoning", "Small test-only cleanup",
        "--test-plan", "uv run pytest tests/unit/test_example.py",
        "--json",
    )
    errors = _validate_against_schema(data)
    assert errors == [], f"Schema violations: {errors}"
    assert data["decision"] == "execute"
    assert data["source"] == "repo_governance_cli"


# ── CLI reject output matches contract ───────────────────────────


def test_cli_reject_matches_contract():
    data = _run_cli(
        "--task-description", "Add env var",
        "--file-path", ".env",
        "--estimated-impact", "medium",
        "--reasoning", "Need new env var",
        "--test-plan", "Check startup",
        "--json",
    )
    errors = _validate_against_schema(data)
    assert errors == [], f"Schema violations: {errors}"
    assert data["decision"] == "reject"
    assert any(".env" in r for r in data["reasons"])


# ── GitHub adapter execute matches contract ───────────────────────


def test_github_adapter_execute_matches_contract():
    data = _run_adapter_github(
        pr_title="Fix flaky test",
        pr_body="## Test Plan\nRun pytest 10 times.",
        files=["tests/unit/test_auth.py"],
    )
    errors = _validate_against_schema(data)
    assert errors == [], f"Schema violations: {errors}"
    assert data["decision"] == "execute"
    assert data["source"] == "github_actions_adapter"
    assert data.get("changed_files_count") == 1


# ── GitHub adapter escalate matches contract ──────────────────────


def test_github_adapter_escalate_matches_contract():
    data = _run_adapter_github(
        pr_title="Optimize query",
        pr_body="## Summary\nN+1 query fix.",
        files=["domains/strategy/service.py"],
    )
    errors = _validate_against_schema(data)
    assert errors == [], f"Schema violations: {errors}"
    assert data["decision"] == "escalate"
    assert data["source"] == "github_actions_adapter"


# ── GitHub adapter reject matches contract ────────────────────────


def test_github_adapter_reject_matches_contract():
    data = _run_adapter_github(
        pr_title="Update deps",
        pr_body="## Test Plan\nRun pip-audit.",
        files=["uv.lock"],
    )
    errors = _validate_against_schema(data)
    assert errors == [], f"Schema violations: {errors}"
    assert data["decision"] == "reject"


# ── Side-effect fields are all false ──────────────────────────────


def test_all_side_effects_are_false():
    data = _run_cli(
        "--task-description", "Fix test",
        "--file-path", "tests/test_x.py",
        "--estimated-impact", "low",
        "--reasoning", "Test fix",
        "--test-plan", "Run tests",
        "--json",
    )
    se = data["side_effects"]
    for field in ("file_writes", "shell", "mcp", "ide", "execution_receipt", "execution_request"):
        assert se[field] is False, f"side_effects.{field} must be False"
    # GitHub adapter extra fields
    data2 = _run_adapter_github(
        pr_title="Fix", pr_body="## Test Plan\nRun tests.",
        files=["a.py"],
    )
    se2 = data2["side_effects"]
    assert se2.get("pr_comments") is False
    assert se2.get("push") is False


# ── Missing required field detected ───────────────────────────────


def test_missing_required_field_fails_contract():
    """A dict missing 'decision' should produce validation errors."""
    bad_data = {"reasons": [], "pack": "repo_governance", "source": "test"}
    errors = _validate_against_schema(bad_data)
    assert len(errors) > 0
    assert any("decision" in e for e in errors)
