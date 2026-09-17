from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from .catalog import _package_revision

_EVIDENCE_KIND = "ordivon.skillspector-evidence"
_TRUTH_ROLE = "scanner-evidence-not-trust-or-authorization"
_BLOCK_SEVERITIES = {"HIGH", "CRITICAL"}
_SAFE_RECOMMENDATIONS = {"SAFE"}
_SAFE_SEVERITIES = {"NONE", "LOW"}
_MAX_ISSUES = 100


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _base_evidence(skill_root: Path, executable: Path, package_revision: str, process_exit: int | None) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "kind": _EVIDENCE_KIND,
        "truthRole": _TRUTH_ROLE,
        "target": {
            "path": str(skill_root),
            "packageRevision": package_revision,
        },
        "scanner": {
            "name": "NVIDIA SkillSpector",
            "executable": str(executable),
            "version": None,
            "processExit": process_exit,
            "llmRequested": None,
            "llmAvailable": None,
        },
        "assessment": {
            "evidenceState": "SCANNER_ERROR",
            "score": None,
            "severity": None,
            "recommendation": None,
            "maxIssueSeverity": None,
            "issueCount": 0,
        },
        "analysis": {
            "status": None,
            "coveragePercent": None,
            "isComplete": False,
            "executionSuccessful": False,
        },
        "issues": [],
        "reportSha256": None,
        "diagnostics": [],
    }


def _normalize_report(
    *,
    skill_root: Path,
    executable: Path,
    package_revision: str,
    process_exit: int,
    stdout: bytes,
    report: dict[str, Any],
) -> dict[str, Any]:
    evidence = _base_evidence(skill_root, executable, package_revision, process_exit)
    evidence["reportSha256"] = _sha256(stdout)

    risk = report.get("risk_assessment")
    risk = risk if isinstance(risk, dict) else {}
    metadata = report.get("metadata")
    metadata = metadata if isinstance(metadata, dict) else {}
    completeness = report.get("analysis_completeness")
    completeness = completeness if isinstance(completeness, dict) else {}
    issues_raw = report.get("issues")
    issues = issues_raw if isinstance(issues_raw, list) else []
    bounded_issues = [item for item in issues[:_MAX_ISSUES] if isinstance(item, dict)]

    score = risk.get("score")
    severity = str(risk.get("severity") or "").upper() or None
    recommendation = str(risk.get("recommendation") or "").upper() or None
    max_issue_severity = str(risk.get("max_issue_severity") or "").upper() or None
    execution_successful = report.get("execution_successful") is True
    status = str(completeness.get("status") or "").lower() or None
    coverage = completeness.get("coverage_percent")
    is_complete = completeness.get("is_complete") is True and status == "complete"

    evidence["scanner"].update(
        {
            "version": metadata.get("skillspector_version"),
            "llmRequested": metadata.get("llm_requested"),
            "llmAvailable": metadata.get("llm_available"),
        }
    )
    evidence["assessment"].update(
        {
            "score": score,
            "severity": severity,
            "recommendation": recommendation,
            "maxIssueSeverity": max_issue_severity,
            "issueCount": len(issues),
        }
    )
    evidence["analysis"].update(
        {
            "status": status,
            "coveragePercent": coverage,
            "isComplete": is_complete,
            "executionSuccessful": execution_successful,
        }
    )
    evidence["issues"] = bounded_issues

    issue_severities = {
        str(item.get("severity") or "").upper()
        for item in bounded_issues
        if isinstance(item, dict)
    }
    block_signal = (
        recommendation == "DO_NOT_INSTALL"
        or severity in _BLOCK_SEVERITIES
        or max_issue_severity in _BLOCK_SEVERITIES
        or bool(issue_severities & _BLOCK_SEVERITIES)
    )

    if process_exit not in {0, 1} or not execution_successful:
        state = "SCANNER_ERROR"
        evidence["diagnostics"].append(
            "SkillSpector did not report a successful completed scan transport"
        )
    elif block_signal:
        state = "BLOCK_SIGNAL"
    elif not is_complete:
        state = "INCOMPLETE"
    else:
        try:
            positive_score = float(score) > 0 if score is not None else False
        except (TypeError, ValueError):
            positive_score = True
        caution = (
            bool(issues)
            or positive_score
            or recommendation not in _SAFE_RECOMMENDATIONS
            or severity not in _SAFE_SEVERITIES
        )
        state = "CAUTION" if caution else "CLEAN_EVIDENCE"
    evidence["assessment"]["evidenceState"] = state
    return evidence


def run_skillspector_scan(
    skill_root: str | Path,
    executable: str | Path,
    *,
    expected_package_revision: str | None = None,
    timeout_seconds: float = 60.0,
) -> dict[str, Any]:
    root = Path(skill_root).resolve(strict=True)
    scanner = Path(executable).resolve(strict=True)
    package_revision = _package_revision(root)
    if expected_package_revision is not None and package_revision != expected_package_revision:
        evidence = _base_evidence(root, scanner, package_revision, None)
        evidence["diagnostics"].append(
            f"package revision changed: expected {expected_package_revision}, current {package_revision}"
        )
        return evidence

    try:
        completed = subprocess.run(
            [str(scanner), "scan", str(root), "--no-llm", "--format", "json"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=timeout_seconds,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        evidence = _base_evidence(root, scanner, package_revision, None)
        evidence["diagnostics"].append(f"SkillSpector execution failed: {type(exc).__name__}")
        return evidence

    stdout = completed.stdout
    try:
        parsed = json.loads(stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        evidence = _base_evidence(root, scanner, package_revision, completed.returncode)
        evidence["reportSha256"] = _sha256(stdout)
        evidence["diagnostics"].append("SkillSpector returned invalid JSON")
        return evidence
    if not isinstance(parsed, dict):
        evidence = _base_evidence(root, scanner, package_revision, completed.returncode)
        evidence["reportSha256"] = _sha256(stdout)
        evidence["diagnostics"].append("SkillSpector JSON root is not an object")
        return evidence

    return _normalize_report(
        skill_root=root,
        executable=scanner,
        package_revision=package_revision,
        process_exit=completed.returncode,
        stdout=stdout,
        report=parsed,
    )
