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
            assert manifest["surfaceEpoch"] == 3

    asyncio.run(scenario())


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
