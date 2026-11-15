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


def _operator_data(grants: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "ordivon": {
            "security": {
                "gateway_artifact_config": {"cf_issuer": "https://issuer.test"},
                "gateway_host_actor_grants": grants,
            }
        }
    }


def _grant() -> dict[str, Any]:
    return {
        "active": True,
        "principalId": "principal:cf-access:" + "a" * 64,
        "issuer": "https://issuer.test",
        "actorRef": "actor:ordivon:agent",
        "notBeforeEpochSeconds": 1_000,
        "expiresAtEpochSeconds": 9_000,
        "allowedTools": ["topic.resume", "message.post"],
        "exactRefs": ["topic:ordivon:test"],
    }


def test_existing_agent_actor_reference_is_a_qualified_grant_candidate(preflight: Any) -> None:
    """The Security policy accepts exact Agent ActorRefs, not only actor: aliases.

    This preflight is necessary-condition detection, never the PDP's ALLOW.
    A real Host collaboration actor already uses the agent: namespace.
    """
    grant = {**_grant(), "actorRef": "agent:chatgpt:gpt6-host-continuation"}
    observed = preflight.assess(
        _operator_data([grant]),
        (
            "ORDIVON_GATEWAY_HOST_URL=http://127.0.0.1:8898/mcp "
            "ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE=%d/host-mcp-bearer"
        ),
        now=1_500,
        anonymous_host_initialize_denied=True,
    )
    assert observed["activeHostDelegationCount"] == 1
    assert "HOST_OPERATOR_DELEGATIONS_ABSENT_OR_INACTIVE" not in observed["reasons"]


def test_real_missing_operator_grants_and_owner_credential_are_blocked(preflight: Any) -> None:
    result = preflight.assess(
        _operator_data([]), "", now=1_500, anonymous_host_initialize_denied=True
    )
    assert result["status"] == "NO_GO"
    assert result["activeHostDelegationCount"] == 0
    assert result["hostOwnerCredentialDeclared"] is False
    assert result["reasons"] == [
        "HOST_OPERATOR_DELEGATIONS_ABSENT_OR_INACTIVE",
        "GATEWAY_HOST_OWNER_CREDENTIAL_NOT_CONFIGURED",
        "HOST_OWNER_ROUTE_NOT_QUALIFIED_FOR_LOCAL_CANARY",
    ]


def test_bounded_promotion_prerequisites_are_distinct_from_authorization(preflight: Any) -> None:
    result = preflight.assess(
        _operator_data([_grant()]),
        (
            "ORDIVON_GATEWAY_HOST_URL=http://127.0.0.1:8898/mcp "
            "ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE=%d/host-mcp-bearer"
        ),
        now=1_500,
        anonymous_host_initialize_denied=True,
    )
    assert result["status"] == "NECESSARY_PRECONDITIONS_PRESENT"
    assert result["activeHostDelegationCount"] == 1
    assert result["hostOwnerCredentialDeclared"] is True
    assert "actual Principal-to-Actor and resource authorization" in result["unverified"]
    assert "direct Host MCP connector migration" in result["unverified"]


@pytest.mark.parametrize(
    "mutation",
    [
        {"active": False},
        {"principalId": ""},
        {"issuer": ""},
        {"actorRef": ""},
        {"notBeforeEpochSeconds": 2_000},
        {"expiresAtEpochSeconds": 1_499},
        {"expiresAtEpochSeconds": True},
        {"allowedTools": ["unrelated.capability"]},
        {"allowedTools": "message.post"},
    ],
)
def test_nonqualified_grants_cannot_unblock_live_release(
    preflight: Any, mutation: dict[str, Any]
) -> None:
    grant = {**_grant(), **mutation}
    assert (
        preflight.assess(
            _operator_data([grant]),
            (
                "ORDIVON_GATEWAY_HOST_URL=http://127.0.0.1:8898/mcp "
                "ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE=/run/credentials/gateway/host"
            ),
            now=1_500,
            anonymous_host_initialize_denied=True,
        )["status"]
        == "NO_GO"
    )


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
    result = preflight.assess(_operator_data([_grant()]), environment, now=1_500)
    assert "GATEWAY_HOST_OWNER_CREDENTIAL_NOT_CONFIGURED" in result["reasons"]


def test_operator_data_file_has_no_symlink_fallback(preflight: Any, tmp_path: Path) -> None:
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(_operator_data([_grant()])))
    symlink = tmp_path / "alias.json"
    symlink.symlink_to(path)
    assert preflight._policy_data(path) == _operator_data([_grant()])
    with pytest.raises(ValueError, match="unavailable"):
        preflight._policy_data(symlink)
    path.write_text("[]")
    with pytest.raises(ValueError, match="object"):
        preflight._policy_data(path)


def test_official_production_promotion_consumer_checks_before_atomic_switch() -> None:
    installer = INSTALLER.read_text(encoding="utf-8")
    needle = '"$RELEASE/.venv/bin/python" "$RELEASE/packaging/check_live_host_admission.py"'
    assert needle in installer
    assert '"$(realpath -m "$PREFIX")" = "/opt/ordivon/gateway"' in installer
    assert "/run/credentials/ordivon-security-gateway-authzen.service/trusted-issuer" in installer
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
        _operator_data([_grant()]),
        env,
        now=1_500,
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
            _operator_data([_grant()]),
            env,
            now=1_500,
            anonymous_host_initialize_denied=observed,
        )
        assert result["status"] == "NO_GO"
        assert result["activeHostDelegationCount"] == 1
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
        _operator_data([_grant()]),
        "ORDIVON_GATEWAY_HOST_URL=http://127.0.0.1:8898/mcp "
        "ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE=%d/host-mcp-bearer",
        now=1_500,
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
        _operator_data([_grant()]),
        "ORDIVON_GATEWAY_HOST_URL=http://127.0.0.1:8898/mcp "
        "ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE=%d/host-mcp-bearer",
        now=1_500,
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
        _operator_data([_grant()]),
        env,
        now=1500,
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
        _operator_data([_grant()] if grant else []),
        env,
        now=1500,
        anonymous_host_initialize_denied=host_anonymous_denied,
        observed_non_gateway_host_tcp_clients=[] if no_live_direct else ["cloudflared"],
        unqualified_active_host_consumers=()
        if no_active_peer
        else ("ordivon-gateway-local-r21.service",),
    )
    reasons = []
    if not grant:
        reasons.append("HOST_OPERATOR_DELEGATIONS_ABSENT_OR_INACTIVE")
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
    monkeypatch.setattr(preflight, "_policy_data", lambda _path: _operator_data([_grant()]))
    monkeypatch.setattr(preflight, "_qualified_systemd_environment", lambda _unit: None)

    result = preflight.main()
    assert result == 3
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "NO_GO"
    assert report["reasons"] == ["HOST_SECURITY_PRECONDITIONS_UNOBSERVABLE"]
