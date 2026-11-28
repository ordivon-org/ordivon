from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tomllib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import metadata
from pathlib import Path
from queue import Queue
from threading import Thread

from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import ExportTraceServiceRequest

ROOT = Path(__file__).resolve().parents[1]
UNIT = ROOT / "systemd" / "ordivon-gateway.service"
PUBLIC = ROOT / "systemd" / "ordivon-gateway.service.d" / "20-public-access.example.conf"
HOST_OWNER = ROOT / "systemd" / "ordivon-gateway.service.d" / "25-host-owner-identity.example.conf"
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
    assert "Wants=network-online.target ordivon-runtime.service ordivon-host-v2.service" in text
    assert "After=network-online.target ordivon-runtime.service ordivon-host-v2.service" in text
    assert "Requires=ordivon-runtime.service" not in text
    assert "Requires=ordivon-host-v2.service" not in text
    assert "PartOf=ordivon-runtime.service" not in text
    assert "PartOf=ordivon-host-v2.service" not in text
    assert "BindsTo=ordivon-runtime.service" not in text
    assert "BindsTo=ordivon-host-v2.service" not in text
    assert "Restart=always" in text


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


def test_host_owner_identity_routes_to_protected_loopback_with_encrypted_credential() -> None:
    text = HOST_OWNER.read_text(encoding="utf-8")
    assert (
        "LoadCredentialEncrypted=host-mcp-bearer:/etc/ordivon/credentials/host-mcp-bearer.cred"
        in text
    )
    assert "ORDIVON_GATEWAY_HOST_URL=http://127.0.0.1:19008/mcp" in text
    assert "ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE=%d/host-mcp-bearer" in text
    assert "127.0.0.1:8898" not in text


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
    assert "OTEL_TRACES_EXPORTER=none" in text
    assert "OTEL_METRICS_EXPORTER=none" in text
    assert "OTEL_LOGS_EXPORTER=none" in text
    assert (
        "ExecStart=/opt/ordivon/gateway/current/.venv/bin/opentelemetry-instrument "
        "/opt/ordivon/gateway/current/.venv/bin/ordivon-gateway"
    ) in text


def test_gateway_external_opentelemetry_runtime_exports_native_otlp() -> None:
    """Exercise the installed launcher and exporter, not a historical version string."""
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    locked = tomllib.loads((ROOT / "uv.lock").read_text(encoding="utf-8"))
    dependencies = {p["name"]: p["version"] for p in locked["package"]}
    for package in ("opentelemetry-distro", "opentelemetry-exporter-otlp-proto-http"):
        assert any(req.startswith(package) for req in project["project"]["dependencies"])
        assert metadata.version(package) == dependencies[package]

    received: Queue[tuple[str, str | None, bytes]] = Queue()

    class Collector(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            body = self.rfile.read(int(self.headers["Content-Length"]))
            received.put((self.path, self.headers.get("Content-Type"), body))
            self.send_response(200)
            self.send_header("Content-Type", "application/x-protobuf")
            self.send_header("Content-Length", "0")
            self.end_headers()

        def log_message(self, *_args: object) -> None:
            pass

    launcher = shutil.which("opentelemetry-instrument")
    assert launcher
    with ThreadingHTTPServer(("127.0.0.1", 0), Collector) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            env = {k: v for k, v in os.environ.items() if not k.startswith("OTEL_")}
            env.update(
                OTEL_SERVICE_NAME="ordivon-gateway-qualification",
                OTEL_TRACES_EXPORTER="otlp_proto_http",
                OTEL_METRICS_EXPORTER="none",
                OTEL_LOGS_EXPORTER="none",
                OTEL_TRACES_SAMPLER="always_on",
                OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=(
                    f"http://127.0.0.1:{server.server_port}/v1/traces"
                ),
                OTEL_EXPORTER_OTLP_PROTOCOL="http/protobuf",
                OTEL_EXPORTER_OTLP_TRACES_TIMEOUT="3",
                NO_PROXY="127.0.0.1,localhost",
                no_proxy="127.0.0.1,localhost",
            )
            result = subprocess.run(
                [
                    launcher,
                    sys.executable,
                    "-c",
                    "from opentelemetry import trace;"
                    "tracer=trace.get_tracer('gateway-qualification');"
                    "span=tracer.start_span('native-export-probe');"
                    "span.end();"
                    "assert trace.get_tracer_provider().force_flush(5000)",
                ],
                env=env,
                capture_output=True,
                text=True,
                timeout=20,
                check=False,
            )
            assert result.returncode == 0, result.stderr
            path, content_type, body = received.get(timeout=3)
        finally:
            server.shutdown()
            thread.join(timeout=3)

    assert path == "/v1/traces"
    assert content_type == "application/x-protobuf"
    request = ExportTraceServiceRequest.FromString(body)
    assert any(
        span.name == "native-export-probe"
        for resource in request.resource_spans
        if any(
            attr.key == "service.name"
            and attr.value.string_value == "ordivon-gateway-qualification"
            for attr in resource.resource.attributes
        )
        for scope in resource.scope_spans
        for span in scope.spans
    )


TRACE_PROFILE = ROOT / "systemd" / "ordivon-gateway.service.d" / "40-otel-traces.example.conf"
TRACE_ENABLER = ROOT / "packaging" / "enable_trace_export.sh"


def test_trace_profile_is_opt_in_standard_otlp_http() -> None:
    text = TRACE_PROFILE.read_text(encoding="utf-8")
    assert "OTEL_TRACES_EXPORTER=otlp_proto_http" in text
    assert "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://127.0.0.1:4318/v1/traces" in text
    assert "OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf" in text


def test_trace_export_enabler_requires_live_local_observability_and_is_fixed_path() -> None:
    text = TRACE_ENABLER.read_text(encoding="utf-8")
    assert "40-otel-traces.example.conf" in text
    assert "/etc/systemd/system/ordivon-gateway.service.d" in text
    assert "systemctl is-active --quiet vector.service" in text
    assert "http://127.0.0.1:3200/ready" in text
    assert "systemctl restart ordivon-gateway.service" in text
    assert "http://127.0.0.1:8899/health" in text
    assert "$1" not in text


LOCAL_SERVICE = (
    ROOT / "systemd" / "ordivon-gateway.service.d" / "10-local-service-identity.example.conf"
)


def test_local_service_identity_is_optional_loadcredential_not_loopback_trust() -> None:
    text = LOCAL_SERVICE.read_text(encoding="utf-8")
    assert "LoadCredential=local-client-bearer:/etc/ordivon/gateway/local-client-bearer" in text
    assert "ORDIVON_GATEWAY_LOCAL_BEARER_TOKEN_FILE=%d/local-client-bearer" in text
    assert "TRUST_LOOPBACK" not in text


LOCAL_SERVICE_ENABLER = ROOT / "packaging" / "enable_local_service_identity.sh"


def test_local_service_identity_enabler_generates_private_credential_without_printing_it() -> None:
    text = LOCAL_SERVICE_ENABLER.read_text(encoding="utf-8")
    assert 'openssl rand -hex 32 > "$CREDENTIAL"' in text
    assert "umask 077" in text
    assert "root:root" in text
    assert "'600'" in text and "'400'" in text
    assert "systemctl restart ordivon-gateway.service" in text
    assert "http://127.0.0.1:8899/health" in text
    assert 'cat "$CREDENTIAL"' not in text


def test_release_service_user_preflight_occurs_before_atomic_promote() -> None:
    """Running a version as root is not proof that systemd can execute it."""
    script = INSTALLER.read_text(encoding="utf-8")
    assert "ORDIVON_GATEWAY_RELEASE_SERVICE_USER" in script
    assert 'runuser -u "$SERVICE_USER" -- "$RELEASE/.venv/bin/python"' in script
    assert 'runuser -u "$SERVICE_USER" -- "$RELEASE/.venv/bin/opentelemetry-instrument"' in script
    assert script.index("service_user_preflight=pass") < script.index('ln -sfn "releases/$COMMIT"')
    assert script.index("service_user_preflight=pass") > script.index(
        '"$RELEASE/.venv/bin/python" "$RELEASE/packaging/windows/verify_release.py"'
    )
