#!/usr/bin/env python3
"""Fixed-root OpenTofu controller for the Ordivon Gateway/Agent-Birth Cloudflare overlay."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import stat
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from typing import Any

TOFU_RELEASE_ROOT = pathlib.Path(
    "/usr/local/lib/ordivon-operations/cloudflare-provider/handoff-tofu"
)
TOFU_ROOT = TOFU_RELEASE_ROOT / "current"
CLOUDFLARE_CONFIG = pathlib.Path("/root/.config/ordivon/secrets/cloudflare.json")
OPERATIONS_ROOT = pathlib.Path("/var/lib/ordivon/operations-v2/tofu/agent-birth-handoff")
PLAN_DIR = OPERATIONS_ROOT / "plans"
RECEIPT_DIR = OPERATIONS_ROOT / "receipts"
TOFU = pathlib.Path("/usr/bin/tofu")
PLAN_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
WINDOWS_RUNTIME_DOMAIN = "canary-mcp.ordivon.com"
WINDOWS_SERVICE_TOKEN_NAME = "Ordivon Gateway Windows Runtime"
WINDOWS_SERVICE_POLICY_NAME = "Ordivon Gateway Windows Runtime"
GATEWAY_CREDENTIAL_DIR = pathlib.Path("/etc/ordivon/gateway")
WINDOWS_CLIENT_ID_PATH = GATEWAY_CREDENTIAL_DIR / "windows-access-client-id"
WINDOWS_CLIENT_SECRET_PATH = GATEWAY_CREDENTIAL_DIR / "windows-access-client-secret"


class HandoffTofuError(RuntimeError):
    pass


def _sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _private_json(path: pathlib.Path) -> dict[str, Any]:
    metadata = path.lstat()
    source = path
    if stat.S_ISLNK(metadata.st_mode):
        parent = path.parent
        parent_mode = stat.S_IMODE(parent.stat().st_mode)
        raw_target = os.readlink(path)
        target_name = pathlib.Path(raw_target)
        if target_name.is_absolute() or len(target_name.parts) != 1 or parent_mode & 0o077:
            raise HandoffTofuError(
                "Cloudflare credential alias must remain inside its private owner directory"
            )
        source = parent / target_name
        metadata = source.lstat()
        if source.is_symlink():
            raise HandoffTofuError("Cloudflare credential alias target must not be another symlink")
    if not stat.S_ISREG(metadata.st_mode):
        raise HandoffTofuError("Cloudflare credential owner must resolve to a regular file")
    if stat.S_IMODE(metadata.st_mode) & 0o077:
        raise HandoffTofuError("Cloudflare credential owner must not be group/world accessible")
    if metadata.st_size > 65536:
        raise HandoffTofuError("Cloudflare credential owner exceeds size bound")
    try:
        value = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HandoffTofuError("Cannot read Cloudflare credential owner") from exc
    if not isinstance(value, dict):
        raise HandoffTofuError("Cloudflare credential owner must be a JSON object")
    return value


def cloudflare_environment() -> dict[str, str]:
    config = _private_json(CLOUDFLARE_CONFIG)
    token = config.get("api_token")
    account_id = config.get("account_id")
    if not isinstance(token, str) or not token:
        raise HandoffTofuError("Cloudflare API token is missing")
    if not isinstance(account_id, str) or not account_id:
        raise HandoffTofuError("Cloudflare account ID is missing")
    environment = os.environ.copy()
    environment.update(
        {
            "CLOUDFLARE_API_TOKEN": token,
            "CLOUDFLARE_ACCOUNT_ID": account_id,
            "TF_VAR_account_id": account_id,
            "TF_CLI_CONFIG_FILE": str(TOFU_ROOT / "tofurc"),
            "CI": "true",
        }
    )
    return environment



def _cloudflare_config() -> tuple[str, str]:
    config = _private_json(CLOUDFLARE_CONFIG)
    token = config.get("api_token")
    account_id = config.get("account_id")
    if not isinstance(token, str) or not token:
        raise HandoffTofuError("Cloudflare API token is missing")
    if not isinstance(account_id, str) or not account_id:
        raise HandoffTofuError("Cloudflare account ID is missing")
    return token, account_id


def _cloudflare_request(
    method: str,
    path: str,
    *,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    token, account_id = _cloudflare_config()
    expected_prefix = f"/accounts/{account_id}/"
    if not path.startswith(expected_prefix):
        raise HandoffTofuError("Cloudflare request escaped the fixed account authority")
    encoded = None if body is None else json.dumps(body, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(
        f"https://api.cloudflare.com/client/v4{path}",
        data=encoded,
        method=method.upper(),
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "ordivon-cloudflare-handoff-tofu/1",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read())
    except urllib.error.HTTPError as exc:
        raise HandoffTofuError(
            f"Cloudflare request failed: {method.upper()} {path} HTTP {exc.code}"
        ) from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise HandoffTofuError(
            f"Cloudflare request failed: {method.upper()} {path}"
        ) from exc
    if not isinstance(payload, dict) or payload.get("success") is not True:
        raise HandoffTofuError(
            f"Cloudflare request returned failure: {method.upper()} {path}"
        )
    return payload


def _cloudflare_collection(path: str) -> list[dict[str, Any]]:
    token, account_id = _cloudflare_config()
    del token
    expected_prefix = f"/accounts/{account_id}/"
    if not path.startswith(expected_prefix) or "?" in path:
        raise HandoffTofuError("Cloudflare collection path is not fixed-account canonical")
    items: list[dict[str, Any]] = []
    page = 1
    while True:
        separator = "&" if "?" in path else "?"
        payload = _cloudflare_request(
            "GET", f"{path}{separator}per_page=100&page={page}"
        )
        result = payload.get("result")
        if not isinstance(result, list):
            raise HandoffTofuError("Cloudflare collection returned an unexpected shape")
        items.extend(item for item in result if isinstance(item, dict))
        info = payload.get("result_info")
        total_pages = (
            int(info.get("total_pages", page))
            if isinstance(info, dict) and isinstance(info.get("total_pages"), int)
            else page
        )
        if page >= total_pages:
            return items
        page += 1


def _windows_runtime_access_application() -> dict[str, Any]:
    _, account_id = _cloudflare_config()
    apps = _cloudflare_collection(f"/accounts/{account_id}/access/apps")
    matches = [
        app
        for app in apps
        if app.get("domain") == WINDOWS_RUNTIME_DOMAIN
        and app.get("type") == "self_hosted"
    ]
    if len(matches) != 1:
        raise HandoffTofuError(
            "Expected exactly one existing self-hosted Windows Runtime Access application"
        )
    return matches[0]


def _windows_runtime_policies(app_id: str) -> list[dict[str, Any]]:
    _, account_id = _cloudflare_config()
    return _cloudflare_collection(
        f"/accounts/{account_id}/access/apps/{app_id}/policies"
    )


def _service_tokens() -> list[dict[str, Any]]:
    _, account_id = _cloudflare_config()
    return _cloudflare_collection(f"/accounts/{account_id}/access/service_tokens")


def _service_token_ids(policy: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for rule in policy.get("include") or []:
        if not isinstance(rule, dict):
            continue
        service_token = rule.get("service_token")
        if not isinstance(service_token, dict):
            continue
        token_id = service_token.get("token_id")
        if isinstance(token_id, str) and token_id:
            values.append(token_id)
    return values


def _resource_values(
    plan: dict[str, Any], section: str, address: str
) -> dict[str, Any] | None:
    try:
        root = plan[section]
        if section == "prior_state":
            root = root["values"]
        module = root["root_module"]
    except (KeyError, TypeError):
        return None
    resource = _resources_by_address(module).get(address)
    if not isinstance(resource, dict):
        return None
    values = resource.get("values")
    return values if isinstance(values, dict) else None


def _resource_actions(plan: dict[str, Any], address: str) -> list[str]:
    for resource in plan.get("resource_changes", []):
        if not isinstance(resource, dict) or resource.get("address") != address:
            continue
        change = resource.get("change")
        if isinstance(change, dict):
            return [str(value) for value in change.get("actions", [])]
    return []


def _windows_service_auth_census(plan: dict[str, Any]) -> dict[str, Any]:
    token_address = "cloudflare_zero_trust_access_service_token.gateway_windows_runtime"
    planned = _resource_values(plan, "planned_values", token_address) or {}
    prior = _resource_values(plan, "prior_state", token_address)
    actions = _resource_actions(plan, token_address)
    app = _windows_runtime_access_application()
    app_id = str(app.get("id", ""))
    if not app_id:
        raise HandoffTofuError("Windows Runtime Access application omitted identity")

    matching_tokens = [
        item for item in _service_tokens() if item.get("name") == WINDOWS_SERVICE_TOKEN_NAME
    ]
    expected_token_id = (
        str(prior.get("id"))
        if isinstance(prior, dict) and isinstance(prior.get("id"), str)
        else None
    )
    if expected_token_id is None:
        token_owner_clean = not matching_tokens and actions == ["create"]
    else:
        token_owner_clean = (
            len(matching_tokens) == 1
            and matching_tokens[0].get("id") == expected_token_id
            and actions in (["no-op"], ["update"])
        )

    policies = _windows_runtime_policies(app_id)
    named = [item for item in policies if item.get("name") == WINDOWS_SERVICE_POLICY_NAME]
    if len(named) > 1:
        policy_state = "duplicate"
        policy_compatible = False
    elif not named:
        policy_state = "absent"
        policy_compatible = expected_token_id is None or token_owner_clean
    else:
        policy_state = "present"
        ids = _service_token_ids(named[0])
        policy_compatible = (
            expected_token_id is not None
            and named[0].get("decision") == "non_identity"
            and ids == [expected_token_id]
        )

    checks = {
        "windows_runtime_app_exact": app.get("domain") == WINDOWS_RUNTIME_DOMAIN
        and app.get("type") == "self_hosted",
        "service_token_plan_exact": planned.get("name") == WINDOWS_SERVICE_TOKEN_NAME
        and planned.get("duration") == "8760h"
        and planned.get("enabled") is True,
        "service_token_remote_ownership_clean": token_owner_clean,
        "service_auth_policy_compatible": policy_compatible,
    }
    return {
        "eligible": all(checks.values()),
        "checks": checks,
        "windows_runtime_app_id": app_id,
        "windows_runtime_app_audience": app.get("aud"),
        "service_token_actions": actions,
        "matching_service_token_count": len(matching_tokens),
        "service_auth_policy_state": policy_state,
        "matching_policy_count": len(named),
    }


def _required_output(environment: dict[str, str], name: str) -> str:
    completed = _run(["output", "-raw", name], environment=environment)
    value = completed.stdout.strip()
    if not value or any(character.isspace() for character in value):
        raise HandoffTofuError(f"OpenTofu output is missing or malformed: {name}")
    return value


def _write_private_value(path: pathlib.Path, value: str) -> None:
    directory = path.parent
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    if directory.is_symlink() or not directory.is_dir():
        raise HandoffTofuError("Gateway credential directory is not a private directory")
    os.chmod(directory, 0o700)
    if path.exists() or path.is_symlink():
        metadata = path.lstat()
        if path.is_symlink() or not stat.S_ISREG(metadata.st_mode):
            raise HandoffTofuError("Gateway credential target must be a regular file")
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=directory)
    temporary = pathlib.Path(temporary_name)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(value)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    finally:
        if temporary.exists():
            temporary.unlink()


def _verify_service_policy(policy: dict[str, Any], token_id: str) -> bool:
    return (
        policy.get("name") == WINDOWS_SERVICE_POLICY_NAME
        and policy.get("decision") == "non_identity"
        and _service_token_ids(policy) == [token_id]
    )


def _ensure_windows_service_auth(token_id: str) -> dict[str, Any]:
    app = _windows_runtime_access_application()
    app_id = str(app.get("id", ""))
    policies = _windows_runtime_policies(app_id)
    named = [item for item in policies if item.get("name") == WINDOWS_SERVICE_POLICY_NAME]
    if len(named) > 1:
        raise HandoffTofuError("Windows Runtime Service Auth policy name is duplicated")
    if named:
        if not _verify_service_policy(named[0], token_id):
            raise HandoffTofuError("Existing Windows Runtime Service Auth policy conflicts")
        policy = named[0]
        disposition = "existing"
    else:
        _, account_id = _cloudflare_config()
        payload = _cloudflare_request(
            "POST",
            f"/accounts/{account_id}/access/apps/{app_id}/policies",
            body={
                "name": WINDOWS_SERVICE_POLICY_NAME,
                "decision": "non_identity",
                "include": [{"service_token": {"token_id": token_id}}],
            },
        )
        result = payload.get("result")
        if not isinstance(result, dict) or not _verify_service_policy(result, token_id):
            raise HandoffTofuError("Created Windows Runtime Service Auth policy failed verification")
        policy = result
        disposition = "created"

    verified = [
        item
        for item in _windows_runtime_policies(app_id)
        if item.get("name") == WINDOWS_SERVICE_POLICY_NAME
    ]
    if len(verified) != 1 or not _verify_service_policy(verified[0], token_id):
        raise HandoffTofuError("Windows Runtime Service Auth policy did not converge")
    return {
        "application_id": app_id,
        "application_audience": app.get("aud"),
        "policy_id": policy.get("id"),
        "policy_disposition": disposition,
        "verified": True,
    }


def _materialize_windows_identity(environment: dict[str, str]) -> dict[str, Any]:
    token_id = _required_output(environment, "gateway_windows_access_service_token_id")
    client_id = _required_output(environment, "gateway_windows_access_client_id")
    client_secret = _required_output(environment, "gateway_windows_access_client_secret")
    service_auth = _ensure_windows_service_auth(token_id)
    _write_private_value(WINDOWS_CLIENT_ID_PATH, client_id)
    _write_private_value(WINDOWS_CLIENT_SECRET_PATH, client_secret)
    return {
        "service_auth": service_auth,
        "credentials_materialized": True,
        "client_id_path": str(WINDOWS_CLIENT_ID_PATH),
        "client_secret_path": str(WINDOWS_CLIENT_SECRET_PATH),
    }


def _run(
    args: list[str],
    *,
    environment: dict[str, str],
    capture: bool = True,
    accepted: set[int] | None = None,
) -> subprocess.CompletedProcess[str]:
    allowed = accepted or {0}
    completed = subprocess.run(
        [str(TOFU), *args],
        cwd=TOFU_ROOT,
        env=environment,
        text=True,
        check=False,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )
    if completed.returncode not in allowed:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise HandoffTofuError(
            f"OpenTofu failed ({completed.returncode}): {' '.join(args)}"
            + (f"\n{detail}" if detail else "")
        )
    return completed


def _source_identity() -> tuple[str, str]:
    try:
        resolved = TOFU_ROOT.resolve(strict=True)
        releases = (TOFU_RELEASE_ROOT / "releases").resolve(strict=True)
        relative = resolved.relative_to(releases)
    except (OSError, ValueError) as exc:
        raise HandoffTofuError(
            "fixed OpenTofu root is outside the operation release owner"
        ) from exc
    if len(relative.parts) != 1 or re.fullmatch(r"[0-9a-f]{40}", relative.name) is None:
        raise HandoffTofuError("fixed OpenTofu release identity is invalid")

    source_files = sorted(TOFU_ROOT.glob("*.tf"), key=lambda path: path.name)
    source_files.extend([TOFU_ROOT / ".terraform.lock.hcl", TOFU_ROOT / "tofurc"])
    if not source_files or not any(path.suffix == ".tf" for path in source_files):
        raise HandoffTofuError("fixed OpenTofu release contains no configuration")

    digest = hashlib.sha256()
    seen: set[str] = set()
    for path in source_files:
        if path.name in seen:
            continue
        seen.add(path.name)
        metadata = path.lstat()
        if path.is_symlink() or not stat.S_ISREG(metadata.st_mode):
            raise HandoffTofuError(f"fixed OpenTofu source is not a regular file: {path.name}")
        if stat.S_IMODE(metadata.st_mode) & 0o022:
            raise HandoffTofuError(f"fixed OpenTofu source is group/world writable: {path.name}")
        digest.update(path.name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(_sha256(path).encode("ascii"))
        digest.update(b"\n")
    return relative.name, "sha256:" + digest.hexdigest()


def _resources_by_address(module: dict[str, Any]) -> dict[str, dict[str, Any]]:
    resources = {
        str(resource.get("address", "")): resource
        for resource in module.get("resources", [])
        if isinstance(resource, dict) and resource.get("address")
    }
    for child in module.get("child_modules", []) or []:
        if isinstance(child, dict):
            resources.update(_resources_by_address(child))
    return resources


def _nested_object(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, list) and value and isinstance(value[0], dict):
        return value[0]
    return {}


def _handoff_semantics(plan: dict[str, Any]) -> dict[str, Any]:
    checks: dict[str, bool] = {}
    details: dict[str, Any] = {}
    try:
        planned_root = plan["planned_values"]["root_module"]
        prior_root = plan["prior_state"]["values"]["root_module"]
        planned = _resources_by_address(planned_root)
        prior = _resources_by_address(prior_root)

        tunnel_address = "cloudflare_zero_trust_tunnel_cloudflared_config.production"
        gateway_address = "cloudflare_zero_trust_access_application.gateway_mcp"
        dns_address = "cloudflare_dns_record.gateway_mcp"
        windows_token_address = (
            "cloudflare_zero_trust_access_service_token.gateway_windows_runtime"
        )
        tunnel_before = _nested_object(prior[tunnel_address]["values"].get("config")).get(
            "ingress", []
        )
        tunnel_after = _nested_object(planned[tunnel_address]["values"].get("config")).get(
            "ingress", []
        )
        if not isinstance(tunnel_before, list) or not isinstance(tunnel_after, list):
            raise KeyError("tunnel ingress is not a list")

        def named(rule: Any) -> tuple[str, str] | None:
            if not isinstance(rule, dict):
                return None
            hostname = rule.get("hostname")
            service = rule.get("service")
            if not hostname:
                return None
            return str(hostname), str(service)

        before_named = [item for rule in tunnel_before if (item := named(rule)) is not None]
        after_named = [item for rule in tunnel_after if (item := named(rule)) is not None]
        before_catch = [
            rule for rule in tunnel_before if isinstance(rule, dict) and not rule.get("hostname")
        ]
        after_catch = [
            rule for rule in tunnel_after if isinstance(rule, dict) and not rule.get("hostname")
        ]

        gateway = planned[gateway_address]["values"]
        oauth = _nested_object(gateway.get("oauth_configuration"))
        dcr = _nested_object(oauth.get("dynamic_client_registration"))
        grant = _nested_object(oauth.get("grant"))
        dns = planned[dns_address]["values"]
        windows_token = planned[windows_token_address]["values"]

        checks.update(
            {
                "prior_named_ingress_preserved": all(item in after_named for item in before_named),
                "gateway_ingress_exactly_once": after_named.count(
                    ("gateway-mcp.ordivon.com", "http://127.0.0.1:8899")
                )
                == 1,
                "single_unchanged_catch_all": len(before_catch) == 1
                and before_catch == after_catch,
                "catch_all_last": bool(tunnel_after)
                and isinstance(tunnel_after[-1], dict)
                and not tunnel_after[-1].get("hostname"),
                "gateway_self_hosted": gateway.get("type") == "self_hosted",
                "gateway_domain_exact": gateway.get("domain") == "gateway-mcp.ordivon.com",
                "managed_oauth_enabled": oauth.get("enabled") is True,
                "dynamic_client_registration_enabled": dcr.get("enabled") is True,
                "access_token_lifetime_15m": grant.get("access_token_lifetime") == "15m",
                "grant_session_duration_336h": grant.get("session_duration") == "336h",
                "owner_policy_present": len(gateway.get("policies") or []) == 1,
                "identity_provider_present": len(gateway.get("allowed_idps") or []) >= 1,
                "gateway_dns_exact": dns.get("name") == "gateway-mcp.ordivon.com"
                and dns.get("type") == "CNAME"
                and dns.get("proxied") is True,
                "windows_service_token_exact": windows_token.get("name")
                == WINDOWS_SERVICE_TOKEN_NAME
                and windows_token.get("duration") == "8760h"
                and windows_token.get("enabled") is True,
            }
        )
        details.update(
            {
                "prior_named_ingress_count": len(before_named),
                "planned_named_ingress_count": len(after_named),
                "prior_catch_all_count": len(before_catch),
                "planned_catch_all_count": len(after_catch),
                "gateway_policy_count": len(gateway.get("policies") or []),
                "gateway_allowed_idp_count": len(gateway.get("allowed_idps") or []),
            }
        )
    except KeyError, TypeError, ValueError:
        checks["plan_shape_valid"] = False

    mutated = sorted(
        str(resource.get("address", ""))
        for resource in plan.get("resource_changes", [])
        if isinstance(resource, dict)
        and isinstance(resource.get("change"), dict)
        and resource["change"].get("actions") not in (["no-op"], ["read"])
    )
    allowed_mutations = {
        "cloudflare_dns_record.gateway_mcp",
        "cloudflare_zero_trust_access_application.gateway_mcp",
        "cloudflare_zero_trust_access_service_token.gateway_windows_runtime",
        "cloudflare_zero_trust_tunnel_cloudflared_config.production",
    }
    unexpected_mutations = sorted(set(mutated) - allowed_mutations)
    checks["no_unexpected_mutations"] = not unexpected_mutations
    details["mutated_resources"] = mutated
    details["unexpected_mutations"] = unexpected_mutations
    return {
        "semantic_gate": bool(checks) and all(checks.values()),
        "checks": checks,
        "details": details,
    }


def _summarize_plan(plan: dict[str, Any]) -> dict[str, Any]:
    changes: list[dict[str, Any]] = []
    dangerous: list[dict[str, Any]] = []
    counts = {"create": 0, "update": 0, "delete": 0, "replace": 0, "read": 0, "no_op": 0}
    for resource in plan.get("resource_changes", []):
        if not isinstance(resource, dict):
            continue
        change = resource.get("change")
        if not isinstance(change, dict):
            continue
        actions = [str(action) for action in change.get("actions", [])]
        address = str(resource.get("address", ""))
        item = {"address": address, "actions": actions}
        changes.append(item)
        action_set = set(actions)
        if "delete" in action_set and "create" in action_set:
            counts["replace"] += 1
            dangerous.append(item)
        elif "delete" in action_set:
            counts["delete"] += 1
            dangerous.append(item)
        elif actions == ["create"]:
            counts["create"] += 1
        elif actions == ["update"]:
            counts["update"] += 1
        elif actions == ["read"]:
            counts["read"] += 1
        elif actions == ["no-op"]:
            counts["no_op"] += 1
    output_changes = sorted(
        key for key, value in (plan.get("output_changes") or {}).items() if isinstance(value, dict)
    )
    return {
        "safe_no_delete_replace": not dangerous,
        "counts": counts,
        "changes": changes,
        "dangerous": dangerous,
        "output_changes": output_changes,
        "semantics": _handoff_semantics(plan),
    }


def _write_json(path: pathlib.Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)
    os.chmod(path, 0o600)


def _plan_paths(digest: str) -> tuple[pathlib.Path, pathlib.Path]:
    if PLAN_DIGEST_RE.fullmatch(digest) is None:
        raise HandoffTofuError("plan SHA-256 must be 64 lowercase hexadecimal characters")
    return PLAN_DIR / f"{digest}.tfplan", RECEIPT_DIR / f"plan-{digest}.json"


def create_plan() -> dict[str, Any]:
    commit, source_digest = _source_identity()
    environment = cloudflare_environment()
    PLAN_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    RECEIPT_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    _run(["init", "-backend=true", "-input=false", "-lockfile=readonly"], environment=environment)
    fd, temporary_name = tempfile.mkstemp(prefix=".candidate-", suffix=".tfplan", dir=PLAN_DIR)
    os.close(fd)
    temporary = pathlib.Path(temporary_name)
    try:
        completed = _run(
            ["plan", "-input=false", f"-out={temporary}", "-detailed-exitcode"],
            environment=environment,
            accepted={0, 2},
        )
        shown = _run(["show", "-json", str(temporary)], environment=environment)
        try:
            plan_json = json.loads(shown.stdout)
        except json.JSONDecodeError as exc:
            raise HandoffTofuError("OpenTofu show returned invalid JSON") from exc
        summary = _summarize_plan(plan_json)
        windows_service_auth = _windows_service_auth_census(plan_json)
        digest = _sha256(temporary)
        plan_path, receipt_path = _plan_paths(digest)
        if plan_path.exists():
            if _sha256(plan_path) != digest:
                raise HandoffTofuError("existing plan digest collision")
            temporary.unlink()
        else:
            os.replace(temporary, plan_path)
            os.chmod(plan_path, 0o600)
        receipt = {
            "schema_version": 1,
            "kind": "ordivon.cloudflare-handoff-tofu-plan",
            "created_at": dt.datetime.now(dt.UTC).isoformat(),
            "source_commit": commit,
            "source_digest": source_digest,
            "plan_sha256": digest,
            "plan_path": str(plan_path),
            "tofu_exit_code": completed.returncode,
            "eligible_for_apply": summary["safe_no_delete_replace"]
            and summary["semantics"]["semantic_gate"]
            and windows_service_auth["eligible"],
            "summary": summary,
            "windows_service_auth": windows_service_auth,
        }
        _write_json(receipt_path, receipt)
        return receipt
    finally:
        if temporary.exists():
            temporary.unlink()


def load_plan_receipt(digest: str) -> dict[str, Any]:
    plan_path, receipt_path = _plan_paths(digest)
    if not plan_path.is_file() or not receipt_path.is_file():
        raise HandoffTofuError("reviewed plan or receipt does not exist")
    if _sha256(plan_path) != digest:
        raise HandoffTofuError("reviewed plan digest mismatch")
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HandoffTofuError("cannot read reviewed plan receipt") from exc
    if not isinstance(receipt, dict) or receipt.get("plan_sha256") != digest:
        raise HandoffTofuError("reviewed plan receipt identity mismatch")
    return receipt


def show_plan(digest: str) -> dict[str, Any]:
    return load_plan_receipt(digest)


def _safe_output(environment: dict[str, str], name: str) -> str | None:
    completed = _run(["output", "-raw", name], environment=environment, accepted={0, 1})
    if completed.returncode != 0:
        return None
    value = completed.stdout.strip()
    return value or None


def apply_reviewed_plan(digest: str) -> dict[str, Any]:
    receipt = load_plan_receipt(digest)
    if receipt.get("eligible_for_apply") is not True:
        raise HandoffTofuError("reviewed plan is not eligible for apply")
    commit, source_digest = _source_identity()
    if receipt.get("source_commit") != commit or receipt.get("source_digest") != source_digest:
        raise HandoffTofuError("fixed OpenTofu source changed after plan")
    plan_path, _ = _plan_paths(digest)
    environment = cloudflare_environment()
    _run(["apply", "-input=false", "-auto-approve", str(plan_path)], environment=environment)
    drift = _run(
        ["plan", "-input=false", "-detailed-exitcode"],
        environment=environment,
        accepted={0, 2},
    )
    if drift.returncode != 0:
        raise HandoffTofuError("post-apply verification detected drift")
    windows_identity = _materialize_windows_identity(environment)
    result = {
        "schema_version": 1,
        "kind": "ordivon.cloudflare-handoff-tofu-apply",
        "completed_at": dt.datetime.now(dt.UTC).isoformat(),
        "source_commit": commit,
        "source_digest": source_digest,
        "plan_sha256": digest,
        "status": "applied",
        "zero_drift": True,
        "gateway_mcp_hostname": _safe_output(environment, "gateway_mcp_hostname"),
        "gateway_mcp_audience": _safe_output(environment, "gateway_mcp_audience"),
        "windows_identity": windows_identity,
    }
    _write_json(RECEIPT_DIR / f"apply-{digest}.json", result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ordivon-cloudflare-handoff-tofu")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("plan")
    show = commands.add_parser("show")
    show.add_argument("--plan-sha256", required=True)
    apply = commands.add_parser("apply-reviewed-plan")
    apply.add_argument("--plan-sha256", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "plan":
            result = create_plan()
        elif args.command == "show":
            result = show_plan(args.plan_sha256)
        elif args.command == "apply-reviewed-plan":
            result = apply_reviewed_plan(args.plan_sha256)
        else:
            raise HandoffTofuError("unsupported operation")
        print(json.dumps({"ok": True, **result}, indent=2, sort_keys=True))
        return 0
    except HandoffTofuError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
