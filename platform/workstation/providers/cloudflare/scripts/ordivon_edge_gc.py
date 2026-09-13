#!/usr/bin/env python3
"""Retry bounded Artifact cleanup tasks stored in private R2."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import subprocess
import sys
import urllib.parse
import urllib.request
from typing import Any

SCRIPT_PATH = pathlib.Path(__file__).resolve()
DEFAULT_PROVIDER_REPOSITORY = pathlib.Path("/root/projects/ordivon-operations-v2/providers/cloudflare")


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
    if not key.startswith(CLEANUP_PREFIX) or not key.endswith(".json"):
        raise GarbageCollectionError(f"Cleanup key is outside the allowed prefix: {key}")
    if task.get("schema_version") != 1:
        raise GarbageCollectionError(f"Unsupported cleanup schema: {key}")
    request_id = task.get("request_id")
    generation = task.get("lease_generation")
    artifact_keys = task.get("artifact_keys")
    if not isinstance(request_id, str) or not request_id:
        raise GarbageCollectionError(f"Cleanup task has no Request ID: {key}")
    if not isinstance(generation, int) or generation < 1:
        raise GarbageCollectionError(f"Cleanup task has invalid generation: {key}")
    if (
        not isinstance(artifact_keys, list)
        or not artifact_keys
        or len(artifact_keys) > 16
        or not all(isinstance(item, str) for item in artifact_keys)
    ):
        raise GarbageCollectionError(f"Cleanup task has invalid Artifact keys: {key}")

    generation_segment = f"/g{generation}/"
    allowed_prefixes = (
        f"fetch/v2/{request_id}/",
        f"browser/v2/{request_id}/",
    )
    for artifact_key in artifact_keys:
        if (
            not artifact_key.startswith(allowed_prefixes)
            or generation_segment not in artifact_key
            or ".." in artifact_key
            or "\\" in artifact_key
        ):
            raise GarbageCollectionError(
                f"Cleanup task attempts an out-of-scope deletion: {artifact_key}"
            )
    return list(dict.fromkeys(artifact_keys))


def delete_object(environment: dict[str, str], key: str) -> None:
    wrangler(
        environment,
        [
            "r2",
            "object",
            "delete",
            f"{BUCKET}/{key}",
            "--remote",
            "--force",
        ],
    )


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
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()
    if args.limit < 1 or args.limit > 1000:
        parser.error("--limit must be between 1 and 1000")

    try:
        token, account_id, environment = load_cloudflare()
        task_keys = list_cleanup_keys(token, account_id, args.limit)
        completed: list[dict[str, Any]] = []
        failed: list[dict[str, str]] = []
        for task_key in task_keys:
            try:
                task = get_task(environment, task_key)
                artifact_keys = validate_task(task_key, task)
                if not args.dry_run:
                    for artifact_key in artifact_keys:
                        delete_object(environment, artifact_key)
                    delete_object(environment, task_key)
                completed.append(
                    {
                        "task_key": task_key,
                        "artifact_keys": artifact_keys,
                        "dry_run": args.dry_run,
                    }
                )
            except Exception as exc:
                failed.append({"task_key": task_key, "error": str(exc)})

        report = {
            "status": "completed" if not failed else "completed_with_failures",
            "completed_at": dt.datetime.now(dt.UTC).isoformat(),
            "dry_run": args.dry_run,
            "scanned": len(task_keys),
            "completed": completed,
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
