#!/usr/bin/env python3
"""Signed single-user client for Ordivon Edge."""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import http.client
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass
from typing import Any

DEFAULT_CONFIG = pathlib.Path("/root/.config/ordivon/secrets/edge-client.json")
USER_AGENT = "ordivon-edge-client/0.2"
MAX_TRANSPORT_ATTEMPTS = 3
TRANSPORT_RETRY_BASE_SECONDS = 0.25


class ClientError(RuntimeError):
    pass


@dataclass(frozen=True)
class Config:
    endpoint: str
    key_id: str
    secret: bytes


def load_config(path: pathlib.Path) -> Config:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ClientError(f"Edge client configuration does not exist: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ClientError(f"Cannot read Edge client configuration: {path}") from exc

    endpoint = raw.get("endpoint")
    key_id = raw.get("key_id")
    secret_text = raw.get("secret")
    if not all(isinstance(value, str) and value for value in (endpoint, key_id, secret_text)):
        raise ClientError("Edge client configuration is incomplete")
    try:
        secret = base64.urlsafe_b64decode(secret_text + "=" * (-len(secret_text) % 4))
    except ValueError as exc:
        raise ClientError("Edge client secret is not valid base64url") from exc
    if len(secret) < 32:
        raise ClientError("Edge client secret is too short")
    return Config(endpoint=endpoint.rstrip("/"), key_id=key_id, secret=secret)


def make_request_id() -> str:
    return f"req_{uuid.uuid4().hex}"


def canonical_target(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit(("", "", parsed.path or "/", parsed.query, ""))


def signed_headers(
    config: Config,
    method: str,
    url: str,
    body: bytes,
    request_id: str,
    timestamp: int | None = None,
) -> dict[str, str]:
    timestamp = int(time.time()) if timestamp is None else timestamp
    body_digest = hashlib.sha256(body).hexdigest()
    canonical = "\n".join(
        [
            "ordivon-edge-v1",
            method.upper(),
            canonical_target(url),
            request_id,
            str(timestamp),
            body_digest,
        ]
    )
    signature = base64.urlsafe_b64encode(
        hmac.new(config.secret, canonical.encode("utf-8"), hashlib.sha256).digest()
    ).rstrip(b"=").decode("ascii")
    return {
        "Authorization": f"Ordivon-HMAC {config.key_id}:{signature}",
        "X-Ordivon-Request-Id": request_id,
        "X-Ordivon-Timestamp": str(timestamp),
        "User-Agent": USER_AGENT,
    }


def request(
    config: Config,
    method: str,
    path: str,
    *,
    body: bytes = b"",
    request_id: str | None = None,
    accept: str = "application/json",
    transport_attempts: int = MAX_TRANSPORT_ATTEMPTS,
    sleep: Any = time.sleep,
) -> tuple[int, dict[str, str], bytes]:
    request_id = request_id or make_request_id()
    if transport_attempts < 1:
        raise ClientError("transport_attempts must be positive")
    url = f"{config.endpoint}{path}"
    last_error: BaseException | None = None
    for attempt in range(1, transport_attempts + 1):
        headers = signed_headers(config, method, url, body, request_id)
        headers["Accept"] = accept
        if body:
            headers["Content-Type"] = "application/json"
        invocation = urllib.request.Request(
            url,
            data=body if method.upper() not in {"GET", "HEAD"} else None,
            method=method.upper(),
            headers=headers,
        )
        try:
            with urllib.request.urlopen(invocation, timeout=30) as response:
                return response.status, dict(response.headers.items()), response.read()
        except urllib.error.HTTPError as exc:
            return exc.code, dict(exc.headers.items()), exc.read()
        except (
            urllib.error.URLError,
            http.client.HTTPException,
            ConnectionError,
            TimeoutError,
        ) as exc:
            last_error = exc
            if attempt >= transport_attempts:
                break
            sleep(TRANSPORT_RETRY_BASE_SECONDS * (2 ** (attempt - 1)))
    detail = getattr(last_error, "reason", None) or str(last_error) or type(last_error).__name__
    raise ClientError(
        f"Edge request failed after {transport_attempts} transport attempts: {detail}"
    ) from last_error


def print_json_bytes(body: bytes) -> None:
    try:
        value = json.loads(body)
    except json.JSONDecodeError:
        raise ClientError("Edge returned a non-JSON response")
    print(json.dumps(value, indent=2, ensure_ascii=False))


def command_json(config: Config, path: str) -> int:
    status, _, body = request(config, "GET", path)
    print_json_bytes(body)
    return 0 if 200 <= status < 300 else 1


WORKER_RELEASE_INPUTS = (
    "src",
    "config/edge-policy.json",
    "wrangler.jsonc",
    "package.json",
    "pnpm-lock.yaml",
    "tsconfig.json",
)


def git(
    repository: pathlib.Path,
    *arguments: str,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        text=True,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise ClientError(
            f"Git command failed: {' '.join(arguments)}"
            + (f"\n{detail}" if detail else "")
        )
    return completed


def resolve_commit(repository: pathlib.Path, reference: str) -> str:
    return git(
        repository,
        "rev-parse",
        "--verify",
        f"{reference}^{{commit}}",
    ).stdout.strip()


def worker_release_pathspecs(repository: pathlib.Path) -> tuple[str, ...]:
    top_level = pathlib.Path(
        git(repository, "rev-parse", "--show-toplevel").stdout.strip()
    ).resolve()
    monorepo_provider = top_level / "providers" / "cloudflare"
    if (monorepo_provider / "wrangler.jsonc").is_file():
        prefix = "providers/cloudflare"
    elif (top_level / "wrangler.jsonc").is_file():
        prefix = ""
    else:
        raise ClientError(
            "Repository does not contain the Cloudflare provider at the root "
            "or providers/cloudflare"
        )
    return tuple(
        f":(top){prefix}/{relative}" if prefix else f":(top){relative}"
        for relative in WORKER_RELEASE_INPUTS
    )


def release_digest(repository: pathlib.Path, commit: str) -> str:
    listing = git(
        repository,
        "ls-tree",
        "-r",
        "--full-tree",
        commit,
        "--",
        *worker_release_pathspecs(repository),
    ).stdout
    if not listing.strip():
        raise ClientError(f"Worker release inputs are empty at commit: {commit}")
    return hashlib.sha256(listing.encode("utf-8")).hexdigest()


def commit_relation(
    repository: pathlib.Path,
    deployed_commit: str,
    expected_commit: str,
) -> str:
    if deployed_commit == expected_commit:
        return "current"
    deployed_ancestor = git(
        repository,
        "merge-base",
        "--is-ancestor",
        deployed_commit,
        expected_commit,
        check=False,
    )
    if deployed_ancestor.returncode == 0:
        return "behind"
    if deployed_ancestor.returncode not in {0, 1}:
        return "unknown"
    expected_ancestor = git(
        repository,
        "merge-base",
        "--is-ancestor",
        expected_commit,
        deployed_commit,
        check=False,
    )
    if expected_ancestor.returncode == 0:
        return "ahead"
    if expected_ancestor.returncode == 1:
        return "diverged"
    return "unknown"


def deployment_identity(health: dict[str, Any]) -> tuple[str | None, str | None]:
    identity = health.get("deployment_identity")
    if isinstance(identity, dict):
        source = identity.get("source_commit")
        digest = identity.get("worker_release_digest")
        return (
            source if isinstance(source, str) else None,
            digest if isinstance(digest, str) else None,
        )
    version = health.get("worker_version")
    tag = version.get("tag") if isinstance(version, dict) else None
    current = re.fullmatch(
        r"git-([0-9a-f]{12})-src-([0-9a-f]{16})-[0-9]+",
        tag or "",
    )
    if current is not None:
        return current.group(1), current.group(2)
    legacy = re.fullmatch(r"git-([0-9a-f]{12})-[0-9]+", tag or "")
    return (legacy.group(1), None) if legacy is not None else (None, None)


def command_status(config: Config, args: argparse.Namespace) -> int:
    status, _, body = request(config, "GET", "/health")
    try:
        health = json.loads(body)
    except json.JSONDecodeError as exc:
        raise ClientError("Edge returned a non-JSON health response") from exc
    if not isinstance(health, dict):
        raise ClientError("Edge health response is not an object")
    if not 200 <= status < 300:
        print(json.dumps(health, indent=2, ensure_ascii=False))
        return 1

    repository = pathlib.Path(args.repo).expanduser().resolve()
    expected_commit = resolve_commit(repository, args.expected_ref)
    source_ref, deployed_digest = deployment_identity(health)
    deployed_commit: str | None = None
    relation = "unknown"
    source_error: str | None = None
    if source_ref is not None:
        try:
            deployed_commit = resolve_commit(repository, source_ref)
            relation = commit_relation(repository, deployed_commit, expected_commit)
        except ClientError as error:
            source_error = str(error)

    expected_digest = release_digest(repository, expected_commit)
    inputs_status = (
        "current"
        if deployed_digest == expected_digest[:16]
        else "drifted"
        if deployed_digest is not None
        else "unknown"
    )
    result = {
        "ok": True,
        "service": health.get("service"),
        "status": health.get("status"),
        "policy_version": health.get("policy_version"),
        "worker_version": health.get("worker_version"),
        "deployment": {
            "source_ref": source_ref,
            "source_commit": deployed_commit,
            "expected_ref": args.expected_ref,
            "expected_commit": expected_commit,
            "source_relation": relation,
            "worker_release_digest": deployed_digest,
            "expected_worker_release_digest": expected_digest[:16],
            "worker_inputs": inputs_status,
            "source_error": source_error,
        },
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def command_fetch(config: Config, args: argparse.Namespace) -> int:
    payload: dict[str, Any] = {
        "url": args.url,
        "maximum_bytes": args.maximum_bytes,
        "timeout_ms": args.timeout_ms,
    }
    if args.accept:
        payload["accept"] = args.accept
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    status, _, response = request(
        config,
        "POST",
        "/v1/fetch",
        body=body,
        request_id=args.request_id,
    )
    print_json_bytes(response)
    return 0 if 200 <= status < 300 else 1


def command_browser_run(config: Config, args: argparse.Namespace) -> int:
    payload: dict[str, Any] = {
        "url": args.url,
        "viewport_width": args.viewport_width,
        "viewport_height": args.viewport_height,
        "full_page": args.full_page,
        "wait_until": args.wait_until,
        "timeout_ms": args.timeout_ms,
        "wait_after_ms": args.wait_after_ms,
    }
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    status, _, response = request(
        config,
        "POST",
        "/v1/browser/run",
        body=body,
        request_id=args.request_id,
    )
    print_json_bytes(response)
    return 0 if 200 <= status < 300 else 1


def command_receipt(config: Config, args: argparse.Namespace) -> int:
    path = f"/v1/receipts/{args.receipt_id}"
    deadline = time.monotonic() + args.timeout
    while True:
        status, _, body = request(config, "GET", path)
        try:
            value = json.loads(body)
        except json.JSONDecodeError as exc:
            raise ClientError("Edge returned a non-JSON receipt response") from exc
        pending = status == 202 and isinstance(value, dict) and value.get("status") == "pending"
        if not pending or not args.wait:
            print(json.dumps(value, indent=2, ensure_ascii=False))
            return 0 if 200 <= status < 300 else 1
        if time.monotonic() >= deadline:
            print(json.dumps(value, indent=2, ensure_ascii=False))
            print(
                json.dumps(
                    {
                        "ok": False,
                        "error": "receipt wait timed out",
                        "receipt_id": args.receipt_id,
                    },
                    ensure_ascii=False,
                ),
                file=sys.stderr,
            )
            return 3
        time.sleep(args.interval)


def command_artifact_get(config: Config, args: argparse.Namespace) -> int:
    encoded = "/".join(urllib.parse.quote(segment, safe="") for segment in args.key.split("/"))
    status, headers, body = request(
        config,
        "GET",
        f"/v1/artifacts/{encoded}",
        accept="application/octet-stream",
    )
    if not 200 <= status < 300:
        print_json_bytes(body)
        return 1
    normalized_headers = {key.lower(): value for key, value in headers.items()}
    edge_sha256 = normalized_headers.get("x-ordivon-sha256")
    local_sha256 = hashlib.sha256(body).hexdigest()
    if edge_sha256 is None:
        raise ClientError("Artifact response is missing X-Ordivon-Sha256")
    if edge_sha256 != local_sha256:
        raise ClientError("Artifact SHA-256 does not match the Edge metadata")
    if args.sha256 is not None and args.sha256.lower() != local_sha256:
        raise ClientError("Artifact SHA-256 does not match the expected Receipt digest")

    destination = pathlib.Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=destination.parent,
    )
    temporary = pathlib.Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb", closefd=True) as stream:
            stream.write(body)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
        os.chmod(destination, 0o600)
    except Exception:
        try:
            os.close(descriptor)
        except OSError:
            pass
        temporary.unlink(missing_ok=True)
        raise

    receipt = {
        "saved": str(destination),
        "bytes": len(body),
        "sha256": local_sha256,
        "edge_sha256": edge_sha256,
        "verified": True,
        "download_content_type": normalized_headers.get("content-type"),
        "media_type": normalized_headers.get("x-ordivon-media-type"),
    }
    print(json.dumps(receipt, indent=2))
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="ordivon-edge")
    root.add_argument(
        "--config",
        default=os.environ.get("ORDIVON_EDGE_CONFIG", str(DEFAULT_CONFIG)),
    )
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("health")
    commands.add_parser("capabilities")
    status = commands.add_parser("status")
    status.add_argument("--repo", default=".")
    status.add_argument("--expected-ref", default="HEAD")

    fetch = commands.add_parser("fetch")
    fetch.add_argument("url")
    fetch.add_argument("--maximum-bytes", type=int, default=262_144)
    fetch.add_argument("--timeout-ms", type=int, default=10_000)
    fetch.add_argument("--accept")
    fetch.add_argument("--request-id", default=make_request_id())

    browser = commands.add_parser("browser-run")
    browser.add_argument("url")
    browser.add_argument("--viewport-width", type=int, default=1365)
    browser.add_argument("--viewport-height", type=int, default=768)
    browser.add_argument("--full-page", action="store_true")
    browser.add_argument(
        "--wait-until",
        choices=("load", "domcontentloaded", "networkidle0", "networkidle2"),
        default="domcontentloaded",
    )
    browser.add_argument("--timeout-ms", type=int, default=15_000)
    browser.add_argument("--wait-after-ms", type=int, default=0)
    browser.add_argument("--request-id", default=make_request_id())

    receipt = commands.add_parser("receipt")
    receipt.add_argument("receipt_id")
    receipt.add_argument("--wait", action="store_true")
    receipt.add_argument("--timeout", type=float, default=120.0)
    receipt.add_argument("--interval", type=float, default=1.0)

    artifact = commands.add_parser("artifact-get")
    artifact.add_argument("key")
    artifact.add_argument("--output", required=True)
    artifact.add_argument("--sha256")
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        config = load_config(pathlib.Path(args.config).expanduser())
        if args.command == "health":
            return command_json(config, "/health")
        if args.command == "capabilities":
            return command_json(config, "/v1/capabilities")
        if args.command == "status":
            return command_status(config, args)
        if args.command == "fetch":
            return command_fetch(config, args)
        if args.command == "browser-run":
            return command_browser_run(config, args)
        if args.command == "receipt":
            if args.timeout <= 0 or args.interval <= 0:
                raise ClientError("receipt wait timeout and interval must be positive")
            return command_receipt(config, args)
        if args.command == "artifact-get":
            return command_artifact_get(config, args)
        raise ClientError(f"Unknown command: {args.command}")
    except ClientError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
