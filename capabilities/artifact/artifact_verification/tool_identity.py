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
        raw_path = fact.get("path")
        # Some existing family providers report a Node package root and the
        # exact package.json digest, not an executable digest for the directory.
        # Observe the declared regular file; never treat a directory as a
        # hashable executable or claim the complete dependency tree was bound.
        package_manifest = "packageJsonSha256" in fact
        expected = fact.get("packageJsonSha256" if package_manifest else "sha256")
        if (
            not isinstance(raw_path, str)
            or not Path(raw_path).is_absolute()
            or not isinstance(expected, str)
            or _SHA256.fullmatch(expected) is None
            or (package_manifest and "sha256" in fact)
        ):
            issues.append(f"native tool identity incomplete: {name}")
            continue
        if fact.get("status", "PASS") != "PASS":
            issues.append(f"native tool not available for observation: {name}")
            continue
        observed_path = Path(raw_path) / "package.json" if package_manifest else Path(raw_path)
        try:
            committed = FileCommitment.from_path(observed_path)
        except (OSError, RuntimeError, ValueError) as error:
            issues.append(f"native tool unreadable after verification: {name}: {type(error).__name__}")
            continue
        observed[name] = {
            "path": str(committed.path),
            "sha256": committed.sha256,
            "size": committed.size,
            "standing": "POSTRUN_PATH_OBSERVATION",
            "identityScope": "PACKAGE_JSON_ONLY" if package_manifest else "DECLARED_FILE_BYTES",
        }
        if committed.sha256 != expected:
            issues.append(f"native tool digest drift after verification: {name}")
        if str(committed.path) != str(observed_path):
            issues.append(f"native tool path resolution changed: {name}")
    return {
        "status": "CONTRADICTORY" if issues else "OBSERVED_POSTRUN_CONSISTENT",
        "observed": observed,
        "rejected": bool(issues),
        "issues": issues,
        "dependenciesComplete": False,
        "scope": (
            "Independent post-verification declared executable/manifest file SHA-256 "
            "and byte-length observation. A package.json digest does not bind "
            "node_modules or a package directory. Does not attest loaded executable "
            "bytes, imported "
            "libraries, execution-time path continuity, or dependency closure."
        ),
    }
