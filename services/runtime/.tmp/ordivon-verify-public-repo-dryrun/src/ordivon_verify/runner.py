"""Ordivon Verify — check orchestration runner."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from ordivon_verify.checks.debt import validate_debt_ledger
from ordivon_verify.checks.docs import validate_document_registry
from ordivon_verify.checks.gates import validate_gate_manifest
from ordivon_verify.checks.receipts import scan_receipt_files

_BUILTIN_ROOT = Path(__file__).resolve().parents[2]

CHECKER_SCRIPTS = {
    "receipts": _BUILTIN_ROOT / "scripts" / "check_receipt_integrity.py",
    "debt": _BUILTIN_ROOT / "scripts" / "check_verification_debt.py",
    "gates": _BUILTIN_ROOT / "scripts" / "check_verification_manifest.py",
    "docs": _BUILTIN_ROOT / "scripts" / "check_document_registry.py",
}

CHECKER_LABELS = {
    "receipts": "Receipt Integrity",
    "debt": "Verification Debt",
    "gates": "Gate Manifest",
    "docs": "Document Registry",
}

ALL_CHECKS = ["receipts", "debt", "gates", "docs"]

_WARN_ADVICE = {
    "debt": "Add verification-debt-ledger.jsonl when moving from advisory to standard mode.",
    "gates": "Add verification-gate-manifest.json before strict CI use.",
    "docs": "Add document-registry.jsonl for document governance.",
}


def run_check(check_id: str, root: Path | None = None) -> dict:
    """Run a native Ordivon checker script as subprocess."""
    script = CHECKER_SCRIPTS[check_id]
    cmd = [sys.executable, str(script)]
    cwd = str(root) if root else str(_BUILTIN_ROOT)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, cwd=cwd)
        return {
            "id": check_id,
            "label": CHECKER_LABELS[check_id],
            "status": "PASS" if result.returncode == 0 else "FAIL",
            "exit_code": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }
    except subprocess.TimeoutExpired:
        return {
            "id": check_id,
            "label": CHECKER_LABELS[check_id],
            "status": "FAIL",
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Checker timed out: {check_id}",
        }
    except Exception as exc:
        return {
            "id": check_id,
            "label": CHECKER_LABELS[check_id],
            "status": "FAIL",
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Runtime error: {exc}",
        }


def run_external_receipts(receipt_paths: list[str], root: Path) -> dict:
    """Run external receipt scan using built-in scanner."""
    failures, scanned = scan_receipt_files(receipt_paths, root)
    if failures:
        return {
            "id": "receipts",
            "label": "Receipt Integrity",
            "status": "FAIL",
            "exit_code": 1,
            "stdout": "",
            "stderr": f"{len(failures)} contradiction(s) in {scanned} receipt(s)",
            "failures": failures,
        }
    return {
        "id": "receipts",
        "label": "Receipt Integrity",
        "status": "PASS",
        "exit_code": 0,
        "stdout": f"{scanned} receipt(s) scanned, 0 contradictions",
        "stderr": "",
    }


def run_external_checker(check_id: str, root: Path, mode: str, config: dict) -> dict:
    """Run checker against external repo using config paths + lightweight validators."""
    config_keys = {"debt": "debt_ledger", "gates": "gate_manifest", "docs": "document_registry"}
    key = config_keys.get(check_id, "")
    cfg_path = config.get(key, "") if config else ""
    target = root / cfg_path if cfg_path else None
    label = CHECKER_LABELS[check_id]

    if target and target.exists() and cfg_path:
        validators = {"debt": validate_debt_ledger, "gates": validate_gate_manifest, "docs": validate_document_registry}
        try:
            result = validators[check_id](target)
        except Exception as exc:
            result = {"status": "FAIL", "exit_code": -1, "stdout": "", "stderr": f"Validation error: {exc}"}
        result["id"] = check_id
        result["label"] = label
        return result

    if mode == "strict":
        return {
            "id": check_id,
            "label": label,
            "status": "FAIL",
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Missing required file: {target or cfg_path}",
        }
    if mode == "standard" and cfg_path:
        return {
            "id": check_id,
            "label": label,
            "status": "FAIL",
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Configured file not found: {target or cfg_path}",
        }
    return {
        "id": check_id,
        "label": label,
        "status": "WARN",
        "exit_code": -1,
        "stdout": "",
        "stderr": f"Not configured: {target or cfg_path} not found",
        "next_action": _WARN_ADVICE.get(check_id, f"Configure {check_id} when ready."),
    }
