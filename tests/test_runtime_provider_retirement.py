from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_legacy_wsl_windows_runtime_provider_source_is_retired():
    assert not (ROOT / "workstation/windows/runtime_provider.py").exists()
    assert not (ROOT / "workstation/windows/runtime-provider.toml").exists()
    assert not (ROOT / "ansible/workstation-windows-runtime-provider.yml").exists()


def test_retirement_playbook_removes_only_legacy_carrier_and_does_not_restart_runtime():
    text = (ROOT / "ansible/retire-wsl-windows-runtime-provider.yml").read_text()
    for value in (
        "ORDIVON_WINDOWS_LAUNCHER_PATH",
        "ORDIVON_WINDOWS_WSL_DISTRIBUTION",
        "20-windows-provider.conf",
        "workstation-windows-runtime-provider",
        "windows-runtime-provider.json",
        "WindowsJobLauncher",
    ):
        assert value in text
    assert text.count("state: absent") >= 8
    assert "daemon_reload: true" in text
    assert "restart" not in text.lower()
    assert "wsl.exe" not in text.lower()
    assert "--shutdown" not in text.lower()
