from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def validate_scorecard_report(
    report: dict[str, Any],
    *,
    expected_repo: str,
    expected_commit: str,
    required_checks: Iterable[str] = (),
) -> dict[str, Any]:
    """Bind provider-native Scorecard evidence to an exact repository revision.

    The aggregate Scorecard score is deliberately metadata only. Applicability and
    admission are policy concerns and must operate on named checks instead.
    """
    repo = report.get("repo")
    if not isinstance(repo, dict):
        raise ValueError("Scorecard report has no repo object")
    if repo.get("name") != expected_repo:
        raise ValueError("Scorecard repository identity mismatch")
    if repo.get("commit") != expected_commit:
        raise ValueError("Scorecard repository revision mismatch")
    if len(expected_commit) != 40 or any(c not in "0123456789abcdef" for c in expected_commit):
        raise ValueError("expected_commit must be a lowercase SHA-1 Git commit")

    checks = report.get("checks")
    if not isinstance(checks, list) or not checks:
        raise ValueError("Scorecard report has no checks")

    by_name: dict[str, dict[str, Any]] = {}
    for check in checks:
        if not isinstance(check, dict):
            raise ValueError("Scorecard check must be an object")
        name = check.get("name")
        score = check.get("score")
        if not isinstance(name, str) or not name:
            raise ValueError("Scorecard check name is required")
        if name in by_name:
            raise ValueError(f"duplicate Scorecard check: {name}")
        if not isinstance(score, (int, float)) or isinstance(score, bool):
            raise ValueError(f"Scorecard check score is not numeric: {name}")
        if score < -1 or score > 10:
            raise ValueError(f"Scorecard check score is outside provider range: {name}")
        by_name[name] = {
            "name": name,
            "score": score,
            "reason": check.get("reason"),
        }

    required = sorted(set(required_checks))
    missing = [name for name in required if name not in by_name]
    if missing:
        raise ValueError(f"missing required Scorecard checks: {', '.join(missing)}")

    aggregate = report.get("score")
    if not isinstance(aggregate, (int, float)) or isinstance(aggregate, bool):
        raise ValueError("Scorecard aggregate score is not numeric")

    return {
        "standing": "SCORECARD_EVIDENCE_CURRENT",
        "repository": expected_repo,
        "sourceRevision": expected_commit,
        "providerAggregateScore": aggregate,
        "aggregateAuthoritative": False,
        "checks": [by_name[name] for name in sorted(by_name)],
        "requiredChecks": required,
    }


def load_and_validate_scorecard_report(
    report_path: Path,
    *,
    expected_repo: str,
    expected_commit: str,
    required_checks: Iterable[str] = (),
) -> dict[str, Any]:
    report = json.loads(report_path.read_text())
    result = validate_scorecard_report(
        report,
        expected_repo=expected_repo,
        expected_commit=expected_commit,
        required_checks=required_checks,
    )
    result["evidenceSha256"] = _sha256(report_path)
    return result
