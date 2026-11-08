"""Independent post-run consistency for declared native tool paths.

Reuses existing provider tool facts and FileCommitment. Not a hermetic runtime,
execution-time path witness, dependency scanner or SLSA provenance claim.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from artifact_core.contracts import FileCommitment

_SHA256 = re.compile(r"[0-9a-f]{64}")


def assess_native_tool_paths(native: dict[str, Any]) -> dict[str, Any]:
    tools = native.get("tools")
    if tools is None or tools == {}:
        return {
            "status": "NOT_EVALUATED", "observed": {}, "rejected": False,
            "issues": [], "dependenciesComplete": False,
            "scope": "No native executable paths declared",
        }
    if not isinstance(tools, dict):
        return {
            "status": "CONTRADICTORY", "observed": {}, "rejected": True,
            "issues": ["native tools is not an object"], "dependenciesComplete": False,
            "scope": "Invalid native executable inventory",
        }

    observed: dict[str, dict[str, Any]] = {}
    issues: list[str] = []
    for name in sorted(tools, key=str):
        fact = tools[name]
        if not isinstance(name, str) or not name or not isinstance(fact, dict):
            issues.append(f"invalid native tool declaration: {name!r}")
            continue
        raw_path, expected = fact.get("path"), fact.get("sha256")
        if (
            not isinstance(raw_path, str)
            or not Path(raw_path).is_absolute()
            or not isinstance(expected, str)
            or _SHA256.fullmatch(expected) is None
        ):
            issues.append(f"native tool identity incomplete: {name}")
            continue
        if fact.get("status", "PASS") != "PASS":
            issues.append(f"native tool not available for observation: {name}")
            continue
        try:
            committed = FileCommitment.from_path(Path(raw_path))
        except (OSError, RuntimeError, ValueError) as error:
            issues.append(f"native tool unreadable after verification: {name}: {type(error).__name__}")
            continue
        observed[name] = {
            "path": str(committed.path),
            "sha256": committed.sha256,
            "size": committed.size,
            "standing": "POSTRUN_PATH_OBSERVATION",
        }
        if committed.sha256 != expected:
            issues.append(f"native tool digest drift after verification: {name}")
        if str(committed.path) != raw_path:
            issues.append(f"native tool path resolution changed: {name}")
    return {
        "status": "CONTRADICTORY" if issues else "OBSERVED_POSTRUN_CONSISTENT",
        "observed": observed,
        "rejected": bool(issues),
        "issues": issues,
        "dependenciesComplete": False,
        "scope": (
            "Independent post-verification executable-path SHA-256 and byte-length "
            "observation. Does not attest loaded executable bytes, imported "
            "libraries, execution-time path continuity, or dependency closure."
        ),
    }
