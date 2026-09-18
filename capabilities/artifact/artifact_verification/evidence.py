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


def write_gate_receipt(
    output_dir: Path,
    gate: str,
    subject: Path,
    profile_path: Path,
    raw: dict[str, Any],
    verifier_id: str,
    verifier_versions: dict[str, str],
    passed: bool | None = None,
) -> dict[str, Any]:
    """Bind one raw verification result to one unsigned local VSA receipt."""
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = output_dir / f"{gate}.raw.json"
    _write_json(raw_path, raw)
    result_passed = raw.get("status") == "PASS" if passed is None else passed
    statement = verification_summary_statement(
        subject,
        profile_path,
        verifier_id,
        verifier_versions,
        result_passed,
    )
    statement_path = output_dir / f"{gate}.vsa.json"
    _write_json(statement_path, statement)
    checked = verify_verification_summary(
        statement_path,
        subject,
        profile_path,
        [verifier_id],
    )
    return {
        "gate": gate,
        "status": "PASS" if checked.get("status") == "PASS" and result_passed else "FAIL",
        "verificationResult": "PASSED" if result_passed else "FAILED",
        "rawEvidence": file_fact(raw_path),
        "vsa": file_fact(statement_path),
        "vsaValidation": checked,
    }
