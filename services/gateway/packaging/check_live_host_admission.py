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
import shlex
import subprocess
import time
from pathlib import Path
from typing import Any

from ordivon_gateway.service import _SOCIAL_WORK_HOST_TOOLS

MAX_POLICY_BYTES = 2_097_152
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


def _declares_host_owner_identity(systemd_environment: str) -> bool:
    try:
        values = shlex.split(systemd_environment)
    except ValueError:
        return False
    for item in values:
        if not item.startswith("ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE="):
            continue
        value = item.partition("=")[2]
        return value.startswith(("/", "%d/")) and len(value) > 3
    return False


def assess(
    document: dict[str, Any],
    systemd_environment: str,
    *,
    now: int,
    anonymous_host_initialize_denied: bool | None = None,
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
    return {
        "schemaVersion": 1,
        "kind": "ordivon.gateway-host-release-precondition",
        "status": "NO_GO" if failures else "NECESSARY_PRECONDITIONS_PRESENT",
        "activeHostDelegationCount": active_count,
        "hostOwnerCredentialDeclared": credential_declared,
        "hostOwnerRouteQualified": owner_route_qualified,
        "anonymousHostInitializeDenied": anonymous_host_initialize_denied is True,
        "reasons": failures,
        "unverified": [
            "actual Principal-to-Actor and resource authorization",
            "positive and negative live Host AuthZEN consumer canaries",
            "actual Host bearer-protected ingress and matching credential",
            "direct Host MCP connector migration",
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
        result = subprocess.run(
            ["/usr/bin/systemctl", "show", args.gateway_unit, "-p", "Environment", "--value"],
            capture_output=True,
            text=True,
            check=True,
            timeout=8,
        )
        security_service = subprocess.run(
            ["/usr/bin/systemctl", "is-active", SECURITY_UNIT],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
        if security_service.returncode != 0 or security_service.stdout.strip() != "active":
            raise ValueError("current Security PDP is not running")
        standing = assess(
            data,
            result.stdout,
            now=int(time.time()),
            anonymous_host_initialize_denied=_rejects_unauthenticated_host_initialize(),
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
