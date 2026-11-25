from __future__ import annotations

import json
import math
import re
import sys
import tomllib
from pathlib import Path
from typing import Any

MAX_CONTRACT_BYTES = 8 * 1024 * 1024
VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def _version(value: str) -> tuple[int, int, int]:
    match = VERSION_RE.fullmatch(value)
    if match is None:
        raise SystemExit(f"packageVersion must be numeric semver: {value!r}")
    return tuple(int(part) for part in match.groups())


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON member")
        result[key] = value
    return result


def _finite(value: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("nonfinite JSON number")
    return result


def _read_json(path: Path) -> Any:
    with path.open("rb") as source:
        raw = source.read(MAX_CONTRACT_BYTES + 1)
    if len(raw) > MAX_CONTRACT_BYTES:
        raise ValueError("native contract exceeds bounded size")
    value = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_unique_object,
        parse_float=_finite,
        parse_constant=_finite,
    )
    # Reject escaped lone surrogates as well as invalid UTF-8 transport bytes.
    json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8")
    return value


def _load_manifest(path: Path) -> dict[str, Any]:
    data = _read_json(path)
    if not isinstance(data, dict):
        raise SystemExit(f"invalid MCP surface manifest: {path}")
    if (
        type(data.get("schemaVersion")) is not int
        or data["schemaVersion"] != 1
        or data.get("kind") != "ordivon.mcp-tool-surface"
    ):
        raise SystemExit(f"invalid MCP surface manifest: {path}")
    tools = data.get("tools")
    if (
        not isinstance(tools, list)
        or not tools
        or not all(isinstance(name, str) and name for name in tools)
        or tools != sorted(set(tools))
    ):
        raise SystemExit(f"tools must be a non-empty sorted unique list: {path}")
    if type(data.get("surfaceEpoch")) is not int or data["surfaceEpoch"] < 1:
        raise SystemExit(f"surfaceEpoch must be a positive integer: {path}")
    _version(str(data.get("packageVersion", "")))
    digest = data.get("contractDigest")
    if digest is not None and (
        not isinstance(digest, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", digest)
    ):
        raise SystemExit(f"invalid native MCP contractDigest: {path}")
    return data


def main() -> None:
    if sys.argv[1:] == ["--emit-native"]:
        import asyncio

        print(json.dumps(asyncio.run(_emit_native_contracts()), sort_keys=True))
        return
    if len(sys.argv) == 4 and sys.argv[1] == "--compare-native":
        try:
            old = _read_json(Path(sys.argv[2]))
            new = _read_json(Path(sys.argv[3]))
            issues = compare_native_tool_contracts(old, new)
        except ValueError, OSError, RecursionError, TypeError:
            issues = ["unqualified native contract representation"]
        print(json.dumps({"compatible": not issues, "incompatibilities": issues}, sort_keys=True))
        if issues:
            raise SystemExit(2)
        return
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
    if "contractDigest" not in candidate:
        raise SystemExit("candidate must carry native MCP tools/list contractDigest")
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
    # The existing Tool names do not uniquely identify a protocol contract:
    # MCP defines inputSchema and optional outputSchema per discovered Tool.
    # Old releases lacking a digest are conservatively treated as changed.
    tools_changed = (
        current["tools"] != candidate["tools"]
        or current.get("contractDigest") != candidate["contractDigest"]
    )
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


def compare_native_tool_contracts(previous: Any, candidate: Any) -> list[str]:
    # The initial manifest check runs on the OS interpreter, but native
    # comparison must use the exact candidate's locked environment.
    from ordivon_gateway.logic.mcp_contract_compatibility import (
        compare_native_tool_contracts as compare,
    )

    return compare(previous, candidate)


async def _emit_native_contracts() -> list[dict[str, Any]]:
    # Use the venv's ORIGINAL installed mcp package and Gateway implementation.
    # No copied registry, Host PG connection, or production effects.
    from mcp import Client

    from ordivon_gateway.mcp_server import build_server

    async with Client(build_server(), raise_exceptions=True) as client:
        tools = (await client.list_tools()).tools
    return [
        {
            "name": row["name"],
            "inputSchema": row["inputSchema"],
            "outputSchema": row.get("outputSchema"),
        }
        for row in (
            tool.model_dump(mode="json", by_alias=True, exclude_none=True) for tool in tools
        )
    ]


if __name__ == "__main__":
    main()
