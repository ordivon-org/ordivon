from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "packaging" / "windows" / "install_release.ps1"


def test_windows_release_installer_is_exact_sha_and_immutable() -> None:
    text = INSTALLER.read_text(encoding="utf-8")
    assert "ValidatePattern('^[0-9a-f]{40}$')" in text
    assert "ProviderPath" in text
    assert "safe.directory=$repoPath" in text
    assert "'rev-parse' '--verify'" in text
    assert "$resolveExitCode = $LASTEXITCODE" in text
    assert "${resolveExitCode}:" in text
    assert "'archive'" in text
    assert "'services/gateway'" in text
    assert "releases" in text
    assert '".tmp-$Commit-$nonce"' in text
    assert "Move-Item -LiteralPath $tmp -Destination $release" in text
    assert "Remove-Item -LiteralPath $release" not in text


def test_windows_release_installer_uses_pinned_managed_python_and_lock() -> None:
    text = INSTALLER.read_text(encoding="utf-8")
    assert "UV_PYTHON_INSTALL_DIR" in text
    assert "'python', 'install'" in text
    assert "'--no-bin'" in text
    assert "& $uvResolved 'python' 'find' '--no-project' '--managed-python'" in text
    assert "'sync'," in text
    assert "'--frozen'," in text
    assert "'--no-dev'," in text
    assert "requires-python must exactly match .python-version" in text
    assert r".venv\Scripts\ordivon-gateway.exe" in text


def test_windows_release_installer_emits_mechanical_receipt_without_current_pointer() -> None:
    text = INSTALLER.read_text(encoding="utf-8")
    assert "ordivon.gateway-windows-release-receipt" in text
    assert "lockSha256" in text
    assert "pyprojectSha256" in text
    assert "uvSha256" in text
    assert "sourceCommit" in text
    assert "current.next" not in text
    assert "New-Item -ItemType SymbolicLink" not in text
    assert "Set-Content -LiteralPath $receiptPath" in text
