#!/usr/bin/env python3
"""Audit legacy cleanup records; native R2 lifecycle owns deferred deletion."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from typing import Any

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
    for candidate in (script_root, configured.resolve()):
        if (candidate / "wrangler.jsonc").is_file():
            return candidate
        nested = candidate / "providers" / "cloudflare"
        if (nested / "wrangler.jsonc").is_file():
            return nested
    return script_root


ROOT = resolve_provider_root()
BUCKET = "ordivon-artifacts"
CLEANUP_PREFIX = "cleanup/v2/"
CLOUDFLARE_CONFIG = pathlib.Path("/root/.config/ordivon/secrets/cloudflare.json")
RECEIPT_DIR = pathlib.Path("/root/backups/ordivon-world/cloudflare-gc")


class GarbageCollectionError(RuntimeError):
    pass


def load_cloudflare() -> tuple[str, str, dict[str, str]]:
    try:
        config = json.loads(CLOUDFLARE_CONFIG.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GarbageCollectionError("Cannot read Cloudflare configuration") from exc
    token = config.get("api_token")
    account_id = config.get("account_id")
    if not isinstance(token, str) or not token:
        raise GarbageCollectionError("Cloudflare API token is missing")
    if not isinstance(account_id, str) or not account_id:
        raise GarbageCollectionError("Cloudflare account ID is missing")
    environment = os.environ.copy()
    environment.update(
        {
            "CLOUDFLARE_API_TOKEN": token,
            "CLOUDFLARE_ACCOUNT_ID": account_id,
            "CI": "true",
        }
    )
    return token, account_id, environment


def api_json(token: str, url: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "User-Agent": "ordivon-edge-gc/0.1",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            value = json.loads(response.read())
    except Exception as exc:
        raise GarbageCollectionError(f"Cloudflare API request failed: {url}") from exc
    if not isinstance(value, dict) or value.get("success") is not True:
        raise GarbageCollectionError("Cloudflare API returned an unsuccessful response")
    return value


def cleanup_list_url(
    account_id: str,
    maximum: int,
    cursor: str | None = None,
) -> str:
    if maximum < 1:
        raise GarbageCollectionError("R2 object-list page size must be positive")
    query = {
        "prefix": CLEANUP_PREFIX,
        "per_page": str(min(1000, maximum)),
    }
    if cursor is not None:
        query["cursor"] = cursor
    return (
        "https://api.cloudflare.com/client/v4/accounts/"
        f"{urllib.parse.quote(account_id, safe='')}/r2/buckets/{BUCKET}/objects?"
        + urllib.parse.urlencode(query)
    )


def list_cleanup_keys(
    token: str,
    account_id: str,
    maximum: int,
) -> list[str]:
    keys: list[str] = []
    cursor: str | None = None
    while len(keys) < maximum:
        url = cleanup_list_url(account_id, maximum - len(keys), cursor)
        payload = api_json(token, url)
        result = payload.get("result")
        if isinstance(result, dict):
            objects = result.get("objects", [])
            truncated = result.get("truncated") is True
            next_cursor = result.get("cursor")
        elif isinstance(result, list):
            objects = result
            truncated = False
            next_cursor = None
        else:
            raise GarbageCollectionError("Unexpected R2 object-list response")
        for item in objects:
            if isinstance(item, dict) and isinstance(item.get("key"), str):
                keys.append(item["key"])
                if len(keys) >= maximum:
                    break
        if not truncated or not isinstance(next_cursor, str) or not next_cursor:
            break
        cursor = next_cursor
    return keys


def wrangler(
    environment: dict[str, str],
    arguments: list[str],
    *,
    capture: bool = False,
) -> subprocess.CompletedProcess[bytes]:
    completed = subprocess.run(
        ["pnpm", "exec", "wrangler", *arguments],
        cwd=ROOT,
        env=environment,
        check=False,
        stdout=subprocess.PIPE if capture else subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise GarbageCollectionError(
            f"Wrangler failed ({completed.returncode}): {' '.join(arguments)}"
            + (f"\n{detail}" if detail else "")
        )
    return completed


def get_task(environment: dict[str, str], key: str) -> dict[str, Any]:
    completed = wrangler(
        environment,
        ["r2", "object", "get", f"{BUCKET}/{key}", "--remote", "--pipe"],
        capture=True,
    )
    try:
        value = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise GarbageCollectionError(f"Cleanup task is invalid JSON: {key}") from exc
    if not isinstance(value, dict):
        raise GarbageCollectionError(f"Cleanup task must be a JSON object: {key}")
    return value


def validate_task(key: str, task: dict[str, Any]) -> list[str]:
    request_id = task.get("request_id")
    generation = task.get("lease_generation")
    operation = task.get("operation")
    reason = task.get("reason")
    artifact_keys = task.get("artifact_keys")
    if type(task.get("schema_version")) is not int or task["schema_version"] != 1:
        raise GarbageCollectionError(f"Unsupported cleanup schema: {key}")
    if not isinstance(request_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{7,63}", request_id):
        raise GarbageCollectionError(f"Cleanup task has invalid Request ID: {key}")
    if type(generation) is not int or not 1 <= generation <= 2**53 - 1:
        raise GarbageCollectionError(f"Cleanup task has invalid generation: {key}")
    if key != f"{CLEANUP_PREFIX}{request_id}/g{generation}.json":
        raise GarbageCollectionError(f"Cleanup key does not bind Request ID and generation: {key}")
    if operation == "fetch":
        prefix = f"fetch/v2/{request_id}/g{generation}/"
        names = {"body"}
    elif operation == "browser.run":
        prefix = f"browser/v2/{request_id}/g{generation}/"
        names = {"screenshot.png", "content.html", "manifest.json"}
    else:
        raise GarbageCollectionError(f"Cleanup task has invalid operation: {key}")
    if not isinstance(reason, str) or not reason or len(reason) > 128:
        raise GarbageCollectionError(f"Cleanup task has invalid reason: {key}")
    if (
        not isinstance(artifact_keys, list)
        or not 1 <= len(artifact_keys) <= 16
        or not all(isinstance(item, str) and item.startswith(prefix) for item in artifact_keys)
    ):
        raise GarbageCollectionError(f"Cleanup task has invalid Artifact keys: {key}")
    bundles = set()
    for item in artifact_keys:
        parts = item[len(prefix):].split("/")
        if len(parts) == 1 and parts[0] in names:
            bundles.add(None)  # legacy generation-only record
        elif (
            len(parts) == 2
            and re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}", parts[0])
            and parts[1] in names
        ):
            bundles.add(parts[0])
        else:
            raise GarbageCollectionError(f"Cleanup task has invalid Artifact keys: {key}")
    if len(bundles) != 1:
        raise GarbageCollectionError(f"Cleanup task mixes Artifact bundles: {key}")
    return list(dict.fromkeys(artifact_keys))


def write_receipt(report: dict[str, Any]) -> pathlib.Path:
    RECEIPT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    path = RECEIPT_DIR / f"gc-{stamp}.json"
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)
    os.chmod(path, 0o600)
    return path


def main() -> int:
    parser = argparse.ArgumentParser(prog="ordivon-edge-gc")
    parser.add_argument("--dry-run", action="store_true", help="compatibility flag; both modes only audit remote objects")
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()
    if args.limit < 1 or args.limit > 1000:
        parser.error("--limit must be between 1 and 1000")

    try:
        token, account_id, environment = load_cloudflare()
        task_keys = list_cleanup_keys(token, account_id, args.limit)
        deferred: list[dict[str, Any]] = []
        failed: list[dict[str, str]] = []
        for task_key in task_keys:
            try:
                task = get_task(environment, task_key)
                artifact_keys = validate_task(task_key, task)
                # A v1 record is not a fenced delete authorization. Even a
                # current read cannot atomically bind another object's deletion.
                # Existing R2 expiration rules bound deferred storage instead.
                deferred.append(
                    {
                        "task_key": task_key,
                        "artifact_keys": artifact_keys,
                        "reason": task["reason"],
                        "disposition": "native_retention",
                        "dry_run": args.dry_run,
                    }
                )
            except Exception as exc:
                failed.append({"task_key": task_key, "error": str(exc)})

        report = {
            "status": "completed_with_failures" if failed else ("completed_with_deferred" if deferred else "completed"),
            "completed_at": dt.datetime.now(dt.UTC).isoformat(),
            "dry_run": args.dry_run,
            "scanned": len(task_keys),
            "completed": [],
            "deferred": deferred,
            "mode": "audit_only",
            "failed": failed,
        }
        receipt = write_receipt(report)
        print(json.dumps({"ok": not failed, "receipt": str(receipt), **report}, indent=2))
        return 0 if not failed else 1
    except GarbageCollectionError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
