"""Physical deployment prerequisite check for the *existing* release installer.

These are bounded negative tests. They do not create actual Security grants or
replace an Owner AuthZEN decision, actual Host canary, or production activation.
"""

from __future__ import annotations

import importlib.util
import itertools
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "packaging" / "check_live_host_admission.py"
INSTALLER = ROOT / "packaging" / "install_release.sh"


@pytest.fixture(scope="module")
def preflight() -> Any:
    spec = importlib.util.spec_from_file_location("gateway_release_security_preflight", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _observed_pair():
    return {"standing": "OBSERVED_FOR_EXACT_READ_PAIR"}


def test_real_missing_operator_grants_and_owner_credential_are_blocked(preflight: Any) -> None:
    result = preflight.assess(None, "", anonymous_host_initialize_denied=True)
    assert result["status"] == "NO_GO"
    assert result["effectivePolicyStanding"] is None
    assert result["hostOwnerCredentialDeclared"] is False
    assert result["reasons"] == [
        "HOST_SECURITY_POLICY_STANDING_UNOBSERVED",
        "GATEWAY_HOST_OWNER_CREDENTIAL_NOT_CONFIGURED",
        "HOST_OWNER_ROUTE_NOT_QUALIFIED_FOR_LOCAL_CANARY",
    ]


def test_bounded_promotion_prerequisites_are_distinct_from_authorization(preflight: Any) -> None:
    result = preflight.assess(
        _observed_pair(),
        (
            "ORDIVON_GATEWAY_HOST_URL=http://127.0.0.1:8898/mcp "
            "ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE=%d/host-mcp-bearer"
        ),
        anonymous_host_initialize_denied=True,
    )
    assert result["status"] == "NECESSARY_PRECONDITIONS_PRESENT"
    assert result["effectivePolicyStanding"] == _observed_pair()
    assert result["hostOwnerCredentialDeclared"] is True
    assert "actual Principal-to-Actor and resource authorization" in result["unverified"]
    assert "direct Host MCP connector migration" in result["unverified"]


@pytest.mark.parametrize(
    "environment",
    [
        "",
        "OTHER_SERVICE_BEARER_TOKEN_FILE=/run/credentials/other",
        "ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE=",
        "ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE=relative/path",
        'ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE=broken\\"',
    ],
)
def test_missing_or_unqualified_owner_identity_remains_no_go(
    preflight: Any, environment: str
) -> None:
    assert not preflight._declares_host_owner_identity(environment)
    result = preflight.assess(
        _observed_pair(),
        environment,
    )
    assert "GATEWAY_HOST_OWNER_CREDENTIAL_NOT_CONFIGURED" in result["reasons"]


def test_official_production_promotion_consumer_checks_before_atomic_switch() -> None:
    installer = INSTALLER.read_text(encoding="utf-8")
    needle = '"$RELEASE/.venv/bin/python" "$RELEASE/packaging/check_live_host_admission.py"'
    assert needle in installer
    assert '"$(realpath -m "$PREFIX")" = "/opt/ordivon/gateway"' in installer
    assert (
        "/run/credentials/ordivon-security-gateway-authzen.service/trusted-issuer" not in installer
    )
    assert installer.index(needle) < installer.index('ln -sfn "releases/$COMMIT"')
    assert installer.index(needle) > installer.index("service_user_preflight=pass")


@pytest.mark.parametrize(
    ("http_status", "qualifies_denial"),
    [
        (200, False),
        (201, False),
        (302, False),
        (400, False),
        (401, True),
        (403, True),
        (404, False),
        (503, False),
    ],
)
def test_local_host_initialize_negative_requires_http_auth_denial(
    preflight: Any,
    monkeypatch: pytest.MonkeyPatch,
    http_status: int,
    qualifies_denial: bool,
) -> None:
    requests: list[tuple[str, str, dict[str, str]]] = []

    class FakeConnection:
        def __init__(self, host: str, port: int, timeout: int) -> None:
            assert (host, port, timeout) == ("127.0.0.1", 8898, 4)

        def request(
            self,
            method: str,
            path: str,
            *,
            body: bytes,
            headers: dict[str, str],
        ) -> None:
            assert b'"method":"initialize"' in body
            assert "Authorization" not in headers
            requests.append((method, path, headers))

        def getresponse(self) -> Any:
            return type("Response", (), {"status": http_status})()

        def close(self) -> None:
            pass

    monkeypatch.setattr(preflight.http.client, "HTTPConnection", FakeConnection)
    assert preflight._rejects_unauthenticated_host_initialize() is qualifies_denial
    assert len(requests) == 1
    assert requests[0][0:2] == ("POST", "/mcp")


def test_host_anonymous_network_failure_is_not_proof(
    preflight: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FailingConnection:
        def __init__(self, *_args: Any, **_kwargs: Any) -> None:
            pass

        def request(self, *_args: Any, **_kwargs: Any) -> None:
            raise ConnectionRefusedError("fixture-only")

        def close(self) -> None:
            pass

    monkeypatch.setattr(preflight.http.client, "HTTPConnection", FailingConnection)
    assert preflight._rejects_unauthenticated_host_initialize() is False


@pytest.mark.parametrize(
    "host_owner_url",
    [
        "",
        "http://127.0.0.1:8898/",
        "http://localhost:8898/mcp",
        "https://host-mcp.ordivon.com/mcp",
        "http://127.0.0.1:9999/mcp",
    ],
)
def test_gateway_must_route_to_exact_negatively_probed_host(
    preflight: Any,
    host_owner_url: str,
) -> None:
    env = f"ORDIVON_GATEWAY_HOST_URL={host_owner_url} "
    env += "ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE=/run/gateway/host"
    result = preflight.assess(
        _observed_pair(),
        env,
        anonymous_host_initialize_denied=True,
    )
    assert result["status"] == "NO_GO"
    assert result["hostOwnerRouteQualified"] is False
    assert "HOST_OWNER_ROUTE_NOT_QUALIFIED_FOR_LOCAL_CANARY" in result["reasons"]


def test_host_direct_anonymous_denial_cannot_be_inferred_from_grants(
    preflight: Any,
) -> None:
    env = (
        "ORDIVON_GATEWAY_HOST_URL=http://127.0.0.1:8898/mcp "
        "ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE=/run/gateway/host"
    )
    for observed in (None, False):
        result = preflight.assess(
            _observed_pair(),
            env,
            anonymous_host_initialize_denied=observed,
        )
        assert result["status"] == "NO_GO"
        assert result["effectivePolicyStanding"] == _observed_pair()
        assert result["hostOwnerCredentialDeclared"] is True
        assert result["hostOwnerRouteQualified"] is True
        assert result["anonymousHostInitializeDenied"] is False
        assert "HOST_DIRECT_ANONYMOUS_MCP_NOT_PROVEN_DENIED" in result["reasons"]


def test_observed_cloudflare_host_socket_is_release_counterexample(
    preflight: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Only a native ESTAB socket, not an installed service name, is positive evidence."""

    def fake_run(argv: list[str], **_kwargs: Any) -> Any:
        if argv[0] == "/usr/bin/systemctl":
            assert argv == [
                "/usr/bin/systemctl",
                "show",
                "ordivon-gateway.service",
                "-p",
                "MainPID",
                "--value",
            ]
            return type("Process", (), {"stdout": "1607\n"})()
        assert argv == ["/usr/bin/ss", "-H", "-t", "-n", "-p", "( dport = :8898 )"]
        return type(
            "Process",
            (),
            {
                "stdout": (
                    "ESTAB 0 0 127.0.0.1:58293 127.0.0.1:8898 "
                    'users:(("ordivon-gateway",pid=1607,fd=12))\n'
                    "ESTAB 0 0 127.0.0.1:57987 127.0.0.1:8898 "
                    'users:(("cloudflared",pid=1856075,fd=16))\n'
                    "CLOSE-WAIT 1 0 127.0.0.1:50000 127.0.0.1:8898 "
                    'users:(("unrelated",pid=8,fd=7))\n'
                )
            },
        )()

    monkeypatch.setattr(preflight.subprocess, "run", fake_run)
    classes = preflight._observed_non_gateway_host_tcp_clients()
    assert classes == ["cloudflared"]
    result = preflight.assess(
        _observed_pair(),
        "ORDIVON_GATEWAY_HOST_URL=http://127.0.0.1:8898/mcp "
        "ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE=%d/host-mcp-bearer",
        anonymous_host_initialize_denied=True,
        observed_non_gateway_host_tcp_clients=classes,
    )
    assert result["status"] == "NO_GO"
    assert result["reasons"] == ["HOST_DIRECT_NON_GATEWAY_TCP_CONSUMER_OBSERVED"]
    assert result["observedDirectHostTcpConsumerClasses"] == ["cloudflared"]


@pytest.mark.parametrize(
    ("socket_line", "expected"),
    [
        (
            'ESTAB 0 0 127.0.0.1:59000 127.0.0.1:8898 users:(("ordivon-gateway",pid=1607,fd=5))',
            [],
        ),
        (
            'ESTAB 0 0 127.0.0.1:59000 127.0.0.1:8898 users:(("ordivon-gateway",pid=1608,fd=5))',
            ["other_non_gateway"],
        ),
        (
            "ESTAB 0 0 127.0.0.1:59000 127.0.0.1:8898",
            ["unattributed"],
        ),
        (
            'ESTAB 0 0 127.0.0.1:59000 127.0.0.1:8888 users:(("cloudflared",pid=1856075,fd=16))',
            [],
        ),
        (
            "TIME-WAIT 0 0 127.0.0.1:59000 127.0.0.1:8898 "
            'users:(("cloudflared",pid=1856075,fd=16))',
            [],
        ),
    ],
)
def test_host_socket_falsifier_uses_exact_gateway_pid_endpoint_and_established_state(
    preflight: Any,
    monkeypatch: pytest.MonkeyPatch,
    socket_line: str,
    expected: list[str],
) -> None:
    def fake_run(argv: list[str], **_kwargs: Any) -> Any:
        if argv[0] == "/usr/bin/systemctl":
            return type("Process", (), {"stdout": "1607\n"})()
        return type("Process", (), {"stdout": socket_line + "\n"})()

    monkeypatch.setattr(preflight.subprocess, "run", fake_run)
    assert preflight._observed_non_gateway_host_tcp_clients() == expected


def test_absent_socket_is_not_claimed_as_cloudflare_migration_proof(preflight: Any) -> None:
    qualified = preflight.assess(
        _observed_pair(),
        "ORDIVON_GATEWAY_HOST_URL=http://127.0.0.1:8898/mcp "
        "ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE=%d/host-mcp-bearer",
        anonymous_host_initialize_denied=True,
        observed_non_gateway_host_tcp_clients=[],
    )
    assert qualified["status"] == "NECESSARY_PRECONDITIONS_PRESENT"
    assert qualified["observedDirectHostTcpConsumerClasses"] == []
    assert (
        "Cloudflare remote Host ingress target and direct-consumer migration"
        in (qualified["unverified"])
    )


@pytest.mark.parametrize("bad_main_pid", ["", "0", "not-a-pid", "-1"])
def test_invalid_running_gateway_pid_fails_closed(
    preflight: Any, monkeypatch: pytest.MonkeyPatch, bad_main_pid: str
) -> None:
    def fake_run(argv: list[str], **_kwargs: Any) -> Any:
        assert argv[0] == "/usr/bin/systemctl"
        return type("Process", (), {"stdout": bad_main_pid})()

    monkeypatch.setattr(preflight.subprocess, "run", fake_run)
    with pytest.raises(ValueError, match="MainPID"):
        preflight._observed_non_gateway_host_tcp_clients()


def test_socket_probe_execution_error_remains_unobservable(
    preflight: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_run(argv: list[str], **_kwargs: Any) -> Any:
        if argv[0] == "/usr/bin/systemctl":
            return type("Process", (), {"stdout": "1607\n"})()
        raise FileNotFoundError("native ss is not installed")

    monkeypatch.setattr(preflight.subprocess, "run", fake_run)
    with pytest.raises(OSError):
        preflight._observed_non_gateway_host_tcp_clients()


def test_active_second_gateway_without_host_bearer_blocks_release(
    preflight: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A primary service alone cannot qualify all active Host callers."""
    calls: list[tuple[str, ...]] = []

    def fake_run(command: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append(tuple(command))
        if "list-units" in command:
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=(
                    "ordivon-gateway-local-r21.service loaded active running legacy\n"
                    "ordivon-gateway.service loaded active running current\n"
                ),
            )
        assert command[2] == "ordivon-gateway-local-r21.service"
        if "EnvironmentFiles" in command:
            return subprocess.CompletedProcess(command, 0, stdout="")
        return subprocess.CompletedProcess(
            command,
            0,
            stdout="ORDIVON_GATEWAY_HOST_URL=http://127.0.0.1:8898/mcp",
        )

    monkeypatch.setattr(preflight.subprocess, "run", fake_run)
    peer_units = preflight._unqualified_active_peer_host_consumers()
    assert peer_units == ("ordivon-gateway-local-r21.service",)
    assert len(calls) == 3
    env = (
        "ORDIVON_GATEWAY_HOST_URL=http://127.0.0.1:8898/mcp "
        "ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE=%d/host-mcp-bearer"
    )
    result = preflight.assess(
        _observed_pair(),
        env,
        anonymous_host_initialize_denied=True,
        unqualified_active_host_consumers=peer_units,
    )
    assert result["status"] == "NO_GO"
    assert result["unqualifiedActiveHostConsumers"] == list(peer_units)
    assert result["reasons"] == ["ACTIVE_HOST_CONSUMER_MISSING_OWNER_CREDENTIAL"]


@pytest.mark.parametrize(
    "secondary_environment",
    [
        (
            "ORDIVON_GATEWAY_HOST_URL=http://127.0.0.1:8898/mcp "
            "ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE=%d/host-mcp-bearer"
        ),
        "ORDIVON_GATEWAY_HOST_URL=http://127.0.0.1:9999/mcp",
    ],
)
def test_migrated_or_unrelated_active_peer_does_not_block(
    preflight: Any, monkeypatch: pytest.MonkeyPatch, secondary_environment: str
) -> None:
    def fake_run(command: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        if "list-units" in command:
            return subprocess.CompletedProcess(
                command,
                0,
                stdout="ordivon-gateway-local-r21.service loaded active running legacy\n",
            )
        if "EnvironmentFiles" in command:
            return subprocess.CompletedProcess(command, 0, stdout="")
        return subprocess.CompletedProcess(command, 0, stdout=secondary_environment)

    monkeypatch.setattr(preflight.subprocess, "run", fake_run)
    # Declaring a bearer is no longer a migration witness. Only this
    # independently observed per-peer authenticated Host canary qualifies.
    monkeypatch.setattr(
        preflight,
        "_authenticated_host_initialize_accepted",
        lambda environment, *, anonymous_denied, unit: True,
    )
    assert preflight._unqualified_active_peer_host_consumers(anonymous_denied=True) == ()


def test_active_peer_discovery_errors_never_qualify_release(
    preflight: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_run(_command: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        raise subprocess.CalledProcessError(1, "systemctl")

    monkeypatch.setattr(preflight.subprocess, "run", fake_run)
    with pytest.raises(subprocess.CalledProcessError):
        preflight._unqualified_active_peer_host_consumers()


@pytest.mark.parametrize(
    (
        "grant",
        "main_bearer",
        "exact_route",
        "host_anonymous_denied",
        "no_live_direct",
        "no_active_peer",
    ),
    list(itertools.product((False, True), repeat=6)),
)
def test_release_necessary_conditions_are_conjunctive_for_all_64_boolean_states(
    preflight: Any,
    grant: bool,
    main_bearer: bool,
    exact_route: bool,
    host_anonymous_denied: bool,
    no_live_direct: bool,
    no_active_peer: bool,
) -> None:
    """Exhaust the 2**6 current release-qualification states, not only sample tests.

    This checks *necessary* preconditions; a positive result is not a grant,
    bearer proof, remotely authenticated consumer, or production GO.
    """
    qualified_env = "ORDIVON_GATEWAY_HOST_URL=http://127.0.0.1:8898/mcp"
    invalid_env = "ORDIVON_GATEWAY_HOST_URL=http://127.0.0.1:9000/mcp"
    bearer_env = "ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE=%d/host-mcp-bearer"
    env = qualified_env if exact_route else invalid_env
    if main_bearer:
        env += " " + bearer_env
    result = preflight.assess(
        _observed_pair() if grant else None,
        env,
        anonymous_host_initialize_denied=host_anonymous_denied,
        observed_non_gateway_host_tcp_clients=[] if no_live_direct else ["cloudflared"],
        unqualified_active_host_consumers=()
        if no_active_peer
        else ("ordivon-gateway-local-r21.service",),
    )
    reasons = []
    if not grant:
        reasons.append("HOST_SECURITY_POLICY_STANDING_UNOBSERVED")
    if not main_bearer:
        reasons.append("GATEWAY_HOST_OWNER_CREDENTIAL_NOT_CONFIGURED")
    if not exact_route:
        reasons.append("HOST_OWNER_ROUTE_NOT_QUALIFIED_FOR_LOCAL_CANARY")
    if not host_anonymous_denied:
        reasons.append("HOST_DIRECT_ANONYMOUS_MCP_NOT_PROVEN_DENIED")
    if not no_live_direct:
        reasons.append("HOST_DIRECT_NON_GATEWAY_TCP_CONSUMER_OBSERVED")
    if not no_active_peer:
        reasons.append("ACTIVE_HOST_CONSUMER_MISSING_OWNER_CREDENTIAL")
    assert result["reasons"] == reasons
    assert result["status"] == ("NECESSARY_PRECONDITIONS_PRESENT" if not reasons else "NO_GO")
    assert result["observedDirectHostTcpConsumerClasses"] == (
        [] if no_live_direct else ["cloudflared"]
    )
    assert result["unqualifiedActiveHostConsumers"] == (
        [] if no_active_peer else ["ordivon-gateway-local-r21.service"]
    )


def test_prepare_only_preserves_production_security_gate_and_symlink() -> None:
    """Pre-stage is inert; final activation still needs the native live P0 gate."""
    installer = INSTALLER.read_text(encoding="utf-8")
    assert '[ "$4" != "--prepare-only" ]' in installer
    assert "PREPARE_ONLY=false" in installer
    assert "PREPARE_ONLY=true" in installer
    prepare = 'if [ "$PREPARE_ONLY" = true ]; then'
    assert installer.count(prepare) == 1
    stage_index = installer.index(prepare)
    sdk_index = installer.index(
        '"$RELEASE/.venv/bin/python" "$RELEASE/packaging/windows/verify_release.py"'
    )
    user_index = installer.index("service_user_preflight=pass")
    admission_index = installer.index(
        '"$RELEASE/.venv/bin/python" "$RELEASE/packaging/check_live_host_admission.py"'
    )
    promote_index = installer.index('ln -sfn "releases/$COMMIT" "$PREFIX/current.next"')
    assert sdk_index < user_index < stage_index < admission_index < promote_index
    assert "activation=NOT_PERFORMED" in installer[stage_index:admission_index]
    assert "exit 0" in installer[stage_index:admission_index]


def test_prepare_only_argument_is_only_supported_optional_mode() -> None:
    """No accidental mode that bypasses live admission before promotion."""
    import subprocess

    for extra in ("--skip-preflight", "--force", "--activate-prepared", "unexpected"):
        checked = subprocess.run(
            ["/usr/bin/bash", str(INSTALLER), "source", "deadbeef", "/tmp/unused", extra],
            check=False,
            text=True,
            capture_output=True,
            timeout=8,
        )
        assert checked.returncode == 2
        assert "usage: install_release.sh" in checked.stderr


@pytest.mark.parametrize(
    ("peer_environment", "environment_files", "must_block"),
    [
        ("", "/etc/ordivon/gateway/peer.env (ignore_errors=no)", True),
        (
            "ORDIVON_GATEWAY_HOST_URL=http://127.0.0.1:8898/mcp "
            "ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE=%d/host-mcp-bearer",
            "/etc/ordivon/gateway/peer.env (ignore_errors=no)",
            True,
        ),
        (
            "ORDIVON_GATEWAY_HOST_URL=http://127.0.0.1:9999/mcp",
            "/etc/ordivon/gateway/peer.env (ignore_errors=no)",
            True,
        ),
        (
            "ORDIVON_GATEWAY_HOST_URL=http://127.0.0.1:8898/mcp "
            "ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE=%d/host-mcp-bearer",
            "",
            False,
        ),
    ],
)
def test_active_peer_envfile_override_does_not_hide_unqualified_host_consumer(
    preflight: Any,
    monkeypatch: pytest.MonkeyPatch,
    peer_environment: str,
    environment_files: str,
    must_block: bool,
) -> None:
    """A systemd EnvironmentFile can override Environment; unknown effective route is NO_GO."""

    peer_unit = "ordivon-gateway-local-r21.service"

    def native_systemd(command: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        if "list-units" in command:
            return subprocess.CompletedProcess(
                command, 0, stdout=f"{peer_unit} loaded active running secondary\n"
            )
        assert command[:4] == ["/usr/bin/systemctl", "show", peer_unit, "-p"]
        if command[4] == "Environment":
            return subprocess.CompletedProcess(command, 0, stdout=peer_environment)
        if command[4] == "EnvironmentFiles":
            return subprocess.CompletedProcess(command, 0, stdout=environment_files)
        raise AssertionError("unexpected native systemd query")

    monkeypatch.setattr(preflight.subprocess, "run", native_systemd)
    monkeypatch.setattr(
        preflight,
        "_authenticated_host_initialize_accepted",
        lambda environment, *, anonymous_denied, unit: True,
    )
    observed = preflight._unqualified_active_peer_host_consumers(anonymous_denied=True)
    assert observed == ((peer_unit,) if must_block else ())


@pytest.mark.parametrize(
    ("environment_files", "expected"),
    [
        ("", "ORDIVON_GATEWAY_HOST_URL=http://127.0.0.1:8898/mcp"),
        ("/etc/ordivon/gateway/upstream.env (ignore_errors=no)", None),
    ],
)
def test_primary_gateway_environment_files_are_not_false_routing_proof(
    preflight: Any,
    monkeypatch: pytest.MonkeyPatch,
    environment_files: str,
    expected: str | None,
) -> None:
    """Systemd file overrides must never produce a false positive Host Owner route."""

    unit = "ordivon-gateway.service"
    calls: list[str] = []

    def native_systemd(command: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        assert command[:4] == ["/usr/bin/systemctl", "show", unit, "-p"]
        name = command[4]
        calls.append(name)
        if name == "Environment":
            return subprocess.CompletedProcess(
                command, 0, stdout="ORDIVON_GATEWAY_HOST_URL=http://127.0.0.1:8898/mcp"
            )
        if name == "EnvironmentFiles":
            return subprocess.CompletedProcess(command, 0, stdout=environment_files)
        raise AssertionError("unexpected systemd property")

    monkeypatch.setattr(preflight.subprocess, "run", native_systemd)
    assert preflight._qualified_systemd_environment(unit) == expected
    assert calls == ["Environment", "EnvironmentFiles"]


def test_primary_gateway_admission_fails_closed_on_unobserved_envfile_override(
    preflight: Any, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Admission must not treat stale systemd Environment as effective process config."""
    import sys

    monkeypatch.setattr(sys, "argv", ["check_live_host_admission.py"])
    monkeypatch.setattr(preflight, "observe_configured_pair", lambda: _observed_pair())
    monkeypatch.setattr(preflight, "_qualified_systemd_environment", lambda _unit: None)

    result = preflight.main()
    assert result == 3
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "NO_GO"
    assert report["reasons"] == ["HOST_SECURITY_PRECONDITIONS_UNOBSERVABLE"]


@pytest.mark.parametrize("unverified_override", [None, [], ["production post-promotion behavior"]])
def test_installer_called_preflight_cannot_promote_on_only_necessary_conditions(
    preflight: Any,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    unverified_override: list[str] | None,
) -> None:
    """Actual main() exit code is the installer's gate; candidate booleans are not consumer evidence."""
    import sys

    env = (
        "ORDIVON_GATEWAY_HOST_URL=http://127.0.0.1:8898/mcp "
        "ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE=%d/host-mcp-bearer"
    )
    monkeypatch.setattr(sys, "argv", ["check_live_host_admission.py"])
    monkeypatch.setattr(preflight, "observe_configured_pair", lambda: _observed_pair())
    monkeypatch.setattr(preflight, "_qualified_systemd_environment", lambda _unit: env)
    monkeypatch.setattr(preflight, "_rejects_unauthenticated_host_initialize", lambda: True)
    monkeypatch.setattr(
        preflight, "_authenticated_host_initialize_accepted", lambda *_args, **_kw: True
    )
    monkeypatch.setattr(preflight, "_observed_non_gateway_host_tcp_clients", lambda: [])
    monkeypatch.setattr(
        preflight,
        "_unqualified_active_peer_host_consumers",
        lambda *, anonymous_denied: (),
    )
    monkeypatch.setattr(preflight, "_installed_security_host_read_surface_qualified", lambda: True)
    monkeypatch.setattr(
        preflight.subprocess,
        "run",
        lambda *_args, **_kw: subprocess.CompletedProcess(
            args=["systemctl"], returncode=0, stdout="active\n"
        ),
    )

    # Presentation-only text must never authorize a physical release.
    # A future refactor might shorten or empty the informational list.
    if unverified_override is not None:
        original_assess = preflight.assess

        def assess_with_diagnostic_text_change(*args: Any, **kwargs: Any) -> dict[str, Any]:
            standing = original_assess(*args, **kwargs)
            standing["unverified"] = list(unverified_override)
            return standing

        monkeypatch.setattr(preflight, "assess", assess_with_diagnostic_text_change)

    assert preflight.main() == 3
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "NO_GO"
    assert report["reasons"] == ["INDEPENDENT_CONSUMER_CUTOVER_NOT_VERIFIED"]
    if unverified_override is None:
        assert "direct Host MCP connector migration" in report["unverified"]
        assert "actual Principal-to-Actor and resource authorization" in report["unverified"]
    else:
        assert report["unverified"] == unverified_override


# R25 reverse-liveness: expand a verified Host ingress before legacy migration.
# The second local port is not a generalized localhost Owner proxy.


@pytest.mark.parametrize("native_owner_verified", [True, False])
def test_secure_parallel_host_route_requires_live_systemd_owner(
    preflight: Any, monkeypatch: pytest.MonkeyPatch, native_owner_verified: bool
) -> None:
    monkeypatch.setattr(
        preflight,
        "_protected_host_service_owns_listener",
        lambda: native_owner_verified,
        raising=False,
    )
    env = (
        "ORDIVON_GATEWAY_HOST_URL=http://127.0.0.1:19008/mcp "
        "ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE=%d/host-mcp-bearer"
    )
    standing = preflight.assess(
        _observed_pair(),
        env,
        anonymous_host_initialize_denied=True,
    )
    assert standing["hostOwnerRouteQualified"] is native_owner_verified
    assert standing["status"] == (
        "NECESSARY_PRECONDITIONS_PRESENT" if native_owner_verified else "NO_GO"
    )


def test_secure_host_never_reads_bearer_for_401_lookalike_unowned_listener(
    preflight: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = (
        "ORDIVON_GATEWAY_HOST_URL=http://127.0.0.1:19008/mcp "
        "ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE=%d/host-mcp-bearer"
    )
    monkeypatch.setattr(
        preflight, "_protected_host_service_owns_listener", lambda: False, raising=False
    )

    def reject_secret_read(_path: str) -> str:
        raise AssertionError("Never read or transmit a bearer to an unowned service")

    monkeypatch.setattr(preflight, "_read_private_token_file", reject_secret_read)
    assert not preflight._authenticated_host_initialize_accepted(env, anonymous_denied=True)


@pytest.mark.parametrize(
    ("native_socket_pid", "native_listen_address", "service_active", "expected"),
    [
        (783, "127.0.0.1:19008", "active", True),
        (784, "127.0.0.1:19008", "active", False),
        (783, "0.0.0.0:19008", "active", False),
        (783, "127.0.0.1:19008", "inactive", False),
    ],
)
def test_protected_host_socket_must_belong_to_expected_active_systemd_unit(
    preflight: Any,
    monkeypatch: pytest.MonkeyPatch,
    native_socket_pid: int,
    native_listen_address: str,
    service_active: str,
    expected: bool,
) -> None:
    def native(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if command[0] == "/usr/bin/systemctl":
            assert command[0:3] == [
                "/usr/bin/systemctl",
                "show",
                "ordivon-host-v2-protected.service",
            ]
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=(
                    "MainPID=783\n"
                    f"ActiveState={service_active}\n"
                    "User=ordivon-host-v2-protected\n"
                    "DynamicUser=yes\n"
                ),
            )
        assert command[0] == "/usr/bin/ss"
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=(
                f"LISTEN 0 2048 {native_listen_address} 0.0.0.0:* "
                f'users:(("uvicorn",pid={native_socket_pid},fd=6))\n'
            ),
        )

    monkeypatch.setattr(preflight.subprocess, "run", native)
    assert preflight._protected_host_service_owns_listener() is expected


def test_candidate_route_anonymous_negative_probes_only_fixed_secure_port(
    preflight: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[int] = []

    class Conn:
        def __init__(self, host: str, port: int, timeout: int) -> None:
            assert host == "127.0.0.1" and timeout == 4
            seen.append(port)

        def request(self, *_args: Any, **_kw: Any) -> None:
            pass

        def getresponse(self) -> Any:
            return type("Response", (), {"status": 401})()

        def close(self) -> None:
            pass

    monkeypatch.setattr(preflight.http.client, "HTTPConnection", Conn)
    assert preflight._rejects_unauthenticated_host_initialize(host_port=19008)
    assert seen == [19008]


def test_active_legacy_peer_still_blocks_when_new_primary_uses_secure_host(
    preflight: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    peer = "ordivon-gateway-local-r21.service"
    env = (
        "ORDIVON_GATEWAY_HOST_URL=http://127.0.0.1:8898/mcp "
        "ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE=%d/host-mcp-bearer"
    )

    def native(command: list[str], **_kw: Any) -> subprocess.CompletedProcess[str]:
        if "list-units" in command:
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=f"{peer} loaded active running legacy\n",
            )
        assert command[2] == peer
        return subprocess.CompletedProcess(
            command,
            0,
            stdout="" if "EnvironmentFiles" in command else env,
        )

    monkeypatch.setattr(preflight.subprocess, "run", native)
    monkeypatch.setattr(
        preflight,
        "_authenticated_host_initialize_accepted",
        lambda *_args, **_kw: (_ for _ in ()).throw(
            AssertionError("Legacy peer must not receive a protected-route token")
        ),
    )
    assert preflight._unqualified_active_peer_host_consumers(
        anonymous_denied=True,
        primary_host_port=19008,
    ) == (peer,)


def test_real_release_main_still_refuses_promotion_for_fully_qualified_parallel_host(
    preflight: Any, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Native protected route and valid bearer are never an Agent cutover receipt."""
    import sys

    env = (
        "ORDIVON_GATEWAY_HOST_URL=http://127.0.0.1:19008/mcp "
        "ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE=%d/host-mcp-bearer"
    )
    monkeypatch.setattr(sys, "argv", ["check_live_host_admission.py"])
    monkeypatch.setattr(preflight, "observe_configured_pair", lambda: _observed_pair())
    monkeypatch.setattr(preflight, "_qualified_systemd_environment", lambda _unit: env)
    monkeypatch.setattr(preflight, "_protected_host_service_owns_listener", lambda: True)
    monkeypatch.setattr(
        preflight,
        "_rejects_unauthenticated_host_initialize",
        lambda *, host_port: host_port == 19008,
    )
    monkeypatch.setattr(
        preflight,
        "_authenticated_host_initialize_accepted",
        lambda *_args, **_kw: True,
    )
    monkeypatch.setattr(preflight, "_observed_non_gateway_host_tcp_clients", lambda: [])
    monkeypatch.setattr(
        preflight,
        "_unqualified_active_peer_host_consumers",
        lambda *, anonymous_denied, primary_host_port: (),
    )
    monkeypatch.setattr(preflight, "_installed_security_host_read_surface_qualified", lambda: True)
    monkeypatch.setattr(
        preflight.subprocess,
        "run",
        lambda *_args, **_kw: subprocess.CompletedProcess(
            args=["systemctl"], returncode=0, stdout="active\n"
        ),
    )
    assert preflight.main() == 3
    report = json.loads(capsys.readouterr().out)
    assert report["hostOwnerRouteQualified"] is True
    assert report["hostOwnerAuthenticatedInitializeAccepted"] is True
    assert report["status"] == "NO_GO"
    assert report["reasons"] == ["INDEPENDENT_CONSUMER_CUTOVER_NOT_VERIFIED"]


@pytest.mark.parametrize(
    "environment",
    [
        "",
        'ORDIVON_GATEWAY_HOST_URL="unterminated',
        "ORDIVON_GATEWAY_HOST_URL=",
        "ORDIVON_GATEWAY_HOST_URL=http://127.0.0.1:8898/mcp "
        "ORDIVON_GATEWAY_HOST_URL=http://127.0.0.1:9999/mcp",
        "ORDIVON_GATEWAY_HOST_URL=http://127.0.0.1:19008/mcp",
        "ORDIVON_GATEWAY_HOST_URL=https://host-alias.test/mcp",
    ],
)
def test_unqualified_peer_route_is_not_proof_of_unrelated_consumer(
    preflight: Any, monkeypatch: pytest.MonkeyPatch, environment: str
) -> None:
    peer = "ordivon-gateway-local-r21.service"
    monkeypatch.setattr(
        preflight.subprocess,
        "run",
        lambda *a, **kw: subprocess.CompletedProcess(
            a, 0, stdout=f"{peer} loaded active running secondary\n"
        ),
    )
    monkeypatch.setattr(preflight, "_qualified_systemd_environment", lambda unit: environment)
    monkeypatch.setattr(preflight, "_protected_host_service_owns_listener", lambda: False)

    def forbidden(*args: Any, **kwargs: Any) -> bool:
        raise AssertionError("Unknown peer route cannot consume Owner credentials")

    monkeypatch.setattr(preflight, "_authenticated_host_initialize_accepted", forbidden)
    assert preflight._unqualified_active_peer_host_consumers(anonymous_denied=True) == (peer,)


def test_peer_census_bounds_all_unique_peers_before_any_credential_probe(
    preflight: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    rows = "".join(
        f"ordivon-gateway-peer-{i}.service loaded active running fixture\n" for i in range(33)
    )
    monkeypatch.setattr(
        preflight.subprocess,
        "run",
        lambda *a, **kw: subprocess.CompletedProcess(a, 0, stdout=rows),
    )

    def forbidden(unit: str) -> str:
        raise AssertionError("Census must be admitted before peer effects")

    monkeypatch.setattr(preflight, "_qualified_systemd_environment", forbidden)
    with pytest.raises(ValueError, match="census exceeds bound"):
        preflight._unqualified_active_peer_host_consumers(anonymous_denied=True)


def test_duplicate_peer_rows_do_not_repeat_native_observation(
    preflight: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    peer = "ordivon-gateway-local-r21.service"
    row = f"{peer} loaded active running fixture\n"
    monkeypatch.setattr(
        preflight.subprocess,
        "run",
        lambda *a, **kw: subprocess.CompletedProcess(a, 0, stdout=row * 2),
    )
    calls: list[str] = []

    def environment(unit: str) -> str:
        calls.append(unit)
        return "ORDIVON_GATEWAY_HOST_URL=http://127.0.0.1:9999/mcp"

    monkeypatch.setattr(preflight, "_qualified_systemd_environment", environment)
    assert preflight._unqualified_active_peer_host_consumers() == ()
    assert calls == [peer]


# Finite decision table: route declaration, native owner observation, and
# credential effects are different obligations. Rows explicitly describe
# which observations may reach the authenticated probe, not its internals.
@pytest.mark.parametrize(
    (
        "route",
        "owner_verified",
        "primary",
        "credential",
        "denial",
        "accepted",
        "expect_block",
        "expect_probe",
    ),
    [
        (None, False, 8898, True, True, True, True, False),
        ("", False, 8898, True, True, True, True, False),
        ("http://127.0.0.1:8898/mcp", False, 8898, True, True, True, False, True),
        ("http://127.0.0.1:8898/mcp", False, 8898, True, True, False, True, True),
        ("http://127.0.0.1:8898/mcp", False, 8898, False, True, True, True, False),
        ("http://127.0.0.1:8898/mcp", False, 8898, True, False, True, True, False),
        ("http://127.0.0.1:8898/mcp", False, 19008, True, True, True, True, False),
        ("http://127.0.0.1:19008/mcp", True, 19008, True, True, True, False, True),
        ("http://127.0.0.1:19008/mcp", True, 19008, True, True, False, True, True),
        ("http://127.0.0.1:19008/mcp", True, 19008, False, True, True, True, False),
        ("http://127.0.0.1:19008/mcp", True, 19008, True, False, True, True, False),
        ("http://127.0.0.1:19008/mcp", False, 19008, True, True, True, True, False),
        ("http://127.0.0.1:19008/mcp", True, 8898, True, True, True, True, False),
        ("http://127.0.0.1:9999/mcp", False, 8898, True, True, True, False, False),
        ("http://127.0.0.1:65536/mcp", False, 8898, True, True, True, True, False),
        ("http://127.0.0.1:08898/mcp", False, 8898, True, True, True, True, False),
        ("http://localhost:8898/mcp", False, 8898, True, True, True, True, False),
        ("http://127.0.0.1:8898/mcp?x=1", False, 8898, True, True, True, True, False),
    ],
)
def test_peer_observation_decision_table(
    preflight: Any,
    monkeypatch: pytest.MonkeyPatch,
    route: str | None,
    owner_verified: bool,
    primary: int,
    credential: bool,
    denial: bool,
    accepted: bool,
    expect_block: bool,
    expect_probe: bool,
) -> None:
    peer = "ordivon-gateway-test.service"
    env = "" if route is None else f"ORDIVON_GATEWAY_HOST_URL={route}"
    if credential:
        env += " ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE=%d/host-mcp-bearer"
    monkeypatch.setattr(
        preflight.subprocess,
        "run",
        lambda *a, **kw: subprocess.CompletedProcess(
            a, 0, stdout=f"{peer} loaded active running fixture\n"
        ),
    )
    monkeypatch.setattr(preflight, "_qualified_systemd_environment", lambda unit: env)
    monkeypatch.setattr(preflight, "_protected_host_service_owns_listener", lambda: owner_verified)
    calls: list[str] = []

    def probe(environment: str, *, anonymous_denied: bool, unit: str) -> bool:
        assert environment == env
        assert anonymous_denied is True
        calls.append(unit)
        return accepted

    monkeypatch.setattr(preflight, "_authenticated_host_initialize_accepted", probe)
    assert preflight._unqualified_active_peer_host_consumers(
        anonymous_denied=denial, primary_host_port=primary
    ) == ((peer,) if expect_block else ())
    assert calls == ([peer] if expect_probe else [])


def test_peer_census_exact_bound_and_deterministic_order(preflight: Any) -> None:
    units = [f"ordivon-gateway-p-{i:02d}.service" for i in range(32)]
    output = "\n".join(f"{unit} loaded active running fixture" for unit in reversed(units))
    output += "\nordivon-gateway.service loaded active running primary\n" + output
    assert preflight._active_peer_units(output) == tuple(units)


@pytest.mark.parametrize(
    ("output", "reason"),
    [
        ("unexpected.service loaded active running fixture", "unexpected active"),
        (" " * 131_073, "census exceeds bound"),
    ],
)
def test_peer_census_rejects_unqualified_native_output(
    preflight: Any, output: str, reason: str
) -> None:
    with pytest.raises(ValueError, match=reason):
        preflight._active_peer_units(output)
