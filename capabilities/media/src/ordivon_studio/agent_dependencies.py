"""Observe exact Studio dependency materializations and propose native acquisition.

Environment checks are read-only. Missing dependencies become explicit plans for
the Runtime/Workstation owner to execute, never side effects of Studio discovery.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
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
    if receipt.get("schemaVersion") != 1 or receipt.get("kind") != "ordivon.studio-python-materialization-receipt":
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
    probe = subprocess.run(
        [str(resolver), "exec", "node", "-e", "process.exit(0)"],
        cwd=root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
        timeout=10,
    )
    ready = probe.returncode == 0
    return {
        "ready": ready,
        "reason": "READY" if ready else "JS_DEPENDENCIES_STALE_OR_UNAVAILABLE",
        "requiredPaths": [str(path.relative_to(root)) for path in required],
        "resolverChecked": True,
        "resolver": str(resolver),
        "boundary": "The project-pinned pnpm resolver performs a non-mutating fail-closed dependency-status check; Studio does not duplicate pnpm currentness semantics.",
    }


def dependency_status(root: Path = ROOT) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.studio-dependency-status",
        "js": _js_status(root),
        "python": _python_receipt_status(root),
        "boundary": "Observation never acquires dependencies. Missing capability is repaired only through an explicit acquisition proposal.",
    }


def dependency_proposal(target: str, root: Path = ROOT) -> dict[str, Any]:
    status = dependency_status(root)
    if target not in {"js", "python"}:
        raise ValueError("dependency target must be js or python")
    current = status[target]
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
