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
    assert "capability/wsl/fresh-session-admission" in text
    assert "mutationAttempted = $false" in text
    for forbidden in ("--terminate", "--shutdown", "terminate-wsl", "stop-service", "restart-service"):
        assert forbidden not in lowered


def test_windows_wsl_provider_uses_exact_system_wsl_path_and_bounded_distro_input():
    text = PS1.read_text(encoding="utf-8")
    assert "Join-Path $env:SystemRoot 'System32\\wsl.exe'" in text
    assert "[ValidatePattern('^[A-Za-z0-9._-]+$')]" in text


def test_admission_probe_is_bounded_and_checks_exact_fresh_session_marker():
    text = PS1.read_text(encoding="utf-8")
    assert "[ValidateRange(1,30)]" in text
    assert "WaitForExit($TimeoutSeconds * 1000)" in text
    assert "$psi.WorkingDirectory = $env:SystemRoot" in text
    assert "ORDIVON_WSL_ADMISSION_OK" in text
    assert "-u root -- /usr/bin/printf" in text
    assert "status = 'TIMEOUT'" in text
    assert "'READY'" in text
    assert "$verified = ($process.ExitCode -eq 0 -and $stdout -eq $marker)" in text
    assert "status = 'DISTRO_NOT_FOUND'" in text


def test_materializer_is_content_addressed_and_does_not_activate_service():
    text = MAT.read_text(encoding="utf-8").lower()
    assert "sha256" in text
    assert "programdata/ordivon/workstation/providers/windowswslprovider" in text
    for forbidden in ("sc.exe", "new-service", "register-scheduledtask", "restart-service", "start-service"):
        assert forbidden not in text
