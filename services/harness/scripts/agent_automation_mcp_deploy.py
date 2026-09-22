#!/usr/bin/env python3
"""Narrow local deployment for Agent Automation MCP only."""

from __future__ import annotations
import argparse
import hashlib
import json
import os
import secrets
import shutil
import stat
import subprocess
import tempfile
import time
import tomllib
import sys
from pathlib import Path

DEFAULT_SOURCE_ROOT = Path(__file__).resolve().parents[1]
ROOT = Path(
    os.environ.get("ORDIVON_AGENT_AUTOMATION_SOURCE_ROOT", str(DEFAULT_SOURCE_ROOT))
).resolve()
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from browserless_podman_deploy import render_config as render_browserless_config  # noqa: E402

CONTRACT = ROOT / "config/agent-automation.toml"
UNIT_SOURCE = ROOT / "systemd/ordivon-agent-automation-mcp.service"


def digest(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def atomic(path: Path, raw: bytes, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as h:
            h.write(raw)
            h.flush()
            os.fsync(h.fileno())
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def cfg() -> dict:
    return tomllib.loads(CONTRACT.read_text())["agent_automation"]


def source_revision() -> str:
    marker = ROOT / ".ordivon-agent-automation-release.json"
    if marker.is_file():
        try:
            row = json.loads(marker.read_text())
        except json.JSONDecodeError as error:
            raise RuntimeError("Agent Automation release marker is malformed") from error
        value = row.get("commit") if isinstance(row, dict) else None
    else:
        proc = subprocess.run(
            ["/usr/bin/git", "-C", str(ROOT), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
        value = proc.stdout.strip()
    if (
        not isinstance(value, str)
        or len(value) != 40
        or any(ch not in "0123456789abcdef" for ch in value)
    ):
        raise RuntimeError("Agent Automation source revision is not one lowercase Git object ID")
    return value


def runtime_config(c: dict) -> dict:
    value = render_browserless_config()
    value["materializationCarrier"] = c.get("materialization_carrier", "browserless")
    user_browser = c.get("windows_user_browser")
    if user_browser is not None:
        value["windowsUserBrowser"] = {
            "gatewayUrl": user_browser["gateway_url"],
            "workspaceId": user_browser["workspace_id"],
            "powershellPath": user_browser["powershell_path"],
            "driverPath": user_browser["driver_path"],
            "proxyUrl": user_browser["proxy_url"],
            "linuxStageRoot": user_browser["linux_stage_root"],
            "windowsStageRoot": user_browser["windows_stage_root"],
            "timeoutMs": int(user_browser["timeout_ms"]),
        }
    return value


def private_token(path: Path, create: bool) -> dict:
    if not path.exists() and create:
        atomic(path, (secrets.token_urlsafe(48) + "\n").encode(), 0o600)
    if path.is_symlink() or not path.is_file():
        raise RuntimeError("MCP token is absent or not a regular file")
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode != 0o600:
        raise RuntimeError(f"MCP token mode must be 0600, observed {oct(mode)}")
    value = path.read_text().strip()
    if len(value) < 32 or any(ch.isspace() for ch in value):
        raise RuntimeError("MCP token content is invalid")
    return {"path": str(path), "mode": "0600", "present": True}


def _runtime_versions(py: Path) -> dict:
    code = """import importlib.metadata as m,json\nnames=["mcp","mcp-types","uvicorn","pydantic","jsonschema","rfc8785"]\nforbidden={}\nfor n in ["ordivon-protocol"]:\n try: forbidden[n]=m.version(n)\n except m.PackageNotFoundError: forbidden[n]=None\nprint(json.dumps({"versions":{n:m.version(n) for n in names},"forbidden":forbidden},sort_keys=True))"""
    proc = subprocess.run(
        [str(py), "-c", code], capture_output=True, text=True, timeout=10, check=True
    )
    return json.loads(proc.stdout)


def runtime_check(c: dict) -> dict:
    py = Path(c["mcp_runtime_python"])
    if not py.is_file():
        raise RuntimeError("dedicated MCP Python runtime is absent")
    observed = _runtime_versions(py)
    versions = observed["versions"]
    expected = {
        "mcp": "2.0.0",
        "mcp-types": "2.0.0",
        "uvicorn": "0.52.1",
        "pydantic": "2.13.4",
        "jsonschema": "4.26.0",
        "rfc8785": "0.1.4",
    }
    if versions != expected:
        raise RuntimeError(f"MCP runtime versions differ: {versions}")
    forbidden = observed.get("forbidden") or {}
    if forbidden.get("ordivon-protocol") is not None:
        raise RuntimeError(f"retired Ordivon Protocol remains installed: {forbidden}")
    return {
        "python": str(py),
        "versions": versions,
        "forbidden": forbidden,
        "pythonDigest": digest(py.read_bytes()),
    }


def converge_runtime(c: dict) -> dict:
    try:
        value = runtime_check(c)
        value["disposition"] = "existing"
        return value
    except Exception:
        pass
    py = Path(c["mcp_runtime_python"])
    venv = py.parent.parent
    staging = venv.parent / (venv.name + ".staging")
    backup = venv.parent / (venv.name + ".previous")
    shutil.rmtree(staging, ignore_errors=True)
    shutil.rmtree(backup, ignore_errors=True)
    subprocess.run(
        [
            "/usr/bin/uv",
            "venv",
            "--offline",
            "--no-python-downloads",
            "--python",
            str(c["mcp_python_version"]),
            str(staging),
        ],
        check=True,
        timeout=60,
    )
    requirements = ROOT / str(c["mcp_requirements"])
    subprocess.run(
        [
            "/usr/bin/uv",
            "pip",
            "install",
            "--offline",
            "--python",
            str(staging / "bin/python"),
            "-r",
            str(requirements),
        ],
        check=True,
        timeout=120,
    )
    staged = dict(c)
    staged["mcp_runtime_python"] = str(staging / "bin/python")
    runtime_check(staged)
    had_live = venv.exists()
    if had_live:
        os.replace(venv, backup)
    try:
        os.replace(staging, venv)
        value = runtime_check(c)
    except Exception:
        shutil.rmtree(venv, ignore_errors=True)
        if had_live and backup.exists():
            os.replace(backup, venv)
        raise
    else:
        shutil.rmtree(backup, ignore_errors=True)
        value["disposition"] = "materialized"
        return value
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def desired(c: dict) -> tuple[bytes, bytes]:
    conf = (json.dumps(runtime_config(c), sort_keys=True, indent=2) + "\n").encode()
    unit = UNIT_SOURCE.read_bytes()
    return conf, unit


def check() -> dict:
    c = cfg()
    conf, unit = desired(c)
    config_path = Path(c["mcp_config"])
    unit_path = Path("/etc/systemd/system") / c["mcp_unit"]
    token_path = Path(c["mcp_token_file"])
    token = private_token(token_path, False)
    runtime = runtime_check(c)
    if config_path.read_bytes() != conf or stat.S_IMODE(config_path.stat().st_mode) != 0o600:
        raise RuntimeError("installed MCP config differs from Agent Automation contract")
    if unit_path.read_bytes() != unit or stat.S_IMODE(unit_path.stat().st_mode) != 0o644:
        raise RuntimeError("installed MCP unit differs from source")
    active = (
        subprocess.run(["/usr/bin/systemctl", "is-active", "--quiet", c["mcp_unit"]]).returncode
        == 0
    )
    enabled = (
        subprocess.run(["/usr/bin/systemctl", "is-enabled", "--quiet", c["mcp_unit"]]).returncode
        == 0
    )
    if not active or not enabled:
        raise RuntimeError("Agent Automation MCP service is not enabled+active")
    return {
        "schemaVersion": 1,
        "kind": "ordivon.agent-automation-mcp-deployment",
        "standing": "current",
        "configDigest": digest(conf),
        "unitDigest": digest(unit),
        "token": token,
        "runtime": runtime,
        "unit": c["mcp_unit"],
        "endpoint": f"http://{c['mcp_bind']}:{c['mcp_port']}/mcp",
    }


def apply() -> dict:
    if os.geteuid() != 0:
        raise RuntimeError("root authority required")
    c = cfg()
    conf, unit = desired(c)
    config_path = Path(c["mcp_config"])
    unit_path = Path("/etc/systemd/system") / c["mcp_unit"]
    token_path = Path(c["mcp_token_file"])
    token_existed_before = token_path.exists()
    runtime = converge_runtime(c)
    private_token(token_path, True)
    for raw in (c["state_root"],):
        root = Path(raw)
        if root.exists() and (root.is_symlink() or not root.is_dir()):
            raise RuntimeError(f"Agent Automation writable root is not a directory: {root}")
        root.mkdir(parents=True, exist_ok=True)
    changes = []
    if (
        not config_path.exists()
        or config_path.read_bytes() != conf
        or stat.S_IMODE(config_path.stat().st_mode) != 0o600
    ):
        atomic(config_path, conf, 0o600)
        changes.append(str(config_path))
    if (
        not unit_path.exists()
        or unit_path.read_bytes() != unit
        or stat.S_IMODE(unit_path.stat().st_mode) != 0o644
    ):
        atomic(unit_path, unit, 0o644)
        changes.append(str(unit_path))
        subprocess.run(["/usr/bin/systemctl", "daemon-reload"], check=True)
    subprocess.run(
        ["/usr/bin/systemctl", "enable", c["mcp_unit"]], check=True, capture_output=True, text=True
    )
    active_before = (
        subprocess.run(["/usr/bin/systemctl", "is-active", "--quiet", c["mcp_unit"]]).returncode
        == 0
    )
    need_restart = (
        bool(changes) or not token_existed_before or runtime.get("disposition") == "materialized"
    )
    if active_before and need_restart:
        subprocess.run(
            ["/usr/bin/systemctl", "restart", c["mcp_unit"]],
            check=True,
            capture_output=True,
            text=True,
        )
    elif not active_before:
        subprocess.run(
            ["/usr/bin/systemctl", "start", c["mcp_unit"]],
            check=True,
            capture_output=True,
            text=True,
        )
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        if (
            subprocess.run(["/usr/bin/systemctl", "is-active", "--quiet", c["mcp_unit"]]).returncode
            == 0
        ):
            break
        time.sleep(0.25)
    result = check()
    result["standing"] = "materialized"
    result["changedPaths"] = changes
    result["tokenCreated"] = not token_existed_before
    return result


def main() -> int:
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--apply", action="store_true")
    g.add_argument("--check", action="store_true")
    a = p.parse_args()
    print(json.dumps(apply() if a.apply else check(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
