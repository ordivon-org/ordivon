from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PS1 = ROOT / "workstation" / "providers" / "windows_wsl" / "WindowsWslProvider.ps1"
MAT = ROOT / "workstation" / "providers" / "windows_wsl" / "materialize.py"


def test_windows_wsl_provider_is_observation_only_and_normalizes_nuls():
    text = PS1.read_text(encoding="utf-8")
    lowered = text.lower()
    assert "normalize-wslname" in lowered
    assert "-replace [char]0" in lowered
    assert "capability/wsl/probe" in text
    assert "capability/wsl/verify-offline" in text
    assert "mutationAttempted = $false" in text
    for forbidden in ("--terminate", "--shutdown", "terminate-wsl", "stop-service", "restart-service"):
        assert forbidden not in lowered


def test_windows_wsl_provider_uses_exact_system_wsl_path_and_bounded_distro_input():
    text = PS1.read_text(encoding="utf-8")
    assert "Join-Path $env:SystemRoot 'System32\\wsl.exe'" in text
    assert "[ValidatePattern('^[A-Za-z0-9._-]+$')]" in text


def test_materializer_is_content_addressed_and_does_not_activate_service():
    text = MAT.read_text(encoding="utf-8").lower()
    assert "sha256" in text
    assert "programdata/ordivon/workstation/providers/windowswslprovider" in text
    for forbidden in ("sc.exe", "new-service", "register-scheduledtask", "restart-service", "start-service"):
        assert forbidden not in text
