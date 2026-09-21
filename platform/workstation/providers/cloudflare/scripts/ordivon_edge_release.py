#!/usr/bin/env python3
"""Versioned release and rollback controller for Ordivon Edge."""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import hmac
import json
import os
import pathlib
import re
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass
from typing import Any, NoReturn

SCRIPT_PATH = pathlib.Path(__file__).resolve()
DEFAULT_PROVIDER_REPOSITORY = pathlib.Path("/root/projects/ordivon/platform/workstation/providers/cloudflare")


def resolve_provider_root(
    script_path: pathlib.Path = SCRIPT_PATH,
    repository_hint: pathlib.Path | None = None,
) -> pathlib.Path:
    script_root = script_path.resolve().parent.parent
    configured = repository_hint
    if configured is None:
        configured_value = (
            os.environ.get("ORDIVON_CLOUDFLARE_PROVIDER_ROOT")
            or os.environ.get("ORDIVON_WORLD_REPO")
            or str(DEFAULT_PROVIDER_REPOSITORY)
        )
        configured = pathlib.Path(configured_value).expanduser()
    candidates = [script_root, configured.resolve()]
    for candidate in candidates:
        if (candidate / "wrangler.jsonc").is_file():
            return candidate
        nested = candidate / "providers" / "cloudflare"
        if (nested / "wrangler.jsonc").is_file():
            return nested
    return script_root


ROOT = resolve_provider_root()
WORKER_NAME = "ordivon-edge"
CLOUDFLARE_CONFIG = pathlib.Path("/root/.config/ordivon/secrets/cloudflare.json")
EDGE_CONFIG = pathlib.Path("/root/.config/ordivon/secrets/edge-client.json")
POLICY_CONFIG = ROOT / "config" / "edge-policy.json"
WRANGLER_CONFIG = ROOT / "wrangler.jsonc"
RELEASE_DIR = pathlib.Path("/root/backups/ordivon-world/cloudflare-releases")
ROUTE_STABILITY_OBSERVATIONS = 3
WORKER_RELEASE_INPUTS = (
    "src",
    "config/edge-policy.json",
    "wrangler.jsonc",
    "package.json",
    "pnpm-lock.yaml",
    "tsconfig.json",
)


def worker_release_pathspecs() -> tuple[str, ...]:
    repository = pathlib.Path(git_output("rev-parse", "--show-toplevel")).resolve()
    try:
        provider_relative = ROOT.resolve().relative_to(repository)
    except ValueError as exc:
        raise ReleaseError(
            f"Cloudflare provider root is outside the Git repository: {ROOT}"
        ) from exc
    prefix = "" if provider_relative == pathlib.Path(".") else provider_relative.as_posix()
    return tuple(
        f":(top){prefix}/{relative}" if prefix else f":(top){relative}"
        for relative in WORKER_RELEASE_INPUTS
    )


class ReleaseError(RuntimeError):
    pass


@dataclass(frozen=True)
class EdgeConfig:
    endpoint: str
    key_id: str
    secret: bytes


@dataclass(frozen=True)
class CloudflareCredentials:
    api_token: str
    account_id: str


def fail(message: str) -> NoReturn:
    raise ReleaseError(message)


def load_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReleaseError(f"Cannot read configuration: {path}") from exc
    if not isinstance(value, dict):
        fail(f"Configuration must be a JSON object: {path}")
    return value


def load_cloudflare_credentials() -> CloudflareCredentials:
    config = load_json(CLOUDFLARE_CONFIG)
    token = config.get("api_token")
    account_id = config.get("account_id")
    if not isinstance(token, str) or not token:
        fail("Cloudflare API token is missing")
    if not isinstance(account_id, str) or not account_id:
        fail("Cloudflare account ID is missing")
    return CloudflareCredentials(api_token=token, account_id=account_id)


def cloudflare_environment() -> dict[str, str]:
    credentials = load_cloudflare_credentials()
    environment = os.environ.copy()
    environment.update(
        {
            "CLOUDFLARE_API_TOKEN": credentials.api_token,
            "CLOUDFLARE_ACCOUNT_ID": credentials.account_id,
            "CI": "true",
        }
    )
    return environment


def cloudflare_api(
    method: str,
    path: str,
    *,
    body: dict[str, Any] | None = None,
    attempts: int = 4,
    base_delay_seconds: float = 1.0,
    sleep: Any = time.sleep,
) -> Any:
    if attempts < 1 or base_delay_seconds < 0:
        fail("Cloudflare API retry parameters are invalid")
    credentials = load_cloudflare_credentials()
    url = f"https://api.cloudflare.com/client/v4{path}"
    encoded = None if body is None else json.dumps(body).encode("utf-8")
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        request = urllib.request.Request(
            url,
            data=encoded,
            method=method.upper(),
            headers={
                "Authorization": f"Bearer {credentials.api_token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "ordivon-edge-release/0.2",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read())
            if not isinstance(payload, dict) or payload.get("success") is not True:
                raise ReleaseError(f"Cloudflare API returned failure: {payload}")
            return payload.get("result")
        except (
            urllib.error.URLError,
            urllib.error.HTTPError,
            TimeoutError,
            json.JSONDecodeError,
            ReleaseError,
        ) as error:
            last_error = error
            if attempt >= attempts:
                break
            sleep(min(base_delay_seconds * (2 ** (attempt - 1)), 10.0))
    raise ReleaseError(
        f"Cloudflare API request failed after {attempts} attempts: "
        f"{method.upper()} {path}\n{last_error}"
    ) from last_error


def expected_policy() -> tuple[str, dict[str, int]]:
    policy = load_json(POLICY_CONFIG)
    wrangler = load_json(WRANGLER_CONFIG)
    allowed_hosts = wrangler.get("vars", {}).get("FETCH_ALLOWED_HOSTS")
    if not isinstance(allowed_hosts, str) or not allowed_hosts:
        fail("FETCH_ALLOWED_HOSTS is missing from Wrangler configuration")
    normalized_hosts = sorted(
        host.strip().lower().rstrip(".")
        for host in allowed_hosts.split(",")
        if host.strip()
    )
    payload = json.dumps(
        {
            "policy": policy,
            "effective_fetch_allowed_hosts": normalized_hosts,
        },
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    family = policy.get("family")
    retention = policy.get("retention_days")
    if not isinstance(family, str) or not isinstance(retention, dict):
        fail("Edge policy configuration is invalid")
    version = f"{family}.{hashlib.sha256(payload).hexdigest()[:16]}"
    return version, retention


def load_edge_config() -> EdgeConfig:
    config = load_json(EDGE_CONFIG)
    endpoint = config.get("endpoint")
    key_id = config.get("key_id")
    secret_text = config.get("secret")
    if not all(isinstance(value, str) and value for value in (endpoint, key_id, secret_text)):
        fail("Edge client configuration is incomplete")
    try:
        secret = base64.urlsafe_b64decode(secret_text + "=" * (-len(secret_text) % 4))
    except ValueError as exc:
        raise ReleaseError("Edge HMAC secret is invalid") from exc
    if len(secret) < 32:
        fail("Edge HMAC secret is too short")
    return EdgeConfig(endpoint=endpoint.rstrip("/"), key_id=key_id, secret=secret)


def run(
    arguments: list[str],
    *,
    environment: dict[str, str] | None = None,
    capture: bool = False,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        arguments,
        cwd=ROOT,
        env=environment,
        text=True,
        check=False,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )
    if completed.returncode != 0:
        detail = ""
        if capture:
            detail = (completed.stderr or completed.stdout or "").strip()
        raise ReleaseError(
            f"Command failed ({completed.returncode}): {' '.join(arguments)}"
            + (f"\n{detail}" if detail else "")
        )
    return completed


def git_output(*arguments: str) -> str:
    return run(["git", *arguments], capture=True).stdout.strip()


def worker_release_digest(commit: str) -> str:
    listing = run(
        [
            "git",
            "ls-tree",
            "-r",
            "--full-tree",
            commit,
            "--",
            *worker_release_pathspecs(),
        ],
        capture=True,
    ).stdout
    if not listing.strip():
        fail(f"Worker release inputs are empty at commit: {commit}")
    return hashlib.sha256(listing.encode("utf-8")).hexdigest()


def worker_version_tag(commit: str, release_digest: str, timestamp: int) -> str:
    if re.fullmatch(r"[0-9a-f]{40}", commit) is None:
        fail("Worker source commit is not a full lowercase Git object ID")
    if re.fullmatch(r"[0-9a-f]{64}", release_digest) is None:
        fail("Worker release digest is not a SHA-256 digest")
    return f"git-{commit[:12]}-src-{release_digest[:16]}-{timestamp}"


def parse_worker_version_tag(tag: str | None) -> tuple[str, str | None]:
    current = re.fullmatch(
        r"git-([0-9a-f]{12})-src-([0-9a-f]{16})-[0-9]+",
        tag or "",
    )
    if current is not None:
        return current.group(1), current.group(2)
    legacy = re.fullmatch(r"git-([0-9a-f]{12})-[0-9]+", tag or "")
    if legacy is not None:
        return legacy.group(1), None
    fail(f"Worker Version has no valid Git source tag: tag={tag!r}")


def verify_release_source() -> str:
    head = git_output("rev-parse", "HEAD")
    dirty = run(
        [
            "git",
            "status",
            "--porcelain",
            "--untracked-files=all",
            "--",
            *worker_release_pathspecs(),
        ],
        capture=True,
    ).stdout.strip()
    if dirty:
        fail(
            "Worker release inputs are dirty and cannot be reconstructed from Git:\n"
            f"{dirty}"
        )
    return head


def wrangler(environment: dict[str, str], *arguments: str, capture: bool = False):
    return run(
        ["pnpm", "exec", "wrangler", *arguments],
        environment=environment,
        capture=capture,
    )


def versions(environment: dict[str, str] | None = None) -> list[dict[str, Any]]:
    del environment
    credentials = load_cloudflare_credentials()
    result = cloudflare_api(
        "GET",
        f"/accounts/{credentials.account_id}/workers/scripts/{WORKER_NAME}/versions?deployable=true",
    )
    items = result.get("items") if isinstance(result, dict) else None
    if not isinstance(items, list):
        fail("Cloudflare versions API returned an unexpected shape")
    return sorted(
        items,
        key=lambda item: (
            item.get("number") if isinstance(item.get("number"), int) else -1,
            item.get("metadata", {}).get("created_on", "")
            if isinstance(item.get("metadata"), dict)
            else "",
        ),
    )


def deployments(environment: dict[str, str] | None = None) -> list[dict[str, Any]]:
    del environment
    credentials = load_cloudflare_credentials()
    result = cloudflare_api(
        "GET",
        f"/accounts/{credentials.account_id}/workers/scripts/{WORKER_NAME}/deployments",
    )
    items = result.get("deployments") if isinstance(result, dict) else None
    if not isinstance(items, list) or not items:
        fail("Cloudflare deployments API returned no active deployments")
    return sorted(
        items,
        key=lambda item: item.get("created_on", "")
        if isinstance(item.get("created_on"), str)
        else "",
    )


def worker_source_equivalent(candidate_ref: str, current_commit: str) -> bool:
    resolved = subprocess.run(
        ["git", "rev-parse", "--verify", f"{candidate_ref}^{{commit}}"],
        cwd=ROOT,
        text=True,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if resolved.returncode != 0:
        raise ReleaseError(
            f"Cannot resolve candidate source commit: {candidate_ref}"
        )
    candidate_commit = resolved.stdout.strip()
    comparison = subprocess.run(
        [
            "git",
            "diff",
            "--quiet",
            candidate_commit,
            current_commit,
            "--",
            *worker_release_pathspecs(),
        ],
        cwd=ROOT,
        check=False,
    )
    if comparison.returncode not in {0, 1}:
        raise ReleaseError("Cannot compare candidate Worker release inputs")
    return comparison.returncode == 0


def resumable_candidate(
    version_list: list[dict[str, Any]],
    version_id: str,
    commit: str,
    *,
    source_equivalent: Any = worker_source_equivalent,
) -> dict[str, Any]:
    candidate = next(
        (item for item in version_list if item.get("id") == version_id),
        None,
    )
    if candidate is None:
        fail(f"Candidate Worker Version does not exist: {version_id}")
    annotations = candidate.get("annotations")
    tag = annotations.get("workers/tag") if isinstance(annotations, dict) else None
    try:
        candidate_ref, candidate_digest = parse_worker_version_tag(tag)
    except ReleaseError as error:
        fail(
            "Candidate Worker Version has no valid Git source tag: "
            f"version={version_id}, tag={tag!r}, error={error}"
        )
    if candidate_digest is not None:
        current_digest = worker_release_digest(commit)
        if candidate_digest != current_digest[:16]:
            fail(
                "Candidate Worker Version release digest does not match current inputs: "
                f"version={version_id}, candidate_digest={candidate_digest}, "
                f"current_digest={current_digest[:16]}"
            )
    if candidate_ref != commit[:12] and not source_equivalent(
        candidate_ref,
        commit,
    ):
        fail(
            "Candidate Worker Version does not match the current Worker release inputs: "
            f"version={version_id}, candidate_ref={candidate_ref}, "
            f"current_commit={commit[:12]}"
        )
    return candidate


def version_record(
    version_list: list[dict[str, Any]],
    version_id: str,
) -> dict[str, Any]:
    record = next((item for item in version_list if item.get("id") == version_id), None)
    if record is None:
        fail(f"Worker Version is missing from the deployable version list: {version_id}")
    return record


def version_source(record: dict[str, Any]) -> tuple[str, str | None]:
    annotations = record.get("annotations")
    tag = annotations.get("workers/tag") if isinstance(annotations, dict) else None
    return parse_worker_version_tag(tag)


def changed_worker_inputs(previous: dict[str, Any], commit: str) -> list[str] | None:
    try:
        previous_ref, _ = version_source(previous)
    except ReleaseError:
        return None
    resolved = subprocess.run(
        ["git", "rev-parse", "--verify", f"{previous_ref}^{{commit}}"],
        cwd=ROOT,
        text=True,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if resolved.returncode != 0:
        return None
    completed = run(
        [
            "git",
            "diff",
            "--name-only",
            resolved.stdout.strip(),
            commit,
            "--",
            *worker_release_pathspecs(),
        ],
        capture=True,
    )
    return [line for line in completed.stdout.splitlines() if line]


def smoke_operations_for_change(
    previous: dict[str, Any],
    commit: str,
) -> set[str]:
    changed = changed_worker_inputs(previous, commit)
    if changed is None or not changed:
        return {"fetch", "browser.run"}
    operations: set[str] = set()
    specific = True
    for path in changed:
        if path.endswith(("/src/external-fetch.ts", "/src/fetch-policy.ts")):
            operations.add("fetch")
        elif path.endswith(("/src/browser-run.ts", "/src/browser-policy.ts")):
            operations.add("browser.run")
        else:
            specific = False
            break
    return operations if specific and operations else {"fetch", "browser.run"}


def active_version(deployment_list: list[dict[str, Any]]) -> str:
    candidates = [
        version
        for version in deployment_list[-1].get("versions", [])
        if version.get("percentage") == 100
    ]
    if len(candidates) != 1 or not isinstance(candidates[0].get("version_id"), str):
        fail("Latest deployment does not have exactly one 100% active version")
    return candidates[0]["version_id"]


def parse_deployment_specifications(
    specifications: list[str],
) -> list[dict[str, Any]]:
    parsed: list[dict[str, Any]] = []
    for specification in specifications:
        version_id, separator, percentage_text = specification.partition("@")
        if not separator or not version_id:
            fail(f"Invalid deployment specification: {specification}")
        try:
            percentage = float(percentage_text)
        except ValueError as exc:
            raise ReleaseError(
                f"Invalid deployment percentage: {specification}"
            ) from exc
        if percentage < 0 or percentage > 100:
            fail(f"Deployment percentage is out of range: {specification}")
        parsed.append(
            {
                "version_id": version_id,
                "percentage": int(percentage)
                if percentage.is_integer()
                else percentage,
            }
        )
    if abs(sum(float(item["percentage"]) for item in parsed) - 100.0) > 0.0001:
        fail("Deployment percentages must sum to 100")
    return parsed


def deployment_matches(
    deployment: dict[str, Any],
    expected_versions: list[dict[str, Any]],
) -> bool:
    actual = deployment.get("versions")
    if not isinstance(actual, list):
        return False
    def normalize(rows: list[dict[str, Any]]) -> list[tuple[str, float]]:
        return sorted(
            (
                str(row.get("version_id")),
                float(row.get("percentage", -1)),
            )
            for row in rows
            if isinstance(row, dict)
        )

    return normalize(actual) == normalize(expected_versions)


def wait_for_deployment(
    expected_versions: list[dict[str, Any]],
    *,
    timeout_seconds: float = 45.0,
    interval_seconds: float = 2.0,
    sleep: Any = time.sleep,
    monotonic: Any = time.monotonic,
) -> dict[str, Any]:
    deadline = monotonic() + timeout_seconds
    last: dict[str, Any] | None = None
    while True:
        last = deployments()[-1]
        if deployment_matches(last, expected_versions):
            return last
        if monotonic() >= deadline:
            fail(
                "Cloudflare deployment did not reach the requested version split: "
                f"expected={expected_versions!r}, latest={last!r}"
            )
        sleep(interval_seconds)


def create_deployment_api(
    expected_versions: list[dict[str, Any]],
    message: str,
    *,
    force: bool = False,
) -> dict[str, Any]:
    credentials = load_cloudflare_credentials()
    suffix = "?force=true" if force else ""
    result = cloudflare_api(
        "POST",
        f"/accounts/{credentials.account_id}/workers/scripts/{WORKER_NAME}/deployments{suffix}",
        body={
            "strategy": "percentage",
            "versions": expected_versions,
            "annotations": {"workers/message": message},
        },
    )
    if not isinstance(result, dict):
        fail("Cloudflare deployment API returned an unexpected shape")
    return wait_for_deployment(expected_versions)


def deploy_versions(
    environment: dict[str, str],
    specifications: list[str],
    message: str,
    *,
    command_timeout_seconds: float = 30.0,
    force: bool = False,
) -> dict[str, Any]:
    expected_versions = parse_deployment_specifications(specifications)
    if all(float(item["percentage"]) > 0 for item in expected_versions):
        return create_deployment_api(
            expected_versions,
            message,
            force=force,
        )
    arguments = [
        "pnpm",
        "exec",
        "wrangler",
        "versions",
        "deploy",
        *specifications,
        "--name",
        WORKER_NAME,
        "--message",
        message,
        "--yes",
    ]
    process = subprocess.Popen(
        arguments,
        cwd=ROOT,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    output = ""
    timed_out = False
    try:
        output, _ = process.communicate(timeout=command_timeout_seconds)
    except subprocess.TimeoutExpired as error:
        timed_out = True
        partial = error.output
        if isinstance(partial, bytes):
            partial = partial.decode("utf-8", errors="replace")
        output = partial or ""
        os.killpg(process.pid, signal.SIGKILL)
        remainder, _ = process.communicate()
        output += remainder or ""

    try:
        deployment = wait_for_deployment(expected_versions)
    except ReleaseError as reconciliation_error:
        detail = output.strip()[-4000:]
        state = "timed out" if timed_out else f"exited {process.returncode}"
        raise ReleaseError(
            f"Wrangler deployment {state} and API reconciliation failed.\n"
            f"{detail}\n{reconciliation_error}"
        ) from reconciliation_error

    if output.strip():
        print(output.rstrip())
    return deployment


def canonical_target(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit(("", "", parsed.path or "/", parsed.query, ""))


def signed_request(
    config: EdgeConfig,
    method: str,
    path: str,
    *,
    body: bytes = b"",
    request_id: str | None = None,
    version_override: str | None = None,
    timeout: float = 75.0,
) -> tuple[int, dict[str, str], Any]:
    request_id = request_id or f"req_release_{uuid.uuid4().hex}"
    url = f"{config.endpoint}{path}"
    timestamp = int(time.time())
    body_sha256 = hashlib.sha256(body).hexdigest()
    canonical = "\n".join(
        [
            "ordivon-edge-v1",
            method.upper(),
            canonical_target(url),
            request_id,
            str(timestamp),
            body_sha256,
        ]
    )
    signature = base64.urlsafe_b64encode(
        hmac.new(config.secret, canonical.encode("utf-8"), hashlib.sha256).digest()
    ).rstrip(b"=").decode("ascii")
    headers = {
        "Authorization": f"Ordivon-HMAC {config.key_id}:{signature}",
        "X-Ordivon-Request-Id": request_id,
        "X-Ordivon-Timestamp": str(timestamp),
        "Accept": "application/json",
        "User-Agent": "ordivon-edge-release/0.1",
    }
    if body:
        headers["Content-Type"] = "application/json"
    if version_override is not None:
        headers["Cloudflare-Workers-Version-Overrides"] = (
            f'{WORKER_NAME}="{version_override}"'
        )
    invocation = urllib.request.Request(
        url,
        data=body if method.upper() not in {"GET", "HEAD"} else None,
        method=method.upper(),
        headers=headers,
    )
    try:
        with urllib.request.urlopen(invocation, timeout=timeout) as response:
            status = response.status
            response_headers = dict(response.headers.items())
            raw = response.read()
    except urllib.error.HTTPError as exc:
        status = exc.code
        response_headers = dict(exc.headers.items())
        raw = exc.read()
    except urllib.error.URLError as exc:
        raise ReleaseError(f"Smoke request failed: {exc.reason}") from exc
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ReleaseError("Smoke request returned non-JSON data") from exc
    return status, response_headers, value


def observed_version(value: Any) -> str | None:
    if not isinstance(value, dict):
        return None
    metadata = value.get("worker_version")
    if isinstance(metadata, dict) and isinstance(metadata.get("id"), str):
        return metadata["id"]
    receipt = value.get("receipt")
    execution = receipt.get("execution") if isinstance(receipt, dict) else None
    actual = execution.get("worker_version_id") if isinstance(execution, dict) else None
    return actual if isinstance(actual, str) else None


def assert_version(value: Any, version_id: str, context: str) -> None:
    if not isinstance(value, dict):
        fail(f"{context} did not return a JSON object")
    actual = observed_version(value)
    if actual != version_id:
        fail(f"{context} reached Worker version {actual!r}, expected {version_id}")


def assert_policy(value: Any, policy_version: str, context: str) -> None:
    if not isinstance(value, dict):
        fail(f"{context} did not return a JSON object")
    actual = value.get("policy_version")
    if actual != policy_version:
        fail(f"{context} reported policy {actual!r}, expected {policy_version}")


def wait_for_version_propagation(
    config: EdgeConfig,
    version_id: str,
    *,
    use_override: bool,
    timeout_seconds: float = 120.0,
    interval_seconds: float = 3.0,
    consecutive_required: int = ROUTE_STABILITY_OBSERVATIONS,
    sleep: Any = time.sleep,
    monotonic: Any = time.monotonic,
) -> dict[str, Any]:
    if timeout_seconds <= 0 or interval_seconds <= 0 or consecutive_required < 1:
        fail("Version propagation parameters are invalid")
    deadline = monotonic() + timeout_seconds
    consecutive = 0
    observations: list[dict[str, Any]] = []
    while True:
        status, headers, health = signed_request(
            config,
            "GET",
            "/health",
            version_override=version_id if use_override else None,
        )
        actual = observed_version(health)
        normalized = {key.lower(): value for key, value in headers.items()}
        observations.append(
            {
                "status": status,
                "worker_version_id": actual,
                "cf_ray": normalized.get("cf-ray"),
            }
        )
        if status == 200 and actual == version_id:
            consecutive += 1
        else:
            consecutive = 0
        if consecutive >= consecutive_required:
            return {
                "target_version": version_id,
                "use_override": use_override,
                "consecutive_required": consecutive_required,
                "attempts": len(observations),
                "observations": observations[-20:],
            }
        if monotonic() >= deadline:
            fail(
                "Worker version propagation did not stabilize: "
                f"target={version_id}, last={actual}, attempts={len(observations)}"
            )
        sleep(interval_seconds)


def read_versioned_document(
    config: EdgeConfig,
    version_id: str,
    path: str,
    context: str,
    *,
    use_override: bool,
    timeout_seconds: float = 60.0,
    interval_seconds: float = 2.0,
    sleep: Any = time.sleep,
    monotonic: Any = time.monotonic,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if timeout_seconds <= 0 or interval_seconds <= 0:
        fail("Versioned read retry parameters are invalid")
    deadline = monotonic() + timeout_seconds
    observations: list[dict[str, Any]] = []
    while True:
        status, headers, value = signed_request(
            config,
            "GET",
            path,
            version_override=version_id if use_override else None,
        )
        actual = observed_version(value)
        normalized = {key.lower(): item for key, item in headers.items()}
        observations.append(
            {
                "status": status,
                "worker_version_id": actual,
                "cf_ray": normalized.get("cf-ray"),
            }
        )
        if status == 200 and actual == version_id and isinstance(value, dict):
            return value, {
                "path": path,
                "target_version": version_id,
                "use_override": use_override,
                "attempts": len(observations),
                "observations": observations[-20:],
            }
        if monotonic() >= deadline:
            fail(
                f"{context} did not reach the requested Worker version: "
                f"target={version_id}, last={actual}, status={status}, "
                f"attempts={len(observations)}"
            )
        sleep(interval_seconds)

def smoke_operation(
    config: EdgeConfig,
    version_id: str,
    path: str,
    body: bytes,
    request_prefix: str,
    *,
    timeout: float = 75.0,
) -> tuple[str, dict[str, Any], list[dict[str, Any]]]:
    last_status = 0
    last_value: Any = None
    route_guards: list[dict[str, Any]] = []
    for attempt in range(1, 4):
        route_guards.append(
            wait_for_version_propagation(
                config,
                version_id,
                use_override=True,
            )
        )
        request_id = f"{request_prefix}_{uuid.uuid4().hex}"
        status, headers, value = signed_request(
            config,
            "POST",
            path,
            body=body,
            request_id=request_id,
            version_override=version_id,
            timeout=timeout,
        )
        last_status = status
        last_value = value
        if not isinstance(value, dict):
            fail(f"Smoke operation {path} returned a non-object response")
        assert_version(value, version_id, f"smoke operation {path}")
        if status != 429:
            return request_id, value, route_guards
        if attempt < 3:
            normalized = {key.lower(): val for key, val in headers.items()}
            try:
                retry_after = int(normalized.get("retry-after", "10"))
            except ValueError:
                retry_after = 10
            time.sleep(min(max(retry_after, 1), 30))
    fail(f"Smoke operation {path} remained rate limited: HTTP {last_status}: {last_value}")


def smoke_version(
    config: EdgeConfig,
    version_id: str,
    policy_version: str,
    retention: dict[str, int],
    operations: set[str],
) -> dict[str, Any]:
    health, health_read = read_versioned_document(
        config,
        version_id,
        "/health",
        "version-specific health smoke",
        use_override=True,
    )
    assert_policy(health, policy_version, "health smoke")

    capabilities, capabilities_read = read_versioned_document(
        config,
        version_id,
        "/v1/capabilities",
        "version-specific capability smoke",
        use_override=True,
    )
    assert_policy(capabilities, policy_version, "capability smoke")
    expected_retention = {
        "idempotency_days": retention["idempotency"],
        "request_state_days": retention["request_state"],
        "receipt_mirror_days": retention["receipt_mirror"],
        "artifact_days": retention["artifacts"],
        "cleanup_task_days": retention["cleanup_tasks"],
    }
    if capabilities.get("retention") != expected_retention:
        fail(
            "Capability retention does not match the release policy: "
            f"{capabilities.get('retention')!r}"
        )

    report: dict[str, Any] = {
        "health": health,
        "health_read": health_read,
        "capabilities": capabilities,
        "capabilities_read": capabilities_read,
        "operations": sorted(operations),
    }

    if "fetch" in operations:
        fetch_body = json.dumps(
            {
                "url": "https://example.com/",
                "maximum_bytes": 65536,
                "timeout_ms": 10000,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        fetch_id, fetch_result, fetch_route_guards = smoke_operation(
            config,
            version_id,
            "/v1/fetch",
            fetch_body,
            "req_release_fetch",
        )
        fetch_status = fetch_result.get("receipt", {}).get("status")
        if fetch_status != "succeeded":
            fail(f"Version-specific fetch smoke failed: {fetch_result}")
        fetch_receipt = fetch_result["receipt"]

        report.update({
            "fetch_request_id": fetch_id,
            "fetch_receipt": fetch_receipt,
            "fetch_route_guards": fetch_route_guards,
        })

    if "browser.run" in operations:
        browser_body = json.dumps(
            {
                "url": "https://example.com/",
                "viewport_width": 1024,
                "viewport_height": 768,
                "full_page": False,
                "wait_until": "domcontentloaded",
                "timeout_ms": 15000,
                "wait_after_ms": 0,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        browser_id, browser_result, browser_route_guards = smoke_operation(
            config,
            version_id,
            "/v1/browser/run",
            browser_body,
            "req_release_browser",
            timeout=90.0,
        )
        browser_status = browser_result.get("receipt", {}).get("status")
        if browser_status != "succeeded":
            fail(f"Version-specific Browser smoke failed: {browser_result}")
        browser_receipt = browser_result["receipt"]
        report.update({
            "browser_request_id": browser_id,
            "browser_receipt": browser_receipt,
            "browser_route_guards": browser_route_guards,
        })

    return report
def write_receipt(prefix: str, report: dict[str, Any]) -> pathlib.Path:
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    path = RELEASE_DIR / f"{prefix}-{stamp}.json"
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)
    os.chmod(path, 0o600)
    return path


def release(args: argparse.Namespace) -> int:
    environment = cloudflare_environment()
    edge = load_edge_config()
    commit = verify_release_source()
    release_digest = worker_release_digest(commit)
    message = args.message or f"Ordivon Edge {commit[:12]}"
    policy_version, retention = expected_policy()
    report: dict[str, Any] = {
        "status": "preflight",
        "started_at": dt.datetime.now(dt.UTC).isoformat(),
        "git_commit": commit,
        "worker_release_digest": release_digest,
        "message": message,
        "expected_policy_version": policy_version,
        "expected_retention": retention,
    }
    previous_version: str | None = None
    new_version: str | None = None
    zero_deployed = False

    try:
        version_list = versions(environment)
        previous_deployments = deployments(environment)
        previous_version = active_version(previous_deployments)
        previous_record = version_record(version_list, previous_version)
        _, previous_digest = version_source(previous_record)
        if previous_digest == release_digest[:16]:
            print(
                json.dumps(
                    {
                        "ok": True,
                        "status": "no_change",
                        "git_commit": commit,
                        "worker_release_digest": release_digest,
                        "version_id": previous_version,
                    },
                    indent=2,
                )
            )
            return 0
        smoke_operations = smoke_operations_for_change(previous_record, commit)
        report["smoke_operations"] = sorted(smoke_operations)
        run(["pnpm", "install", "--frozen-lockfile", "--offline"])
        run(["pnpm", "run", "ci"])
        report["status"] = "ci_passed"
        resume_version_id = getattr(args, "candidate_version_id", None)
        if resume_version_id is not None:
            candidate = resumable_candidate(
                version_list,
                resume_version_id,
                commit,
            )
            new_version = resume_version_id
            annotations = candidate.get("annotations")
            tag = (
                annotations.get("workers/tag")
                if isinstance(annotations, dict)
                else None
            )
            report.update(
                {
                    "tag": tag,
                    "previous_version": previous_version,
                    "candidate_version": new_version,
                    "candidate_reused": True,
                    "status": "smoke_pending",
                }
            )
        else:
            before_versions = {item.get("id") for item in version_list}
            tag = worker_version_tag(commit, release_digest, int(time.time()))
            report.update(
                {
                    "tag": tag,
                    "previous_version": previous_version,
                    "status": "upload_pending",
                }
            )
            wrangler(
                environment,
                "versions",
                "upload",
                "--name",
                WORKER_NAME,
                "--tag",
                tag,
                "--message",
                message,
                "--keep-vars",
                "--strict",
            )
            after = versions(environment)
            new_versions = [
                item
                for item in after
                if item.get("id") not in before_versions
                and isinstance(item.get("id"), str)
            ]
            if len(new_versions) != 1:
                fail(
                    f"Expected one newly uploaded version, found {len(new_versions)}"
                )
            new_version = new_versions[0]["id"]
            report.update(
                {
                    "candidate_version": new_version,
                    "candidate_reused": False,
                    "status": "smoke_pending",
                }
            )

        deploy_versions(
            environment,
            [f"{previous_version}@100", f"{new_version}@0"],
            f"Smoke candidate {commit[:12]}",
        )
        zero_deployed = True
        report["status"] = "smoke_pending"
        report["candidate_propagation"] = wait_for_version_propagation(
            edge,
            new_version,
            use_override=True
        )
        report["smoke"] = smoke_version(
            edge,
            new_version,
            policy_version,
            retention,
            smoke_operations,
        )
        report["status"] = "smoke_passed"
        deploy_versions(
            environment,
            [f"{new_version}@100"],
            f"Promote verified Ordivon Edge {commit[:12]}",
        )
        report["promotion_propagation"] = wait_for_version_propagation(
            edge,
            new_version,
            use_override=False
        )
        health, post_promotion_read = read_versioned_document(
            edge,
            new_version,
            "/health",
            "post-promotion health",
            use_override=False,
        )
        assert_policy(health, policy_version, "post-promotion health")
        report.update(
            {
                "status": "promoted",
                "completed_at": dt.datetime.now(dt.UTC).isoformat(),
                "post_promotion_health": health,
                "post_promotion_read": post_promotion_read,
                "deployment": deployments(environment)[-1],
            }
        )
        receipt_path = write_receipt("release", report)
        print(
            json.dumps(
                {
                    "ok": True,
                    "status": report["status"],
                    "git_commit": commit,
                    "worker_release_digest": release_digest,
                    "previous_version": previous_version,
                    "version_id": new_version,
                    "receipt": str(receipt_path),
                },
                indent=2,
            )
        )
        return 0
    except Exception as error:
        report.update(
            {
                "status": "failed",
                "failed_at": dt.datetime.now(dt.UTC).isoformat(),
                "failed_stage": report.get("status", "unknown"),
                "error": str(error),
                "candidate_version": new_version,
                "previous_version": previous_version,
            }
        )
        if zero_deployed and previous_version is not None:
            try:
                deploy_versions(
                    environment,
                    [f"{previous_version}@100"],
                    f"Restore previous version after failed release {commit[:12]}",
                )
                report["restored_previous_version"] = True
            except Exception as restore_error:
                report["restored_previous_version"] = False
                report["restore_error"] = str(restore_error)
        receipt_path = write_receipt("release-failed", report)
        raise ReleaseError(
            f"Release failed; receipt: {receipt_path}\n{error}"
        ) from error

def rollback(args: argparse.Namespace) -> int:
    environment = cloudflare_environment()
    edge = load_edge_config()
    deployment_list = deployments(environment)
    current = active_version(deployment_list)
    target = args.version_id
    if target is None:
        for deployment in reversed(deployment_list[:-1]):
            try:
                candidate = active_version([deployment])
            except ReleaseError:
                continue
            if candidate != current:
                target = candidate
                break
    if target is None:
        fail("No previous 100% deployment was found; provide --version-id")

    message = args.message or f"Rollback Ordivon Edge from {current} to {target}"
    deploy_versions(
        environment,
        [f"{target}@100"],
        message,
        force=True,
    )
    status, _, health = signed_request(edge, "GET", "/health")
    if status != 200:
        fail(f"Rollback health returned HTTP {status}: {health}")
    assert_version(health, target, "rollback health")
    report = {
        "status": "rolled_back",
        "completed_at": dt.datetime.now(dt.UTC).isoformat(),
        "from_version": current,
        "to_version": target,
        "message": message,
        "health": health,
        "deployment": deployments(environment)[-1],
    }
    path = write_receipt("rollback", report)
    print(json.dumps({"ok": True, "receipt": str(path), **report}, indent=2))
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="ordivon-edge-release")
    commands = root.add_subparsers(dest="command", required=True)

    release_command = commands.add_parser("release")
    release_command.add_argument("--message")
    release_command.add_argument(
        "--candidate-version-id",
        help="Reuse an uploaded Worker Version bound to the current Git commit.",
    )

    rollback_command = commands.add_parser("rollback")
    rollback_command.add_argument("--version-id")
    rollback_command.add_argument("--message")
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "release":
            return release(args)
        if args.command == "rollback":
            return rollback(args)
        fail(f"Unknown command: {args.command}")
    except ReleaseError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
