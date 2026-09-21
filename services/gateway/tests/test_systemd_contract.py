from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UNIT = ROOT / "systemd" / "ordivon-gateway.service"
PUBLIC = ROOT / "systemd" / "ordivon-gateway.service.d" / "20-public-access.example.conf"
WINDOWS = (
    ROOT / "systemd" / "ordivon-gateway.service.d" / "30-windows-service-identity.example.conf"
)


def test_gateway_unit_is_loopback_dynamic_user_and_credential_scoped() -> None:
    text = UNIT.read_text(encoding="utf-8")
    assert "DynamicUser=true" in text
    assert "LoadCredential=linux-runtime-bearer:/etc/ordivon/runtime-mcp.token" in text
    assert "ORDIVON_GATEWAY_LINUX_RUNTIME_BEARER_TOKEN_FILE=%d/linux-runtime-bearer" in text
    assert "ORDIVON_GATEWAY_HOST=127.0.0.1" in text
    assert "ORDIVON_GATEWAY_PORT=8899" in text
    assert "NoNewPrivileges=true" in text
    assert "ProtectSystem=strict" in text
    assert "CapabilityBoundingSet=" in text
    assert "AmbientCapabilities=" in text
    assert "ORDIVON_GATEWAY_PUBLIC_ORIGIN" not in text
    assert "WINDOWS_ACCESS_CLIENT_SECRET" not in text


def test_public_access_is_a_separate_cutover_dropin() -> None:
    text = PUBLIC.read_text(encoding="utf-8")
    assert "https://gateway-mcp.ordivon.com" in text
    assert "ORDIVON_GATEWAY_TRUST_CF_ACCESS=true" in text
    assert "ORDIVON_GATEWAY_CF_ACCESS_AUDIENCE=<gateway-access-application-aud>" in text
    assert "client-secret" not in text.lower()


def test_windows_machine_identity_is_credential_file_only() -> None:
    text = WINDOWS.read_text(encoding="utf-8")
    assert "LoadCredential=windows-access-client-id:" in text
    assert "LoadCredential=windows-access-client-secret:" in text
    assert "ORDIVON_GATEWAY_WINDOWS_ACCESS_CLIENT_ID_FILE=%d/windows-access-client-id" in text
    assert (
        "ORDIVON_GATEWAY_WINDOWS_ACCESS_CLIENT_SECRET_FILE=%d/windows-access-client-secret" in text
    )
    assert "CF-Access-Client-Secret" not in text
