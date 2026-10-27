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
            assert manifest["surfaceEpoch"] == 6
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
