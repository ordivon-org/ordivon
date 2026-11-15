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
import time
from pathlib import Path
from typing import Any

from ordivon_gateway.service import _SOCIAL_WORK_HOST_TOOLS
from ordivon_gateway.upstream_identity import OwnerCallError, _read_private_token_file

MAX_POLICY_BYTES = 2_097_152
MAX_SOCKET_EVIDENCE_BYTES = 131_072
GATEWAY_UNIT = "ordivon-gateway.service"
SECURITY_UNIT = "ordivon-security-gateway-authzen.service"
ACTIVE_POLICY_CREDENTIAL = Path(
    "/run/credentials/ordivon-security-gateway-authzen.service/trusted-issuer"
)
# No second list of permitted Host actions or AuthZEN policy.
HOST_TOOLS = frozenset(_SOCIAL_WORK_HOST_TOOLS) | {"host.status"}

# The installed Gateway Owner endpoint is local; do not chase caller-provided
# hosts, redirects or public URLs from a production release preflight.
HOST_OWNER_URL = "http://127.0.0.1:8898/mcp"
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


def _rejects_unauthenticated_host_initialize() -> bool:
    """A real, read-only local HTTP canary: only 401/403 prove this negative.

    This request intentionally has no Authorization header. 200, other HTTP
    responses, network failures and unknown transports all mean NOT PROVEN.
    stdlib HTTPConnection does not follow redirects or honor HTTP proxies.
    """
    conn = http.client.HTTPConnection("127.0.0.1", 8898, timeout=4)
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


def _owner_route_is_probed_endpoint(systemd_environment: str) -> bool:
    try:
        entries = shlex.split(systemd_environment)
    except ValueError:
        return False
    return f"ORDIVON_GATEWAY_HOST_URL={HOST_OWNER_URL}" in entries


def _policy_data(path: Path) -> dict[str, Any]:
    if not path.is_absolute() or path.is_symlink() or not path.is_file():
        raise ValueError("installed Security operator policy data is unavailable")
    if path.stat().st_size > MAX_POLICY_BYTES:
        raise ValueError("installed Security operator policy data exceeds bounded size")
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ValueError("installed Security operator policy data must be an object")
    return document


def _active_host_grant_count(document: dict[str, Any], *, now: int) -> int:
    root = document.get("ordivon")
    security = root.get("security") if isinstance(root, dict) else None
    grants = security.get("gateway_host_actor_grants") if isinstance(security, dict) else None
    if not isinstance(grants, list):
        return 0

    def active(grant: Any) -> bool:
        if not isinstance(grant, dict) or grant.get("active") is not True:
            return False
        before = grant.get("notBeforeEpochSeconds")
        expiry = grant.get("expiresAtEpochSeconds")
        tools = grant.get("allowedTools")
        return (
            type(before) in (int, float)
            and type(expiry) in (int, float)
            and before <= now < expiry
            and isinstance(grant.get("principalId"), str)
            and grant["principalId"].startswith("principal:")
            and isinstance(grant.get("issuer"), str)
            and bool(grant["issuer"])
            and isinstance(grant.get("actorRef"), str)
            and grant["actorRef"].startswith("actor:")
            and isinstance(tools, list)
            and any(isinstance(tool, str) and tool in HOST_TOOLS for tool in tools)
        )

    return sum(active(grant) for grant in grants)


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
    if not anonymous_denied or not _owner_route_is_probed_endpoint(systemd_environment):
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

    connection = http.client.HTTPConnection("127.0.0.1", 8898, timeout=4)
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


def _unqualified_active_peer_host_consumers(*, anonymous_denied: bool = False) -> tuple[str, ...]:
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
        elif _owner_route_is_probed_endpoint(environment):
            # A declared bearer might be absent or differ from the protected
            # Host's real secret. Each active peer must prove its *own* private
            # service credential, not borrow the primary Gateway's canary.
            if (
                not _declares_host_owner_identity(environment)
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
    document: dict[str, Any],
    systemd_environment: str,
    *,
    now: int,
    anonymous_host_initialize_denied: bool | None = None,
    observed_non_gateway_host_tcp_clients: list[str] | None = None,
    unqualified_active_host_consumers: tuple[str, ...] = (),
) -> dict[str, Any]:
    active_count = _active_host_grant_count(document, now=now)
    credential_declared = _declares_host_owner_identity(systemd_environment)
    owner_route_qualified = _owner_route_is_probed_endpoint(systemd_environment)
    failures: list[str] = []
    if active_count == 0:
        failures.append("HOST_OPERATOR_DELEGATIONS_ABSENT_OR_INACTIVE")
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
        "activeHostDelegationCount": active_count,
        "hostOwnerCredentialDeclared": credential_declared,
        "hostOwnerRouteQualified": owner_route_qualified,
        "anonymousHostInitializeDenied": anonymous_host_initialize_denied is True,
        "observedDirectHostTcpConsumerClasses": observed_non_gateway_host_tcp_clients,
        "unqualifiedActiveHostConsumers": list(unqualified_active_host_consumers),
        "reasons": failures,
        "unverified": [
            "actual Principal-to-Actor and resource authorization",
            "positive and negative live Host AuthZEN consumer canaries",
            "Host bearer rotation, peer consistency and post-promotion revalidation",
            "direct Host MCP connector migration",
            "Cloudflare remote Host ingress target and direct-consumer migration",
            "production post-promotion behavior",
        ],
        "truthBoundary": "release precondition only; Security PDP and Host remain authoritative",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--policy-data",
        type=Path,
        default=ACTIVE_POLICY_CREDENTIAL,
        help="CURRENT systemd-loaded Security PDP policy credential (not raw source)",
    )
    parser.add_argument(
        "--gateway-unit",
        default=GATEWAY_UNIT,
        help="Real installed Gateway systemd unit to inspect",
    )
    args = parser.parse_args()
    if args.gateway_unit != GATEWAY_UNIT:
        raise SystemExit("production release preflight only supports its natural Gateway unit")

    try:
        data = _policy_data(args.policy_data)
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
        anonymous_denied = _rejects_unauthenticated_host_initialize()
        # Only after a negative anonymous canary can a private workload token
        # safely be offered to this exact known-local Host MCP endpoint.
        authenticated_accepted = _authenticated_host_initialize_accepted(
            environment, anonymous_denied=anonymous_denied
        )
        standing = _apply_installed_security_read_surface(
            _apply_authenticated_host_canary(
                assess(
                    data,
                    environment,
                    now=int(time.time()),
                    anonymous_host_initialize_denied=anonymous_denied,
                    observed_non_gateway_host_tcp_clients=_observed_non_gateway_host_tcp_clients(),
                    unqualified_active_host_consumers=_unqualified_active_peer_host_consumers(
                        anonymous_denied=anonymous_denied
                    ),
                ),
                qualified=authenticated_accepted,
            ),
            qualified=_installed_security_host_read_surface_qualified(),
        )
    except OSError, ValueError, subprocess.SubprocessError, json.JSONDecodeError:
        standing = {
            "schemaVersion": 1,
            "kind": "ordivon.gateway-host-release-precondition",
            "status": "NO_GO",
            "reasons": ["HOST_SECURITY_PRECONDITIONS_UNOBSERVABLE"],
            "truthBoundary": "release precondition only; Security PDP and Host remain authoritative",
        }
    print(json.dumps(standing, sort_keys=True))
    return 0 if standing["status"] == "NECESSARY_PRECONDITIONS_PRESENT" else 3


if __name__ == "__main__":
    raise SystemExit(main())
