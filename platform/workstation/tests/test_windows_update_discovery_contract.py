from __future__ import annotations

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
