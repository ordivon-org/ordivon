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


def test_windows_wsl_provider_storage_reclaim_is_sparse_aware_and_read_only():
    text = PS1.read_text(encoding="utf-8")
    lowered = text.lower()
    assert "storage-reclaim" in text
    assert "capability/wsl/storage-reclaim-observe" in text
    assert "fsutil.exe" in lowered
    assert "queryextents" in lowered
    assert "uint64]::maxvalue" in lowered
    assert "[io.fileattributes]::sparsefile" in lowered
    assert "allocatedbytes" in lowered
    assert "holebytes" in lowered
    assert "batstanding = 'unknown_not_observed'" in lowered
    for forbidden in ("set-sparse", "setzerodata", "--compact", "optimize-vhd", "diskpart"):
        assert forbidden not in lowered


def test_windows_wsl_provider_fast_storage_health_avoids_extent_scan():
    text = PS1.read_text(encoding="utf-8")
    block = text.split("  'storage-health' {", 1)[1].split("  'storage-reclaim' {", 1)[0]
    assert "capability/wsl/storage-health-observe" in block
    assert "SparseFile" in block
    assert "AvailableFreeSpace" in block
    assert "NOT_SAMPLED_FAST_TIER" in block
    assert "queryextents" not in block.lower()
