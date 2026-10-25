from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

WINDOWS = Path(__file__).resolve().parents[1] / "windows"
REPORT = WINDOWS / "update_candidate_report.ps1"
INSTALLER = WINDOWS / "install_update_discovery.ps1"


def test_windows_discovery_is_read_only_and_native():
    text = REPORT.read_text(encoding="utf-8")
    assert "Microsoft.DesktopAppInstaller" in text
    assert "winget.exe" in text
    assert "upgrade --source winget" in text
    assert "New-Object -ComObject Microsoft.Update.Session" not in text
    assert "Get-ScheduledTask" in text
    assert "(?<id>\\S+)" in text
    assert "$Matches.available" in text
    for forbidden in (
        " upgrade --all",
        "install --",
        "Start-Process",
        "Restart-Computer",
        "UsoClient Start",
    ):
        assert forbidden not in text


def test_windows_report_has_explicit_effect_zeroes_and_unknown_states():
    text = REPORT.read_text(encoding="utf-8")
    for field in (
        "packagesUpgraded = 0",
        "windowsUpdatesInstalled = 0",
        "processesRestarted = 0",
        "rebootRequested = $false",
        'state = "unknown"',
        'kind = "ordivon.workstation.windows-update-candidates"',
    ):
        assert field in text


def test_windows_installer_is_system_task_with_bounded_runtime():
    text = INSTALLER.read_text(encoding="utf-8")
    assert 'UserId "SYSTEM"' in text
    assert "ServiceAccount" in text
    assert "ExecutionTimeLimit" in text
    assert "StartWhenAvailable" in text
    assert "MultipleInstances IgnoreNew" in text
    assert "Start-ScheduledTask" in text


def test_windows_installer_protects_system_payload_from_standard_users():
    text = INSTALLER.read_text(encoding="utf-8")
    assert "icacls.exe $InstallRoot /inheritance:r /grant:r" in text
    assert "icacls.exe $installed /inheritance:r /grant:r" in text
    assert '"*S-1-5-18:(OI)(CI)F"' in text
    assert '"*S-1-5-32-544:(OI)(CI)F"' in text
    assert '"*S-1-5-18:F"' in text
    assert '"*S-1-5-32-544:F"' in text
    assert "Failed to harden update discovery directory ACL" in text
    assert "Failed to harden update discovery script ACL" in text
    assert "Get-Acl -LiteralPath $path" in text
    assert 'S-1-5-18", "S-1-5-32-544' in text
    assert "unexpected principal" in text
    assert text.index("Get-Acl -LiteralPath $path") < text.index("Register-ScheduledTask")


def test_winget_rows_preserve_id_versions_and_optional_source_in_native_powershell():
    # Run the real function, not a Python mirror. Do not execute the SYSTEM-task
    # side effects at the bottom of the report script.
    command = r'''
$tokens = $null
$errors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile($env:ORDIVON_PS_SOURCE, [ref]$tokens, [ref]$errors)
if ($errors.Count -gt 0) { throw "PowerShell parse errors" }
$fn = $ast.Find({
  param($node)
  $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and
  $node.Name -eq 'Convert-WingetUpgradeOutput'
}, $true)
if (-not $fn) { throw "missing parser function" }
. ([scriptblock]::Create($fn.Extent.Text))
$rows = @(
  'Name                       Id                        Version   Available Source',
  '--------------------------------------------------------------------------',
  'Microsoft Visual Studio Code Microsoft.VisualStudioCode 1.96.0 1.97.0 winget',
  'Git                         Git.Git                   2.50.1    2.51.0    winget',
  'Legacy Tool                 Vendor.Legacy             1.0       1.1',
  '3 upgrades available.'
)
ConvertTo-Json -Compress -Depth 6 -InputObject @(Convert-WingetUpgradeOutput -Lines $rows)
'''
    env = {**os.environ, "ORDIVON_PS_SOURCE": str(REPORT)}
    completed = subprocess.run(
        ["pwsh", "-NoProfile", "-NonInteractive", "-Command", command],
        check=True, capture_output=True, text=True, env=env, timeout=25,
    )
    records = json.loads(completed.stdout)
    assert len(records) == 3
    assert records[0]["name"] == "Microsoft Visual Studio Code"
    assert records[0]["id"] == "Microsoft.VisualStudioCode"
    assert records[0]["current"] == "1.96.0"
    assert records[0]["available"] == "1.97.0"
    assert records[0]["source"] == "winget"
    assert records[1]["id"] == "Git.Git"
    assert records[1]["available"] == "2.51.0"
    assert records[2]["id"] == "Vendor.Legacy"
    assert records[2]["available"] == "1.1"
    assert "source" not in records[2]
