from __future__ import annotations

import asyncio
import json
from importlib.metadata import version
from pathlib import Path

from mcp import Client

from ordivon_host_v2.mcp_server import build_server

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "mcp-surface.json"


def test_release_manifest_matches_exact_mcp_surface_and_package_identity() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    async def scenario() -> None:
        async with Client(
            build_server("postgresql://unused.invalid/unused"), raise_exceptions=True
        ) as client:
            listed = await client.list_tools()
            names = sorted(tool.name for tool in listed.tools)
            assert names == manifest["tools"]
            assert version("ordivon-host-v2") == manifest["packageVersion"]
            assert client.server_info is not None
            assert client.server_info.version == manifest["packageVersion"]
            assert manifest["surfaceEpoch"] == 8

    asyncio.run(scenario())


def test_epoch8_surface_release_advances_package_identity_from_epoch7(tmp_path: Path) -> None:
    import subprocess

    candidate = json.loads(MANIFEST.read_text(encoding="utf-8"))
    current = dict(candidate)
    current["packageVersion"] = "0.9.0"
    current["surfaceEpoch"] = 7
    current["contractDigest"] = "sha256:0c3553e4fb9b9134d9e3867e0419d7b119c78b3a55d48463e5d938810b4a2f3a"
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
    assert result.returncode == 0, result.stderr
    assert "epoch=8" in result.stdout
    assert "version=0.10.0" in result.stdout
    assert "changed=true" in result.stdout


def test_release_guard_rejects_surface_change_without_epoch_advance(tmp_path: Path) -> None:
    import subprocess

    candidate = json.loads(MANIFEST.read_text(encoding="utf-8"))
    current = dict(candidate)
    current["packageVersion"] = "0.3.0"
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
    """A changed MCP input contract must advance the surface epoch and version."""
    import subprocess

    candidate = json.loads(MANIFEST.read_text(encoding="utf-8"))
    current = dict(candidate)
    current["contractDigest"] = "sha256:" + "1" * 64
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


def test_release_manifest_matches_native_mcp_schemas_not_just_names() -> None:
    import importlib.util

    verifier = ROOT / "packaging" / "verify_release.py"
    spec = importlib.util.spec_from_file_location("host_native_contract", verifier)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    asyncio.run(module.main())


def test_installed_sdk_verifier_rejects_schema_drift_even_with_same_names() -> None:
    import importlib.util

    import pytest

    verifier = ROOT / "packaging" / "verify_release.py"
    spec = importlib.util.spec_from_file_location("host_sdk_drift_negative", verifier)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.EXPECTED_CONTRACT_DIGEST = "sha256:" + "1" * 64
    with pytest.raises(BaseExceptionGroup) as error:
        asyncio.run(module.main())
    assert "Host native MCP input/output schema drift" in repr(error.value)


def test_linux_installer_verifies_frozen_host_schema_before_symlink_cutover() -> None:
    installer = (ROOT / "packaging" / "install_release.sh").read_text(encoding="utf-8")
    sdk_check = '"$RELEASE/.venv/bin/python" "$RELEASE/packaging/verify_release.py"'
    assert sdk_check in installer
    assert installer.index(sdk_check) < installer.index(
        'ln -sfn "releases/$COMMIT" "$PREFIX/current.next"'
    )
