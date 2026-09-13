#!/usr/bin/env python3
"""Apply Ordivon Edge R2 lifecycle rules through the Cloudflare API."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import urllib.error
import urllib.request
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parent.parent
BUCKET = "ordivon-artifacts"
CLOUDFLARE_CONFIG = pathlib.Path("/root/.config/ordivon/secrets/cloudflare.json")
SOURCE_POLICY_CONFIG = ROOT / "config" / "edge-policy.json"
INSTALLED_POLICY_CONFIG = pathlib.Path("/usr/local/lib/ordivon-operations/cloudflare-provider/edge-policy.json")
POLICY_CONFIG = pathlib.Path(
    os.environ.get(
        "ORDIVON_EDGE_POLICY",
        str(SOURCE_POLICY_CONFIG if SOURCE_POLICY_CONFIG.is_file() else INSTALLED_POLICY_CONFIG),
    )
)
MANAGED_PREFIX = "edge-v2-"
SECONDS_PER_DAY = 86400


class LifecycleError(RuntimeError):
    pass


def load_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LifecycleError(f"Cannot read configuration: {path}") from exc
    if not isinstance(value, dict):
        raise LifecycleError(f"Configuration must be an object: {path}")
    return value


def api_request(method: str, path: str, token: str, body: dict[str, Any] | None = None) -> Any:
    encoded = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        f"https://api.cloudflare.com/client/v4{path}",
        data=encoded,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "ordivon-edge-lifecycle/0.1",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read())
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as exc:
        raise LifecycleError(f"Cloudflare lifecycle request failed: {method} {path}") from exc
    if not isinstance(payload, dict) or payload.get("success") is not True:
        raise LifecycleError(f"Cloudflare lifecycle request returned failure: {payload}")
    return payload.get("result")


def managed_rules(retention: dict[str, int]) -> list[dict[str, Any]]:
    definitions = [
        ("request-state", "requests/v2/", retention["request_state"]),
        ("receipt-mirror", "receipts/v2/", retention["receipt_mirror"]),
        ("fetch-artifacts", "fetch/v2/", retention["artifacts"]),
        ("browser-artifacts", "browser/v2/", retention["artifacts"]),
        ("cleanup-tasks", "cleanup/v2/", retention["cleanup_tasks"]),
    ]
    return [
        {
            "id": f"{MANAGED_PREFIX}{name}-{days}d",
            "enabled": True,
            "conditions": {"prefix": prefix},
            "deleteObjectsTransition": {
                "condition": {"type": "Age", "maxAge": days * SECONDS_PER_DAY}
            },
        }
        for name, prefix, days in definitions
    ]


def _managed_subset(rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        (rule for rule in rules if str(rule.get("id", "")).startswith(MANAGED_PREFIX)),
        key=lambda rule: str(rule.get("id")),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="read current lifecycle state and compare it with policy without mutating it",
    )
    args = parser.parse_args(argv)

    cloudflare = load_json(CLOUDFLARE_CONFIG)
    policy = load_json(POLICY_CONFIG)
    token = cloudflare.get("api_token")
    account_id = cloudflare.get("account_id")
    retention = policy.get("retention_days")
    if not isinstance(token, str) or not isinstance(account_id, str):
        raise LifecycleError("Cloudflare credentials are incomplete")
    if not isinstance(retention, dict):
        raise LifecycleError("Retention policy is missing")
    path = f"/accounts/{account_id}/r2/buckets/{BUCKET}/lifecycle"
    current = api_request("GET", path, token)
    rules = current.get("rules") if isinstance(current, dict) else None
    if not isinstance(rules, list):
        raise LifecycleError("Cloudflare lifecycle response has no rules")

    expected_managed = managed_rules(retention)
    expected_sorted = sorted(expected_managed, key=lambda rule: str(rule.get("id")))
    actual_managed = _managed_subset(rules)
    if args.check:
        healthy = actual_managed == expected_sorted
        print(
            json.dumps(
                {
                    "ok": healthy,
                    "bucket": BUCKET,
                    "expected": expected_sorted,
                    "actual": actual_managed,
                },
                indent=2,
            )
        )
        return 0 if healthy else 1

    preserved = [
        rule
        for rule in rules
        if isinstance(rule, dict) and not str(rule.get("id", "")).startswith(MANAGED_PREFIX)
    ]
    api_request("PUT", path, token, {"rules": [*preserved, *expected_managed]})
    verified = api_request("GET", path, token)
    verified_rules = verified.get("rules") if isinstance(verified, dict) else None
    if not isinstance(verified_rules, list):
        raise LifecycleError("Updated lifecycle response has no rules")
    actual_managed = _managed_subset(verified_rules)
    if actual_managed != expected_sorted:
        raise LifecycleError("Lifecycle verification did not match the policy")
    print(json.dumps({"ok": True, "bucket": BUCKET, "rules": verified_rules}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
