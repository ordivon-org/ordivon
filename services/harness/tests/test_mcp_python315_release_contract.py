"""Keep the already-installed MCP product, change only its verified interpreter carrier."""

from __future__ import annotations

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREFIX = (
    "/root/.local/share/ordivon-workstation/agent-automation-mcp-v1/py315-sqlite354-r18-release-v2"
)
INTERPRETER = PREFIX + "/bin/python"


def test_mcp_runtime_uses_versioned_source_qualified_latest_interpreter():
    config = tomllib.loads((ROOT / "config/agent-automation.toml").read_text())["agent_automation"]
    assert config["mcp_runtime_python"] == INTERPRETER
    owner_python = tomllib.loads((ROOT / "mise.toml").read_text())["tools"]["python"]
    assert config["mcp_python_version"] == owner_python
    assert config["mcp_sqlite_version"] == "3.54.0"
    python_minor = ".".join(owner_python.split(".")[:2])
    expected_executable = (
        f"/opt/ordivon/toolchains/python/cpython-{owner_python}-"
        f"sqlite-{config['mcp_sqlite_version']}-official-r18/bin/python{python_minor}"
    )
    assert config["mcp_python_executable"] == expected_executable


def test_mcp_locked_packages_have_real_python315_binary_carrier():
    requirements = (ROOT / "config/agent-automation-mcp-requirements.txt").read_text().splitlines()
    assert "pydantic==2.14.1" in requirements
    assert "pydantic-core==2.50.1" in requirements
    assert "mcp==2.0.0" in requirements
    assert "mcp-types==2.0.0" in requirements
    assert "pydantic-core==2.46.4" not in requirements


def test_mcp_systemd_uses_single_carrier_and_preserves_installed_permissions():
    source = (ROOT / "systemd/ordivon-agent-automation-mcp.service").read_text()
    for directive in ("ExecStartPre=", "ExecStart=", "ExecStartPost="):
        assert directive + INTERPRETER + " " in source
    assert "ReadWritePaths=/mnt/c/ProgramData/Ordivon/chat-ingress/session-continuity" in source
    assert "ProtectSystem=strict" in source
    assert "ProtectHome=read-only" in source
