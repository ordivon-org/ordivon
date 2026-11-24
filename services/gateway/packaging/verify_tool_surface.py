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
        old = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
        new = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
        issues = compare_native_tool_contracts(old, new)
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


# JSON Schema keywords whose values are subschemas, not arbitrary JSON.
_SCHEMA_MAPS = {"properties", "patternProperties", "$defs", "definitions", "dependentSchemas"}
_SCHEMA_ARRAYS = {"allOf", "anyOf", "oneOf", "prefixItems"}
_SCHEMA_VALUES = {
    "additionalProperties", "unevaluatedProperties", "propertyNames",
    "additionalItems", "unevaluatedItems", "contains", "not", "if", "then", "else",
    "contentSchema", "items",
}
_SCHEMA_ANNOTATIONS = {"title", "description", "examples"}


def _semantic_schema(value: Any) -> Any:
    """Ignore prose only at schema positions; preserve data and named maps.

    JSON Schema properties and definition names can themselves be "title",
    "description" or "examples". Defaults, constants, enumerations and
    unrecognized extension keywords are opaque JSON, never subschemas.
    The comparator is conservative, not a schema implication solver.
    """
    if not isinstance(value, dict):
        return value
    result = {}
    for key, item in value.items():
        if key in _SCHEMA_ANNOTATIONS:
            continue
        if key in _SCHEMA_MAPS and isinstance(item, dict):
            result[key] = {name: _semantic_schema(schema) for name, schema in item.items()}
        elif (key in _SCHEMA_ARRAYS or key == "items") and isinstance(item, list):
            result[key] = [_semantic_schema(schema) for schema in item]
        elif key in _SCHEMA_VALUES:
            result[key] = _semantic_schema(item)
        elif key == "dependencies" and isinstance(item, dict):
            # Legacy dialect: a dependency is either a schema or property names.
            result[key] = {name: _semantic_schema(schema) for name, schema in item.items()}
        else:
            result[key] = item
    return result


def _same_schema(previous: Any, candidate: Any) -> bool:
    # JSON booleans are not numbers, unlike Python's True == 1.
    return json.dumps(_semantic_schema(previous), sort_keys=True) == json.dumps(
        _semantic_schema(candidate), sort_keys=True
    )


def _tool_contract_map(contracts: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(contracts, list):
        raise ValueError("native MCP contracts must be a list")
    values: dict[str, dict[str, Any]] = {}
    for item in contracts:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            raise ValueError("invalid native MCP tool row")
        name = item["name"]
        if not name or name in values or not isinstance(item.get("inputSchema"), dict):
            raise ValueError(f"duplicate/invalid native MCP input tool: {name}")
        if (
            "outputSchema" in item
            and item["outputSchema"] is not None
            and not isinstance(item["outputSchema"], dict)
        ):
            raise ValueError(f"invalid native MCP output schema: {name}")
        values[name] = item
    return values


def _compare_object_schema(
    name: str, field: str, previous: Any, candidate: Any, *, input_side: bool
) -> list[str]:
    issues: list[str] = []
    if previous is None:
        return issues
    if not isinstance(previous, dict) or not isinstance(candidate, dict):
        return [f"{field} removed schema {name}"]
    previous_props = previous.get("properties", {})
    next_props = candidate.get("properties", {})
    previous_defs = previous.get("$defs", {})
    next_defs = candidate.get("$defs", {})
    if not all(
        isinstance(value, dict) for value in (previous_props, next_props, previous_defs, next_defs)
    ):
        return [f"{field} malformed schema {name}"]

    old_required = set(previous.get("required", []))
    new_required = set(candidate.get("required", []))
    required_delta = new_required - old_required if input_side else old_required - new_required
    for prop in sorted(required_delta):
        issues.append(f"{field} {'new' if input_side else 'lost'} required {name}.{prop}")
    for prop in sorted(previous_props.keys() - next_props.keys()):
        issues.append(f"{field} removed field {name}.{prop}")
    for prop in sorted(previous_props.keys() & next_props.keys()):
        if not _same_schema(previous_props[prop], next_props[prop]):
            issues.append(f"{field} changed field {name}.{prop}")
    for definition in sorted(previous_defs.keys() - next_defs.keys()):
        issues.append(f"{field} removed definition {name}.{definition}")
    for definition in sorted(previous_defs.keys() & next_defs.keys()):
        if not _same_schema(previous_defs[definition], next_defs[definition]):
            issues.append(f"{field} changed definition {name}.{definition}")
    # The outer object constraints matter too: additionalProperties=false,
    # oneOf/anyOf, maxProperties and new closed-world clauses can break callers.
    ignored = {"properties", "required", "$defs", "title", "description", "examples"}
    old_outer = {k: v for k, v in previous.items() if k not in ignored}
    new_outer = {k: v for k, v in candidate.items() if k not in ignored}
    if not _same_schema(old_outer, new_outer):
        issues.append(f"{field} changed object constraints {name}")
    return issues


def compare_native_tool_contracts(previous: Any, candidate: Any) -> list[str]:
    """Conservative provider check: old tools and call/result schemas must survive.

    This is NOT a claim of behavioral, authorization, or deployed Agent
    compatibility. A reported change requires owner-qualified consumer
    evidence or a versioned ABI, not a guessed waiver.
    """
    old = _tool_contract_map(previous)
    new = _tool_contract_map(candidate)
    issues = [f"removed tool {name}" for name in sorted(old.keys() - new.keys())]
    for name in sorted(old.keys() & new.keys()):
        issues.extend(
            _compare_object_schema(
                name,
                "input",
                old[name]["inputSchema"],
                new[name]["inputSchema"],
                input_side=True,
            )
        )
        issues.extend(
            _compare_object_schema(
                name,
                "output",
                old[name].get("outputSchema"),
                new[name].get("outputSchema"),
                input_side=False,
            )
        )
    return issues


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
