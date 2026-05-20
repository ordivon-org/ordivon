"""OPA policy engine integration — evaluate governance policies via OPA.

Replaces hand-rolled Python checker logic with Rego policy evaluation.
Uses `opa eval` CLI for evaluation. Policies live in policies/opa/rules/.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Optional


POLICY_DIR = Path(__file__).resolve().parents[2] / "policies/opa/rules"


def _opa_eval(query: str, input_data: dict, data_files: Optional[list[Path]] = None) -> dict:
    """Run `opa eval` with query and input data. Returns parsed JSON result."""
    cmd = ["opa", "eval", "--format", "json", "--fail-defined", "-d", str(POLICY_DIR)]
    if data_files:
        for df in data_files:
            cmd.extend(["-d", str(df)])

    # Write input to temp file to avoid shell escaping
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(input_data, f)
        input_path = f.name

    cmd.extend(["-i", input_path, query])

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        Path(input_path).unlink(missing_ok=True)
        if proc.returncode not in (0, 1):  # OPA returns 1 for undefined results
            return {"error": proc.stderr.strip()}
        return json.loads(proc.stdout) if proc.stdout.strip() else {}
    except Exception as e:
        Path(input_path).unlink(missing_ok=True)
        return {"error": str(e)}


def check_overclaim_files(files: list[dict]) -> list[dict]:
    """Check files for overclaim language via OPA.

    Args:
        files: [{"path": "...", "content": "..."}, ...]
    Returns:
        List of findings.
    """
    result = _opa_eval("data.governance.overclaim.check_files(input.files)", {"files": files})
    if "error" in result:
        return [{"severity": "ERROR", "finding_id": "OPA-ERROR", "description": result["error"]}]

    findings = []
    for r in result.get("result", []):
        for expr in r.get("expressions", []):
            for f in expr.get("value") or []:
                if isinstance(f, dict):
                    findings.append(f)
    return findings


def check_overclaim_dir(directory: str) -> list[dict]:
    """Check all markdown files in a directory for overclaim language.
    Returns list of findings.
    """
    dir_path = Path(directory)
    if not dir_path.exists():
        return [
            {"severity": "ERROR", "finding_id": "OPA-DIR-NOT-FOUND", "description": f"Directory not found: {directory}"}
        ]

    files = []
    for md in dir_path.glob("**/*.md"):
        files.append({"path": str(md.relative_to(dir_path)), "content": md.read_text()[:50000]})

    if not files:
        return []

    return check_overclaim_files(files)


def validate_registry_entry(entry: dict) -> list[dict]:
    """Validate a registry entry via OPA."""
    result = _opa_eval("data.governance.registry.validate_entry(input.entry)", {"entry": entry})
    return _parse_findings(result)


def validate_registry_entries(entries: list[dict]) -> list[dict]:
    """Validate a set of registry entries via OPA."""
    result = _opa_eval("data.governance.registry.validate_registry(input.entries)", {"entries": entries})
    return _parse_findings(result)


def _parse_findings(opa_result: dict) -> list[dict]:
    if "error" in opa_result:
        return [{"severity": "ERROR", "finding_id": "OPA-ERROR", "description": opa_result["error"]}]
    findings = []
    for r in opa_result.get("result", []):
        for expr in r.get("expressions", []):
            val = expr.get("value")
            if isinstance(val, list):
                for f in val:
                    if isinstance(f, dict):
                        findings.append(f)
    return findings


def opa_available() -> bool:
    """Check if OPA is installed and policies exist."""
    try:
        proc = subprocess.run(["opa", "version"], capture_output=True, text=True, timeout=5)
        return proc.returncode == 0 and POLICY_DIR.exists()
    except FileNotFoundError:
        return False
