from __future__ import annotations

import json
import re
import sys
import tomllib
from pathlib import Path
from typing import Any

VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def _version(value: str) -> tuple[int, int, int]:
    match = VERSION_RE.fullmatch(value)
    if match is None:
        raise SystemExit(f"packageVersion must be numeric semver: {value!r}")
    return tuple(int(part) for part in match.groups())


def _load_manifest(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schemaVersion") != 1 or data.get("kind") != "ordivon.mcp-tool-surface":
        raise SystemExit(f"invalid MCP surface manifest: {path}")
    tools = data.get("tools")
    if not isinstance(tools, list) or not tools or tools != sorted(set(tools)):
        raise SystemExit(f"tools must be a non-empty sorted unique list: {path}")
    if not isinstance(data.get("surfaceEpoch"), int) or data["surfaceEpoch"] < 1:
        raise SystemExit(f"surfaceEpoch must be a positive integer: {path}")
    _version(str(data.get("packageVersion", "")))
    return data


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit(
            "usage: verify_tool_surface.py <candidate-manifest> <candidate-pyproject> <current-manifest>"
        )
    candidate_path = Path(sys.argv[1])
    pyproject_path = Path(sys.argv[2])
    current_path = Path(sys.argv[3])
    if not candidate_path.is_file():
        raise SystemExit(f"candidate release is missing {candidate_path.name}")
    candidate = _load_manifest(candidate_path)
    project = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))["project"]
    project_version = str(project["version"])
    if project_version != candidate["packageVersion"]:
        raise SystemExit(
            f"manifest packageVersion {candidate['packageVersion']} != pyproject version {project_version}"
        )
    if not current_path.is_file():
        print(
            f"surface_contract=bootstrap service={candidate['service']} epoch={candidate['surfaceEpoch']} version={project_version}"
        )
        return

    current = _load_manifest(current_path)
    if current["service"] != candidate["service"]:
        raise SystemExit("candidate/current MCP surface service identity differs")
    current_epoch = int(current["surfaceEpoch"])
    candidate_epoch = int(candidate["surfaceEpoch"])
    tools_changed = current["tools"] != candidate["tools"]
    if tools_changed:
        if candidate_epoch <= current_epoch:
            raise SystemExit("tool surface changed without advancing surfaceEpoch")
        if _version(candidate["packageVersion"]) <= _version(current["packageVersion"]):
            raise SystemExit("tool surface changed without advancing packageVersion")
    elif candidate_epoch != current_epoch:
        raise SystemExit("surfaceEpoch changed even though the tool surface is unchanged")
    print(
        "surface_contract=pass "
        f"service={candidate['service']} epoch={candidate_epoch} version={project_version} changed={str(tools_changed).lower()}"
    )


if __name__ == "__main__":
    main()
