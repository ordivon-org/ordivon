"""Observe exact Studio dependency materializations and propose native acquisition.

Environment checks are read-only. Missing dependencies become explicit plans for
the Runtime/Workstation owner to execute, never side effects of Studio discovery.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PYTHON_RECEIPT = Path(".venv/.ordivon-materialization.json")
PYTHON_INPUTS = ("pyproject.toml", "uv.lock", ".python-version")


def _digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _python_receipt_status(root: Path) -> dict[str, Any]:
    receipt_path = root / PYTHON_RECEIPT
    python_path = root / ".venv/bin/python"
    result: dict[str, Any] = {
        "ready": False,
        "receipt": str(PYTHON_RECEIPT),
        "python": ".venv/bin/python",
        "reason": None,
    }
    if not python_path.is_file():
        result["reason"] = "PYTHON_ENV_ABSENT"
        return result
    if not receipt_path.is_file():
        result["reason"] = "PYTHON_RECEIPT_ABSENT"
        return result
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        result["reason"] = "PYTHON_RECEIPT_INVALID"
        return result
    if (not isinstance(receipt, dict) or receipt.get("schemaVersion") != 1
            or receipt.get("kind") != "ordivon.studio-python-materialization-receipt"):
        result["reason"] = "PYTHON_RECEIPT_INVALID"
        return result
    inputs = receipt.get("inputs")
    if not isinstance(inputs, dict):
        result["reason"] = "PYTHON_RECEIPT_INVALID"
        return result
    for name in PYTHON_INPUTS:
        path = root / name
        if not path.is_file() or inputs.get(name) != _digest(path):
            result["reason"] = "PYTHON_RECEIPT_STALE"
            return result
    # The materialization receipt is a historical acquisition observation, not
    # evidence of the current executable or its installed package state.
    # Delegate to the same source-owned gate used by the ordinary Studio CLI.
    gate = root / "scripts/require-python-deps.py"
    result["environmentChecked"] = False
    if not gate.is_file():
        result["reason"] = "PYTHON_GATE_UNAVAILABLE"
        return result
    try:
        probe = subprocess.run(
            [sys.executable, "-E", "-s", str(gate.resolve())],
            cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            env={key: value for key, value in os.environ.items() if key != "PYTHONOPTIMIZE"},
            check=False, timeout=45,
        )
    except (OSError, subprocess.TimeoutExpired):
        result["reason"] = "PYTHON_GATE_UNOBSERVED"
        return result
    result["environmentChecked"] = True
    if probe.returncode != 0:
        result["reason"] = "PYTHON_ENV_STALE_OR_UNAVAILABLE"
        return result
    result["ready"] = True
    result["reason"] = "READY"
    result["pythonVersion"] = receipt.get("python")
    result["uvVersion"] = receipt.get("uv")
    return result


def _js_status(root: Path) -> dict[str, Any]:
    required = (root / "node_modules/.modules.yaml", root / "node_modules/.bin/tsc")
    if not all(path.is_file() for path in required):
        return {
            "ready": False,
            "reason": "JS_DEPENDENCIES_ABSENT",
            "requiredPaths": [str(path.relative_to(root)) for path in required],
            "resolverChecked": False,
        }
    resolver_name = shutil.which("pnpm")
    if resolver_name is None:
        return {
            "ready": False,
            "reason": "JS_RESOLVER_UNAVAILABLE",
            "requiredPaths": [str(path.relative_to(root)) for path in required],
            "resolverChecked": False,
        }
    resolver = Path(resolver_name)
    gate = root / "scripts/require-js-deps.mjs"
    base = {
        "requiredPaths": [str(path.relative_to(root)) for path in required],
        "resolver": str(resolver),
        "resolverChecked": False,
        "environmentChecked": False,
    }
    if not gate.is_file():
        return {**base, "ready": False, "reason": "JS_GATE_UNAVAILABLE"}
    try:
        probe = subprocess.run(
            [str(resolver), "exec", "node", str(gate.resolve())],
            cwd=root, capture_output=True, text=True, check=False, timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired, UnicodeError):
        return {**base, "ready": False, "reason": "JS_RESOLVER_UNOBSERVED"}
    # Only the source-owned gate's typed outcome can establish materialization
    # failure. A resolver failure or an unrecognized response is UNKNOWN.
    outcomes = {
        (0, "studio_js_dependencies=ready"): "READY",
        (2, "studio_js_dependencies=not-ready"): "JS_DEPENDENCIES_STALE_OR_UNAVAILABLE",
        (3, "studio_js_dependencies=contract-invalid"): "JS_CONTRACT_INVALID",
        (4, "studio_js_dependencies=unobserved"): "JS_GATE_UNOBSERVED",
    }
    markers = [line for line in probe.stdout.splitlines() if line.startswith("studio_js_dependencies=")]
    reason = outcomes.get((probe.returncode, markers[0])) if len(markers) == 1 else None
    if reason is None:
        return {**base, "ready": False, "reason": "JS_GATE_UNOBSERVED"}
    return {
        **base,
        "ready": reason == "READY",
        "reason": reason,
        "resolverChecked": True,
        "environmentChecked": reason != "JS_GATE_UNOBSERVED",
        "boundary": "Delegate to the project-pinned pnpm resolver and the same Studio CLI package identity gate; neither observation acquires dependencies.",
    }


_UNOBSERVED_REASONS = {
    "PYTHON_GATE_UNAVAILABLE", "PYTHON_GATE_UNOBSERVED",
    "JS_RESOLVER_UNOBSERVED", "JS_RESOLVER_UNAVAILABLE", "JS_GATE_UNAVAILABLE", "JS_GATE_UNOBSERVED",
}


def _standing(status: dict[str, Any]) -> str:
    if status["ready"]:
        return "ready"
    if status["reason"] in _UNOBSERVED_REASONS:
        return "unknown"
    return "not-ready"


def dependency_status(root: Path = ROOT) -> dict[str, Any]:
    js, python = _js_status(root), _python_receipt_status(root)
    return {
        "schemaVersion": 1,
        "kind": "ordivon.studio-dependency-status",
        "js": {**js, "standing": _standing(js)},
        "python": {**python, "standing": _standing(python)},
        "boundary": "Observation never acquires dependencies. Missing capability is repaired only through an explicit acquisition proposal.",
    }


def dependency_proposal(target: str, root: Path = ROOT) -> dict[str, Any]:
    if target not in {"js", "python"}:
        raise ValueError("dependency target must be js or python")
    current = _js_status(root) if target == "js" else _python_receipt_status(root)
    standing = _standing(current)
    current = {**current, "standing": standing}
    if standing == "unknown" or current["reason"] == "JS_CONTRACT_INVALID":
        return {
            "schemaVersion": 1,
            "kind": "ordivon.studio-dependency-acquisition-proposal",
            "target": target,
            "ready": False,
            "effectRequired": None,
            "plan": None,
            "status": current,
            "authorityBoundary": "Observation is unavailable or the declared release contract is invalid; repair that boundary before proposing acquisition.",
        }
    if current["ready"]:
        return {
            "schemaVersion": 1,
            "kind": "ordivon.studio-dependency-acquisition-proposal",
            "target": target,
            "ready": True,
            "effectRequired": False,
            "plan": None,
            "status": current,
        }
    if target == "js":
        executable = shutil.which("pnpm") or "pnpm"
        args = ["install", "--frozen-lockfile"]
    else:
        executable = "/usr/bin/python3"
        args = ["scripts/materialize-python.py"]
    return {
        "schemaVersion": 1,
        "kind": "ordivon.studio-dependency-acquisition-proposal",
        "target": target,
        "ready": False,
        "effectRequired": True,
        "plan": {
            "executable": executable,
            "args": args,
            "cwdRelative": ".",
            "effect": "dependency-materialization",
            "postcondition": "re-observe studio.dependencies.status and require target.ready=true",
        },
        "status": current,
        "authorityBoundary": "Dependency acquisition is explicit mutation authority. Ordinary Studio execution must not invoke this plan implicitly.",
    }
