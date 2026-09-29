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
    assert "NT SERVICE\\$ServiceName" in text
    assert "'sidtype', $ServiceName, 'unrestricted'" in text
    assert "ValidatePattern('^[0-9a-f]{40}$')" in text
    assert "releases" in text
    assert ".venv\\Scripts\\ordivon-gateway.exe" in text
    assert "ORDIVON_GATEWAY_WINDOWS_SERVICE_NAME" in text
    assert "ORDIVON_GATEWAY_PORT" in text
    assert "$releaseReceiptPath" in text
    assert "Gateway release receipt source commit mismatch" in text
    assert "releaseReceiptSha256" in text


def test_windows_service_materializer_never_reads_secret_values() -> None:
    text = MATERIALIZER.read_text(encoding="utf-8")
    assert "LinuxRuntimeBearerTokenFile" in text
    assert "WindowsRuntimeBearerTokenFile" in text
    assert "HostBearerTokenFile" in text
    assert "ORDIVON_GATEWAY_LINUX_RUNTIME_BEARER_TOKEN_FILE" in text
    assert "ORDIVON_GATEWAY_WINDOWS_RUNTIME_BEARER_TOKEN_FILE" in text
    assert "Get-Content -LiteralPath $releaseReceiptPath" in text
    assert "Get-Content -LiteralPath $LinuxRuntimeBearerTokenFile" not in text
    assert "Get-Content -LiteralPath $WindowsRuntimeBearerTokenFile" not in text
    assert "Get-Content -LiteralPath $HostBearerTokenFile" not in text


def test_windows_service_receipt_separates_path_configuration_from_physical_presence() -> None:
    text = MATERIALIZER.read_text(encoding="utf-8")
    for prefix in ("linux", "windows", "host"):
        assert f"{prefix}BearerPathConfigured" in text
        assert f"{prefix}BearerFilePresentAtMaterialization" in text
        assert f"{prefix}BearerConfigured =" not in text
    assert "Test-Path -LiteralPath $LinuxRuntimeBearerTokenFile" in text
    assert "Test-Path -LiteralPath $WindowsRuntimeBearerTokenFile" in text
    assert "Test-Path -LiteralPath $HostBearerTokenFile" in text


def test_windows_service_materializer_requires_auth_paths_for_runtime_upstreams() -> None:
    text = MATERIALIZER.read_text(encoding="utf-8")
    assert "Linux Runtime URL requires LinuxRuntimeBearerTokenFile" in text
    assert "Windows Runtime URL requires WindowsRuntimeBearerTokenFile" in text
    linux_guard = text.index("Linux Runtime URL requires LinuxRuntimeBearerTokenFile")
    windows_guard = text.index("Windows Runtime URL requires WindowsRuntimeBearerTokenFile")
    destructive = text.index("$existing = Get-Service")
    assert linux_guard < destructive
    assert windows_guard < destructive


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


def test_windows_service_materializer_preserves_public_access_contract() -> None:
    text = MATERIALIZER.read_text()
    assert "[string]$PublicOrigin = ''" in text
    assert "[switch]$TrustCfAccess" in text
    assert "[string]$CfAccessIssuer = ''" in text
    assert "[string]$CfAccessAudience = ''" in text
    assert "ORDIVON_GATEWAY_PUBLIC_ORIGIN" in text
    assert "ORDIVON_GATEWAY_TRUST_CF_ACCESS" in text
    assert "ORDIVON_GATEWAY_CF_ACCESS_ISSUER" in text
    assert "ORDIVON_GATEWAY_CF_ACCESS_AUDIENCE" in text
    assert (
        "Cloudflare Access trust requires PublicOrigin, CfAccessIssuer, and CfAccessAudience"
        in text
    )
    assert "CfAccessIssuer/CfAccessAudience require -TrustCfAccess" in text
    assert "publicOriginConfigured" in text
    assert "trustCfAccess" in text


def test_windows_service_materializer_fences_mcp_surface_changes() -> None:
    text = MATERIALIZER.read_text(encoding="utf-8")
    assert "mcp-surface.json" in text
    assert "ordivon.mcp-tool-surface" in text
    assert "Gateway MCP tool surface changed without advancing surfaceEpoch" in text
    assert "Gateway MCP tool surface changed without advancing packageVersion" in text
    assert "Gateway MCP surfaceEpoch changed while tool surface is unchanged" in text
    assert "$existingCim.PathName" in text


def test_windows_service_materializer_keeps_authzen_opt_in_and_path_only() -> None:
    text = MATERIALIZER.read_text(encoding="utf-8")
    assert "AuthZenEvaluationEndpoint" in text
    assert "AuthZenBearerTokenFile" in text
    assert (
        "AuthZEN enablement requires both AuthZenEvaluationEndpoint and AuthZenBearerTokenFile"
        in text
    )
    assert "ORDIVON_GATEWAY_AUTHZEN_EVALUATION_ENDPOINT" in text
    assert "ORDIVON_GATEWAY_AUTHZEN_BEARER_TOKEN_FILE" in text
    assert "configured AuthZEN bearer token file is missing" in text
    authzen_guard = text.index("configured AuthZEN bearer token file is missing")
    destructive = text.index("$existing = Get-Service")
    assert authzen_guard < destructive
    assert "Get-Content -LiteralPath $AuthZenBearerTokenFile" not in text
