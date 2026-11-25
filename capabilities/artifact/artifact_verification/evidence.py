from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from artifact_core.contracts import file_fact
from artifact_trust.vsa import verification_summary_statement, verify_verification_summary


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def gate_input_issues(
    subject: Path,
    profile_path: Path,
    admitted: dict[str, dict[str, Any]],
) -> list[str]:
    """Compare current paths with stage-admitted facts; not an ABA-proof snapshot."""
    issues: list[str] = []
    for role, path in (("subject", subject), ("profile", profile_path)):
        try:
            matches = file_fact(path) == admitted[role]
        except (OSError, RuntimeError):
            matches = False
        if not matches:
            issues.append(f"verification {role} identity drift since admission")
    return issues


def write_gate_receipt(
    output_dir: Path,
    gate: str,
    subject: Path,
    profile_path: Path,
    raw: dict[str, Any],
    verifier_id: str,
    verifier_versions: dict[str, str],
    passed: bool | None = None,
    *,
    admitted: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Bind one raw verification result to one unsigned local VSA receipt."""
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = output_dir / f"{gate}.raw.json"
    _write_json(raw_path, raw)

    def rejected(issues: list[str]) -> dict[str, Any]:
        return {
            "gate": gate, "status": "FAIL", "verificationResult": "NOT_EVALUATED",
            "rawEvidence": file_fact(raw_path),
            "vsaValidation": {"status": "FAIL", "failures": issues},
        }

    if admitted is not None:
        issues = gate_input_issues(subject, profile_path, admitted)
        if issues:
            return rejected(issues)
    result_passed = raw.get("status") == "PASS" if passed is None else passed
    try:
        statement = verification_summary_statement(
            subject,
            profile_path,
            verifier_id,
            verifier_versions,
            result_passed,
        )
    except (OSError, RuntimeError):
        if admitted is None:
            raise
        return rejected(["verification summary input unavailable during construction"])
    if admitted is not None:
        # A statement constructed from a later pathname read must not rebind
        # an already observed result to different subject or policy bytes.
        if (
            statement["subject"][0]["digest"] != admitted["subject"]["digest"]
            or statement["predicate"]["policy"]["digest"] != admitted["profile"]["digest"]
        ):
            return rejected(["verification summary differs from admitted input identity"])
    statement_path = output_dir / f"{gate}.vsa.json"
    _write_json(statement_path, statement)
    try:
        checked = verify_verification_summary(
            statement_path,
            subject,
            profile_path,
            [verifier_id],
        )
    except (OSError, RuntimeError):
        if admitted is None:
            raise
        return rejected(["verification summary input unavailable during readback"])
    if admitted is not None:
        if any(checked.get(role) != admitted[role] for role in ("subject", "profile")):
            return rejected(["validated verification summary differs from admitted input identity"])
    return {
        "gate": gate,
        "status": "PASS" if checked.get("status") == "PASS" and result_passed else "FAIL",
        "verificationResult": "PASSED" if result_passed else "FAILED",
        "rawEvidence": file_fact(raw_path),
        "vsa": file_fact(statement_path),
        "vsaValidation": checked,
    }
