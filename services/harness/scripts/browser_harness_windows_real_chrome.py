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
BROWSER_HARNESS_WINDOWS = (
    r"C:\ProgramData\Ordivon\RuntimeCandidateR6\service-home"
    r"\browser-use-win\bin\browser-harness.exe"
)
BROWSER_HARNESS_WSL = Path(
    "/mnt/c/ProgramData/Ordivon/RuntimeCandidateR6/service-home/"
    "browser-use-win/bin/browser-harness.exe"
)
EXPECTED_BROWSER_HARNESS_VERSION = "0.1.13"

WINDOWS_PROBE = rf"""
$ErrorActionPreference='SilentlyContinue'
$browserHarness='{BROWSER_HARNESS_WINDOWS}'
$chromeExe='C:\Program Files\Google\Chrome\Application\chrome.exe'
$chrome=@(Get-Process chrome -ErrorAction SilentlyContinue)
$chromeVersion=$null
if(Test-Path $chromeExe){{$chromeVersion=(Get-Item $chromeExe).VersionInfo.ProductVersion}}
$devTools=Join-Path $env:LOCALAPPDATA 'Google\Chrome\User Data\DevToolsActivePort'
$doctor=$null
$doctorExit=$null
if(Test-Path $browserHarness){{
  $raw=& $browserHarness doctor --json 2>$null
  $doctorExit=$LASTEXITCODE
  try{{$doctor=($raw -join "`n") | ConvertFrom-Json}}catch{{$doctor=$null}}
}}
[pscustomobject]@{{
  browserHarnessPresent=(Test-Path $browserHarness)
  chromeRunning=($chrome.Count -gt 0)
  chromeVersion=$chromeVersion
  devToolsActivePortPresent=(Test-Path $devTools)
  doctorExitCode=$doctorExit
  doctor=$doctor
}} | ConvertTo-Json -Compress -Depth 6
"""


def _probe() -> dict[str, Any]:
    base = {
        "executionTarget": "windows_native",
        "windowsAuthority": "active_user",
    }
    if not WINDOWS_POWERSHELL.is_file():
        return {**base, "ready": False, "standing": "WINDOWS_INTEROP_UNAVAILABLE"}
    proc = subprocess.run(
        [
            str(WINDOWS_POWERSHELL),
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            WINDOWS_PROBE,
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
    version_exact = version == EXPECTED_BROWSER_HARNESS_VERSION

    if not executable_present:
        standing = "BROWSER_HARNESS_UNAVAILABLE"
    elif version is not None and not version_exact:
        standing = "BROWSER_HARNESS_VERSION_MISMATCH"
    elif not chrome_running:
        standing = "WINDOWS_CHROME_UNAVAILABLE"
    elif not consent_present:
        standing = "HUMAN_REMOTE_DEBUGGING_REQUIRED"
    else:
        standing = "READY"

    ready = standing == "READY"
    return {
        **base,
        "ready": ready,
        "standing": standing,
        "browserHarnessVersion": version,
        "browserHarnessVersionExact": version_exact,
        "chromeRunning": chrome_running,
        "chromeVersion": value.get("chromeVersion"),
        "humanRemoteDebuggingConsentPresent": consent_present,
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
    args = parser.parse_args()
    value = _probe()
    print(json.dumps(value, sort_keys=True))
    return 0 if value["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
