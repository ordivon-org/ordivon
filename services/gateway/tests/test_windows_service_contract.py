from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATERIALIZER = ROOT / "packaging" / "windows" / "materialize_service.ps1"
ACL = ROOT / "packaging" / "windows" / "protect_candidate_acl.ps1"


def test_windows_service_materializer_keeps_owner_lifecycle_independent() -> None:
    text = MATERIALIZER.read_text(encoding="utf-8")
    assert "--no-restart" in text
    assert "--kill-process-tree" in text
    assert "--stop-timeout" in text
    assert "ownerServiceDependencies = @()" in text
    assert "[string]$StartMode = 'Manual'" in text
    assert "$scStartMode" in text
    assert "--dependencies" not in text
    assert "'failure'" in text
    assert "restart/5000/restart/15000/restart/60000" in text


def test_windows_service_materializer_uses_virtual_service_identity_and_exact_release() -> None:
    text = MATERIALIZER.read_text(encoding="utf-8")
    assert 'NT SERVICE\\$ServiceName' in text
    assert "'sidtype', $ServiceName, 'unrestricted'" in text
    assert "ValidatePattern('^[0-9a-f]{40}$')" in text
    assert "releases" in text
    assert ".venv\\Scripts\\ordivon-gateway.exe" in text
    assert "ORDIVON_GATEWAY_WINDOWS_SERVICE_NAME" in text
    assert "ORDIVON_GATEWAY_PORT" in text


def test_windows_service_materializer_never_reads_secret_values() -> None:
    text = MATERIALIZER.read_text(encoding="utf-8")
    assert "LinuxRuntimeBearerTokenFile" in text
    assert "WindowsRuntimeBearerTokenFile" in text
    assert "HostBearerTokenFile" in text
    assert "ORDIVON_GATEWAY_LINUX_RUNTIME_BEARER_TOKEN_FILE" in text
    assert "ORDIVON_GATEWAY_WINDOWS_RUNTIME_BEARER_TOKEN_FILE" in text
    assert "Get-Content" not in text


def test_windows_acl_materializer_uses_service_sid_and_protected_dacls() -> None:
    text = ACL.read_text(encoding="utf-8")
    assert "NT SERVICE\\$ServiceName" in text
    assert "SecurityIdentifier" in text
    assert "/inheritance:r" in text
    assert "*S-1-5-18:" in text
    assert "*S-1-5-32-544:" in text
    assert "ServiceRights RX" in text
    assert "ServiceRights M" in text
    assert "ServiceRights R" in text


def test_windows_acl_materializer_protects_directory_root_then_resets_descendants() -> None:
    text = ACL.read_text(encoding="utf-8")
    section = text.split("function Protect-Directory", 1)[1].split(
        "function Grant-TraverseDirectory", 1
    )[0]
    root_phase, descendant_phase = section.split("$childPattern", 1)
    assert "'/T'" not in root_phase
    assert "'/reset'" in descendant_phase
    assert "'/T'" in descendant_phase
    assert "Grant-TraverseDirectory" in text
    assert "Join-Path $prefixPath 'releases'" in text
    assert "Join-Path $prefixPath 'toolchain'" in text
