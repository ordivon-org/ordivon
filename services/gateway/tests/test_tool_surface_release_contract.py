from __future__ import annotations

import asyncio
import json
from importlib.metadata import version
from pathlib import Path

from mcp import Client

from ordivon_gateway.mcp_server import build_server

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "mcp-surface.json"


def test_release_manifest_matches_exact_mcp_surface_and_package_identity() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    async def scenario() -> None:
        async with Client(build_server(), raise_exceptions=True) as client:
            listed = await client.list_tools()
            names = sorted(tool.name for tool in listed.tools)
            assert names == manifest["tools"]
            assert version("ordivon-gateway") == manifest["packageVersion"]
            assert client.server_info is not None
            assert client.server_info.version == manifest["packageVersion"]
            assert manifest["surfaceEpoch"] == 18
            import importlib.util

            verifier = ROOT / "packaging" / "windows" / "verify_release.py"
            spec = importlib.util.spec_from_file_location(
                "gateway_native_contract_digest", verifier
            )
            assert spec is not None and spec.loader is not None
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            assert module.native_tool_contract_digest(listed.tools) == manifest["contractDigest"]

    asyncio.run(scenario())


def test_release_guard_rejects_surface_change_without_epoch_advance(tmp_path: Path) -> None:
    import subprocess

    candidate = json.loads(MANIFEST.read_text(encoding="utf-8"))
    current = dict(candidate)
    current["packageVersion"] = "0.4.0"
    current["tools"] = candidate["tools"][:-1]
    current_path = tmp_path / "current.json"
    current_path.write_text(json.dumps(current), encoding="utf-8")
    result = subprocess.run(
        [
            "python3",
            str(ROOT / "packaging" / "verify_tool_surface.py"),
            str(MANIFEST),
            str(ROOT / "pyproject.toml"),
            str(current_path),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode != 0
    assert "without advancing surfaceEpoch" in result.stderr


def test_release_guard_detects_schema_drift_with_unchanged_tool_names(tmp_path: Path) -> None:
    """Changing MCP inputs with the same names must advance release identity."""
    import subprocess

    candidate = json.loads(MANIFEST.read_text(encoding="utf-8"))
    candidate["contractDigest"] = "sha256:" + "1" * 64
    current = dict(candidate)
    current["contractDigest"] = "sha256:" + "0" * 64
    candidate_path = tmp_path / "candidate.json"
    current_path = tmp_path / "current.json"
    candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
    current_path.write_text(json.dumps(current), encoding="utf-8")
    result = subprocess.run(
        [
            "python3",
            str(ROOT / "packaging" / "verify_tool_surface.py"),
            str(candidate_path),
            str(ROOT / "pyproject.toml"),
            str(current_path),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode != 0
    assert "without advancing surfaceEpoch" in result.stderr


def test_linux_release_promotion_requires_actual_installed_sdk_surface() -> None:
    # Static source manifest checks do not prove what the installed MCP SDK
    # and owner server really expose after the frozen environment is created.
    installer = (ROOT / "packaging" / "install_release.sh").read_text(encoding="utf-8")
    sdk_check = '"$RELEASE/.venv/bin/python" "$RELEASE/packaging/windows/verify_release.py"'
    assert sdk_check in installer
    assert installer.index(sdk_check) < installer.index(
        'ln -sfn "releases/$COMMIT" "$PREFIX/current.next"'
    )


def test_installed_sdk_verifier_fails_closed_when_live_tool_set_differs() -> None:
    # Real MCP SDK + real Gateway server, with a deliberately wrong expected
    # surface. A JSON manifest alone cannot detect this candidate drift.
    import importlib.util

    import pytest

    verifier = ROOT / "packaging" / "windows" / "verify_release.py"
    spec = importlib.util.spec_from_file_location("gateway_sdk_release_consumer", verifier)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.EXPECTED = module.EXPECTED[:-1]
    with pytest.raises(BaseExceptionGroup) as error:
        asyncio.run(module.main())
    assert "Gateway MCP surface drift" in repr(error.value)


def test_installed_sdk_verifier_rejects_schema_drift_even_when_tools_unchanged() -> None:
    """Official SDK tools/list schema matters, even if all names remain."""
    import importlib.util

    import pytest

    verifier = ROOT / "packaging" / "windows" / "verify_release.py"
    spec = importlib.util.spec_from_file_location("gateway_sdk_schema_consumer", verifier)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.EXPECTED_CONTRACT_DIGEST = "sha256:" + "0" * 64
    with pytest.raises(BaseExceptionGroup) as error:
        asyncio.run(module.main())
    assert "Gateway MCP tool input/output schema drift" in repr(error.value)


def test_linux_release_installer_enforces_surface_manifest() -> None:
    installer = (ROOT / "packaging" / "install_release.sh").read_text(encoding="utf-8")
    assert "verify_tool_surface.py" in installer
    assert '"$RELEASE/mcp-surface.json"' in installer


def _native_abi_verifier():
    """Reuse the existing release verifier, never introduce another tool registry."""
    import importlib.util

    verifier = ROOT / "packaging" / "verify_tool_surface.py"
    spec = importlib.util.spec_from_file_location("gateway_native_public_abi", verifier)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _old_client_contract() -> list[dict]:
    return [
        {
            "name": "topic.list",
            "inputSchema": {
                "type": "object",
                "properties": {"spaceRef": {"type": "string"}},
                "required": ["spaceRef"],
            },
            "outputSchema": {
                "type": "object",
                "properties": {"topics": {"type": "array"}},
                "required": ["topics"],
            },
        }
    ]


def test_native_public_abi_preserves_old_clients_after_optional_addition() -> None:
    from copy import deepcopy

    old = _old_client_contract()
    candidate = deepcopy(old)
    candidate[0]["inputSchema"]["properties"]["includeArchived"] = {
        "type": "boolean",
        "default": False,
        "title": "Includearchived",
    }
    candidate.append(
        {"name": "capability.search", "inputSchema": {"type": "object"}, "outputSchema": None}
    )
    assert _native_abi_verifier().compare_native_tool_contracts(old, candidate) == []


def test_native_public_abi_detects_deleted_tool_and_argument() -> None:
    from copy import deepcopy

    old = _old_client_contract()
    assert any(
        "removed tool topic.list" in e
        for e in _native_abi_verifier().compare_native_tool_contracts(old, [])
    )
    candidate = deepcopy(old)
    del candidate[0]["inputSchema"]["properties"]["spaceRef"]
    assert any(
        "input removed field topic.list.spaceRef" in e
        for e in _native_abi_verifier().compare_native_tool_contracts(old, candidate)
    )


def test_native_public_abi_detects_new_required_and_tightened_input() -> None:
    from copy import deepcopy

    old = _old_client_contract()
    candidate = deepcopy(old)
    candidate[0]["inputSchema"]["properties"]["includeArchived"] = {"type": "boolean"}
    candidate[0]["inputSchema"]["required"].append("includeArchived")
    assert any(
        "input new required topic.list.includeArchived" in e
        for e in _native_abi_verifier().compare_native_tool_contracts(old, candidate)
    )

    candidate = deepcopy(old)
    candidate[0]["inputSchema"]["properties"]["spaceRef"] = {"type": "string", "minLength": 100}
    assert any(
        "input changed field topic.list.spaceRef" in e
        for e in _native_abi_verifier().compare_native_tool_contracts(old, candidate)
    )


def test_native_public_abi_detects_output_contract_loss() -> None:
    from copy import deepcopy

    old = _old_client_contract()
    candidate = deepcopy(old)
    candidate[0]["outputSchema"]["properties"].pop("topics")
    assert any(
        "output removed field topic.list.topics" in e
        for e in _native_abi_verifier().compare_native_tool_contracts(old, candidate)
    )


def test_native_public_abi_ignores_descriptions_but_not_defaults() -> None:
    from copy import deepcopy

    old = _old_client_contract()
    old[0]["inputSchema"]["properties"]["spaceRef"]["description"] = "Original"
    candidate = deepcopy(old)
    candidate[0]["inputSchema"]["properties"]["spaceRef"]["description"] = "Updated"
    assert _native_abi_verifier().compare_native_tool_contracts(old, candidate) == []
    candidate[0]["inputSchema"]["properties"]["spaceRef"]["default"] = "unexpected"
    assert any(
        "input changed field topic.list.spaceRef" in e
        for e in _native_abi_verifier().compare_native_tool_contracts(old, candidate)
    )


def test_release_native_public_abi_gate_is_before_atomic_promotion() -> None:
    """A changed digest/epoch alone cannot authorize breaking older Agents."""
    installer = (ROOT / "packaging" / "install_release.sh").read_text(encoding="utf-8")
    assert '"$PREFIX/current/.venv/bin/python"' in installer
    assert "--emit-native" in installer
    assert "--compare-native" in installer
    assert "native_public_abi=INCOMPATIBLE" in installer
    assert installer.index("--compare-native") < installer.index('ln -sfn "releases/$COMMIT"')
    # Preparations can preserve a precise incompatibility report, while
    # promotion MUST fail before changing the existing current symlink.
    assert 'if [ "$PREPARE_ONLY" != true ]; then' in installer


def test_native_public_abi_detects_lost_required_output_and_schema_definition() -> None:
    from copy import deepcopy

    old = _old_client_contract()
    new = deepcopy(old)
    new[0]["outputSchema"]["required"] = []
    assert any(
        "output lost required topic.list.topics" in e
        for e in _native_abi_verifier().compare_native_tool_contracts(old, new)
    )
    old[0]["inputSchema"]["$defs"] = {"Custom": {"type": "string"}}
    new = deepcopy(old)
    new[0]["inputSchema"]["$defs"]["Custom"] = {"type": "integer"}
    assert any(
        "input changed definition topic.list.Custom" in e
        for e in _native_abi_verifier().compare_native_tool_contracts(old, new)
    )


def test_native_abi_preserves_schema_named_fields_and_literal_values() -> None:
    """Schema annotations are not names in a property map or JSON values."""
    from copy import deepcopy

    verifier = _native_abi_verifier()
    old = _old_client_contract()
    old[0]["inputSchema"]["properties"]["data"] = {
        "type": "object",
        "properties": {key: {"type": "string"} for key in ("description", "title", "examples")},
        "required": ["description", "title", "examples"],
        "description": "original documentation",
    }
    for name in ("description", "title", "examples"):
        new = deepcopy(old)
        new[0]["inputSchema"]["properties"]["data"]["properties"][name]["type"] = "integer"
        assert verifier.compare_native_tool_contracts(old, new), name
    for keyword, key in (("default", "description"), ("const", "title"), ("enum", "examples")):
        literal_old = deepcopy(old)
        literal = {name: "original" for name in ("description", "title", "examples")}
        literal_old[0]["inputSchema"]["properties"]["data"][keyword] = (
            [literal] if keyword == "enum" else literal
        )
        new = deepcopy(literal_old)
        value = new[0]["inputSchema"]["properties"]["data"][keyword]
        (value[0] if keyword == "enum" else value)[key] = "different"
        assert verifier.compare_native_tool_contracts(literal_old, new), keyword
    new = deepcopy(old)
    new[0]["inputSchema"]["properties"]["data"]["description"] = "new prose"
    new[0]["inputSchema"]["properties"]["data"]["properties"]["title"]["title"] = "new title"
    assert verifier.compare_native_tool_contracts(old, new) == []


def test_native_abi_preserves_names_and_schema_positions_under_applicators() -> None:
    from copy import deepcopy

    verifier = _native_abi_verifier()
    old = _old_client_contract()
    old[0]["outputSchema"]["properties"]["topics"] = {
        "type": "array",
        "items": {
            "anyOf": [{
                "type": "object",
                "$defs": {"title": {"type": "string"}},
                "properties": {"description": {"$ref": "#/$defs/title"}},
                "patternProperties": {"examples": {"type": "string"}},
                "dependentSchemas": {"title": {"required": ["description"]}},
            }, {"type": "null"}],
        },
    }
    for map_name, name, replacement in (
        ("$defs", "title", {"type": "integer"}),
        ("patternProperties", "examples", {"type": "integer"}),
        ("dependentSchemas", "title", {"required": ["other"]}),
    ):
        new = deepcopy(old)
        new[0]["outputSchema"]["properties"]["topics"]["items"]["anyOf"][0][map_name][name] = replacement
        assert verifier.compare_native_tool_contracts(old, new), map_name
    new = deepcopy(old)
    new[0]["outputSchema"]["properties"]["topics"]["items"]["anyOf"][0]["$defs"]["title"]["description"] = "prose"
    assert verifier.compare_native_tool_contracts(old, new) == []


def test_native_abi_does_not_equate_boolean_and_number_in_json_values() -> None:
    from copy import deepcopy

    old = _old_client_contract()
    old[0]["inputSchema"]["properties"]["spaceRef"] = {
        "type": "object", "default": {"description": True},
    }
    new = deepcopy(old)
    new[0]["inputSchema"]["properties"]["spaceRef"]["default"] = {"description": 1}
    assert _native_abi_verifier().compare_native_tool_contracts(old, new)


def test_native_sdk_nested_business_field_change_rejects_old_valid_call() -> None:
    """The actual SDK creates same-named nested definitions, not hand-written schema."""
    from mcp.server import MCPServer
    from pydantic import create_model

    async def observe(field_type):
        payload = create_model("Payload", description=(field_type, ...))
        outer = create_model("Outer", data=(payload, ...))

        def tool(value):
            return value

        tool.__annotations__ = {"value": outer, "return": outer}
        server = MCPServer("abi-context-native")
        server.tool(name="sample.tool")(tool)
        async with Client(server, raise_exceptions=False) as client:
            listed = (await client.list_tools()).tools
            assert len(listed) == 1
            response = await client.call_tool(
                "sample.tool", {"value": {"data": {"description": "old-valid"}}}
            )
            row = listed[0]
            return [{
                "name": row.name,
                "inputSchema": row.input_schema,
                "outputSchema": row.output_schema,
            }], response.is_error

    old, old_error = asyncio.run(observe(str))
    candidate, candidate_error = asyncio.run(observe(int))
    assert not old_error
    assert candidate_error
    changes = _native_abi_verifier().compare_native_tool_contracts(old, candidate)
    assert "input changed definition sample.tool.Payload" in changes
    assert "output changed definition sample.tool.Payload" in changes
