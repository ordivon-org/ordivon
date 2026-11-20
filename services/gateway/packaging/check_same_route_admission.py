#!/usr/bin/env python3
"""Read-only, fail-closed qualification for an unchanged-authority Gateway upgrade.

This checks only the existing installed Gateway -> same ingress/PEP/Owner routes.
Host or Cloudflare routing, Principal grants, Owner identity and authorization
migrations must still use the original protected cutover preflight. A result
never grants a new Principal permission or certifies external domain effects.
"""

from __future__ import annotations

import argparse
import ast
import http.client
import json
import os
import re
import shlex
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

GATEWAY_UNIT = "ordivon-gateway.service"
HOST_UNIT = "ordivon-host-v2.service"
SECURITY_UNIT = "ordivon-security-gateway-authzen.service"
LIVE_PREFIX = Path("/opt/ordivon/gateway")
KNOWN_HOST_URL = "http://127.0.0.1:8898/mcp"
KNOWN_PUBLIC_ORIGIN = "https://gateway-mcp.ordivon.com"
KNOWN_AUTHZEN_ENDPOINT = "https://127.0.0.1:18787/access/v1/evaluation"

# Actual ingress/authorization policy implementation and published contract.
# The owner-credential helpers and composition root have their own exact AST
# equivalence checks below because R36 moved them without changing authority.
STABLE_SECURITY_SOURCE = (
    ".python-version",
    "packaging/verify_tool_surface.py",
    "packaging/windows/verify_release.py",
    "packaging/check_live_host_admission.py",
    "src/ordivon_gateway/__init__.py",
    "src/ordivon_gateway/service.py",
    "src/ordivon_gateway/contracts.py",
    "src/ordivon_gateway/logic/routing.py",
    "src/ordivon_gateway/logic/execution_refs.py",
    "src/ordivon_gateway/logic/host_tool_contracts.py",
    "src/ordivon_gateway/capabilities/host/dispatch.py",
    "src/ordivon_gateway/transport/__init__.py",
    "src/ordivon_gateway/security/access_auth.py",
    "src/ordivon_gateway/security/authzen_authorizer.py",
    "src/ordivon_gateway/security/authorization_targets.py",
    "src/ordivon_gateway/security/capability_authz.py",
    "src/ordivon_gateway/security/http_ingress_guard.py",
    "src/ordivon_gateway/security/ingress_identity.py",
    "src/ordivon_gateway/security/entrypoint.py",
    "src/ordivon_gateway/security/execution_access.py",
    "src/ordivon_gateway/security/audit.py",
    "src/ordivon_gateway/transport/http.py",
    "systemd/ordivon-gateway.service",
    "mcp-surface.json",
    "enforcement-surface.json",
)
OWNER_IDENTITY_SOURCE = "src/ordivon_gateway/security/owner_identity.py"
UPSTREAM_SOURCE = "src/ordivon_gateway/transport/upstream.py"
MCP_ROOT = "src/ordivon_gateway/mcp_server.py"
IDENTITY_FUNCTIONS = (
    "OwnerEndpoint",
    "_runtime_identity_configured",
    "_validate_windows_private_secret_file",
    "_read_private_secret_file",
    "_read_private_token_file",
    "_headers_for_endpoint",
)


def _safe_regular(root: Path, relative: str) -> Path:
    base = root.resolve(strict=True)
    path = base / relative
    parent = base
    for part in Path(relative).parts[:-1]:
        parent /= part
        if parent.is_symlink():
            raise ValueError("release source parent redirects through a symlink")
    if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(base):
        raise ValueError("release source is not a bounded regular file")
    if path.stat().st_size > 2_097_152:
        raise ValueError("release source exceeds bounded size")
    return path


def _source_equal(installed: Path, candidate: Path, relative: str) -> bool:
    return (
        _safe_regular(installed, relative).read_bytes()
        == _safe_regular(candidate, relative).read_bytes()
    )


def _ast_item(root: Path, relative: str, name: str) -> ast.AST:
    tree = ast.parse(_safe_regular(root, relative).read_text(encoding="utf-8"))
    rows = [
        node
        for node in tree.body
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == name
    ]
    if len(rows) != 1:
        raise ValueError("Owner identity declaration is missing or ambiguous")
    return rows[0]


def _ast_method(root: Path, relative: str, klass: str, method: str) -> ast.AST:
    parent = _ast_item(root, relative, klass)
    assert isinstance(parent, ast.ClassDef)
    matches = [
        n
        for n in parent.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == method
    ]
    if len(matches) != 1:
        raise ValueError("Owner transport method missing or ambiguous")
    return matches[0]


def _same_owner_credentials(installed: Path, candidate: Path) -> bool:
    for name in IDENTITY_FUNCTIONS:
        a = _ast_item(installed, OWNER_IDENTITY_SOURCE, name)
        b = _ast_item(candidate, OWNER_IDENTITY_SOURCE, name)
        if ast.dump(a) != ast.dump(b):
            return False
    if ast.dump(_ast_item(installed, UPSTREAM_SOURCE, "OwnerEndpointAuth")) != ast.dump(
        _ast_item(candidate, UPSTREAM_SOURCE, "OwnerEndpointAuth")
    ):
        return False
    for method in (
        "__init__",
        "_http_client",
        "aclose",
        "has_route",
        "configuration_error",
        "is_configured",
    ):
        if ast.dump(_ast_method(installed, UPSTREAM_SOURCE, "McpOwnerCaller", method)) != ast.dump(
            _ast_method(candidate, UPSTREAM_SOURCE, "McpOwnerCaller", method)
        ):
            return False
    # R36 relocates precisely the legacy Host8898 exemption. Neither moving
    # it to another Owner nor loosening the host/port/path is an in-place patch.
    old_loopback = (
        OWNER_IDENTITY_SOURCE
        if "_is_legacy_loopback_host_endpoint"
        in _safe_regular(installed, OWNER_IDENTITY_SOURCE).read_text()
        else UPSTREAM_SOURCE
    )
    return ast.dump(
        _ast_item(installed, old_loopback, "_is_legacy_loopback_host_endpoint")
    ) == ast.dump(_ast_item(candidate, OWNER_IDENTITY_SOURCE, "_is_legacy_loopback_host_endpoint"))


def _same_mcp_composition(installed: Path, candidate: Path) -> bool:
    """Permit only the R36 Owner-error import and Host registrar wiring move.

    Every other top-level MCP/PEP AST node, including middleware composition,
    must be identical to the installed server. Future nontrivial wiring work
    requires independent change qualification rather than a generic bypass.
    """
    old = ast.parse(_safe_regular(installed, MCP_ROOT).read_text(encoding="utf-8"))
    new = ast.parse(_safe_regular(candidate, MCP_ROOT).read_text(encoding="utf-8"))
    if ast.dump(old) == ast.dump(new):
        return True

    def marker(node: ast.AST) -> bool:
        return (
            isinstance(node, ast.ImportFrom)
            and len(node.names) == 1
            and node.names[0].name == "owner_error_result"
            and node.names[0].asname == "_owner_error_result"
            and node.level == 1
        )

    old_positions = [i for i, n in enumerate(old.body) if marker(n)]
    new_positions = [i for i, n in enumerate(new.body) if marker(n)]
    if len(old_positions) != 1 or len(new_positions) != 1:
        return False
    old_import = old.body[old_positions[0]]
    new_import = new.body[new_positions[0]]
    if not (
        isinstance(old_import, ast.ImportFrom)
        and old_import.module == "security"
        and isinstance(new_import, ast.ImportFrom)
        and new_import.module == "transport.owner_error_projection"
    ):
        return False
    new.body.pop(new_positions[0])
    new_import.module = old_import.module
    new.body.insert(old_positions[0], new_import)

    registrar = [
        node
        for node in ast.walk(new)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "register_host_tools"
    ]
    if len(registrar) != 1:
        return False
    invocation = registrar[0]
    if (
        len(invocation.args) != 4
        or invocation.keywords
        or not isinstance(invocation.args[-1], ast.Name)
        or invocation.args[-1].id != "_owner_error_result"
    ):
        return False
    invocation.args.pop()
    return ast.dump(old) == ast.dump(new)


def _same_security_package(installed: Path, candidate: Path) -> bool:
    """No new or hidden Security module may alter an otherwise stable PEP."""
    folder = Path("src/ordivon_gateway/security")
    excluded = {folder / "__init__.py", folder / "owner_identity.py"}

    def inventory(root: Path) -> set[Path]:
        path = root / folder
        if not path.is_dir() or path.is_symlink():
            raise ValueError("Security package source unavailable")
        return {p.relative_to(root) for p in path.rglob("*.py")}

    old_files, new_files = inventory(installed), inventory(candidate)
    if old_files != new_files or not excluded.issubset(old_files):
        return False
    if not all(_source_equal(installed, candidate, str(rel)) for rel in old_files - excluded):
        return False
    old_facade = _safe_regular(installed, str(folder / "__init__.py")).read_text()
    new_facade = _safe_regular(candidate, str(folder / "__init__.py")).read_text()
    if old_facade == new_facade:
        return True

    # R36 replaces only the old Owner error projection facade with a direct
    # transport import, and exports the precisely relocated legacy Host helper.
    # No credential or authorization export may be substituted.
    moves = (
        (
            "    _headers_for_endpoint,\n",
            "    _headers_for_endpoint,\n    _is_legacy_loopback_host_endpoint,\n",
        ),
        (
            "from .owner_identity import (\n    _owner_error_result as owner_error_result,\n)\n",
            "",
        ),
        ('    "owner_error_result",\n', ""),
        (
            '    "_validate_windows_private_secret_file",\n',
            '    "_validate_windows_private_secret_file",\n'
            '    "_is_legacy_loopback_host_endpoint",\n',
        ),
    )
    for old_text, new_text in moves:
        if old_facade.count(old_text) != 1:
            return False
        old_facade = old_facade.replace(old_text, new_text)
    return old_facade == new_facade


def _same_package_release_contract(installed: Path, candidate: Path) -> bool:
    """Allow package version maintenance, not an unreviewed dependency change.

    Every byte of pyproject.toml and uv.lock except the exact editable
    ordivon-gateway project version must remain unchanged. Python interpreter,
    native SDK, and published Tool ABI are fenced by the original installer.
    """
    versions = []
    projected = []
    project_pattern = re.compile(
        r'(?m)^version = "((?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*))"$'
    )
    lock_pattern = re.compile(
        r'(?m)^\[\[package\]\]\nname = "ordivon-gateway"\n'
        r'version = "((?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*))"$'
    )
    for root in (installed, candidate):
        project = _safe_regular(root, "pyproject.toml").read_text(encoding="utf-8")
        lock = _safe_regular(root, "uv.lock").read_text(encoding="utf-8")
        projects = list(project_pattern.finditer(project))
        locks = list(lock_pattern.finditer(lock))
        if len(projects) != 1 or len(locks) != 1:
            return False
        version = projects[0].group(1)
        if version != locks[0].group(1):
            return False
        versions.append(tuple(map(int, version.split("."))))
        projected.append(
            (
                project[: projects[0].start(1)] + "<version>" + project[projects[0].end(1) :],
                lock[: locks[0].start(1)] + "<version>" + lock[locks[0].end(1) :],
            )
        )
    return projected[0] == projected[1] and versions[1] >= versions[0]


def _same_executable_source(installed: Path, candidate: Path) -> bool:
    """Fence the complete Gateway runtime source, not a historical filename list.

    All imported leaf adapters can control the actual Owner operation AFTER
    Gateway Security has evaluated the *public* Tool name. For class A, their
    executable Python AST must therefore remain unchanged; comments alone do
    not change Python execution. Non-Python package resources remain byte
    exact. Any module addition, deletion, symlink or unrecognized resource is
    unqualified, regardless of the SDK's unchanged public input schema.

    This is a conservative source/authority-equivalence check, not a proof
    that every future functional change requires Host/Cloudflare migration.
    Changed code needs independent action/Security/consumer qualification.
    """
    package = Path("src/ordivon_gateway")

    def observe(root: Path) -> dict[Path, str | bytes]:
        base = root.resolve(strict=True)
        directory = base / package
        if not directory.is_dir() or directory.is_symlink():
            raise ValueError("Gateway executable source directory is unavailable")
        result: dict[Path, str | bytes] = {}
        for item in directory.rglob("*"):
            relative = item.relative_to(base)
            # Check symlinks before ignoring native Python's generated bytecode
            # cache; a path inside the source release must not redirect out.
            if item.is_symlink():
                raise ValueError("Gateway source contains a symlink")
            if "__pycache__" in relative.parts:
                continue
            if item.is_dir():
                continue
            source = _safe_regular(root, str(relative))
            if source.suffix == ".py":
                result[relative] = ast.dump(
                    ast.parse(source.read_text(encoding="utf-8")),
                    include_attributes=False,
                )
            else:
                result[relative] = source.read_bytes()
        if len(result) < 25 or package / "__init__.py" not in result:
            raise ValueError("Gateway executable source inventory is incomplete")
        return result

    return observe(installed) == observe(candidate)


def source_same_route(installed: Path, candidate: Path) -> bool:
    """Native SDK full public ABI is additionally verified by install_release.sh."""
    if not all(_source_equal(installed, candidate, rel) for rel in STABLE_SECURITY_SOURCE):
        return False
    return (
        _same_package_release_contract(installed, candidate)
        and _same_executable_source(installed, candidate)
        and _same_security_package(installed, candidate)
        and _same_owner_credentials(installed, candidate)
        and _same_mcp_composition(installed, candidate)
    )


def _unit_value(name: str) -> str:
    result = subprocess.run(
        ["/usr/bin/systemctl", "show", GATEWAY_UNIT, "-p", name, "--value"],
        check=True,
        capture_output=True,
        text=True,
        timeout=8,
    )
    return result.stdout.strip()


def _service_active(name: str) -> bool:
    result = subprocess.run(
        ["/usr/bin/systemctl", "is-active", name],
        capture_output=True,
        text=True,
        timeout=8,
        check=False,
    )
    return result.returncode == 0 and result.stdout.strip() == "active"


def _parse_unit_environment(value: str) -> dict[str, str]:
    entries = shlex.split(value)
    parts = [item.split("=", 1) for item in entries]
    if any(len(pair) != 2 for pair in parts) or len({pair[0] for pair in parts}) != len(parts):
        raise ValueError("systemd environment is ambiguous")
    return dict(parts)


def _qualified_live_config(installed: Path) -> tuple[dict[str, str], int]:
    if _unit_value("EnvironmentFiles"):
        raise ValueError("unobserved EnvironmentFile override")
    if not _service_active(GATEWAY_UNIT) or not _service_active(HOST_UNIT):
        raise ValueError("installed Gateway/Host not active")
    if not _service_active(SECURITY_UNIT):
        raise ValueError("installed Security PDP not active")
    if _unit_value("User") != "ordivon-gateway" or _unit_value("DynamicUser") != "yes":
        raise ValueError("Gateway service identity drift")
    if _unit_value("WorkingDirectory") != str(LIVE_PREFIX / "current"):
        raise ValueError("Gateway service working directory drift")
    raw_pid = _unit_value("MainPID")
    if not raw_pid.isdecimal() or int(raw_pid) < 1:
        raise ValueError("Gateway physical MainPID absent")
    pid = int(raw_pid)
    if (Path("/proc") / str(pid) / "cwd").resolve() != installed.resolve():
        raise ValueError("running Gateway is not current installed SourceCut")
    env = _parse_unit_environment(_unit_value("Environment"))
    expected = {
        "ORDIVON_GATEWAY_TRANSPORT": "streamable-http",
        "ORDIVON_GATEWAY_HOST": "127.0.0.1",
        "ORDIVON_GATEWAY_PORT": "8899",
        "ORDIVON_GATEWAY_PATH": "/mcp",
        "ORDIVON_GATEWAY_HOST_URL": KNOWN_HOST_URL,
        "ORDIVON_GATEWAY_PUBLIC_ORIGIN": KNOWN_PUBLIC_ORIGIN,
        "ORDIVON_GATEWAY_TRUST_CF_ACCESS": "true",
        "ORDIVON_GATEWAY_AUTHZEN_EVALUATION_ENDPOINT": KNOWN_AUTHZEN_ENDPOINT,
    }
    if any(env.get(key) != val for key, val in expected.items()):
        raise ValueError("current Gateway routing or verified ingress drift")
    for key in (
        "ORDIVON_GATEWAY_LOCAL_BEARER_TOKEN_FILE",
        "ORDIVON_GATEWAY_AUTHZEN_BEARER_TOKEN_FILE",
        "ORDIVON_GATEWAY_LINUX_RUNTIME_BEARER_TOKEN_FILE",
    ):
        if not env.get(key, "").startswith("/"):
            raise ValueError("current service identity filename unavailable")
    # No secret or Credential contents are ever read or logged.
    return env, pid


_OWNER_ENDPOINT_SCRIPT = """
import json
from ordivon_gateway.transport.upstream import McpOwnerCaller
caller = McpOwnerCaller.from_env()
rows = sorted((
    name, endpoint.url, endpoint.mcp_mode,
    endpoint.bearer_token_file, endpoint.access_client_id_file,
    endpoint.access_client_secret_file, caller.configuration_error(name),
) for name, endpoint in caller._owners.items())
print(json.dumps(rows, separators=(',', ':')))
"""


def _owner_profiles_same(
    installed: Path, candidate: Path, unit_env: dict[str, str]
) -> tuple[bool, int]:
    profiles = []
    for release in (installed, candidate):
        python = release / ".venv" / "bin" / "python"
        if not python.is_file() or not os.access(python, os.X_OK):
            raise ValueError("release interpreter unavailable")
        # Only pass current unit declarations; never import another service's
        # private credentials, or load any of their contents.
        env = {"PATH": "/usr/bin:/bin"}
        env.update({k: v for k, v in unit_env.items() if k.startswith("ORDIVON_GATEWAY_")})
        result = subprocess.run(
            [str(python), "-c", _OWNER_ENDPOINT_SCRIPT],
            capture_output=True,
            text=True,
            check=True,
            timeout=12,
            env=env,
        )
        if len(result.stdout.encode()) > 16_384:
            raise ValueError("Owner endpoint observation oversized")
        rows = json.loads(result.stdout)
        if not isinstance(rows, list):
            raise ValueError("Owner endpoint observation malformed")
        profiles.append(rows)
    expected_owners = {"host", "runtime.linux", "runtime.windows", "skills"}
    actual = {row[0] for row in profiles[0] if isinstance(row, list) and len(row) == 7}
    if actual != expected_owners or any(row[6] is not None for row in profiles[0]):
        return False, len(actual)
    return profiles[0] == profiles[1], len(actual)


_CANDIDATE_HOST_READ = """
import asyncio
import json
from ordivon_gateway.transport.upstream import McpOwnerCaller

async def check():
    caller = McpOwnerCaller.from_env()
    try:
        return await caller.call_tool("host", "host.status", {"detail": "summary"})
    finally:
        await caller.aclose()

observed = asyncio.run(check())
if observed.get("kind") != "ordivon.host-status" or type(observed.get("schemaVersion")) is not int:
    raise SystemExit(3)
print(json.dumps({"kind": observed["kind"], "schemaVersion": observed["schemaVersion"]}))
"""


def _candidate_host_read_accepted(candidate: Path, unit_env: dict[str, str]) -> bool:
    env = {"PATH": "/usr/bin:/bin"}
    env.update({k: v for k, v in unit_env.items() if k.startswith("ORDIVON_GATEWAY_")})
    result = subprocess.run(
        [str(candidate / ".venv" / "bin" / "python"), "-c", _CANDIDATE_HOST_READ],
        capture_output=True,
        text=True,
        timeout=18,
        check=False,
        env=env,
    )
    if result.returncode != 0 or len(result.stdout.encode()) > 1_024:
        return False
    response = json.loads(result.stdout)
    return (
        isinstance(response, dict)
        and response.get("kind") == "ordivon.host-status"
        and type(response.get("schemaVersion")) is int
        and response["schemaVersion"] >= 1
    )


def _local_anonymous_denied() -> bool:
    payload = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": "gateway-same-route-anonymous-negative",
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "gateway-release-check", "version": "1"},
            },
        },
        separators=(",", ":"),
    ).encode()
    connection = http.client.HTTPConnection("127.0.0.1", 8899, timeout=4)
    try:
        connection.request(
            "POST",
            "/mcp",
            payload,
            {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "MCP-Protocol-Version": "2025-06-18",
            },
        )
        return connection.getresponse().status in (401, 403)
    finally:
        connection.close()


def _remote_anonymous_denied() -> bool:
    # The remote Access route is checked with no bearer/cookie/proxy or
    # redirects. An HTTP 200/302 or network failure is never a denial proof.
    request = urllib.request.Request(KNOWN_PUBLIC_ORIGIN + "/mcp", method="GET")

    class _NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, request, fp, code, msg, headers, newurl):
            return None

    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect())
    try:
        response = opener.open(request, timeout=8)
        response.close()
        return False
    except urllib.error.HTTPError as exc:
        return exc.code in (401, 403)


def assess(installed: Path, candidate: Path) -> dict[str, object]:
    if installed.resolve() == candidate.resolve():
        raise ValueError("candidate equals currently installed source")
    if not (
        installed.resolve().is_relative_to(LIVE_PREFIX / "releases")
        and candidate.resolve().is_relative_to(LIVE_PREFIX / "releases")
    ):
        raise ValueError("release roots outside the original immutable prefix")
    if (LIVE_PREFIX / "current").resolve() != installed.resolve():
        raise ValueError("installed release is not current")
    same_source = source_same_route(installed, candidate)
    if not same_source:
        return {
            "schemaVersion": 1,
            "kind": "ordivon.gateway-same-route-qualification",
            "status": "NO_GO",
            "reason": "SOURCE_AUTHORITY_OR_COMPOSITION_DRIFT",
        }

    env, initial_pid = _qualified_live_config(installed)
    same_owner, owner_count = _owner_profiles_same(installed, candidate, env)
    candidate_owner_read = _candidate_host_read_accepted(candidate, env)
    local_denied = _local_anonymous_denied()
    remote_denied = _remote_anonymous_denied()
    current_still_same = (
        (LIVE_PREFIX / "current").resolve() == installed.resolve()
        and _unit_value("MainPID") == str(initial_pid)
        and (Path("/proc") / str(initial_pid) / "cwd").resolve() == installed.resolve()
        and not _unit_value("EnvironmentFiles")
        and _parse_unit_environment(_unit_value("Environment")) == env
    )
    qualified = (
        same_owner
        and candidate_owner_read
        and local_denied
        and remote_denied
        and current_still_same
    )
    return {
        "schemaVersion": 1,
        "kind": "ordivon.gateway-same-route-qualification",
        "status": "QUALIFIED_SAME_ROUTE" if qualified else "NO_GO",
        "sameSourceSecurityAndComposition": same_source,
        "sameConfiguredOwnerEndpoints": same_owner,
        "candidateRealHostReadAccepted": candidate_owner_read,
        "ownerCount": owner_count,
        "installedLocalAnonymousDenied": local_denied,
        "remotePublicAnonymousDenied": remote_denied,
        "installedSourceAndServiceUnchanged": current_still_same,
        "truthBoundary": (
            "Same installed ingress, unmodified Security PEP, natural Owner routes and "
            "pre-promotion negative canaries only. Does NOT certify a new "
            "Principal grant, Host/Cloudflare cutover, post-promotion result or "
            "ChatGPT connector refresh."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--installed-release", type=Path, required=True)
    parser.add_argument("--candidate-release", type=Path, required=True)
    arguments = parser.parse_args()
    try:
        result = assess(arguments.installed_release, arguments.candidate_release)
    except (
        OSError,
        ValueError,
        SyntaxError,
        UnicodeError,
        subprocess.SubprocessError,
        json.JSONDecodeError,
    ) as exc:
        result = {
            "schemaVersion": 1,
            "kind": "ordivon.gateway-same-route-qualification",
            "status": "NO_GO",
            "reason": "SAME_ROUTE_PRECONDITIONS_UNOBSERVABLE",
            "diagnosticType": type(exc).__name__,
        }
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "QUALIFIED_SAME_ROUTE" else 3


if __name__ == "__main__":
    sys.exit(main())
