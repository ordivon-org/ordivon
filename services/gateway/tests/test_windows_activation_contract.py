from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTIVATOR = ROOT / "packaging" / "windows" / "activate_service.ps1"
SERVICE = ROOT / "packaging" / "windows" / "materialize_service.ps1"


def test_service_materialization_is_pre_activation_by_default() -> None:
    text = SERVICE.read_text(encoding="utf-8")
    assert "[string]$StartMode = 'Manual'" in text
    assert "activationRequired = $true" in text
    assert "linuxBearerTokenFile" in text
    assert "windowsBearerTokenFile" in text
    assert "hostBearerTokenFile" in text


def test_activation_requires_receipts_and_current_physical_credentials() -> None:
    text = ACTIVATOR.read_text(encoding="utf-8")
    assert "$ServiceName.materialization.json" in text
    assert "$ServiceName.credentials.json" in text
    assert "Test-Path -LiteralPath $fullPath -PathType Leaf" in text
    assert "Get-FileHash -LiteralPath $fullPath -Algorithm SHA256" in text
    assert "credential bytes no longer match materialization receipt" in text
    assert "AreAccessRulesProtected" in text
    assert "credential ACL principal set mismatch" in text


def test_activation_starts_only_after_credential_preflight() -> None:
    text = ACTIVATOR.read_text(encoding="utf-8")
    verify_at = text.index("Assert-CredentialProjection")
    start_at = text.rindex("Start-Service -Name $ServiceName")
    assert verify_at < start_at
    assert "Gateway candidate must be stopped before activation" in text
    assert "credentialPreflight = 'pass'" in text
    assert "ordivon.gateway-windows-service-activation" in text


def test_activation_rejects_runtime_routes_without_auth_paths() -> None:
    text = ACTIVATOR.read_text(encoding="utf-8")
    assert "'linuxRuntimeUrl', 'windowsRuntimeUrl'" in text
    assert "Linux Runtime activation requires a bearer token path" in text
    assert "Windows Runtime activation requires a bearer token path" in text
    linux_guard = text.index("Linux Runtime activation requires a bearer token path")
    windows_guard = text.index("Windows Runtime activation requires a bearer token path")
    start_at = text.rindex("Start-Service -Name $ServiceName")
    assert linux_guard < start_at
    assert windows_guard < start_at


def test_activation_does_not_read_or_emit_secret_values() -> None:
    text = ACTIVATOR.read_text(encoding="utf-8")
    assert "Get-Content -LiteralPath $fullPath" not in text
    assert "entry.sha256" in text
    assert "actualDigest" in text
    receipt_section = text.split("$receipt = [ordered]@{", 1)[1]
    assert "sha256" not in receipt_section.lower()
