from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAYBOOK = ROOT / "ansible" / "host-substrate.yml"


def test_linux_host_playbook_cannot_revert_windows_user_global_wsl_policy() -> None:
    """Linux host convergence must not own a Windows user's global .wslconfig."""
    source = PLAYBOOK.read_text(encoding="utf-8")

    # Regression witness: this previously rewrote memory=10GB/swap=0 from
    # historical memory=8GB/swap=6GB/sparseVhd=true declarations.
    assert ".wslconfig" not in source
    assert "/mnt/c/Users/" not in source
    assert "operations_wslconfig_path" not in source
    assert "operations_wsl2_settings" not in source
    assert "operations_wsl_experimental_settings" not in source

    # Positive control: do not delete Linux-side host convergence as a shortcut.
    assert "Converge WSL distribution settings" in source
    assert "path: /etc/wsl.conf" in source
    assert "system.conf.d/20-ordivon-agent-limits.conf" in source
    assert "Keep unneeded systemd-homed units disabled" in source
