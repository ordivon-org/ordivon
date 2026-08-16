from __future__ import annotations

import hashlib
import json
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .equipment import load_equipment_world, propose_operation

ROOT = Path(__file__).resolve().parents[2]
PYTHON_RECEIPT = Path(".venv/.ordivon-materialization.json")
PYTHON_INPUTS = ("pyproject.toml", "uv.lock", ".python-version")


def _digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _python_receipt_status(root: Path, *, require_resolve: bool) -> dict[str, Any]:
    receipt_path = root / PYTHON_RECEIPT
    python_path = root / ".venv/bin/python"
    result: dict[str, Any] = {
        "ready": False,
        "receipt": str(PYTHON_RECEIPT),
        "python": ".venv/bin/python",
        "requiredExtra": "resolve" if require_resolve else None,
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
    extras = set(receipt.get("extras", []))
    if require_resolve and "resolve" not in extras:
        result["reason"] = "PYTHON_RESOLVE_EXTRA_ABSENT"
        return result
    result["ready"] = True
    result["reason"] = "READY"
    result["extras"] = sorted(extras)
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
    resolver = Path("/root/tools/bin/pnpm")
    if not resolver.is_file():
        return {
            "ready": False,
            "reason": "JS_RESOLVER_UNAVAILABLE",
            "requiredPaths": [str(path.relative_to(root)) for path in required],
            "resolverChecked": False,
        }
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
        "boundary": "The Workstation pnpm resolver performs a non-mutating fail-closed dependency-status check; Studio does not duplicate pnpm currentness semantics.",
    }


def dependency_status(root: Path = ROOT) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.studio-dependency-status",
        "js": _js_status(root),
        "python": _python_receipt_status(root, require_resolve=False),
        "resolve": _python_receipt_status(root, require_resolve=True),
        "boundary": "Observation never acquires dependencies. Missing capability is repaired only through an explicit acquisition proposal.",
    }


def dependency_proposal(target: str, root: Path = ROOT) -> dict[str, Any]:
    status = dependency_status(root)
    if target not in {"js", "python", "resolve"}:
        raise ValueError("dependency target must be js, python, or resolve")
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
        executable = "/root/tools/bin/pnpm"
        args = ["install", "--frozen-lockfile"]
    else:
        executable = "/usr/bin/python3"
        args = ["scripts/materialize-python.py"] + (["--extra", "resolve"] if target == "resolve" else [])
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


def tool_definitions() -> list[dict[str, Any]]:
    return [
        {
            "name": "studio_dependencies_status",
            "description": "Observe whether Studio JavaScript, core Python, and Resolve Python dependencies are exactly materialized in this Workspace. This never installs anything.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "studio_dependencies_propose",
            "description": "Compile an explicit dependency-materialization proposal for one missing Studio capability. It does not execute the acquisition; ordinary execution must never acquire implicitly.",
            "inputSchema": {
                "type": "object",
                "properties": {"target": {"type": "string", "enum": ["js", "python", "resolve"]}},
                "required": ["target"],
                "additionalProperties": False,
            },
        },
        {
            "name": "studio_equipment_propose",
            "description": "Select freshly observed equipment for one exact Studio capability and compile a truthful operation proposal with readiness, blockers, exact physical plan, and owner-specific verification contract. This does not execute the effect.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "capability": {"type": "string", "minLength": 1},
                    "equipmentId": {"type": "string", "minLength": 1},
                    "parameters": {"type": "object"},
                },
                "required": ["capability", "parameters"],
                "additionalProperties": False,
            },
        },
    ]


def execute_surface_action(name: str, arguments: Mapping[str, Any], *, root: Path = ROOT) -> dict[str, Any]:
    if name == "studio_dependencies_status":
        return dependency_status(root)
    if name == "studio_dependencies_propose":
        return dependency_proposal(str(arguments["target"]), root)
    if name == "studio_equipment_propose":
        world = load_equipment_world(root / "research/equipment/equipment-world.json")
        equipment_id = arguments.get("equipmentId")
        if equipment_id is not None and not isinstance(equipment_id, str):
            raise ValueError("equipmentId must be a string when supplied")
        parameters = arguments.get("parameters")
        if not isinstance(parameters, Mapping):
            raise ValueError("parameters must be an object")
        return propose_operation(
            world,
            str(arguments["capability"]),
            dict(parameters),
            equipment_id=equipment_id,
            local=True,
        )
    raise ValueError(f"unsupported Studio Agent surface action: {name}")


def surface_projection() -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.studio-agent-tool-surface",
        "truthRole": "studio-domain-semantic-actions",
        "domainId": "domain:ordivon-studio",
        "revision": "studio-agent-surface-af6-v1",
        "tools": tool_definitions(),
        "runtimeOwnsPhysicalExecution": True,
        "harnessMayAdmitSubsetOnly": True,
        "mcpRequired": False,
        "boundary": "Studio owns readiness, dependency and medium semantics. Harness may bind these definitions into a turn but does not gain Studio authority; Runtime remains the physical executor of compiled plans.",
    }
