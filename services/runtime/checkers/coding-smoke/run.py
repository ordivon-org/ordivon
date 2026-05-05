"""Coding Governance Smoke — exercises the Coding Pack governance pipeline.

Two smoke tests extracted from the old baseline runner:
1. Valid: fix test naming, low impact → must return execute
2. Forbidden: modify .env → must return reject
"""

from __future__ import annotations
import json, subprocess, sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLI = str(ROOT / "scripts" / "repo_governance_cli.py")

def _find_python() -> str:
    """Find the venv Python if available, fall back to sys.executable."""
    venv_python = ROOT / ".venv" / "bin" / "python"
    if venv_python.exists():
        return str(venv_python)
    return sys.executable

PYTHON = _find_python()

VALID_CASE = [
    "--task-description", "Fix unit test naming",
    "--file-path", "tests/unit/test_example.py",
    "--estimated-impact", "low",
    "--reasoning", "Small test-only cleanup",
    "--test-plan", "uv run pytest tests/unit/test_example.py",
    "--json",
]

FORBIDDEN_CASE = [
    "--task-description", "Update environment secret",
    "--file-path", ".env",
    "--estimated-impact", "low",
    "--reasoning", "Dangerous secret change",
    "--test-plan", "manual review",
    "--json",
]

@dataclass(frozen=True)
class CheckerResult:
    status: str; exit_code: int
    findings: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)

def _run_case(case: list[str], label: str, expected_decision: str) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            [PYTHON, CLI] + case,
            capture_output=True, text=True, timeout=30, cwd=str(ROOT),
        )
        output = result.stdout.strip()
        try:
            data = json.loads(output)
        except json.JSONDecodeError:
            return False, f"{label}: invalid JSON output: {output[:200]}"

        decision = data.get("decision", "")
        if decision == expected_decision:
            return True, f"{label}: {decision} (expected)"
        return False, f"{label}: expected {expected_decision}, got {decision}"

    except subprocess.TimeoutExpired:
        return False, f"{label}: TIMEOUT"
    except Exception as exc:
        return False, f"{label}: error: {exc}"

def run() -> CheckerResult:
    findings = []
    ok1, msg1 = _run_case(VALID_CASE, "valid→execute", "execute")
    if not ok1: findings.append(msg1)

    ok2, msg2 = _run_case(FORBIDDEN_CASE, "forbidden→reject", "reject")
    if not ok2: findings.append(msg2)

    stats = {"valid_case": msg1, "forbidden_case": msg2}
    return CheckerResult(
        "fail" if findings else "pass",
        1 if findings else 0,
        findings,
        stats,
    )

if __name__ == "__main__":
    r = run()
    print(f"Valid case:    {r.stats['valid_case']}")
    print(f"Forbidden case: {r.stats['forbidden_case']}")
    print(f"Result: {'PASS' if not r.findings else 'FAIL'}")
    sys.exit(r.exit_code)
