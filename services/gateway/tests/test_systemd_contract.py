from __future__ import annotations

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UNIT = ROOT / "systemd" / "ordivon-gateway.service"
PUBLIC = ROOT / "systemd" / "ordivon-gateway.service.d" / "20-public-access.example.conf"
WINDOWS = (
    ROOT / "systemd" / "ordivon-gateway.service.d" / "30-windows-service-identity.example.conf"
)
INSTALLER = ROOT / "packaging" / "install_release.sh"


def test_gateway_unit_is_loopback_dynamic_user_and_credential_scoped() -> None:
    text = UNIT.read_text(encoding="utf-8")
    assert "DynamicUser=true" in text
    assert "LoadCredential=linux-runtime-bearer:/etc/ordivon/runtime-mcp.token" in text
    assert "ORDIVON_GATEWAY_LINUX_RUNTIME_BEARER_TOKEN_FILE=%d/linux-runtime-bearer" in text
    assert "ORDIVON_GATEWAY_HOST=127.0.0.1" in text
    assert "ORDIVON_GATEWAY_PORT=8899" in text
    assert "ExecStart=/opt/ordivon/gateway/current/.venv/bin/opentelemetry-instrument " in text
    assert " /opt/ordivon/gateway/current/.venv/bin/ordivon-gateway" in text
    assert "current-env" not in text
    assert "NoNewPrivileges=true" in text
    assert "ProtectSystem=strict" in text
    assert "ProtectHome=true" in text
    assert "CapabilityBoundingSet=" in text
    assert "AmbientCapabilities=" in text
    assert "ORDIVON_GATEWAY_PUBLIC_ORIGIN" not in text
    assert "WINDOWS_ACCESS_CLIENT_SECRET" not in text


def test_release_python_uses_same_managed_pattern_as_host() -> None:
    text = INSTALLER.read_text(encoding="utf-8")
    assert "UV_PYTHON_INSTALL_DIR" in text
    assert "python install" in text
    assert "python find" in text
    assert "--managed-python" in text
    assert '--project "$RELEASE"' in text
    assert 'mv "$TMP" "$RELEASE"' in text
    assert "current-env" not in text
    assert "/root/" not in text


def test_python_pin_matches_project_requirement() -> None:
    pinned = (ROOT / ".python-version").read_text(encoding="utf-8").strip()
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert project["project"]["requires-python"] == f"=={pinned}"


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


WINDOWS_ENABLER = ROOT / "packaging" / "enable_windows_service_identity.sh"


def test_windows_identity_enabler_is_fixed_path_and_fail_closed() -> None:
    text = WINDOWS_ENABLER.read_text(encoding="utf-8")
    assert "CREDENTIAL_DIR=/etc/ordivon/gateway" in text
    assert 'CLIENT_ID="$CREDENTIAL_DIR/windows-access-client-id"' in text
    assert 'CLIENT_SECRET="$CREDENTIAL_DIR/windows-access-client-secret"' in text
    assert "/etc/systemd/system/ordivon-gateway.service.d" in text
    assert "30-windows-service-identity.conf" in text
    assert "30-windows-service-identity.example.conf" in text
    assert "mode=$(stat -Lc '%a' \"$path\")" in text
    assert "root:root" in text
    assert "systemctl daemon-reload" in text
    assert "systemctl restart ordivon-gateway.service" in text
    assert "http://127.0.0.1:8899/health" in text
    assert "$1" not in text
    assert "$2" not in text
    assert "cat " not in text


def test_gateway_uses_standard_opentelemetry_zero_code_trace_export() -> None:
    text = UNIT.read_text(encoding="utf-8")
    assert "OTEL_SERVICE_NAME=ordivon-gateway" in text
    assert "OTEL_TRACES_EXPORTER=otlp_proto_http" in text
    assert "OTEL_METRICS_EXPORTER=none" in text
    assert "OTEL_LOGS_EXPORTER=none" in text
    assert "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://127.0.0.1:4318/v1/traces" in text
    assert (
        "ExecStart=/opt/ordivon/gateway/current/.venv/bin/opentelemetry-instrument "
        "/opt/ordivon/gateway/current/.venv/bin/ordivon-gateway"
    ) in text


def test_gateway_pins_external_opentelemetry_runtime() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = set(project["project"]["dependencies"])
    assert "opentelemetry-distro==0.65b0" in dependencies
    assert "opentelemetry-exporter-otlp-proto-http==1.44.0" in dependencies
