#!/usr/bin/env python3
"""Read-only readiness projection for the operator's existing Windows Chrome.

This adapter observes the Workstation-materialized Browser Harness executable,
running Chrome state, user-owned remote-debugging consent, and Browser Harness
daemon/browser health. It never launches Chrome, enables consent, navigates,
clicks, types, or grants browser/provider effect authority.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

WINDOWS_POWERSHELL = Path("/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe")
DEFAULT_WORKSTATION_STATUS = Path("/root/tools/bin/workstation-windows-jev-provider")
EXPECTED_BROWSER_HARNESS_VERSION = "0.1.13"

WINDOWS_PROBE = r"""
$ErrorActionPreference='SilentlyContinue'
$browserHarness='__BROWSER_HARNESS__'
$chromeExe='C:\Program Files\Google\Chrome\Application\chrome.exe'
$chrome=@(Get-Process chrome -ErrorAction SilentlyContinue)
$chromeVersion=$null
if(Test-Path $chromeExe){$chromeVersion=(Get-Item $chromeExe).VersionInfo.ProductVersion}
$devTools=Join-Path $env:LOCALAPPDATA 'Google\Chrome\User Data\DevToolsActivePort'
$port=$null
$endpointReady=$false
if(Test-Path $devTools){
  $lines=@(Get-Content -LiteralPath $devTools -ErrorAction SilentlyContinue)
  $parsed=0
  if($lines.Count -ge 1 -and [int]::TryParse([string]$lines[0],[ref]$parsed)){
    $port=$parsed
    try{
      $response=Invoke-WebRequest -UseBasicParsing -Uri ("http://127.0.0.1:{0}/json/version" -f $port) -TimeoutSec 2
      $reply=([string]$response.Content) | ConvertFrom-Json
      $endpointReady=($response.StatusCode -eq 200 -and $null -ne $reply -and [string]$reply.Browser -match 'Chrome')
    }catch{$endpointReady=$false}
  }
}
$doctor=$null
$doctorExit=$null
if(Test-Path $browserHarness){
  $raw=& $browserHarness doctor --json 2>$null
  $doctorExit=$LASTEXITCODE
  try{$doctor=($raw -join [Environment]::NewLine) | ConvertFrom-Json}catch{$doctor=$null}
}
[pscustomobject]@{
  browserHarnessPresent=(Test-Path $browserHarness)
  chromeRunning=($chrome.Count -gt 0)
  chromeVersion=$chromeVersion
  devToolsActivePortPresent=(Test-Path $devTools)
  cdpPort=$port
  cdpEndpointReady=$endpointReady
  doctorExitCode=$doctorExit
  doctor=$doctor
} | ConvertTo-Json -Compress -Depth 6
"""


def _workstation_status(command: Path = DEFAULT_WORKSTATION_STATUS) -> dict[str, Any] | None:
    if not command.is_file():
        return None
    try:
        proc = subprocess.run(
            [str(command), "status"],
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=12,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"healthy": False, "standing": "WORKSTATION_STATUS_TIMEOUT"}
    except OSError:
        return {"healthy": False, "standing": "WORKSTATION_STATUS_UNAVAILABLE"}
    if proc.returncode != 0:
        return {"healthy": False, "standing": "WORKSTATION_STATUS_FAILED"}
    try:
        value = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def _managed_browser_harness_windows(status: dict[str, Any]) -> str | None:
    python = status.get("python")
    packages = status.get("packages")
    if (
        status.get("healthy") is not True
        or not isinstance(python, dict)
        or not isinstance(packages, dict)
        or packages.get("exact") is not True
        or packages.get("browserHarnessVersion") != EXPECTED_BROWSER_HARNESS_VERSION
    ):
        return None
    venv_python = python.get("providerVenvWindows")
    suffix = r"\Scripts\python.exe"
    if not isinstance(venv_python, str) or not venv_python.lower().endswith(suffix.lower()):
        return None
    return venv_python[: -len("python.exe")] + "browser-harness.exe"


def _probe() -> dict[str, Any]:
    base = {
        "executionTarget": "windows_native",
        "windowsAuthority": "active_user",
    }
    status = _workstation_status()
    managed = _managed_browser_harness_windows(status or {})
    if managed is None:
        packages = status.get("packages") if isinstance(status, dict) else None
        owner_standing = (
            status.get("standing")
            if isinstance(status, dict) and isinstance(status.get("standing"), str)
            else "WORKSTATION_PROVIDER_UNHEALTHY"
        )
        return {
            **base,
            "ready": False,
            "standing": owner_standing,
            "browserHarnessVersion": (
                packages.get("browserHarnessVersion")
                if isinstance(packages, dict)
                else None
            ),
        }
    if not WINDOWS_POWERSHELL.is_file():
        return {**base, "ready": False, "standing": "WINDOWS_INTEROP_UNAVAILABLE"}
    probe_script = WINDOWS_PROBE.replace(
        "__BROWSER_HARNESS__", managed.replace("'", "''")
    )
    proc = subprocess.run(
        [
            str(WINDOWS_POWERSHELL),
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            probe_script,
        ],
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=20,
        check=False,
    )
    if proc.returncode != 0:
        return {
            **base,
            "ready": False,
            "standing": "WINDOWS_PROBE_FAILED",
            "detail": (proc.stderr or proc.stdout or "")[-500:].strip() or None,
        }
    try:
        value = json.loads(proc.stdout.lstrip("\ufeff").strip())
    except json.JSONDecodeError:
        return {**base, "ready": False, "standing": "WINDOWS_PROBE_INVALID"}

    doctor = value.get("doctor") if isinstance(value.get("doctor"), dict) else {}
    daemon = doctor.get("daemon") if isinstance(doctor.get("daemon"), dict) else {}
    version = doctor.get("version")
    executable_present = value.get("browserHarnessPresent") is True
    chrome_running = value.get("chromeRunning") is True
    consent_present = value.get("devToolsActivePortPresent") is True
    endpoint_ready = value.get("cdpEndpointReady") is True
    version_exact = version == EXPECTED_BROWSER_HARNESS_VERSION

    if not executable_present:
        standing = "BROWSER_HARNESS_UNAVAILABLE"
    elif version is not None and not version_exact:
        standing = "BROWSER_HARNESS_VERSION_MISMATCH"
    elif not chrome_running:
        standing = "WINDOWS_CHROME_UNAVAILABLE"
    elif not consent_present:
        standing = "HUMAN_REMOTE_DEBUGGING_REQUIRED"
    elif not endpoint_ready:
        standing = "DEVTOOLS_ENDPOINT_UNAVAILABLE"
    else:
        standing = "READY"

    ready = standing == "READY"
    return {
        **base,
        "ready": ready,
        "standing": standing,
        "browserHarnessVersion": version,
        "browserHarnessVersionExact": version_exact,
        "browserHarnessOwner": "workstation-windows-jev-provider",
        "chromeRunning": chrome_running,
        "chromeVersion": value.get("chromeVersion"),
        "humanRemoteDebuggingConsentPresent": consent_present,
        "cdpEndpointReady": endpoint_ready,
        "cdpPort": value.get("cdpPort") if endpoint_ready else None,
        "daemonAlive": daemon.get("alive") is True,
        "browserReadyNow": daemon.get("browser_ready") is True,
        "bootstrapAvailable": ready,
        "probeReturnCode": proc.returncode,
        "doctorExitCode": value.get("doctorExitCode"),
        "nonClaims": [
            "browser_action_authorized",
            "provider_effect_authorized",
            "task_semantic_success",
            "gateway_projection_authoritative",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("doctor",))
    parser.parse_args()
    value = _probe()
    print(json.dumps(value, sort_keys=True))
    return 0 if value["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
