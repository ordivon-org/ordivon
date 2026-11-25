"""Read-only production Gateway/Host admission preflight.

This is NOT an authorization decision or a substitute for actual
Principal->Actor/Owner-canary testing. It rejects known deployment
precondition failures before the existing Gateway symlink promotion.
The Security policy and Systemd remain the natural authorities.
"""

from __future__ import annotations

import argparse
import http.client
import json
import os
import re
import shlex
import subprocess
from pathlib import Path
from typing import Any

import requests

from ordivon_gateway.security.owner_identity import OwnerCallError, _read_private_token_file
from ordivon_gateway.security.standing_transport import observe_configured_pair

MAX_POLICY_BYTES = 2_097_152
MAX_SOCKET_EVIDENCE_BYTES = 131_072
GATEWAY_UNIT = "ordivon-gateway.service"
SECURITY_UNIT = "ordivon-security-gateway-authzen.service"
# The installed Gateway Owner endpoint is local; do not chase caller-provided
# hosts, redirects or public URLs from a production release preflight.
HOST_OWNER_URL = "http://127.0.0.1:8898/mcp"
# R25: explicit second stage of Parallel Change, NOT arbitrary local routing.
# The legacy endpoint remains pinned for its real direct Host MCP consumers.
PROTECTED_HOST_OWNER_URL = "http://127.0.0.1:19008/mcp"
PROTECTED_HOST_UNIT = "ordivon-host-v2-protected.service"
PROTECTED_HOST_PORT = 19008
MCP_INITIALIZE = json.dumps(
    {
        "jsonrpc": "2.0",
        "id": "gateway-host-anonymous-release-negative",
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "ordivon-gateway-release-negative", "version": "1"},
        },
    },
    separators=(",", ":"),
).encode("utf-8")


def _rejects_unauthenticated_host_initialize(*, host_port: int = 8898) -> bool:
    """A real, read-only local HTTP canary: only 401/403 prove this negative.

    This request intentionally has no Authorization header. 200, other HTTP
    responses, network failures and unknown transports all mean NOT PROVEN.
    stdlib HTTPConnection does not follow redirects or honor HTTP proxies.
    """
    if host_port not in (8898, PROTECTED_HOST_PORT):
        return False
    conn = http.client.HTTPConnection("127.0.0.1", host_port, timeout=4)
    try:
        conn.request(
            "POST",
            "/mcp",
            body=MCP_INITIALIZE,
            headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
                "MCP-Protocol-Version": "2025-06-18",
            },
        )
        response = conn.getresponse()
        return response.status in (401, 403)
    except OSError, http.client.HTTPException:
        return False
    finally:
        conn.close()


def _observed_non_gateway_host_tcp_clients() -> list[str]:
    """A one-way, read-only physical falsifier of Host direct-client migration.

    Only a socket *actually established* on the known Host Owner endpoint
    qualifies as positive evidence. Empty observation is NEVER proof that
    remote Cloudflare ingress and all other direct clients have migrated.
    The running Gateway service PID, not an executable name, defines the
    excluded natural Gateway->Host upstream connection.
    """
    pid_result = subprocess.run(
        ["/usr/bin/systemctl", "show", GATEWAY_UNIT, "-p", "MainPID", "--value"],
        capture_output=True,
        text=True,
        check=True,
        timeout=8,
    )
    pid_raw = pid_result.stdout.strip()
    if not pid_raw.isdecimal() or int(pid_raw) <= 0:
        raise ValueError("current Gateway MainPID is unavailable")
    gateway_pid = int(pid_raw)
    sockets = subprocess.run(
        ["/usr/bin/ss", "-H", "-t", "-n", "-p", "( dport = :8898 )"],
        capture_output=True,
        text=True,
        check=True,
        timeout=8,
    )
    if len(sockets.stdout.encode("utf-8")) > MAX_SOCKET_EVIDENCE_BYTES:
        raise ValueError("direct Host TCP observation exceeds bounded size")
    clients: set[str] = set()
    for row in sockets.stdout.splitlines():
        fields = row.split()
        if len(fields) < 5 or fields[0] != "ESTAB" or fields[4] != "127.0.0.1:8898":
            continue
        pids = {int(match) for match in re.findall(r"pid=(\d+)", row)}
        if pids == {gateway_pid}:
            continue
        if '"cloudflared"' in row:
            clients.add("cloudflared")
        elif pids:
            clients.add("other_non_gateway")
        else:
            # A privileged socket probe without process attribution cannot
            # establish that this connection belongs to the known Gateway.
            clients.add("unattributed")
    return sorted(clients)


def _qualified_systemd_environment(unit: str) -> str | None:
    """Return source-visible service env only when no EnvironmentFile can override it.

    systemctl show -p Environment reports unit-declared values, not effective
    process values after EnvironmentFile overrides. Never infer an unrelated
    route or a working bearer from such incomplete evidence. No private env
    file contents are read or logged here; unqualified yields None.
    """
    environment = subprocess.run(
        ["/usr/bin/systemctl", "show", unit, "-p", "Environment", "--value"],
        capture_output=True,
        text=True,
        check=True,
        timeout=8,
    )
    files = subprocess.run(
        ["/usr/bin/systemctl", "show", unit, "-p", "EnvironmentFiles", "--value"],
        capture_output=True,
        text=True,
        check=True,
        timeout=8,
    )
    return None if files.stdout.strip() else environment.stdout


def _protected_host_service_owns_listener() -> bool:
    """Verify a *specific systemd workload* owns the new loopback listener.

    An arbitrary local HTTP service that returns 401 is NOT a trusted Host
    and must never receive the Gateway's private bearer. This is a native
    preflight witness only, not an Agent identity or an AuthZEN ALLOW.
    """
    try:
        service = subprocess.run(
            [
                "/usr/bin/systemctl",
                "show",
                PROTECTED_HOST_UNIT,
                "-p",
                "ActiveState",
                "-p",
                "MainPID",
                "-p",
                "User",
                "-p",
                "DynamicUser",
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=8,
        )
        values = dict(line.split("=", 1) for line in service.stdout.splitlines() if "=" in line)
        pid = values.get("MainPID", "")
        if not (
            values.get("ActiveState") == "active"
            and values.get("User") == "ordivon-host-v2-protected"
            and values.get("DynamicUser") == "yes"
            and pid.isdecimal()
            and int(pid) > 0
        ):
            return False
        sockets = subprocess.run(
            [
                "/usr/bin/ss",
                "-H",
                "-l",
                "-t",
                "-n",
                "-p",
                f"( sport = :{PROTECTED_HOST_PORT} )",
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=8,
        )
        if len(sockets.stdout.encode("utf-8")) > MAX_SOCKET_EVIDENCE_BYTES:
            return False
        listeners = [line.split() for line in sockets.stdout.splitlines()]
        return bool(
            len(listeners) == 1
            and len(listeners[0]) >= 5
            and listeners[0][0] == "LISTEN"
            and listeners[0][3] == f"127.0.0.1:{PROTECTED_HOST_PORT}"
            and {int(x) for x in re.findall(r"pid=(\d+)", sockets.stdout)} == {int(pid)}
        )
    except OSError, ValueError, subprocess.SubprocessError:
        return False


def _qualified_host_route_port(systemd_environment: str) -> int | None:
    """Bind a declared Gateway route to its *actual* locally qualified Owner."""
    try:
        entries = shlex.split(systemd_environment)
    except ValueError:
        return None
    declared = [
        entry.partition("=")[2]
        for entry in entries
        if entry.startswith("ORDIVON_GATEWAY_HOST_URL=")
    ]
    if declared == [HOST_OWNER_URL]:
        return 8898
    if declared == [PROTECTED_HOST_OWNER_URL] and _protected_host_service_owns_listener():
        return PROTECTED_HOST_PORT
    return None


def _owner_route_is_probed_endpoint(systemd_environment: str) -> bool:
    return _qualified_host_route_port(systemd_environment) is not None


def _declared_owner_credential_path(
    systemd_environment: str, *, unit: str = GATEWAY_UNIT
) -> str | None:
    """Resolve only the existing Gateway owner-bearer declaration.

    The production Gateway's systemd %d specifier resolves to its credential
    directory; we never interpret shell, read a private env file or accept a
    caller-supplied upstream URL. Two competing declarations are ambiguous.
    """
    try:
        entries = shlex.split(systemd_environment)
    except ValueError:
        return None
    values = [
        item.partition("=")[2]
        for item in entries
        if item.startswith("ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE=")
    ]
    if len(values) != 1:
        return None
    value = values[0]
    if value.startswith("%d/"):
        relative = value[3:]
        if (
            not relative
            or relative.startswith("/")
            or any(part in (".", "..", "") for part in relative.split("/"))
        ):
            return None
        return f"/run/credentials/{unit}/{relative}"
    if value.startswith("/") and ".." not in value.split("/") and not value.startswith("//"):
        return value
    return None


def _declares_host_owner_identity(systemd_environment: str) -> bool:
    return _declared_owner_credential_path(systemd_environment) is not None


def _authenticated_host_initialize_accepted(
    systemd_environment: str, *, anonymous_denied: bool, unit: str = GATEWAY_UNIT
) -> bool:
    """Proof that the declared *current* Gateway bearer reaches the exact Host MCP.

    Never send operator secret bytes to the Host until its *separate* unauthenticated
    initialize returned an HTTP 401/403. A declaration, socket connection, 200
    from a different app, redirect or malformed MCP JSON is not acceptance.
    Actual Principal/Actor grants and real business tool use still need AuthZEN.
    """
    port = _qualified_host_route_port(systemd_environment)
    if not anonymous_denied or port is None:
        # Check trusted unit identity BEFORE reading any token, even if a
        # malicious 401-looking local listener has been provisioned.
        return False
    path = _declared_owner_credential_path(systemd_environment, unit=unit)
    if path is None:
        return False
    try:
        # Reuse the very same bounded, no-follow, same-inode credential reader
        # as Gateway's existing Owner upstream client; never print the token.
        bearer = _read_private_token_file(path)
    except OSError, OwnerCallError, ValueError:
        return False
    if len(bearer) < 32:
        return False

    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=4)
    try:
        connection.request(
            "POST",
            "/mcp",
            body=MCP_INITIALIZE,
            headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
                "MCP-Protocol-Version": "2025-06-18",
                "Authorization": f"Bearer {bearer}",
            },
        )
        response = connection.getresponse()
        if response.status != 200:
            return False
        raw = response.read(65_537)
        if len(raw) > 65_536:
            return False
        result = json.loads(raw)
        protocol = result.get("result") if isinstance(result, dict) else None
        return bool(
            isinstance(result, dict)
            and result.get("jsonrpc") == "2.0"
            and result.get("id") == "gateway-host-anonymous-release-negative"
            and isinstance(protocol, dict)
            and protocol.get("protocolVersion") == "2025-06-18"
            and isinstance(protocol.get("capabilities"), dict)
            and isinstance(protocol.get("serverInfo"), dict)
            and protocol["serverInfo"].get("name") == "ordivon-host-v2"
            and isinstance(protocol["serverInfo"].get("version"), str)
            and bool(protocol["serverInfo"]["version"].strip())
        )
    except OSError, http.client.HTTPException, ValueError, UnicodeDecodeError:
        return False
    finally:
        connection.close()


def _apply_authenticated_host_canary(
    standing: dict[str, Any], *, qualified: bool
) -> dict[str, Any]:
    """A necessary physical M2M proof, separate from Security authorization."""
    standing["hostOwnerAuthenticatedInitializeAccepted"] = qualified
    if not qualified:
        standing["status"] = "NO_GO"
        standing["reasons"].append("HOST_OWNER_AUTHENTICATED_MCP_NOT_PROVEN")
    return standing


def _unqualified_active_peer_host_consumers(
    *, anonymous_denied: bool = False, primary_host_port: int = 8898
) -> tuple[str, ...]:
    """Check other ACTIVE Gateway services that point at this Host Owner route.

    The release installer promotes only the primary Gateway, but a distinct
    active Gateway could lose Host connectivity when the Host is hardened.
    This read-only discovery checks service config, not live Agent credentials
    or the successful migration of independent direct Host connectors.
    A failed systemd query is never a positive release witness.
    """
    units = subprocess.run(
        [
            "/usr/bin/systemctl",
            "list-units",
            "ordivon-gateway*.service",
            "--type=service",
            "--state=active",
            "--no-legend",
            "--plain",
            "--no-pager",
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=8,
    )
    observed: set[str] = set()
    for line in units.stdout.splitlines():
        columns = line.split()
        if not columns:
            continue
        unit = columns[0]
        if not re.fullmatch(r"ordivon-gateway(?:-[a-z0-9._-]+)?\.service", unit):
            raise ValueError("unexpected active Gateway consumer unit")
        if unit == GATEWAY_UNIT:
            continue
        if len(observed) >= 32:
            raise ValueError("active Gateway consumer census exceeds bound")
        environment = _qualified_systemd_environment(unit)
        if environment is None:
            observed.add(unit)
        else:
            peer_port = _qualified_host_route_port(environment)
            if peer_port is None:
                continue  # Unknown/different Owner target; not this exact Host.
            # In Parallel Change a peer still using legacy 8898 is a migration
            # blocker even when the new primary has a working protected port.
            # NEVER send a new Host bearer to the peer's old/other listener.
            if (
                peer_port != primary_host_port
                or not _declares_host_owner_identity(environment)
                or not anonymous_denied
                or not _authenticated_host_initialize_accepted(
                    environment, anonymous_denied=anonymous_denied, unit=unit
                )
            ):
                observed.add(unit)
    return tuple(sorted(observed))


def _installed_security_host_read_surface_qualified() -> bool:
    """One-way installed Security Rego => Gateway source consumer qualification.

    Native Security's actual systemd-declared OPA and Rego paths are read
    without tokens. A policy file inspection is only a necessary source-
    installation condition, NOT an installed PDP ALLOW, loaded live model
    proof or a Principal/Actor grant.
    """
    try:
        unit = subprocess.run(
            ["/usr/bin/systemctl", "show", SECURITY_UNIT, "-p", "Environment", "--value"],
            capture_output=True,
            text=True,
            check=True,
            timeout=8,
        )
        settings = dict(item.split("=", 1) for item in shlex.split(unit.stdout) if "=" in item)
        policy = Path(settings["ORDIVON_SECURITY_AUTHZEN_POLICY_FILE"])
        opa = Path(settings["ORDIVON_SECURITY_AUTHZEN_OPA"])
        if (
            not policy.is_absolute()
            or not policy.is_file()
            or policy.is_symlink()
            or policy.stat().st_size > MAX_POLICY_BYTES
            or not opa.is_absolute()
            or not opa.is_file()
            or opa.is_symlink()
            or not os.access(opa, os.X_OK)
        ):
            return False

        inventory = json.loads(
            (Path(__file__).resolve().parents[1] / "enforcement-surface.json").read_text(
                encoding="utf-8"
            )
        )
        expected = {
            row["name"]
            for row in inventory["tools"]
            if row["routeOwner"] == "host" and row["operation"] == "read"
        }
        if not expected or "message.get" not in expected:
            return False

        namespace = "data.ordivon.security.gateway_artifact."

        def read_opa_object(property_name: str) -> dict[str, list[str]] | None:
            result = subprocess.run(
                [
                    str(opa),
                    "eval",
                    "--data",
                    str(policy),
                    "--format=json",
                    namespace + property_name,
                ],
                capture_output=True,
                text=True,
                check=True,
                timeout=8,
            )
            if len(result.stdout.encode("utf-8")) > MAX_SOCKET_EVIDENCE_BYTES:
                return None
            response = json.loads(result.stdout)
            rows = response.get("result")
            if not isinstance(rows, list) or len(rows) != 1:
                return None
            expressions = rows[0].get("expressions")
            if not isinstance(expressions, list) or len(expressions) != 1:
                return None
            value = expressions[0].get("value")
            if not isinstance(value, dict) or not all(
                isinstance(k, str) and isinstance(v, list) and all(isinstance(f, str) for f in v)
                for k, v in value.items()
            ):
                return None
            return value

        selectors = read_opa_object("host_read_selector_fields")
        mandatory = read_opa_object("host_read_required_fields")
        return bool(
            selectors is not None
            and mandatory is not None
            and set(selectors) == expected
            and set(mandatory).issubset(selectors)
            and all(set(fields).issubset(selectors[name]) for name, fields in mandatory.items())
            and mandatory.get("message.get") == ["messageRef"]
        )
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        subprocess.SubprocessError,
        json.JSONDecodeError,
    ):
        return False


def _apply_installed_security_read_surface(
    standing: dict[str, Any], *, qualified: bool
) -> dict[str, Any]:
    """Keep the existing six-factor preconditions; add an installed PDP fence."""
    standing["installedSecurityHostReadSurfaceQualified"] = qualified
    if not qualified:
        standing["status"] = "NO_GO"
        standing["reasons"].append("HOST_SECURITY_INSTALLED_READ_SURFACE_MISMATCH")
    return standing


def assess(
    policy_standing: dict[str, Any] | None,
    systemd_environment: str,
    *,
    anonymous_host_initialize_denied: bool | None = None,
    observed_non_gateway_host_tcp_clients: list[str] | None = None,
    unqualified_active_host_consumers: tuple[str, ...] = (),
) -> dict[str, Any]:
    qualified_standing = (
        policy_standing is not None
        and policy_standing.get("standing") == "OBSERVED_FOR_EXACT_READ_PAIR"
    )
    credential_declared = _declares_host_owner_identity(systemd_environment)
    owner_route_qualified = _owner_route_is_probed_endpoint(systemd_environment)
    failures: list[str] = []
    if not qualified_standing:
        failures.append("HOST_SECURITY_POLICY_STANDING_UNOBSERVED")
    if not credential_declared:
        failures.append("GATEWAY_HOST_OWNER_CREDENTIAL_NOT_CONFIGURED")
    if not owner_route_qualified:
        failures.append("HOST_OWNER_ROUTE_NOT_QUALIFIED_FOR_LOCAL_CANARY")
    if anonymous_host_initialize_denied is not True:
        failures.append("HOST_DIRECT_ANONYMOUS_MCP_NOT_PROVEN_DENIED")
    # Only positive socket evidence can falsify migration. A momentarily
    # empty socket set NEVER establishes Cloudflare route or Agent migration.
    if observed_non_gateway_host_tcp_clients:
        failures.append("HOST_DIRECT_NON_GATEWAY_TCP_CONSUMER_OBSERVED")
    if unqualified_active_host_consumers:
        failures.append("ACTIVE_HOST_CONSUMER_MISSING_OWNER_CREDENTIAL")
    return {
        "schemaVersion": 1,
        "kind": "ordivon.gateway-host-release-precondition",
        "status": "NO_GO" if failures else "NECESSARY_PRECONDITIONS_PRESENT",
        "effectivePolicyStanding": policy_standing,
        "hostOwnerCredentialDeclared": credential_declared,
        "hostOwnerRouteQualified": owner_route_qualified,
        "anonymousHostInitializeDenied": anonymous_host_initialize_denied is True,
        "observedDirectHostTcpConsumerClasses": observed_non_gateway_host_tcp_clients,
        "unqualifiedActiveHostConsumers": list(unqualified_active_host_consumers),
        "reasons": failures,
        "unverified": [
            "actual Principal-to-Actor and resource authorization",
            "actual live Agent and other Host AuthZEN consumer canaries",
            "Host bearer rotation, peer consistency and post-promotion revalidation",
            "direct Host MCP connector migration",
            "Cloudflare remote Host ingress target and direct-consumer migration",
            "production post-promotion behavior",
        ],
        "truthBoundary": "release precondition only; Security PDP and Host remain authoritative",
    }


def _independent_host_readiness_observations() -> dict[str, Any]:
    """Diagnose independent blockers without crossing Owner credential boundaries.

    This is only reached after qualified Security evidence failed: no inspection
    of another systemd unit's private credentials, bearer transmission, PDP
    evaluation, or change to the original fail-closed admission verdict.
    A probe error is UNKNOWN, never an inferred clean system.
    """

    def observe(probe: Any) -> Any:
        try:
            return probe()
        except Exception:
            # Bounded diagnostic probes cannot override the original NO_GO.
            # Neither their exception text nor a credential is an output.
            return None

    environment = observe(lambda: _qualified_systemd_environment(GATEWAY_UNIT))
    route_qualified = (
        _owner_route_is_probed_endpoint(environment) if isinstance(environment, str) else None
    )
    credential_declared = (
        _declares_host_owner_identity(environment) if isinstance(environment, str) else None
    )
    candidate_port = observe(
        lambda: _qualified_host_route_port(environment) if isinstance(environment, str) else None
    )
    anonymous_denied = observe(
        _rejects_unauthenticated_host_initialize
        if candidate_port in (None, 8898)
        else lambda: _rejects_unauthenticated_host_initialize(host_port=candidate_port)
    )
    clients = observe(_observed_non_gateway_host_tcp_clients)
    # Deliberately NEVER transmit an Owner token in this diagnostic branch.
    peers = observe(
        lambda: _unqualified_active_peer_host_consumers(
            anonymous_denied=False,
            **(
                {"primary_host_port": candidate_port}
                if candidate_port is not None and candidate_port != 8898
                else {}
            ),
        )
    )
    if type(anonymous_denied) is not bool:
        anonymous_denied = None
    if not isinstance(clients, list) or any(not isinstance(v, str) for v in clients):
        clients = None
    if not isinstance(peers, (tuple, list)) or any(not isinstance(v, str) for v in peers):
        peers = None

    blockers: list[str] = []
    if route_qualified is False:
        blockers.append("HOST_OWNER_ROUTE_NOT_QUALIFIED_FOR_LOCAL_CANARY")
    if credential_declared is False:
        blockers.append("GATEWAY_HOST_OWNER_CREDENTIAL_NOT_CONFIGURED")
    if anonymous_denied is False:
        blockers.append("HOST_DIRECT_ANONYMOUS_MCP_NOT_PROVEN_DENIED")
    if clients:
        blockers.append("HOST_DIRECT_NON_GATEWAY_TCP_CONSUMER_OBSERVED")
    if peers:
        blockers.append("ACTIVE_HOST_PEER_AUTHENTICATED_MCP_NOT_PROVEN")

    return {
        "hostOwnerRouteQualified": route_qualified,
        "hostOwnerCredentialDeclared": credential_declared,
        "anonymousHostInitializeDenied": anonymous_denied,
        "observedDirectHostTcpConsumerClasses": clients,
        "unverifiedActiveHostPeerConsumers": sorted(peers) if peers is not None else None,
        "independentBlockers": blockers,
        "truthBoundary": (
            "read-only independent diagnostics, not Security authorization or "
            "Host release admission; empty socket observation does not prove migration"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--gateway-unit",
        default=GATEWAY_UNIT,
        help="Real installed Gateway systemd unit to inspect",
    )
    args = parser.parse_args()
    if args.gateway_unit != GATEWAY_UNIT:
        raise SystemExit("production release preflight only supports its natural Gateway unit")

    try:
        policy_standing = observe_configured_pair()
        environment = _qualified_systemd_environment(args.gateway_unit)
        if environment is None:
            raise ValueError("Gateway EnvironmentFile overrides are not a qualified owner route")
        security_service = subprocess.run(
            ["/usr/bin/systemctl", "is-active", SECURITY_UNIT],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
        if security_service.returncode != 0 or security_service.stdout.strip() != "active":
            raise ValueError("current Security PDP is not running")
        candidate_port = _qualified_host_route_port(environment)
        if candidate_port is None:
            raise ValueError("systemd configured Host Owner is not an accepted live workload")
        anonymous_denied = (
            _rejects_unauthenticated_host_initialize()
            if candidate_port == 8898
            else _rejects_unauthenticated_host_initialize(host_port=candidate_port)
        )
        # Only after a negative anonymous canary can a private workload token
        # safely be offered to this exact known-local Host MCP endpoint.
        authenticated_accepted = _authenticated_host_initialize_accepted(
            environment, anonymous_denied=anonymous_denied
        )
        standing = _apply_installed_security_read_surface(
            _apply_authenticated_host_canary(
                assess(
                    policy_standing,
                    environment,
                    anonymous_host_initialize_denied=anonymous_denied,
                    observed_non_gateway_host_tcp_clients=_observed_non_gateway_host_tcp_clients(),
                    unqualified_active_host_consumers=_unqualified_active_peer_host_consumers(
                        anonymous_denied=anonymous_denied,
                        **({"primary_host_port": candidate_port} if candidate_port != 8898 else {}),
                    ),
                ),
                qualified=authenticated_accepted,
            ),
            qualified=_installed_security_host_read_surface_qualified(),
        )
    except (
        OSError,
        ValueError,
        OwnerCallError,
        requests.RequestException,
        subprocess.SubprocessError,
        RecursionError,
    ):
        standing = {
            "schemaVersion": 1,
            "kind": "ordivon.gateway-host-release-precondition",
            "status": "NO_GO",
            "reasons": ["HOST_SECURITY_PRECONDITIONS_UNOBSERVABLE"],
            "independentHostReadinessObservations": _independent_host_readiness_observations(),
            "truthBoundary": "release precondition only; Security PDP and Host remain authoritative",
        }
    # The installer treats exit 0 as permission to promote, whereas this
    # checker currently proves *necessary* conditions only. Explanatory
    # "unverified" strings are not trustworthy release-authorization inputs:
    # even an empty or renamed list cannot qualify a real Agent consumer.
    # Deliberately fail closed until natural Owners supply independently
    # verifiable pre-promotion Principal/Host/Cloudflare/Agent receipts and
    # the existing checker is refined to consume them. Post-promotion
    # revalidation is a separate obligation, not a pre-promotion condition.
    if standing["status"] == "NECESSARY_PRECONDITIONS_PRESENT":
        standing["status"] = "NO_GO"
        standing["reasons"].append("INDEPENDENT_CONSUMER_CUTOVER_NOT_VERIFIED")
    print(json.dumps(standing, sort_keys=True))
    return 0 if standing["status"] == "NECESSARY_PRECONDITIONS_PRESENT" else 3


if __name__ == "__main__":
    raise SystemExit(main())
