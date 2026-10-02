#!/usr/bin/env python3
"""Structured Browser Use actions against the operator's current Windows Chrome.

Chrome owns the user profile, login state, and remote-debugging authorization.
Browser Use owns web perception/actions. systemd owns the named Browser Use daemon
outside Runtime Attempt cgroups. This adapter never launches Chrome, copies a
profile, enables remote debugging, or handles browser credentials.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from browser_use_browserless import (
    _run_browser_use,
    program_back,
    program_click,
    program_input,
    program_observe,
    program_open,
    program_scroll,
    program_tabs,
    session_name,
)

WINDOWS_POWERSHELL = Path("/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe")
BROWSER_USE_EXECUTABLE = Path("/root/.local/share/uv/tools/browser-use/bin/browser-use")
BROWSER_USE_PYTHON = BROWSER_USE_EXECUTABLE.parent / "python"
UNIT_RE = re.compile(r"^ordivon-browser-use-windows-[0-9a-f]{24}\.service$")
MAX_CDP_CANDIDATES = 32

WINDOWS_PROBE = r"""
$ErrorActionPreference = 'Stop'
$chrome = @(Get-CimInstance Win32_Process -Filter "name='chrome.exe'")
$ids = @($chrome | ForEach-Object { [int]$_.ProcessId })
$listeners = @()
if ($ids.Count -gt 0) {
  $listeners = @(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
    Where-Object {
      ($_.LocalAddress -eq '127.0.0.1' -or $_.LocalAddress -eq '::1') -and
      $ids -contains [int]$_.OwningProcess
    } |
    Select-Object LocalAddress,LocalPort,OwningProcess)
}
$version = $null
$chromeExe = 'C:\Program Files\Google\Chrome\Application\chrome.exe'
if (Test-Path $chromeExe) {
  $version = (Get-Item $chromeExe).VersionInfo.ProductVersion
}
[pscustomobject]@{
  chromeRunning = ($ids.Count -gt 0)
  chromeVersion = $version
  listenerCount = @($listeners).Count
  listeners = @($listeners)
} | ConvertTo-Json -Compress -Depth 4
"""


def _windows_probe() -> dict[str, Any]:
    if not WINDOWS_POWERSHELL.is_file():
        return {
            "chromeRunning": False,
            "chromeVersion": None,
            "listeners": [],
            "probeStanding": "WINDOWS_INTEROP_UNAVAILABLE",
        }
    proc = subprocess.run(
        [str(WINDOWS_POWERSHELL), "-NoProfile", "-NonInteractive", "-Command", WINDOWS_PROBE],
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=15,
        check=False,
    )
    if proc.returncode != 0:
        return {
            "chromeRunning": False,
            "chromeVersion": None,
            "listeners": [],
            "probeStanding": "WINDOWS_PROBE_FAILED",
            "detail": (proc.stderr or proc.stdout or "")[-1000:].strip(),
        }
    try:
        value = json.loads(proc.stdout.lstrip("\ufeff").strip())
    except json.JSONDecodeError:
        return {
            "chromeRunning": False,
            "chromeVersion": None,
            "listeners": [],
            "probeStanding": "WINDOWS_PROBE_INVALID",
        }
    listeners = value.get("listeners")
    if listeners is None:
        listeners = []
    elif isinstance(listeners, dict):
        listeners = [listeners]
    elif not isinstance(listeners, list):
        listeners = []
    return {
        "chromeRunning": value.get("chromeRunning") is True,
        "chromeVersion": value.get("chromeVersion"),
        "listeners": listeners[:MAX_CDP_CANDIDATES],
        "probeStanding": "OBSERVED",
    }


def _devtools_version(port: int) -> dict[str, Any] | None:
    if not isinstance(port, int) or not 1 <= port <= 65535:
        return None
    url = f"http://127.0.0.1:{port}/json/version"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Ordivon-BrowserUse-CDP-Probe/1"})
        with urllib.request.urlopen(req, timeout=1.0) as response:
            if response.status != 200:
                return None
            raw = response.read(64 * 1024)
    except (OSError, urllib.error.URLError, TimeoutError):
        return None
    try:
        value = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    if not isinstance(value, dict):
        return None
    websocket = value.get("webSocketDebuggerUrl")
    browser = value.get("Browser")
    if not isinstance(websocket, str) or not websocket.startswith("ws://"):
        return None
    if not isinstance(browser, str) or "Chrome" not in browser:
        return None
    return {
        "port": port,
        "httpEndpoint": f"http://127.0.0.1:{port}",
        "browser": browser,
        "protocolVersion": value.get("Protocol-Version"),
    }


def discover_windows_chrome_cdp() -> dict[str, Any]:
    observed = _windows_probe()
    if observed.get("probeStanding") != "OBSERVED":
        return {
            "ready": False,
            "standing": observed.get("probeStanding"),
            "chromeRunning": observed.get("chromeRunning") is True,
            "chromeVersion": observed.get("chromeVersion"),
        }
    if observed.get("chromeRunning") is not True:
        return {
            "ready": False,
            "standing": "WINDOWS_CHROME_UNAVAILABLE",
            "chromeRunning": False,
            "chromeVersion": observed.get("chromeVersion"),
        }
    seen: set[int] = set()
    for row in observed.get("listeners", []):
        try:
            port = int(row.get("LocalPort"))
        except (AttributeError, TypeError, ValueError):
            continue
        if port in seen:
            continue
        seen.add(port)
        value = _devtools_version(port)
        if value is not None:
            return {
                "ready": True,
                "standing": "READY",
                "chromeRunning": True,
                "chromeVersion": observed.get("chromeVersion"),
                "cdpHttpEndpoint": value["httpEndpoint"],
                "cdpPort": port,
                "protocolVersion": value.get("protocolVersion"),
            }
    return {
        "ready": False,
        "standing": "HUMAN_REMOTE_DEBUGGING_REQUIRED",
        "chromeRunning": True,
        "chromeVersion": observed.get("chromeVersion"),
        "observedChromeLoopbackListeners": len(seen),
    }


def _generated_env(session_id: str) -> dict[str, str]:
    env = dict(os.environ)
    env["BU_NAME"] = session_name(session_id)
    env["BH_OPEN_LIVE_URL"] = "0"
    env["BH_TAB_MARKER"] = "0"
    env["BH_REQUIRE_EXISTING_DAEMON"] = "1"
    env.pop("BU_CDP_WS", None)
    env.pop("BU_CDP_URL", None)
    return env


def _owner_unit(session_id: str) -> str:
    digest = session_name(session_id).removeprefix("ordivon-bu-")
    unit = f"ordivon-browser-use-windows-{digest}.service"
    if not UNIT_RE.fullmatch(unit):
        raise ValueError("invalid Browser Use Windows daemon unit")
    return unit


def _daemon_ready(session_id: str, timeout: float = 1.5) -> bool:
    if not BROWSER_USE_EXECUTABLE.is_file():
        return False
    proc = _run_browser_use(
        str(BROWSER_USE_EXECUTABLE),
        'import json\nprint(json.dumps({"standing":"DAEMON_READY","page":page_info()},sort_keys=True))\n',
        _generated_env(session_id),
        timeout=max(1, int(timeout + 0.5)),
    )
    return proc.returncode == 0


def ensure_daemon(session_id: str) -> dict[str, Any]:
    if _daemon_ready(session_id):
        return {"standing": "REUSED", "unit": _owner_unit(session_id)}
    discovery = discover_windows_chrome_cdp()
    if discovery.get("ready") is not True:
        raise RuntimeError(str(discovery.get("standing") or "Windows Chrome CDP unavailable"))
    if not BROWSER_USE_PYTHON.is_file():
        raise RuntimeError("Browser Use Python executable is unavailable")
    unit = _owner_unit(session_id)
    envs = [
        f"BU_NAME={session_name(session_id)}",
        "BH_OPEN_LIVE_URL=0",
        "BH_TAB_MARKER=0",
        f"BU_CDP_URL={discovery['cdpHttpEndpoint']}",
    ]
    argv = [
        "/usr/bin/systemd-run",
        "--unit", unit.removesuffix(".service"),
        "--collect",
        "--property=KillMode=control-group",
        "--property=Restart=no",
    ]
    for entry in envs:
        argv.extend(["--setenv", entry])
    argv.extend([str(BROWSER_USE_PYTHON), "-m", "browser_harness.daemon"])
    proc = subprocess.run(
        argv,
        text=True,
        capture_output=True,
        timeout=20,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "systemd-run failed").strip()[-1200:])
    deadline = time.monotonic() + 20.0
    while time.monotonic() < deadline:
        if _daemon_ready(session_id):
            return {"standing": "STARTED", "unit": unit}
        time.sleep(0.2)
    raise RuntimeError("systemd-owned Windows Browser Use daemon did not become ready")


def execute(session_id: str, program: str, *, timeout: int = 90) -> int:
    ensure_daemon(session_id)
    proc = _run_browser_use(
        str(BROWSER_USE_EXECUTABLE),
        program,
        _generated_env(session_id),
        timeout=timeout,
    )
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=os.sys.stderr)
    return int(proc.returncode)


def close(session_id: str) -> dict[str, Any]:
    proc = subprocess.run(
        [str(BROWSER_USE_EXECUTABLE), "--reload"],
        text=True,
        capture_output=True,
        env={k: v for k, v in _generated_env(session_id).items() if k != "BH_REQUIRE_EXISTING_DAEMON"},
        timeout=15,
        check=False,
    )
    unit = _owner_unit(session_id)
    stop = subprocess.run(
        ["/usr/bin/systemctl", "stop", unit],
        text=True,
        capture_output=True,
        timeout=15,
        check=False,
    )
    return {
        "schemaVersion": 1,
        "kind": "ordivon.browser-use-windows-session-close",
        "sessionId": session_id,
        "daemonOwnerUnit": unit,
        "standing": "CLOSED" if proc.returncode == 0 and stop.returncode == 0 else "HOLD",
        "browserUseReturnCode": proc.returncode,
        "ownerStopReturnCode": stop.returncode,
        "chromeStopped": False,
    }


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--session-id")
    sub = p.add_subparsers(dest="operation", required=True)
    sub.add_parser("doctor")
    op = sub.add_parser("open")
    op.add_argument("--url", required=True)
    obs = sub.add_parser("observe")
    obs.add_argument("--include-text", action="store_true")
    obs.add_argument("--max-chars", type=int, default=6000)
    click = sub.add_parser("click")
    click.add_argument("--index", type=int, required=True)
    click.add_argument("--expect-role", required=True)
    click.add_argument("--expect-name", required=True)
    inp = sub.add_parser("input")
    inp.add_argument("--index", type=int, required=True)
    inp.add_argument("--expect-role", required=True)
    inp.add_argument("--expect-name", required=True)
    inp.add_argument("--text", required=True)
    scroll = sub.add_parser("scroll")
    scroll.add_argument("--dy", type=int, required=True)
    sub.add_parser("back")
    sub.add_parser("tabs")
    sub.add_parser("close")
    return p


def main() -> int:
    a = parser().parse_args()
    if a.operation == "doctor":
        print(json.dumps(discover_windows_chrome_cdp(), sort_keys=True))
        return 0
    if not a.session_id:
        raise SystemExit("--session-id is required for browser actions")
    if a.operation == "close":
        print(json.dumps(close(a.session_id), sort_keys=True))
        return 0
    programs = {
        "open": lambda: program_open(a.url),
        "observe": lambda: program_observe(include_text=a.include_text, max_chars=a.max_chars),
        "click": lambda: program_click(a.index, a.expect_role, a.expect_name),
        "input": lambda: program_input(a.index, a.expect_role, a.expect_name, a.text),
        "scroll": lambda: program_scroll(a.dy),
        "back": program_back,
        "tabs": program_tabs,
    }
    return execute(a.session_id, programs[a.operation]())


if __name__ == "__main__":
    raise SystemExit(main())
